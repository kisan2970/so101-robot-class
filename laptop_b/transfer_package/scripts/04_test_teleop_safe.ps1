$ErrorActionPreference = "Stop"

$PackageRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ProjectDir = Join-Path $PackageRoot "lerobot-so101"
$TeleopExe = Join-Path $ProjectDir ".venv\Scripts\lerobot-teleoperate.exe"

if (!(Test-Path $TeleopExe)) {
    Write-Host "LeRobot 환경이 아직 설치되지 않았습니다."
    Write-Host "먼저 .\scripts\01_install_lerobot_env.ps1 를 실행하세요."
    exit 1
}

$LeaderPort = Read-Host "leader arm COM 포트를 입력하세요. 예: COM10"
$FollowerPort = Read-Host "follower arm COM 포트를 입력하세요. 예: COM11"

Write-Host ""
Write-Host "안전 제한 teleop를 10초 동안 실행합니다."
Write-Host "로봇 주변을 비우고 전원 스위치에 손을 가까이 두세요."
Write-Host ""

Set-Location $ProjectDir

& $TeleopExe `
  --robot.type=so101_follower `
  --robot.port=$FollowerPort `
  --robot.id=my_so101_follower_2 `
  --robot.max_relative_target=3 `
  --teleop.type=so101_leader `
  --teleop.port=$LeaderPort `
  --teleop.id=my_so101_leader_2 `
  --fps=15 `
  --teleop_time_s=10

