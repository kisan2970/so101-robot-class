$ErrorActionPreference = "Stop"

$ProjectDir = Join-Path (Get-Location) "lerobot-so101"

Write-Host "SO-101 LeRobot 환경을 설치합니다."
Write-Host "설치 위치: $ProjectDir"

if (!(Test-Path $ProjectDir)) {
    New-Item -ItemType Directory -Path $ProjectDir | Out-Null
}

Set-Location $ProjectDir

if (!(Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Python 가상환경을 생성합니다."
    py -3.12 -m venv .venv
}

Write-Host "pip를 업데이트합니다."
.\.venv\Scripts\python.exe -m pip install --upgrade pip

Write-Host "LeRobot과 필요한 패키지를 설치합니다."
.\.venv\Scripts\pip.exe install "lerobot[feetech]" opencv-python pyserial

Write-Host ""
Write-Host "설치 확인:"
.\.venv\Scripts\python.exe -c "import lerobot; import serial; import cv2; print('LeRobot / pyserial / opencv OK')"

Write-Host ""
Write-Host "완료되었습니다."

