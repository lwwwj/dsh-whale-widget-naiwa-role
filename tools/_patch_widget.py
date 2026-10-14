# -*- coding: utf-8 -*-
"""给 dsh-whale-widget 客户端打「五状态形象机」补丁（幂等：已打过则跳过）。
用法: python _patch_widget.py [--revert] [--client <whale-widget.js 的完整路径>]
      不传 --client 时，自动在 $DSH_HOME（默认 %USERPROFILE%\\.dsh）下所有 profile 里查找插件并逐个处理。

v4（按用户 2026-10-08 20:30 的需求重写）：
  · state0 = 初始形象（黄色生物，站立）
  · 点击一次 → state1 + 奶蛙笑声音效，2.5s 后回 state0
  · 再点一次 → state2 + 安迪（不知火舞）音效，1s 后回 state0（两次点击来回交替）
  · DSH 处于思考/生成中 → state3（点击行为同上，点击态结束后仍回到 state3）
  · 每轮任务结束（宿主 last-turn.json 的 seq 增加，即插件播任务结束音那一刻）→ state4，1s 后回 state0
  · 仍保留：屏蔽插件自带按压/松开音（只在点击挂件这条路径上临时关 soundOn）、点击态轻微抖动
  · 命中剪裁不再用固定凸包：每次换图都调插件自己的 setupHitTest(url)，按该图自身轮廓重算 clip-path 与命中画布

v5（2026-10-08 21:0x，按用户「角色形象选择只用一个」）：
  · CLICKFACE.showRoles = ['default', 'state0'] —— 角色面板与「资源管理」里的角色列表只显示
    「奶蛙」与插件自带的小鲸鱼两条，其余 4 张状态图仍留在 roles.json 里
    （/dsh-whale/role-image.png?id=… 要用），只是不进选择列表；
  · A8/A9：形象机在用的角色不允许在界面里删除（误点会弹提示）。

v6（2026-10-09 13:0x，按用户「打字时出现叉腰指点的图片」）：
  · CLICKFACE.typing = 'state5'（叉腰指点），typingIdleMs = 900；
  · 在输入框里打字（input / compositionupdate / paste / 可打印键 keydown，且不在挂件自己的
    面板里）→ 立刻换成 state5；停止输入 900ms 后由 500ms 轮询切回思考态或初始形象；
  · 状态优先级：点击态(1/2) / 完成态(4) > 打字态(5) > 思考态(3) > 初始形象(0)；
  · 消息一发出去（Enter / 点发送）就清掉打字态，让思考态接管。

v7（2026-10-14，按用户「把奶龙角色改名为奶蛙」）：
  · 所有**显示名**改成「奶蛙」（角色名、音效名、删除保护提示里的称呼）；
  · 技术 id 保持不动（state0..5 / nailong_laugh / andi）—— 这些是 URL 与磁盘文件名的一部分，
    改了两边不同步就会静音 / 断图。
"""
import os
import shutil
import sys

MARK = "/* dshwv-clickface-patch v7 */"
CLIENT = ""  # 运行时解析，见 resolve_targets()


def resolve_targets():
    """找出所有装了这个插件的 profile 里的 whale-widget.js。

    优先级：命令行 --client <路径> > $DSH_HOME/profiles/*/node_modules/dsh-whale-widget >
    %USERPROFILE%\\.dsh\\profiles/*/... （DSH_HOME 未设置时的默认位置）。
    """
    for i, a in enumerate(sys.argv):
        if a == "--client" and i + 1 < len(sys.argv):
            return [sys.argv[i + 1]]
    home = os.environ.get("DSH_HOME") or os.path.join(
        os.environ.get("USERPROFILE") or os.path.expanduser("~"), ".dsh")
    prof_root = os.path.join(home, "profiles")
    cands = []
    if os.path.isdir(prof_root):
        for name in sorted(os.listdir(prof_root)):
            p = os.path.join(prof_root, name, "node_modules", "dsh-whale-widget", "assets", "whale-widget.js")
            if os.path.isfile(p) and p not in cands:
                cands.append(p)
    if not cands:
        cands.append(os.path.join(prof_root, "desktop", "node_modules", "dsh-whale-widget", "assets", "whale-widget.js"))
    return cands

