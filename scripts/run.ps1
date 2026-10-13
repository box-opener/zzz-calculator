#requires -Version 5.1
[CmdletBinding()]
param(
    [ValidateRange(1024, 65535)][int]$Port = 8000,
    [switch]$NoBrowser,
    [switch]$SetupOnly,
    [switch]$Reinstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
# Keep native exit-code handling consistent across Windows PowerShell and pwsh.
if (Test-Path variable:PSNativeCommandUseErrorActionPreference) {
    $PSNativeCommandUseErrorActionPreference = $false
}
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$taskRepo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$taskCache = Join-Path $taskRepo '.cache\launcher'
$taskRuntimes = Join-Path $taskCache 'runtimes'
$taskServer = $null
$taskSetupLock = $null
$taskOldPath = $env:PATH

function Invoke-Checked {
    param([string]$Executable, [string[]]$Arguments, [string]$Step)
    & $Executable @Arguments | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "$Step 失败（退出码 $LASTEXITCODE）。请检查上方输出后重新运行。" }
}

function Get-SHA256 {
    param([string]$Path)
    # .NET hashing also works when Windows PowerShell cannot autoload Get-FileHash.
    $stream = [IO.File]::OpenRead((Resolve-Path -LiteralPath $Path).ProviderPath)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-', '') }
    finally { $algorithm.Dispose(); $stream.Dispose() }
}

function Get-PythonPath {
    param([string]$Executable, [string[]]$Prefix = @())
    if (-not $Executable -or -not (Test-Path -LiteralPath $Executable)) { return $null }
    try {
        $result = @(& $Executable @Prefix -c 'import sys; sys.exit(2) if sys.version_info < (3, 11) else None; print(sys.executable)' 2>$null)
        if ($LASTEXITCODE -eq 0 -and $result.Count -gt 0) { return [string]$result[-1] }
    } catch { }
    return $null
}

function Find-Python {
    $launcher = Get-Command py.exe -CommandType Application -ErrorAction SilentlyContinue
    if ($launcher) {
        $candidate = Get-PythonPath $launcher.Source @('-3')
        if ($candidate) { return $candidate }
    }
    $candidates = @(
        Get-Command python.exe, python3.exe -CommandType Application -All -ErrorAction SilentlyContinue |
            Where-Object { $_.Source -notlike '*\WindowsApps\*' } | ForEach-Object { $_.Source }
        Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python*\python.exe", "$env:ProgramFiles\Python*\python.exe" -ErrorAction SilentlyContinue |
            Sort-Object FullName -Descending | ForEach-Object { $_.FullName }
        Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    )
    foreach ($path in $candidates) {
        $candidate = Get-PythonPath $path
        if ($candidate) { return $candidate }
    }
    return $null
}

function Ensure-Python {
    $venvPython = Join-Path $taskRepo '.venv\Scripts\python.exe'
    $candidate = Get-PythonPath $venvPython
    if ($candidate) { return $candidate }
    $candidate = Find-Python
    if (-not $candidate) {
        $winget = Get-Command winget.exe -CommandType Application -ErrorAction SilentlyContinue
        if (-not $winget) { throw '未找到 Python 3.11+。请先安装 https://www.python.org/downloads/windows/ ，再双击 run.cmd。' }
        Write-Host '未找到 Python，正在通过 winget 安装 Python 3.12（当前用户）…'
        Invoke-Checked $winget.Source @('install', '--id', 'Python.Python.3.12', '--exact', '--source', 'winget', '--scope', 'user', '--silent', '--disable-interactivity', '--accept-source-agreements', '--accept-package-agreements') 'Python 安装'
        $candidate = Find-Python
        if (-not $candidate) { throw 'Python 已安装，但未找到可用解释器。请重新打开 run.cmd，或检查 Python 安装。' }
    }
    Write-Host '正在创建项目 .venv 虚拟环境…'
    Invoke-Checked $candidate @('-m', 'venv', (Join-Path $taskRepo '.venv')) '创建虚拟环境'
    return $venvPython
}

function Get-NodeTools {
    param([string]$Directory)
    $node = Join-Path $Directory 'node.exe'
    $npm = Join-Path $Directory 'node_modules\npm\bin\npm-cli.js'
    if (-not (Test-Path -LiteralPath $node) -or -not (Test-Path -LiteralPath $npm)) { return $null }
    try {
        $text = [string](& $node --version 2>$null)
        if ($LASTEXITCODE -ne 0 -or $text -notmatch '^v(\d+\.\d+\.\d+)$') { return $null }
        $version = [version]$Matches[1]
        if (-not (($version.Major -eq 20 -and $version.Minor -ge 19) -or ($version.Major -eq 22 -and $version.Minor -ge 12) -or $version.Major -gt 22)) { return $null }
        $null = & $node $npm --version 2>$null
        if ($LASTEXITCODE -ne 0) { return $null }
        return [pscustomobject]@{ Node = $node; Npm = $npm; Version = $text }
    } catch { return $null }
}

