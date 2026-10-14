<#
  奶蛙角色拓展（dsh-whale-widget 魔改）安装脚本
  ------------------------------------------------------------------
  最省事：把解压出来的文件夹拖到任意位置，然后在文件夹里按住 Shift 右键
          →「在此处打开 PowerShell 窗口」，执行：

            powershell -ExecutionPolicy Bypass -File .\install.ps1

  前提：对方已经装过 DeepSeek Harness（DSH）并至少启动过一次（会生成 %USERPROFILE%\.dsh）。
  如果对方还没装过 dsh-whale-widget 这个插件，用完整模式（会把插件包一起装上）：

            powershell -ExecutionPolicy Bypass -File .\install.ps1 -Full

  有多个 profile（desktop / web / …）时可指定：

            powershell -ExecutionPolicy Bypass -File .\install.ps1 -Profile web
#>
param(
  [switch]$Full,          # 连插件包一起装（含 lib/index.js、package.json、素材），并登记到 profile
  [string]$Profile = ''   # 指定 profile 名；默认自动探测
)
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not (Test-Path (Join-Path $root 'plugin'))) { $root = (Get-Location).Path }
$srcPlugin = Join-Path $root 'plugin'
$srcData   = Join-Path $root 'data'
$srcTools  = Join-Path $root 'tools'

function Say($m, $c = 'Gray') { Write-Host $m -ForegroundColor $c }
function Line() { Say ('-' * 62) 'DarkGray' }

Line
Say '奶蛙角色拓展 安装脚本' 'Cyan'
Line

if (-not (Test-Path $srcPlugin)) { Say "分享包不完整：找不到 $srcPlugin" 'Red'; exit 1 }

$dshHome = if ($env:DSH_HOME) { $env:DSH_HOME } else { Join-Path $env:USERPROFILE '.dsh' }
Say "DSH_HOME   : $dshHome"
if (-not (Test-Path $dshHome)) {
  Say "找不到 $dshHome —— 请先安装 DSH 并启动一次，再运行本脚本。" 'Red'
  exit 1
}

$profRoot = Join-Path $dshHome 'profiles'
if (-not (Test-Path $profRoot)) { Say "找不到 profiles 目录：$profRoot（先启动一次 DSH）" 'Red'; exit 1 }
$profNames = @(Get-ChildItem $profRoot -Directory -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name)
if ($profNames.Count -eq 0) { Say "profiles 目录是空的：先启动一次 DSH。" 'Red'; exit 1 }

# ---- 选 profile -------------------------------------------------------------
$prof = ''
if ($Profile) {
  if ($profNames -notcontains $Profile) { Say "没有名为 $Profile 的 profile；现有：$($profNames -join ', ')" 'Red'; exit 1 }
  $prof = $Profile
} else {
  foreach ($n in $profNames) {
    if (Test-Path (Join-Path $profRoot "$n\node_modules\dsh-whale-widget")) { $prof = $n; break }
  }
  if (-not $prof) {
    foreach ($n in $profNames) {
      $pj = Join-Path $profRoot "$n\package.json"
      if ((Test-Path $pj) -and ((Get-Content $pj -Raw) -match 'dsh-whale-widget')) { $prof = $n; break }
    }
  }
  if (-not $prof -and ($profNames -contains 'desktop')) { $prof = 'desktop' }
  if (-not $prof) { $prof = $profNames[0] }
}
Say "profile    : $prof  (现有: $($profNames -join ', '))"

$target = Join-Path $profRoot "$prof\node_modules\dsh-whale-widget"
$stamp  = Get-Date -Format 'yyyyMMdd-HHmmss'

# ---- 1) 客户端文件 ----------------------------------------------------------
if (-not (Test-Path $target)) {
  Say "目标插件目录不存在：$target" 'Yellow'
  if (-not $Full) {
    Say '对方还没装 dsh-whale-widget。' 'Yellow'
    Say '请先用 DSH 的「插件管理 / 插件市场」安装 dsh-whale-widget（版本 0.4.2），再重跑本脚本；' 'Yellow'
    Say '或者直接加 -Full 参数，由本脚本把插件包一起装上：' 'Yellow'
    Say '    powershell -ExecutionPolicy Bypass -File .\install.ps1 -Full' 'White'
    exit 1
  }
  New-Item -ItemType Directory -Force -Path $target | Out-Null
}