A1_OLD = "var currentRole = { id: 'default', name: '小鲸鱼', url: IMG_URL }"
A1_NEW = A1_OLD + "\n" + MARK + r"""

// ===== 补丁：六状态形象机（0 初始 / 1 大笑 / 2 安迪 / 3 思考 / 4 完成 / 5 打字-叉腰指点）=====
var CLICKFACE = {
  autoRole: 'state0',     // 浏览器没有角色选择记录时自动选中的角色
  idle: 'state0',         // 静止态
  thinking: 'state3',     // DSH 思考/生成中
  typing: 'state5',       // 用户正在输入框里打字（叉腰指点）
  typingIdleMs: 900,      // 最后一次输入之后多久离开打字态
  done: 'state4',         // 每轮任务结束
  doneMs: 1000,           // 完成态持续时长
  shake: true,            // 点击态轻微抖动
  volume: 0.95,
  // 角色选择列表的白名单（v5）：只让「奶蛙(初始形象)」与插件自带的小鲸鱼出现在「角色」面板与
  // 资源管理里；其余状态图（state1..4）不列出来 —— 它们仍然在 roles.json 里，补丁按 URL 直接换图。
  showRoles: ['default', 'state0'],
  // 点击按顺序循环：奶蛙大笑(2.5s) → 安迪(1s)
  clicks: [
    { state: 'state1', ms: 2500, voice: { url: '/dsh-whale/audio-fragment.wav?id=nailong_laugh', maxMs: 2600, name: '奶蛙笑声' } },
    { state: 'state2', ms: 1000, voice: { url: '/dsh-whale/audio-fragment.wav?id=andi', maxMs: 1600, name: '安迪' } }
  ],
}
var clickFaceTimer = null
var clickFaceStopTimer = null
var clickFaceShakeTimer = null
var clickFaceAudio = null
var clickFaceClickIdx = 0
var clickFaceHold = false    // 正在显示点击态(1/2)
var clickFaceFlash = false   // 正在显示完成态(4)
var clickFaceShown = ''      // 当前显示的补丁状态 id（''= 没接管）
function clickFaceRoleUrl(id) { return '/dsh-whale/role-image.png?id=' + encodeURIComponent(id) }
// 是否是形象机正在用的角色（这些不允许在界面里删除，删了形象机就废了）
function clickFaceProtectedRole(id) {
  try {
    if (!id) return false
    if (id === CLICKFACE.idle || id === CLICKFACE.thinking || id === CLICKFACE.done || id === CLICKFACE.typing) return true
    var cs = CLICKFACE.clicks || []
    for (var i = 0; i < cs.length; i++) if (cs[i].state === id) return true
  } catch (err) {}
  return false
}
// 角色列表白名单过滤（v5）：角色面板、资源管理里的角色列表都走这里，只留 CLICKFACE.showRoles 里的角色。
function clickFaceVisibleRoles(list) {
  try {
    var show = CLICKFACE.showRoles
    if (!show || !show.length) return list || []
    return (list || []).filter(function (r) { return r && show.indexOf(r.id) >= 0 })
  } catch (err) { return list || [] }
}
// 只在这个角色被选中时接管（避免干扰用户自己挑的其它角色）
function clickFaceCfg() {
  try { return !!(currentRole && currentRole.id === CLICKFACE.idle) } catch (err) { return false }
}
function clickFaceShake(on) {
  try { if (on) img.classList.add('dshwv-clickface-shake'); else img.classList.remove('dshwv-clickface-shake') } catch (err) {}
}
// 抖动关键帧（只注入一次；不动 img 的内联 transform，避免跟插件自己的变换打架）
try {
  var _cfStyle = document.createElement('style')
  _cfStyle.id = 'dshwv-clickface-style'
  _cfStyle.textContent =
    '@keyframes dshwvClickFaceShake{' +
    '0%{transform:translateY(0) rotate(-1.5deg) scale(1)}' +
    '100%{transform:translateY(-3px) rotate(1.5deg) scale(1.03)}}' +
    '.dshwv-img.dshwv-clickface-shake{animation:dshwvClickFaceShake .22s ease-in-out infinite alternate;transform-origin:50% 100%;will-change:transform}'
  document.head.appendChild(_cfStyle)
} catch (err) {}
// 换图 + 用插件自己的 setupHitTest 重算该图轮廓（命中画布与 clip-path 都会跟着换）
function clickFaceDraw(id, url) {
  try {
    if (!url) url = clickFaceRoleUrl(id)
    clickFaceShown = id || ''
    if (img.getAttribute('data-cf-src') === url) return
    img.setAttribute('data-cf-src', url)
    img.src = url
    try { if (typeof setupHitTest === 'function') setupHitTest(url) } catch (err) {}
  } catch (err) {}
}
function clickFaceBase() {
  try { return { id: (currentRole && currentRole.id) || 'default', url: (currentRole && currentRole.url) || IMG_URL } }
  catch (err) { return { id: 'default', url: IMG_URL } }
}
function clickFaceShow(id, ms) {
  clickFaceDraw(id)
  if (clickFaceTimer) { clearTimeout(clickFaceTimer); clickFaceTimer = null }
  if (Number(ms) > 0) {
    clickFaceTimer = setTimeout(function () { clickFaceTimer = null; clickFaceReturn() }, Math.max(200, Number(ms)))
  }
}
// 回到「该显示的东西」：还在思考 → state3；否则基础形象
function clickFaceReturn() {
  clickFaceHold = false
  clickFaceFlash = false
  if (clickFaceTyping()) { clickFaceShow(CLICKFACE.typing, 0); return }
  if (clickFaceCfg() && clickFaceThinking()) { clickFaceShow(CLICKFACE.thinking, 0); return }
  var b = clickFaceBase()
  clickFaceDraw(b.id, b.url)
}
function playClickFaceSound(url, vol, maxMs) {
  try {
    if (!url || !soundOn) return
    if (clickFaceAudio) { try { clickFaceAudio.pause() } catch (err) {} clickFaceAudio = null }
    if (clickFaceStopTimer) { clearTimeout(clickFaceStopTimer); clickFaceStopTimer = null }
    if (typeof dshwvWarm === 'function') { try { dshwvWarm([url]) } catch (err) {} }
    var a = dshwvSound(url)
    a.volume = Math.max(0, Math.min(1, typeof vol === 'number' ? vol : soundVol))
    var p = a.play()
    if (p && typeof p.catch === 'function') p.catch(function () {})
    clickFaceAudio = a
    var lim = Number(maxMs) || 0
    if (lim > 0) {
      clickFaceStopTimer = setTimeout(function () {
        clickFaceStopTimer = null
        try { if (clickFaceAudio === a) a.pause() } catch (err) {}
      }, lim)
    }
  } catch (err) {}
}
// DSH 是否在思考/生成：① 前端自己的状态标记 ② 刚发出消息（发出去就当作在做任务，直到本轮结束）
var clickFaceSendTs = 0
// v6：用户正在输入框里打字的截止时刻（打字 → 叉腰指点 state5）
var clickFaceTypingUntil = 0
function clickFaceMarkSend() { clickFaceSendTs = Date.now(); clickFaceTypingUntil = 0 }
function clickFaceTyping() {
  try { return !!(CLICKFACE.typing && clickFaceTypingUntil && Date.now() < clickFaceTypingUntil) } catch (err) { return false }
}
// 打字时立刻换成「叉腰指点」；停手后交给 500ms 轮询切回思考态/初始形象
function clickFaceMarkTyping() {
  try {
    if (!CLICKFACE.typing || !clickFaceCfg()) return
    clickFaceTypingUntil = Date.now() + Math.max(200, Number(CLICKFACE.typingIdleMs) || 900)
    if (clickFaceHold || clickFaceFlash) return
    if (clickFaceShown !== CLICKFACE.typing) clickFaceShow(CLICKFACE.typing, 0)
  } catch (err) {}
}
function clickFaceThinking() {
  try {
    if (document.querySelector('[data-state="ongoing"]')) return true
    if (document.querySelector('[data-shimmer]')) return true
    if (document.querySelector('[data-running]')) return true
    var bs = document.querySelectorAll('button')
    for (var i = 0; i < bs.length; i++) {
      var b = bs[i]
      var lab = String(b.getAttribute('aria-label') || '') + ' ' + String(b.title || '') + ' ' + String(b.getAttribute('data-testid') || '')
      if (/停止|中断|stop generating|stopGenerating/i.test(lab)) return true
    }
  } catch (err) {}
  // 兜底信号：用户刚把话发出去（Enter 或点发送按钮）⇒ 在下一轮任务结束前都算「思考中」。
  // 上限 30 分钟，避免某次没发出去/没收到轮次结束信号时永远停在 state3。
  try { if (clickFaceSendTs && Date.now() - clickFaceSendTs < 30 * 60 * 1000) return true } catch (err) {}
  return false
}
// 听「用户发出消息」：输入框里回车（不带修饰键）或点发送按钮
try {
  document.addEventListener('keydown', function (e) {
    try {
      if (e.key !== 'Enter' || e.shiftKey || e.ctrlKey || e.altKey || e.metaKey) return
      var t = e.target
      if (!t) return
      var tag = String(t.tagName || '').toLowerCase()
      if (tag !== 'textarea' && !t.isContentEditable) return
      clickFaceMarkSend()
    } catch (err) {}
  }, true)
  document.addEventListener('click', function (e) {
    try {
      var el = e.target
      var b = el && el.closest ? el.closest('button') : null
      if (!b) return
      var lab = String(b.getAttribute('aria-label') || '') + ' ' + String(b.title || '')
      if (/发送|提交|send/i.test(lab)) clickFaceMarkSend()
    } catch (err) {}
  }, true)
  // v6：输入框里打字 → 打字态。只认「不是挂件自己面板」里的 textarea / contenteditable。
  var _cfIsComposer = function (t) {
    try {
      if (!t) return false
      var tag = String(t.tagName || '').toLowerCase()
      if (tag !== 'textarea' && !t.isContentEditable) return false
      if (typeof root !== 'undefined' && root && root.contains && root.contains(t)) return false
      return true
    } catch (err) { return false }
  }
  document.addEventListener('input', function (e) { if (_cfIsComposer(e.target)) clickFaceMarkTyping() }, true)
  document.addEventListener('compositionupdate', function (e) { if (_cfIsComposer(e.target)) clickFaceMarkTyping() }, true)
  document.addEventListener('paste', function (e) { if (_cfIsComposer(e.target)) clickFaceMarkTyping() }, true)
  document.addEventListener('keydown', function (e) {
    try {
      if (e.ctrlKey || e.altKey || e.metaKey || e.isComposing) return
      if (e.key && e.key.length === 1 && _cfIsComposer(e.target)) clickFaceMarkTyping()
    } catch (err) {}
  }, true)
} catch (err) {}
// 点击 → 交替切 1/2 + 对应语音
function clickFaceSwap() {
  try {
    if (!clickFaceCfg()) return
    var list = CLICKFACE.clicks || []
    if (!list.length) return
    var c = list[clickFaceClickIdx % list.length]
    clickFaceClickIdx++
    clickFaceHold = true
    clickFaceFlash = false
    var ms = Math.max(200, Number(c.ms) || 1000)
    clickFaceShow(c.state, ms)
    if (CLICKFACE.shake) {
      clickFaceShake(true)
      if (clickFaceShakeTimer) { clearTimeout(clickFaceShakeTimer); clickFaceShakeTimer = null }
      clickFaceShakeTimer = setTimeout(function () { clickFaceShakeTimer = null; clickFaceShake(false) }, ms)
    }
    if (c.voice) playClickFaceSound(c.voice.url, CLICKFACE.volume, c.voice.maxMs)
  } catch (err) {}
}
// —— 不播插件自带的按压/松开音：只在「点击挂件」这条路径上临时把 soundOn 关掉。
// playPress/playRelease/playReleaseAt 三个函数都在开头 `if (!soundOn) return`，所以这样最省事，
// 又不会影响菜单里的音效试听、任务结束音、待答提示音。按下时的挤压动画照旧（在 soundOn 判断之后）。
var _cfPressDown = pressDown
var _cfPressUp = pressUp
pressDown = function () {
  if (clickFaceCfg()) {
    var saveOn = soundOn
    soundOn = false
    try { return _cfPressDown() } finally { soundOn = saveOn }
  }
  return _cfPressDown()
}
pressUp = function () {
  if (clickFaceCfg()) {
    var saveOn2 = soundOn
    soundOn = false
    try { return _cfPressUp() } finally { soundOn = saveOn2 }
  }
  return _cfPressUp()
}
// —— 每轮任务结束（宿主 seq 增加、插件播任务结束音的那一刻）→ state4 一秒
var _cfPlayTaskEnd = playTaskEndSound
playTaskEndSound = function () {
  try {
    if (clickFaceCfg()) {
      clickFaceSendTs = 0        // 本轮结束：清掉「刚发出消息」的兜底思考信号
      clickFaceHold = false
      clickFaceFlash = true
      clickFaceShow(CLICKFACE.done, Math.max(200, Number(CLICKFACE.doneMs) || 1000))
    }
  } catch (err) {}
  return _cfPlayTaskEnd.apply(this, arguments)
}
// —— 思考态轮询（插件自己已有 1s 的轮询，这里另起一个 500ms 的专职看形象）
setInterval(function () {
  try {
    if (!clickFaceCfg()) return
    if (clickFaceHold || clickFaceFlash) return
    // v6：打字优先于思考（正在打字说明这一轮已经结束、用户在写下一句）
    if (clickFaceTyping()) {
      if (clickFaceShown !== CLICKFACE.typing) clickFaceShow(CLICKFACE.typing, 0)
      return
    }
    var th = clickFaceThinking()
    if (th) {
      if (clickFaceShown !== CLICKFACE.thinking) clickFaceShow(CLICKFACE.thinking, 0)
    } else if (clickFaceShown) {
      clickFaceReturn()
    }
  } catch (err) {}
}, 500)
// 预取三张常用状态图 + 预热两条语音，避免第一次点击闪空白
try {
  var _cfPreIds = [CLICKFACE.thinking, CLICKFACE.typing, CLICKFACE.done]
  for (var _pi = 0; _pi < _cfPreIds.length; _pi++) { var _pimg = new Image(); _pimg.src = clickFaceRoleUrl(_cfPreIds[_pi]) }
  for (var _ci = 0; _ci < (CLICKFACE.clicks || []).length; _ci++) { var _cimg = new Image(); _cimg.src = clickFaceRoleUrl(CLICKFACE.clicks[_ci].state) }
} catch (err) {}
try {
  var _cfWarm = []
  for (var _vi = 0; _vi < (CLICKFACE.clicks || []).length; _vi++) { var _vv = CLICKFACE.clicks[_vi].voice; if (_vv && _vv.url) _cfWarm.push(_vv.url) }
  if (typeof dshwvWarm === 'function' && _cfWarm.length) dshwvWarm(_cfWarm)
} catch (err) {}
"""

