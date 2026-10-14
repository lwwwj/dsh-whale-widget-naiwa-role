# dsh-whale-widget 角色拓展 —— 奶蛙

把 DSH（DeepSeek Harness）Web 界面右下角那只「DeepSeek 余额小鲸鱼」换成**奶蛙**：
平时站着，点一下仰头大笑并出声，思考时变托腮，任务结束点下头，你在输入框打字时叉腰指点。

> 这是一个**第三方插件的角色拓展（魔改）**，不是官方插件。
> 上游插件：**dsh-whale-widget v0.4.2**（作者 `MeteorNOX`，MIT 许可，
> 仓库 <https://github.com/MeteorNOX/DeepSeek-Balance-Whale-Widget>）。
> 本仓库保留了上游的 `LICENSE` 与 `PROVENANCE.md`，只做角色/音效/状态机的本地改动。

---

## 效果

| 时机 | 形象 | 说明 |
| --- | --- | --- |
| 平时 | **奶蛙**（`state0`） | 拖动、余额气泡、每轮花销、音效等上游功能全部保留 |
| 点一下挂件 | **奶蛙·大笑**（`state1`） | 播放**奶蛙笑声**，2.5 秒后回到站立（带轻微抖动） |
| 再点一下 | **安迪**（`state2`） | 播放**安迪**音效，1 秒后回到站立；再点又回到大笑 —— 两条音效**交替** |
| 我思考时 | **奶蛙·思考**（`state3`） | 你发出消息后自动切，直到这一轮结束 |
| 任务结束 | **奶蛙·完成**（`state4`） | 每轮任务结束闪 1 秒，然后回到站立 |
| 你打字时 | **奶蛙·指点**（`state5`） | 在输入框里打字就出现，停手 0.9 秒后离开 |

挂件菜单 →「角色」里只有两条：**奶蛙** 与插件自带的 **小鲸鱼**（其余 5 张状态图不列出来，
由补丁按 URL 直接换图；选中「小鲸鱼」时不再有上面这套状态机）。

## 安装

### 方式 A：已经装过 dsh-whale-widget（推荐）

```powershell
# 在解压后的目录里执行：
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

脚本会把打过补丁的客户端覆盖到现役插件，并把角色图/音效放进 `%USERPROFILE%\.dsh`。
原有的客户端与索引都会先备份成 `*.before-naiwa-<时间戳>`。

### 方式 B：同学那边还没装插件（连插件一起装）

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Full
```

`-Full` 会把完整插件包（0.4.2 + 奶蛙补丁）装到默认 profile，并把 `dsh-whale-widget`
写进 profile 的 `package.json`（`dsh.profile.bundles` 与 `dependencies`）。

装完**完全重启 DSH**，然后刷新网页（F5）。只想重载客户端时 F5 就够 ——
插件是按 mtime 重读 `assets/whale-widget.js` 且响应 `Cache-Control: no-store`。

## 目录

```
dsh-whale-widget-naiwa-role\
  install.ps1                 安装脚本（默认只覆盖客户端 + 角色/音效；-Full 连插件一起装）
  plugin\                     打过补丁的 dsh-whale-widget 0.4.2 完整插件包
    assets\whale-widget.js      客户端（含奶蛙状态机补丁 v7）
    assets\whale-widget.js.dshwv-bak   上游原始客户端（要还原就改回这个名字）
  data\
    whale-roles\               state0..5.png + roles.json
    whale-audio\               nailong_laugh.wav（奶蛙笑声）、andi.wav（安迪）、gagalaxia*.wav
  tools\                      角色/音效安装、补丁与冒烟测试脚本
  patches\                    客户端改动的 unified diff（原始 0.4.2 → 补丁后）
  docs\naiwa-widget-notes.md  完整技术说明（行为、文件落点、旋钮、回退、限制）
```

## 换成你自己的形象 / 音效

* **换形象**：替换 `%USERPROFILE%\.dsh\whale-roles\state0.png … state5.png`（方形透明 PNG，
  正方画布、主体贴底边居中），刷新即可；也可以跑 `tools\_install_states.py`。
* **换音效**：`tools\_install_audio.py <音频文件> [片段id] [显示名]`；注意客户端里写死了两个 id：
  `nailong_laugh`（点击大笑）与 `andi`（点击第二下），换文件时保持 id 不变就行。
* **调节奏**：客户端补丁块（搜 `/* dshwv-clickface-patch v7 */`）顶部的 `CLICKFACE` 配置里有
  每个状态的停留毫秒 `ms`、打字态停手时长 `typingIdleMs`、抖动开关 `shake` 等。

## 还原

把 `plugin\assets\whale-widget.js.dshwv-bak` 覆盖成 `assets\whale-widget.js` 即可回到上游原版；
角色与音效文件删掉即可（或者留着也不影响原版客户端）。

## 换回上游原版 / 关于补丁

* **还原**：把 `plugin\assets\whale-widget.js.dshwv-bak`（上游 0.4.2 原始客户端）覆盖成
  `assets\whale-widget.js` 即可；角色与音效文件删掉即可（留着也不影响原版客户端）。
* **改了什么**：`patches\naiwa-role-states-0.4.2.patch` 是「原始 0.4.2 → 奶蛙补丁 v7」的完整 unified diff，
  在客户端里搜 `/* dshwv-clickface-patch v7 */` 也能看到补丁块（配置与逻辑都在一起）。
* `tools\_patch_widget.py` 里的锚点是按 **0.3.18** 的客户端写的（当年用它打补丁），对 0.4.2 会
  在第二个锚点处**安全地中止、不改文件**；0.4.2 直接用本仓库里已经打好补丁的客户端就行。

## 许可与致谢

* 上游插件 **dsh-whale-widget**（MIT）作者 **MeteorNOX** —— 本仓库的挂件主体、气泡、账本等功能都由它提供。
* 本拓展（角色图处理、状态机补丁、音效与安装脚本）以 MIT 许可一并发布，见 `LICENSE`。
* 角色形象取自用户提供的《奶蛙/奶龙》相关图片与公开音效站素材，**仅供个人学习自用，请勿商用或二次分发盈利**。
