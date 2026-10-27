$ErrorActionPreference = "Stop"

$PackageRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Python = Join-Path $PackageRoot "lerobot-so101\.venv\Scripts\python.exe"

if (!(Test-Path $Python)) {
    Write-Host "LeRobot 환경이 아직 설치되지 않았습니다."
    Write-Host "먼저 .\scripts\01_install_lerobot_env.ps1 를 실행하세요."
    exit 1
}

Write-Host "연결된 serial / COM 포트를 확인합니다."
Write-Host "Bluetooth 포트는 무시하고 USB-Enhanced-SERIAL CH343 포트를 찾으세요."
Write-Host ""

& $Python -m serial.tools.list_ports -v