A2_OLD = """    whaleClick()
    refresh(true)"""
A2_NEW = """    whaleClick()
    clickFaceSwap()
    refresh(true)"""

# A3：角色已被删除时的回退（补丁：优先回退到 clickface 首选角色）+ 首次进入自动选 autoRole
A3_OLD = """        } else if (saved && saved !== 'default') {
          // 保存的角色已被删除：回退默认鲸鱼娘
          applyRole('default', '小鲸鱼', IMG_URL)
        }"""
A3_NEW = """        } else if (saved && saved !== 'default') {
          // 保存的角色已被删除：回退默认鲸鱼娘（补丁：有 clickface 首选角色时回退到它）
          var _fbRole = null
          for (var _fi = 0; _fi < roleList.length; _fi++) {
            if (roleList[_fi].id === CLICKFACE.autoRole) { _fbRole = roleList[_fi]; break }
          }
          if (_fbRole) applyRole(_fbRole.id, _fbRole.name, _fbRole.url)
          else applyRole('default', '小鲸鱼', IMG_URL)
        } else if (!saved && CLICKFACE.autoRole) {
          // 补丁：首次进入（尚无角色选择记录）自动选中初始形象
          var _autoRole = null
          for (var _ai = 0; _ai < roleList.length; _ai++) {
            if (roleList[_ai].id === CLICKFACE.autoRole) { _autoRole = roleList[_ai]; break }
          }
          if (_autoRole) applyRole(_autoRole.id, _autoRole.name, _autoRole.url)
        }"""

