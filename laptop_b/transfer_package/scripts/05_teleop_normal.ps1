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
Write-Host "일반 teleop를 실행합니다."
Write-Host "안전 테스트가 정상일 때만 사용하세요."
Write-Host ""

Set-Location $ProjectDir

& $TeleopExe `
  --robot.type=so101_follower `
  --robot.port=$FollowerPort `
  --robot.id=my_so101_follower_2 `
  --teleop.type=so101_leader `
  --teleop.port=$LeaderPort `
  --teleop.id=my_so101_leader_2

