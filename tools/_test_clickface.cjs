// 冒烟测试（v6）：把打过补丁的 clickface 代码块抽出来，在 Node 里用桩环境跑一遍状态机
// 用法: node _test_clickface.cjs [whale-widget.js 路径]
const fs = require('fs')
const wf = process.argv[2] || 'C:\\Users\\李唯佳\\.dsh\\profiles\\desktop\\node_modules\\dsh-whale-widget\\assets\\whale-widget.js'
const lines = fs.readFileSync(wf, 'utf8').split('\n')
const start = lines.findIndex((l) => /\/\* dshwv-clickface-patch v\d+ \*\//.test(l))
const endIdx = lines.findIndex((l, i) => i > start && l.trim() === 'var roleList = []')
if (start < 0 || endIdx < 0) { console.log('FAIL: 找不到补丁块 start=' + start + ' end=' + endIdx); process.exit(1) }
const block = lines.slice(start, endIdx).join('\n')
console.log('补丁块行数: ' + (endIdx - start) + ' (line ' + (start + 1) + '-' + endIdx + ')')

const log = []
function stubEl() {
  const attrs = {}
  return {
    id: '', textContent: '', style: {}, src: '',
    classList: { add: (c) => log.push('class+ ' + c), remove: (c) => log.push('class- ' + c) },
    getAttribute: (k) => (k in attrs ? attrs[k] : null),
    setAttribute: (k, v) => { attrs[k] = v },
  }
}
const img = stubEl()
const handlers = {}
const pollRef = { fn: null }
const sandbox = {
  img,
  IMG_URL: '/dsh-whale/image.png',
  currentRole: { id: 'state0', url: '/dsh-whale/image.png' },
  soundOn: true, soundVol: 0.9,
  root: { contains: (t) => !!(t && t.__inWidget) },
  __handlers: handlers,
  __pollRef: pollRef,
  document: {
    head: { appendChild: () => {} },
    createElement: () => stubEl(),
    querySelector: () => null,
    querySelectorAll: () => [],
    addEventListener: (type, fn) => { (handlers[type] = handlers[type] || []).push(fn) },
  },
  Image: function () { return {} },
  setupHitTest: (u) => log.push('setupHitTest ' + u),
  dshwvSound: (u) => { log.push('audio.play ' + u); return { volume: 1, play: () => ({ catch: () => {} }), pause: () => log.push('audio.pause') } },
  dshwvWarm: () => {},
  pressDown: () => log.push('pressDown(orig)'),
  pressUp: () => log.push('pressUp(orig)'),
  playTaskEndSound: () => log.push('playTaskEndSound(orig)'),
  setTimeout, clearTimeout, Date, Math, String, Number, Array, Object, encodeURIComponent, console,
  setInterval: (fn) => { pollRef.fn = fn; return 1 },
  clearInterval: () => {},
}
const names = Object.keys(sandbox)
const fn = new Function(...names, block + `
  return { CLICKFACE, clickFaceSwap, clickFaceThinking, clickFaceTyping, clickFaceReturn, clickFaceShow, clickFaceMarkSend,
           clickFaceMarkTyping, pressDown, pressUp, playTaskEndSound, clickFaceRoleUrl, clickFaceDraw,
           clickFaceVisibleRoles, clickFaceProtectedRole,
           fire: function (type, target) { var hs = __handlers[type] || []; for (var i = 0; i < hs.length; i++) hs[i]({ target: target, key: target && target.__key, ctrlKey: false, altKey: false, metaKey: false, isComposing: false }) },
           poll: function () { if (__pollRef.fn) __pollRef.fn() },
           state: () => ({ shown: clickFaceShown, src: img.src, hold: clickFaceHold, flash: clickFaceFlash, sendTs: clickFaceSendTs, typing: clickFaceTypingUntil }) }
`)
let api
try { api = fn(...names.map((n) => sandbox[n])) } catch (e) { console.log('FAIL 装载补丁块: ' + e.message); process.exit(1) }
console.log('装载 OK')

function show(tag) { const s = api.state(); console.log(tag + ' -> shown=' + (s.shown || '(base)') + ' src=' + s.src + ' hold=' + s.hold + ' flash=' + s.flash) }
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const ok = (cond, what) => console.log((cond ? 'PASS ' : 'FAIL ') + what)

async function main() {
  show('初始')
  api.clickFaceSwap(); show('第1次点击(期望 state1)')
  api.clickFaceReturn(); show('点击态结束、未思考(期望 base state0)')
  api.clickFaceSwap(); show('第2次点击(期望 state2)')
  api.clickFaceReturn(); show('再次结束(期望 base)')
  api.clickFaceMarkSend(); console.log('clickFaceThinking() 发消息后 = ' + api.clickFaceThinking() + ' (期望 true)')
  api.clickFaceShow(api.CLICKFACE.idle); api.clickFaceReturn(); show('思考中结束点击态(期望 state3)')
  api.playTaskEndSound(); show('任务结束(期望 state4, flash=true)')
  console.log('结束后 clickFaceThinking() = ' + api.clickFaceThinking() + ' (期望 false)')
  api.clickFaceReturn(); show('完成态结束(期望 base state0)')

  console.log('--- v6 打字态（叉腰指点 state5）---')
  api.fire('input', { tagName: 'TEXTAREA', isContentEditable: false })
  show('输入框 input(期望 state5)')
  ok(api.state().shown === 'state5', 'input → state5')
  api.poll(); show('打字期间轮询(应保持 state5)')
  ok(api.state().shown === 'state5', '打字期间不被轮询切走')
  api.fire('input', { tagName: 'DIV', isContentEditable: true, __inWidget: true })
  console.log('挂件自己面板里的输入 -> typingUntil 仍为 ' + api.state().typing + '（不新增）')
  await sleep(1000)
  console.log('停止输入 1s 后 clickFaceTyping() = ' + api.clickFaceTyping() + ' (期望 false)')
  api.poll(); show('停手后轮询(期望 base state0)')
  ok(api.state().shown === 'state0', '停手 → 回 state0')
  api.fire('keydown', { tagName: 'TEXTAREA', isContentEditable: false, __key: 'a' })
  show('可打印键 keydown(期望 state5)')
  api.clickFaceMarkSend(); console.log('发消息后 clickFaceTyping() = ' + api.clickFaceTyping() + ' (期望 false)')
  api.poll(); show('发消息后轮询(期望 state3)')
  ok(api.state().shown === 'state3', '发消息 → 思考态 state3')

  console.log('--- v5 白名单/保护 ---')
  const allRoles = [{ id: 'default' }, { id: 'state0' }, { id: 'state1' }, { id: 'state2' }, { id: 'state3' }, { id: 'state4' }, { id: 'state5' }]
  console.log('可见角色 = ' + JSON.stringify(api.clickFaceVisibleRoles(allRoles).map((r) => r.id)) + ' (期望 ["default","state0"])')
  console.log('受保护 state0/state3/state5/default = ' + api.clickFaceProtectedRole('state0') + '/' + api.clickFaceProtectedRole('state3') + '/' + api.clickFaceProtectedRole('state5') + '/' + api.clickFaceProtectedRole('default') + ' (期望 true/true/true/false)')
  console.log('--- 调用轨迹（尾部 12 条）---')
  console.log(log.slice(-12).join('\n'))
  process.exit(0)
}
main()