A4_OLD = "  var initRoleId = localStorage.getItem('dshw-role') || ''"
A4_NEW = "  var initRoleId = localStorage.getItem('dshw-role') || 'state0'"

# A5：浏览器里存的若是「空」或「旧的默认鲸鱼娘(default)」，都当作未选择 → 让 autoRole 生效。
A5_OLD = """        var saved = ''
        try { saved = localStorage.getItem('dshw-role') || '' } catch (err) {}
        var found = null"""
A5_NEW = """        var saved = ''
        try { saved = localStorage.getItem('dshw-role') || '' } catch (err) {}
        // 补丁：未记录 / 旧默认(default) 一律视为未选择，交给 autoRole
        if (CLICKFACE.autoRole && (saved === '' || saved === 'default')) saved = CLICKFACE.autoRole
        var found = null"""

# A8/A9（v5）：形象机在用的角色不允许在界面里删除（角色面板 / 资源管理两条删除路径）
_GUARD = r"""  // 补丁（v5/v6）：形象机在用的角色受保护，删掉形象机就废了
  if (clickFaceProtectedRole(id)) {
    try { alert('「奶蛙」系列角色正在被形象机使用，不能在这里删除。\n要换形象请替换 %USERPROFILE%\.dsh\whale-roles 里的 state0..5.png。') } catch (err) {}
    return
  }
"""
A8_OLD = "function deleteRole(id) {"
A8_NEW = A8_OLD + "\n" + _GUARD
A9_OLD = "function resDelRole(id) {"
A9_NEW = A9_OLD + "\n" + _GUARD