function Ensure-Node {
    $directories = @(
        Get-Command node.exe, npm.cmd -CommandType Application -All -ErrorAction SilentlyContinue |
            ForEach-Object { Split-Path $_.Source -Parent }
        Join-Path $env:ProgramFiles 'nodejs'
        Join-Path $env:LOCALAPPDATA 'Programs\nodejs'
        Get-ChildItem -LiteralPath $taskRuntimes -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match '^node-v\d+\.\d+\.\d+-win-(x64|arm64)$' } |
            Sort-Object Name -Descending | ForEach-Object { $_.FullName }
    )
    foreach ($directory in $directories) {
        $tools = Get-NodeTools $directory
        if ($tools) { return $tools }
    }
    if (-not [Environment]::Is64BitOperatingSystem) { throw '自动安装 Node.js 需要64位 Windows。' }
    $arch = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64' -or $env:PROCESSOR_ARCHITEW6432 -eq 'ARM64') { 'arm64' } else { 'x64' }
    Write-Host '未找到兼容的 Node.js + npm，正在从 nodejs.org 下载项目专用 LTS…'
    $index = Invoke-RestMethod -Uri 'https://nodejs.org/dist/index.json' -TimeoutSec 30
    $release = $index | Where-Object { $_.lts -and $_.version -match '^v(22|24)\.\d+\.\d+$' -and $_.files -contains "win-$arch-zip" } | Select-Object -First 1
    if (-not $release) { throw '未找到兼容的 Node.js LTS 下载，请安装 https://nodejs.org/en/download 后重试。' }
    $name = "node-$($release.version)-win-$arch"
    $zipName = "$name.zip"
    $zipPath = Join-Path $taskCache $zipName
    $baseUrl = "https://nodejs.org/dist/$($release.version)"
    $sums = (Invoke-WebRequest -UseBasicParsing -Uri "$baseUrl/SHASUMS256.txt" -TimeoutSec 30).Content
    $line = $sums -split "`n" | Where-Object { $_ -match ("^[a-fA-F0-9]{64}\s+" + [regex]::Escape($zipName) + '\s*$') } | Select-Object -First 1
    if (-not $line) { throw 'Node.js 官方下载校验信息不完整。' }
    $expectedHash = ($line -split '\s+')[0]
    if (-not (Test-Path -LiteralPath $zipPath) -or (Get-SHA256 $zipPath) -ne $expectedHash) {
        Invoke-WebRequest -UseBasicParsing -Uri "$baseUrl/$zipName" -OutFile $zipPath -TimeoutSec 180
    }
    if ((Get-SHA256 $zipPath) -ne $expectedHash) { throw 'Node.js 下载校验失败，请重新运行。' }
    Expand-Archive -LiteralPath $zipPath -DestinationPath $taskRuntimes -Force
    $tools = Get-NodeTools (Join-Path $taskRuntimes $name)
    if (-not $tools) { throw 'Node.js 解压或启动失败，请检查系统与网络后重试。' }
    return $tools
}

function Test-Stamp {
    param([string]$Path, [string]$Value)
    return (-not $Reinstall -and (Test-Path -LiteralPath $Path) -and (Get-Content -LiteralPath $Path -Raw).Trim() -eq $Value)
}

function Find-FreePort {
    for ($candidate = $Port; $candidate -le [Math]::Min($Port + 19, 65535); $candidate++) {
        $listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, $candidate)
        try { $listener.Start(); return $candidate } catch [Net.Sockets.SocketException] { }
        finally { $listener.Stop() }
    }
    throw "端口 $Port 附近没有空闲端口，请使用 run.cmd -Port 其他端口。"
}

