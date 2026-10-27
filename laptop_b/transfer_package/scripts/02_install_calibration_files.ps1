$ErrorActionPreference = "Stop"

$PackageRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

$SourceFollower = Join-Path $PackageRoot "calibration\robots\so_follower\my_so101_follower_2.json"
$SourceLeader = Join-Path $PackageRoot "calibration\teleoperators\so_leader\my_so101_leader_2.json"

$TargetFollowerDir = Join-Path $env:USERPROFILE ".cache\huggingface\lerobot\calibration\robots\so_follower"
$TargetLeaderDir = Join-Path $env:USERPROFILE ".cache\huggingface\lerobot\calibration\teleoperators\so_leader"

New-Item -ItemType Directory -Force -Path $TargetFollowerDir | Out-Null
New-Item -ItemType Directory -Force -Path $TargetLeaderDir | Out-Null

Copy-Item -LiteralPath $SourceFollower -Destination (Join-Path $TargetFollowerDir "my_so101_follower_2.json") -Force
Copy-Item -LiteralPath $SourceLeader -Destination (Join-Path $TargetLeaderDir "my_so101_leader_2.json") -Force

Write-Host "캘리브레이션 파일 복사가 완료되었습니다."
Write-Host "Follower:" (Join-Path $TargetFollowerDir "my_so101_follower_2.json")
Write-Host "Leader:  " (Join-Path $TargetLeaderDir "my_so101_leader_2.json")