A6_OLD = """function renderRolePanel() {
  try {
    rolePanel.innerHTML = ''
    roleList.forEach(function (r) {"""
A6_NEW = """function renderRolePanel() {
  try {
    rolePanel.innerHTML = ''
    // 补丁（v5）：角色选择列表只展示白名单里的角色（state1..5 是状态图，不列出来）
    clickFaceVisibleRoles(roleList).forEach(function (r) {"""

# A7（v5）：资源管理里的角色列表与计数也只算白名单里的角色
A7_OLD = """function resRenderData(wrap, roles, bubbleImgs, audio) {
  try {
    wrap.innerHTML = ''"""
A7_NEW = """function resRenderData(wrap, roles, bubbleImgs, audio) {
  try {
    // 补丁（v5）：资源管理里的角色列表/计数同样只算白名单里的角色
    roles = clickFaceVisibleRoles(roles)
    wrap.innerHTML = ''"""


def apply_to(client, patches):
    with open(client, "r", encoding="utf-8") as f:
        text = f.read()
    for name, old, new in patches:
        n = text.count(old)
        if n != 1:
            raise SystemExit("anchor %s matched %d times -> abort (file unchanged: %s)" % (name, n, client))
        text = text.replace(old, new)
        print("  patched", name)
    with open(client, "w", encoding="utf-8", newline="") as f:
        f.write(text)


