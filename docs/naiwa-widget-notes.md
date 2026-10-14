# 奶蛙桌面挂件改造说明（dsh-whale-widget）

## 做了什么（六状态形象机）

用你放进 `whale-assets` 的 6 张图做了一套状态形象，全部写进用户数据目录（插件升级不丢）：

| 状态 | 角色 id | 来自 | 什么时候出现 |
| --- | --- | --- | --- |
| 0 初始 | `state0` | `0.png`（手机截图，只留主体） | 平时一直是它（也是默认选中的角色） |
| 1 大笑 | `state1` | `1.jpg`（双手抱头大笑） | 第 1 次点击：切过去 **2.5 s**，同时播**奶蛙笑声** |
| 2 安迪 | `state2` | `2.jpg`（抱头惊讶） | 第 2 次点击：切过去 **1 s**，同时播**安迪**音效 |
| 3 思考 | `state3` | `3.jpg`（托腮思考） | DeepSeek 在思考/生成/跑工具时 |
| 4 完成 | `state4` | `4.jpg`（抱臂点头） | 每轮任务结束：**1 s** 后回到 0 |
| 5 打字 | `state5` | `奶蛙-4K-叉腰指点-03.jpg`（叉腰指点） | 你在输入框里打字时；停手 **0.9 s** 后离开 |

- 点击**按顺序交替** 1 → 2 → 1 → 2 …（各带自己的音效与时长）；点击态里形象轻微抖动（±1.5°、上移 3 px，0.22 s 一次来回）。
- 点击态倒计时结束时：**如果那时还在思考 → 落到状态 3**，否则回到状态 0。
- 插件自带的按压/松开音效在「点击挂件」这条路径上被静音（按压的挤压动画保留；菜单试听、任务结束音、待答提示音都不受影响）。
- 首次打开（浏览器里没有角色选择记录）会自动选中 `state0`；旧的 `dshw-role=default`（或指向已删角色）也会回退到 `state0`。
- **角色选择列表里只有两条**：`奶蛙`（初始形象）和插件自带的小鲸鱼（`CLICKFACE.showRoles = ['default', 'state0']`）。`state1..5` 这 5 张状态图仍然在 `roles.json` 里（换图要用 `/dsh-whale/role-image.png?id=…`），只是不会出现在「角色」面板和「资源管理」的角色列表里。另外这几个角色在界面上**删不掉**（误点删除会弹提示，避免把形象机删废）；小鲸鱼本来就是不可删的默认角色。

### 「思考中」是怎么判断的

DSH 前端里**没有**一个可靠表示「模型正在推理」的 DOM 标记（bundle 里只有工具执行中的 `data-state="ongoing"`、终端块的 `data-running`、流式文本的 `data-shimmer`，没有 `data-streaming` 之类），所以用了两层判据：

1. 前端标记：`[data-state="ongoing"]` / `[data-shimmer]` / `[data-running]` / 带「停止/中断/stop generating」字样的按钮 —— 覆盖「跑工具、流式输出」阶段。
2. 兜底：**你刚把消息发出去**（输入框里回车，或点带「发送/send」字样的按钮）→ 从那一刻起到「本轮任务结束」都算思考中（上限 30 分钟，防止某次没发出去时永远停在状态 3）。
3. 「任务结束」是插件自己的现成信号：它每秒查一次 `/dsh-whale/last-turn.json`，轮次 seq 增加就播任务结束音 —— 补丁包住这个函数，于是每轮结束都会闪一下状态 4 再回 0。

所以正常用起来是：**你按下回车 → 变思考 → 我答完/工具跑完 → 闪一下完成 → 回到初始**。

### 「正在打字」是怎么判断的（v6 新增）

- 监听输入框上的 `input` / `compositionupdate`（中文输入法）/ `paste` / 可打印键 `keydown`，只认 `textarea` 或 `contenteditable`、且**不在挂件自己面板里**的元素 ⇒ 一打字就切 `state5`（叉腰指点）。
- 最后一次输入后 **900 ms**（`CLICKFACE.typingIdleMs`）没人碰键盘就离开打字态，回到思考态或初始形象。
- 优先级：点击态（1/2）/ 完成态（4）> **打字态（5）** > 思考态（3）> 初始形象（0）；消息一发出去（回车 / 点发送）立刻清掉打字态，让思考态接管。
- 判据故意做得宽松（不依赖容易变的前端类名），所以 DSH 界面里**任何**别的输入框（例如侧栏搜索）里打字也会触发一下 `state5`。

## 素材与制作

