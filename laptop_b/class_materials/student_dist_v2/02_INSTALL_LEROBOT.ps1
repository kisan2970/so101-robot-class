$ErrorActionPreference = "Stop"

Write-Host "SO-101 LeRobot classroom setup" -ForegroundColor Cyan
Write-Host "This installs Python 3.12 when needed, creates a virtual environment, and installs LeRobot." -ForegroundColor Gray

$documents = [Environment]::GetFolderPath("MyDocuments")
$project = Join-Path $documents "lerobot-so101"

function Find-Python312 {
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($py) {
        try {
            & $py.Source -3.12 -c "import sys; print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                return (& $py.Source -3.12 -c "import sys; print(sys.executable)").Trim()
            }
        } catch {}
    }

    $candidate = Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"
    if (Test-Path -LiteralPath $candidate) {
        return $candidate
    }
    return $null
}

$python = Find-Python312
if (-not $python) {
    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw "winget을 찾지 못했습니다. Microsoft Store에서 Python 3.12를 설치한 뒤 다시 실행하세요."
    }

    Write-Host "Installing Python 3.12..." -ForegroundColor Yellow
    & $winget.Source install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        throw "Python 설치가 완료되지 않았습니다. 출력된 오류를 Codex에 전달하세요."
    }
    $python = Find-Python312
}

if (-not $python) {
    throw "Python 3.12를 설치했지만 현재 PowerShell에서 찾지 못했습니다. PowerShell을 닫았다가 다시 열고 이 파일을 재실행하세요."
}

Write-Host "Python: $python" -ForegroundColor Green
New-Item -ItemType Directory -Force -Path $project | Out-Null
Set-Location -LiteralPath $project

if (-not (Test-Path -LiteralPath ".venv\Scripts\python.exe")) {
    Write-Host "Creating .venv..." -ForegroundColor Yellow
    & $python -m venv .venv
}

$venvPython = Join-Path $project ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    throw ".venv 생성에 실패했습니다."
}

Write-Host "Updating pip..." -ForegroundColor Yellow
& $venvPython -m pip install --upgrade pip

Write-Host "Installing LeRobot and SO-101 dependencies..." -ForegroundColor Yellow
& $venvPython -m pip install "lerobot[core_scripts,feetech]" opencv-python pyserial
if ($LASTEXITCODE -ne 0) {
    throw "LeRobot 설치에 실패했습니다. 마지막 오류 부분을 Codex에 전달하세요."
}

Write-Host "" 
Write-Host "SETUP COMPLETE" -ForegroundColor Green
Write-Host "Project folder: $project"
Write-Host "Python: $venvPython"
Write-Host "Next command:"
Write-Host "& `"$venvPython`" -m serial.tools.list_ports -v" -ForegroundColor Cyan