try {
    Push-Location -LiteralPath $taskRepo
    New-Item -ItemType Directory -Force -Path $taskCache, $taskRuntimes | Out-Null
    try {
        $taskSetupLock = [IO.File]::Open((Join-Path $taskCache 'setup.lock'), [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    } catch { throw '另一个启动窗口正在配置项目，请等待配置完成后再运行。' }

    Write-Host '[1/4] 检查 Python 和 Node.js 环境…' -ForegroundColor Cyan
    $taskPython = Ensure-Python
    $taskNode = Ensure-Node
    $env:PATH = "$(Split-Path $taskNode.Node -Parent);$env:PATH"
    Write-Host "Python: $taskPython"
    Write-Host "Node.js: $($taskNode.Version)"

    Write-Host '[2/4] 安装或检查后端依赖…' -ForegroundColor Cyan
    $pythonHash = Get-SHA256 (Join-Path $taskRepo 'pyproject.toml')
    $pythonStamp = Join-Path $taskCache 'python-deps.sha256'
    $pythonReady = $false
    if (Test-Stamp $pythonStamp $pythonHash) {
        try {
            & $taskPython -c 'import fastapi, uvicorn, genshin, qrcode' 2>$null
            $pythonReady = ($LASTEXITCODE -eq 0)
        } catch { $pythonReady = $false }
    }
    if (-not $pythonReady) {
        Invoke-Checked $taskPython @('-m', 'pip', 'install', '--disable-pip-version-check', '-e', '.[web]') '后端依赖安装'
        Set-Content -LiteralPath $pythonStamp -Value $pythonHash -Encoding ASCII
    } else { Write-Host '后端依赖已就绪。' }

    Write-Host '[3/4] 安装前端依赖并构建页面…' -ForegroundColor Cyan
    Push-Location -LiteralPath (Join-Path $taskRepo 'frontend')
    try {
        $frontendHash = (Get-SHA256 'package.json') + ':' + (Get-SHA256 'package-lock.json')
        $frontendStamp = Join-Path $taskCache 'frontend-deps.sha256'
        if (-not (Test-Stamp $frontendStamp $frontendHash) -or -not (Test-Path -LiteralPath 'node_modules\vite\bin\vite.js') -or -not (Test-Path -LiteralPath 'node_modules\typescript\bin\tsc')) {
            Invoke-Checked $taskNode.Node @($taskNode.Npm, 'ci', '--no-audit', '--no-fund') '前端依赖安装'
            Set-Content -LiteralPath $frontendStamp -Value $frontendHash -Encoding ASCII
        } else { Write-Host '前端依赖已就绪。' }
        Invoke-Checked $taskNode.Node @($taskNode.Npm, 'run', 'build') '前端构建'
    } finally { Pop-Location }
    $taskSetupLock.Dispose(); $taskSetupLock = $null
    if ($SetupOnly) { Write-Host '配置与构建完成。' -ForegroundColor Green; exit 0 }

    Write-Host '[4/4] 启动本地服务…' -ForegroundColor Cyan
    $taskPort = Find-FreePort
    $taskUrl = "http://127.0.0.1:$taskPort"
    if ($taskPort -ne $Port) { Write-Host "端口 $Port 已被占用，改用 $taskPort。" }
    $logTag = "$(Get-Date -Format 'yyyyMMdd-HHmmss')-$PID"
    $stdout = Join-Path $taskCache "server-$logTag.log"
    $stderr = Join-Path $taskCache "server-$logTag.error.log"
    $taskServer = Start-Process -FilePath $taskPython -WorkingDirectory $taskRepo -ArgumentList @('-m', 'uvicorn', 'web.api:app', '--host', '127.0.0.1', '--port', "$taskPort") -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
    $ready = $false
    $deadline = [DateTime]::UtcNow.AddSeconds(30)
    while ([DateTime]::UtcNow -lt $deadline) {
        $taskServer.Refresh()
        if ($taskServer.HasExited) { throw "服务启动失败：$(Get-Content -LiteralPath $stderr -Raw)" }
        try {
            $health = Invoke-RestMethod -Uri "$taskUrl/api/health" -TimeoutSec 1
            if ($health.status -eq 'ok' -and $health.schema_version -eq 'presentation-v1') { $ready = $true; break }
        } catch { }
        Start-Sleep -Milliseconds 250
    }
    if (-not $ready) { throw "服务启动超时，请检查日志 $stderr" }
    Write-Host "`n已启动：$taskUrl" -ForegroundColor Green
    Write-Host "按 Ctrl+C 停止服务。日志：$stderr"
    if (-not $NoBrowser) {
        try { Start-Process -FilePath $taskUrl } catch { Write-Host "未能自动打开浏览器，请手动打开 $taskUrl" }
    }
    while (-not $taskServer.HasExited) { Start-Sleep -Milliseconds 500; $taskServer.Refresh() }
    if ($taskServer.ExitCode -ne 0) { throw "服务异常退出：$(Get-Content -LiteralPath $stderr -Raw)" }
} catch {
    Write-Host "`n启动失败：$($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    if ($taskSetupLock) { $taskSetupLock.Dispose() }
    if ($taskServer) {
        if (-not $taskServer.HasExited) { Stop-Process -Id $taskServer.Id -ErrorAction SilentlyContinue }
        $taskServer.Dispose()
    }
    $env:PATH = $taskOldPath
    Pop-Location
}