- 6 张状态图都抠成透明底，各自贴在**按自身分辨率**定尺寸的正方形画布上（内容占画布 93.33%、底边留 6 px、水平居中），所以各状态之间体型/站位对齐、不会跳；挂件用 `object-fit:contain`，屏幕上的大小只由这个比例决定。
- 画布尺寸随素材原生分辨率走（`state0` 692²、`state1` 455²、`state2` 502²、`state5` 442²、`state3`/`state4` 1000²），**不放大**小图（放大只会插值变糊），也**不做颜色量化**；只有原生超过 1000 px 的才缩到 1000 便于控制体积。
- 去背规则：先取「确定是角色」的像素（饱和度 ≥55 或最暗通道 ≤120）当核心 → 膨胀 3 px 把邻近奶油色并入 → 「从边界扩散」补回被围住的区域（奶油肚皮、腿间）→ 腐蚀 1 px + 高斯 0.8 抗锯齿 → 按 alpha 归一化去掉白边污染。
- 抠完再走一遍 USM 锐化（radius 1.0 / 85% / threshold 2），权重按 alpha 羽化 ⇒ 角色内部变锐、轮廓不产生彩边。
- `0.png` 是手机截图：地面那块暖色投影与肚皮同色系，单靠颜色分不开，于是按源图高度（y ≥ 1140）把亮像素清掉，只留深色脚掌。
- 每张图另外算一份**自己的命中凸包**（alpha>10 的逐行最左/最右 → 凸包 → clip-path 百分比 polygon），换图时交给插件自己的 `setupHitTest()` 按新图重算 ⇒ 透明像素照样穿透、点到身体才算点。

### 色调统一（怎么让 6 张图看起来像同一只）

6 张素材来自 3 个不同来源（手机截图 / 三张压缩 JPEG / 两张亮调渲染），原本黄得深浅不一、`0.png` 的手脚甚至带蓝紫边。逐通道线性对齐做不到（要拉住高饱和的身体黄就会把暗部推脏），所以改成在 **Y / Cb / Cr** 空间分两步：

1. **亮度**：用「身体黄的亮度」与「最暗 3% 的亮度」两点解出 `Y' = a·Y + b`，6 张统一到同一中位目标（限幅 `a∈[0.80,1.30]`、`b∈[-60,60]`，最后只混入 85%）；
2. **色度**：把身体黄在 CbCr 平面上的**色度幅值**与**色相角**统一到中位目标（全局缩放 + 旋转，限 `[0.70,1.40]` / ±22°，同样混 85%）⇒ 黄色/橘黄的偏色被拉平，而近乎中性的高光几乎不受影响；
3. **肚皮**：再按「奶油色像素的亮度」做一次软权重微调，肚皮明暗也跟着一致。

实测参数在 `whale-assets\tone_report.txt`：例如 `state0` 亮度 `a=1.024 b=+7.4`、色度 `sat=0.745`（原来太橘太艳，被拉回）、`state4` 亮度 `a=1.255 b=-51.0`（原来整体偏亮）。

## 文件落点

| 内容 | 路径 |
| --- | --- |
| 6 张状态图（透明 PNG，442²–1000²） | `D:\deepseekworkshop\whale-assets\state0.png` … `state5.png`（92–396 KB/张，共 ~1.19 MB） |
| 上一版（480² 量化版，留档对比，只到 state4） | `D:\deepseekworkshop\whale-assets\old480\state0.png` … `state4.png` |
| 色调统一参数报告 | `D:\deepseekworkshop\whale-assets\tone_report.txt` |
| 6 份命中凸包 | `D:\deepseekworkshop\whale-assets\hulls.json` |
| 新旧对比 / 头部放大 / 灰底预览 | `D:\deepseekworkshop\whale-assets\preview_compare.png`、`preview_detail.png`、`preview_states.png` |
| 插件里的角色文件 | `C:\Users\李唯佳\.dsh\whale-roles\state0.png` … `state5.png` |
| 角色索引（state0 置顶） | `C:\Users\李唯佳\.dsh\whale-roles\roles.json` |
| 音效片段 | `C:\Users\李唯佳\.dsh\whale-audio\nailong_laugh.wav`（奶蛙笑声，39 123 B）、`andi.wav`（安迪，32 168 B）+ 同目录 `audio.json` |
| 客户端补丁 | `C:\Users\李唯佳\.dsh\profiles\desktop\node_modules\dsh-whale-widget\assets\whale-widget.js`（第 15019 行起，标记 `/* dshwv-clickface-patch v7 */`；共 9 处锚点：A1 补丁块、A2 点击钩子、A3/A4/A5 默认角色回退、A6 角色面板白名单、A7 资源管理白名单、A8/A9 两条删除路径的保护） |
| 补丁前备份（插件原始文件） | 同目录 `whale-widget.js.dshwv-bak` |
| 可重跑的脚本 | `D:\deepseekworkshop\_build_state_assets4.py`（当前：抠图→原生画布→USM→色调统一→凸包，改素材后跑它）、`_install_states.py`（装角色）、`_patch_widget.py`（打补丁 / `--revert`）、`_install_audio.py`（换音）、`_compare_states.py`（新旧对比图）、`_measure_states.py`（量三色锚点）、`_dbg_state_bottom.py`（检查底部残留） |
| 旧版脚本（已被 4 取代） | `_build_state_assets.py`（480² 量化版）、`_build_state_assets2.py`（900² 放大版，弃用）、`_build_state_assets3.py`（原生画布 + 逐通道仿射版） |