PATCHES = [("A1-clickface-config", A1_OLD, A1_NEW),
           ("A2-enddrag-hook", A2_OLD, A2_NEW),
           ("A3-autorole", A3_OLD, A3_NEW),
           ("A4-initrole", A4_OLD, A4_NEW),
           ("A5-saved-default", A5_OLD, A5_NEW),
           ("A6-rolepanel-filter", A6_OLD, A6_NEW),
           ("A7-resmanager-filter", A7_OLD, A7_NEW),
           ("A8-delete-protect-panel", A8_OLD, A8_NEW),
           ("A9-delete-protect-res", A9_OLD, A9_NEW)]


def one(client, revert):
    if not os.path.isfile(client):
        print("!! 找不到：" + client)
        return False
    print("client ->", client)
    if revert:
        bak = client + ".dshwv-bak"
        if not os.path.exists(bak):
            print("!! 没有备份文件 " + bak + "，跳过")
            return False
        shutil.copyfile(bak, client)
        print("  reverted from", bak)
        return True
    with open(client, "r", encoding="utf-8") as f:
        cur = f.read()
    if MARK in cur:
        print("  already patched (mark present) -> nothing to do")
        return True
    bak = client + ".dshwv-bak"
    if not os.path.exists(bak):
        shutil.copyfile(client, bak)
        print("  backup ->", bak)
    apply_to(client, PATCHES)
    with open(client, "r", encoding="utf-8") as f:
        out = f.read()
    assert MARK in out and "clickFaceSwap()" in out and "clickFaceVisibleRoles(roleList)" in out and "clickFaceProtectedRole" in out and "clickFaceMarkTyping" in out
    print("  done; size %d -> %d bytes" % (len(cur), len(out)))
    return True


def main():
    revert = "--revert" in sys.argv
    targets = resolve_targets()
    ok = False
    for t in targets:
        ok = one(t, revert) or ok
    if not ok:
        raise SystemExit("没找到 whale-widget.js。请设置 DSH_HOME，或用 --client <路径> 指定。")


if __name__ == "__main__":
    main()