if ($Full) {
  $bak = "$target.bak-$stamp"
  Say "[1/3] 备份旧插件 → $bak"
  if (Test-Path $target) { Move-Item -LiteralPath $target -Destination $bak }
  New-Item -ItemType Directory -Force -Path $target | Out-Null
  Copy-Item -Path (Join-Path $srcPlugin '*') -Destination $target -Recurse -Force
  Say "      已写入完整插件（0.4.2 + 奶蛙补丁）" 'Green'
} else {
  $dst = Join-Path $target 'assets\whale-widget.js'
  if (-not (Test-Path (Split-Path $dst -Parent))) { New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null }
  if (Test-Path $dst) { Copy-Item $dst "$dst.before-naiwa-$stamp" -Force }
  Copy-Item (Join-Path $srcPlugin 'assets\whale-widget.js') $dst -Force
  Say "[1/3] 已覆盖 assets\whale-widget.js（旧文件已备份为 whale-widget.js.before-naiwa-$stamp）" 'Green'
}

# ---- 2) 角色图 + 音效 -------------------------------------------------------
Say "[2/3] 写入角色图与音效到 $dshHome"
foreach ($pair in @(@('whale-roles', 'whale-roles'), @('whale-audio', 'whale-audio'))) {
  $from = Join-Path $srcData $pair[0]
  $to   = Join-Path $dshHome $pair[1]
  if (-not (Test-Path $from)) { continue }
  New-Item -ItemType Directory -Force -Path $to | Out-Null
  foreach ($f in @('roles.json', 'audio.json')) {
    $p = Join-Path $to $f
    if (Test-Path $p) { Copy-Item $p "$p.before-naiwa-$stamp" -Force }
  }
  Copy-Item -Path (Join-Path $from '*') -Destination $to -Recurse -Force
  Say "      $($pair[1]) ✓" 'Green'
}

# ---- 3) 登记插件（仅 -Full）-------------------------------------------------
if ($Full) {
  $pkgPath = Join-Path $profRoot "$prof\package.json"
  if (Test-Path $pkgPath) {
    Copy-Item $pkgPath "$pkgPath.before-naiwa-$stamp" -Force
    try {
      $pkg = Get-Content -LiteralPath $pkgPath -Raw -Encoding UTF8 | ConvertFrom-Json
      if (-not ($pkg.PSObject.Properties.Name -contains 'dsh')) { $pkg | Add-Member -NotePropertyName dsh -NotePropertyValue ([pscustomobject]@{}) }
      if (-not ($pkg.dsh.PSObject.Properties.Name -contains 'profile')) { $pkg.dsh | Add-Member -NotePropertyName profile -NotePropertyValue ([pscustomobject]@{}) }
      if (-not ($pkg.dsh.profile.PSObject.Properties.Name -contains 'bundles')) { $pkg.dsh.profile | Add-Member -NotePropertyName bundles -NotePropertyValue @() }
      $b = @($pkg.dsh.profile.bundles)
      if ($b -notcontains 'dsh-whale-widget') { $b += 'dsh-whale-widget' }
      $pkg.dsh.profile.bundles = $b
      if (-not ($pkg.PSObject.Properties.Name -contains 'dependencies')) { $pkg | Add-Member -NotePropertyName dependencies -NotePropertyValue ([pscustomobject]@{}) }
      $pkg.dependencies | Add-Member -NotePropertyName 'dsh-whale-widget' -NotePropertyValue '0.4.2' -Force
      [System.IO.File]::WriteAllText($pkgPath, ($pkg | ConvertTo-Json -Depth 12), (New-Object System.Text.UTF8Encoding($false)))
      Say "[3/3] 已把 dsh-whale-widget 登记进 profile 的 package.json" 'Green'
    } catch {
      Say "[3/3] 自动改 package.json 失败：$($_.Exception.Message)" 'Yellow'
      Say "      请手动在 $pkgPath 里加上：" 'Yellow'
      Say '        "dsh": { "profile": { "bundles": [ …, "dsh-whale-widget" ] } },' 'White'
      Say '        "dependencies": { …, "dsh-whale-widget": "0.4.2" }' 'White'
    }
  }
} else {
  Say '[3/3] 跳过程序登记（默认模式认为插件已存在）；如需一并登记请加 -Full' 'DarkGray'
}

Line
Say '完成 ✓' 'Green'
Say '接下来：' 'Cyan'
Say '  1. 只升级客户端时刷新网页（F5 / Ctrl+Shift+R）即可；装了完整插件则完全重启 DSH。'
Say '  2. 打开挂件右下角菜单 → 角色，应能看到「奶蛙」和「小鲸鱼」两条。'
Say '  3. 选「奶蛙」后：点挂件 = 大笑(1) + 奶蛙笑声，再点 = 安迪(2) + 安迪音效，两次音效交替；'
Say '     DSH 思考时自动变思考态(3)，一轮任务结束时变完成态(4) 1 秒再回初始态；你在输入框打字时变指点态(5)。'
Say '  4. 想换回原版：删掉 assets\whale-widget.js 后把同目录的 whale-widget.js.dshwv-bak 改名回来。'
Line