## 音效来源

- **奶蛙笑声**：你给的 `https://www.aigei.com/item/nai_long_da_xia.html` 整站取不到文件（页面 403、直连 TLS 被断、脚本抓取同样 403），换了同素材来源的条目：`sound.jichun29.cn` 的 **id 2409「奶龙笑声锁车音效」（该站原条目名）**，直链 `https://sound.jichun29.cn/api/stream.php?id=2409` → `audio/mpeg`，39 123 B，4.88 s（指纹 `sha256 3537389194e5bde575895e43390f84637b53893c76b3c90e0ce98e5cd77f804b`）。
- **安迪**：用你放进 `whale-assets` 的 `安迪~_爱给网_aigei_com.mp3`（1.46 s）。
- 两条都是 **MP3 字节放在 `.wav` 名下**：宿主按原字节回传，客户端 Web Audio 按容器内容解码，文件名不影响播放；播放端按 `maxMs` 定时截断。
- 换音：`python _install_audio.py <文件> <片段id> <名字>`；改时长/换片段改 `CLICKFACE.clicks[].voice`。

## 生效方式

页面**普通刷新（F5）**即可：宿主每次请求按 mtime 重读客户端脚本，响应是 `Cache-Control: no-store`，不用重启 DSH。看不到变化就 Ctrl+Shift+R 硬刷一次。

## 想微调的地方

都在客户端补丁顶部的 `CLICKFACE`（`whale-widget.js` 第 15014 行起）：

| 旋钮 | 现值 | 说明 |
| --- | --- | --- |
| `idle` / `autoRole` | `state0` | 静止态角色（补丁只在当前角色 = `state0` 时接管） |
| `thinking` | `state3` | 思考态角色 |
| `typing` / `typingIdleMs` | `state5` / `900` | 打字态角色与停手后停留毫秒 |
| `done` / `doneMs` | `state4` / `1000` | 完成态角色与停留毫秒 |
| `clicks[0]` | `state1`, `2500`, 奶蛙笑声 | 第一次点击的形象/时长/音效 |
| `clicks[1]` | `state2`, `1000`, 安迪 | 第二次点击的形象/时长/音效 |
| `clicks[].voice.maxMs` | `2600` / `1600` | 两条语音各自播多久（到时截断） |
| `shake` | `true` | 点击态抖动开关 |
| `volume` | `0.95` | 语音音量 |
| `showRoles` | `['default', 'state0']` | 角色选择列表的白名单（现在显示「奶蛙 + 小鲸鱼」两条；想多放一个状态进去就加 id，例如 `['default','state0','state2']`） |

改素材：把新的状态图放进 `whale-assets`（`state0..4` 沿用 `0.png` / `1..4.jpg` 的命名，`state5` 是 `奶蛙-4K-叉腰指点-03.jpg`），跑 `_build_state_assets4.py` 再跑 `_install_states.py`（角色 id 与客户端补丁都不用动）。

## 回退

- 恢复插件原始客户端代码：`python D:\deepseekworkshop\_patch_widget.py --revert`
- 删角色：`~\.dsh\whale-roles\` 下 6 张 PNG 与 `roles.json` 里的条目（或在挂件菜单里删）

## 已知限制

- 客户端补丁写在插件包内，**插件升级/重装会被覆盖**（角色文件与音效在 `~\.dsh` 下，不受影响）。升级后重跑 `_patch_widget.py` 即可。
- 「思考中」判据 2 是启发式的：如果某轮你发了消息但任务结束信号没回来，会停在状态 3（最长 30 分钟后自动解除）。想更准就得改插件宿主端（`lib/index.js` 里给 `turn/start` 也记一笔并在 `/dsh-whale/wait.json` 里回 `busy`），那需要重启 DSH。
- 「打字中」判据见上：DSH 界面里任何别的输入框（侧栏搜索、气泡编辑框之外的普通 textarea 等）打字也会闪一下 `state5`；如果你觉得烦，把 `CLICKFACE.typing` 置空字符串即可关掉这个状态。
- 插件本身升级（重新安装 `dsh-whale-widget`）会覆盖 `assets\whale-widget.js`，补丁会消失；重跑 `_patch_widget.py`（或分享包 `tools\_patch_widget.py`）即可，`~\.dsh\whale-roles`、`~\.dsh\whale-audio` 下的素材不受影响。
- 点击切换只在**当前角色是 `state0`** 时触发；手动在菜单里选了别的角色后，点击就只是普通戳一下。
- 6 张角色图走 `/dsh-whale/role-image.png` 路由，带 `Cache-Control: no-store` ⇒ 每次刷新页面会重新拉这 ~1.19 MB（本机 localhost，无网络开销）。
- 这轮只改形象与音效的配合，没有新增任何界面元素（黄底面板、黑描边卡片、声波条、印章等都没做）。
