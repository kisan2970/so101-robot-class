# SO-101 로봇팔 수업: 주사위를 집어 왼쪽 칸에 옮기기

SO-101 로봇팔과 손목 카메라로 **빨간 주사위를 집어 왼쪽 칸에 옮기는** 실습 코드입니다.
두 가지 방법을 직접 해 볼 수 있어요.

| 방법 | 내용 | 파일 |
|---|---|---|
| 방법 1 · AI 모방학습 | 사람이 리더 팔로 시범 → 녹화 → AI(ACT / SmolVLA) 학습 → 실행 | `record_sector.py`, `train_launch.py`, `run_eval.py` |
| 방법 2 · 색 + 피드백 제어 | 빨간색으로 주사위를 찾고, 목표 위치와의 차이를 줄이며 다가가기 (비주얼 서보) | `dice_live.py`, `servo_pick.py` |

> 아래 명령은 모두 **Windows PowerShell**에서 이 저장소 폴더 안에서 실행합니다. 회색 상자 안의 내용을 그대로 복사해 붙여 넣으세요.

---

## 0. 준비물

- SO-101 팔로워 팔 + 리더 팔 (각각 12V 전원, USB 연결)
- 그리퍼(집게) 위에 단 USB 카메라 1대
- 빨간 주사위, 3×3 칸이 그려진 판, 그 왼쪽에 놓을 칸 1개
- Windows PC, Python 3.12, Git (AI 학습까지 하려면 NVIDIA GPU)

## 1. 내려받기와 설치 (처음 한 번)

```powershell
git clone https://github.com/kisan2970/so101-robot-class.git
cd so101-robot-class
powershell -ExecutionPolicy Bypass -File setup.ps1
```

마지막에 `OK  torch ...`가 보이면 설치 성공입니다. 몇 GB를 내려받으니 시간이 걸려요.

## 2. 포트(COM 번호) 찾기

팔로워만 USB로 연결한 상태에서:

```powershell
[System.IO.Ports.SerialPort]::GetPortNames()
```

나온 번호가 팔로워입니다. 그다음 리더도 연결하고 같은 명령을 다시 실행하면 **새로 생긴 번호**가 리더입니다.
`autograsp\config\rig.json`을 메모장으로 열어 `follower`와 `leader`의 `port`를 바꿔 주세요.

```powershell
notepad autograsp\config\rig.json
```

## 3. 캘리브레이션 (팔마다 한 번)

팔을 모든 관절이 가운데쯤 오는 자세로 두고 Enter → 안내에 따라 **모든 관절을 끝에서 끝까지** 천천히 움직인 뒤 Enter.
`COM5`, `COM6`은 2단계에서 찾은 번호로 바꾸세요.

```powershell
.\.venv\Scripts\lerobot-calibrate.exe --robot.type=so101_follower --robot.port=COM5 --robot.id=so101_follower
```

```powershell
.\.venv\Scripts\lerobot-calibrate.exe --teleop.type=so101_leader --teleop.port=COM6 --teleop.id=so101_leader
```

## 4. 텔레오퍼레이션 확인 (리더를 움직이면 팔로워가 따라와요)

```powershell
.\.venv\Scripts\python.exe -m lerobot.scripts.lerobot_teleoperate --robot.type=so101_follower --robot.port=COM5 --robot.id=so101_follower --teleop.type=so101_leader --teleop.port=COM6 --teleop.id=so101_leader
```

멈출 때는 `Ctrl+C`. 토크가 풀리면 팔이 떨어지니 **손으로 받쳐 주세요**.

## 5. 카메라 확인

```powershell
.\.venv\Scripts\python.exe autograsp\tools\cam_bench.py --scan
```

`autograsp\runs\cam_bench\scan_index*.jpg` 중 손목 카메라 화면인 번호를 `rig.json`의 `index_or_path`에 적어요.
(노트북 내장 카메라는 보통 0번입니다.)

주사위가 잘 인식되는지 보기 (초록 원 = 찾은 주사위, `q`로 종료):

```powershell
.\.venv\Scripts\python.exe autograsp\tools\dice_live.py
```

---

## 방법 2 · 색 + 피드백 제어로 집기 (먼저 해 보길 추천)

**① 안전 범위 파일 준비** (예시 파일을 복사. 자기 시범을 녹화했다면 방법 1의 `derive_limits.py`로 새로 만드는 게 더 안전해요)

```powershell
Copy-Item autograsp\config\safety.example.json autograsp\config\safety.json
```

**② 시작 자세 저장**: 토크가 풀리면 팔로워를 손으로 움직여, 손목 카메라에 **격자 전체와 집게 두 개**가 보이는 자세로 두고 Enter

```powershell
.\.venv\Scripts\python.exe autograsp\tools\servo_pick.py --teach-start
```

**③ 놓을 자세 저장**: 팔로워를 손으로 움직여 주사위가 **왼쪽 칸 안에 내려놓일 자세**로 두고 Enter

```powershell
.\.venv\Scripts\python.exe autograsp\tools\servo_pick.py --teach-place
```

**④ 실행**: 주사위를 칸 하나에 놓고, `START`(영어) 입력 → 단계마다 Enter

```powershell
.\.venv\Scripts\python.exe autograsp\tools\servo_pick.py
```

진행 단계: 시작 자세 → 주사위 찾기 + 관절을 4°씩 살짝 움직여 보기(자코비안 측정) → 주사위로 다가가기 → 집기 → 들어 올려 왼쪽 칸으로 → 놓기

---

## 방법 1 · AI 모방학습 (심화, NVIDIA GPU 필요)

**① 녹화 계획 만들기** (시작 칸 1~9를 섞은 순서)

```powershell
.\.venv\Scripts\python.exe autograsp\tools\make_left_plan.py --seed 0
```

**② 시범 녹화**: 화면에 나오는 시작 칸에 주사위를 놓고 `→`로 시작, 리더로 왼쪽 칸에 옮긴 뒤 `→`로 끝. `←` 다시 하기, `Esc` 중단.

```powershell
.\.venv\Scripts\python.exe autograsp\tools\record_sector.py --plan left_plan.json --block R1-B1 --sync
```

다음 블록은 `R1-B2`, `R1-B3` … 로 바꿔 실행하세요. 데이터가 많을수록 좋아요(9개로는 부족했어요).

**③ 데이터 점검과 안전 범위 만들기**

```powershell
.\.venv\Scripts\python.exe autograsp\tools\check_dataset.py datasets\so101_sector_train
```

```powershell
.\.venv\Scripts\python.exe autograsp\tools\derive_limits.py --datasets datasets\so101_sector_train --out autograsp\config\safety.json
```

**④ ACT 학습** (약 10~15분)

```powershell
.\.venv\Scripts\python.exe autograsp\tools\train_launch.py --policy act --steps 4000 --name act_left_p1
```

**⑤ 실제 로봇으로 시험** (`START` 입력 후 시도마다 Enter, `Esc` = 비상 정지)

```powershell
powershell -ExecutionPolicy Bypass -File autograsp\tools\eval_act.ps1
```

SmolVLA로 해 보려면 별도 환경이 필요해요(약 4GB 다운로드):

```powershell
powershell -ExecutionPolicy Bypass -File autograsp\setup_smolvla_env.ps1
```

---

## 안전 규칙

- 로봇이 움직이는 동안 **작업 공간에 손을 넣지 않아요.** `Esc` = 그 자리에서 정지.
- 프로그램을 끝내면 토크가 풀려 팔이 떨어져요. **끝내기 전에 팔을 손으로 받쳐요.**
- 모든 자동 동작은 `safety.json`의 관절 범위와 한 번에 움직이는 각도 제한을 거쳐요.
- 모터 6개가 한꺼번에 응답하지 않으면(`There is no status packet`) 12V 전원과 케이블을 먼저 확인해요.

## 자주 생기는 문제

| 증상 | 해결 |
|---|---|
| COM 포트가 안 보여요 | USB를 다른 구멍에 꽂기, 데이터용 케이블인지 확인, 12V 전원 확인 |
| 카메라가 160×120으로 떨어지거나 멈춰요 | USB 허브 대신 PC에 직접 꽂기 |
| `.ps1` 실행이 막혀요 | 명령 앞에 `powershell -ExecutionPolicy Bypass -File` 붙이기 |
| 녹화 시작 시 `FileExistsError` | 에피소드가 0개인 빈 `datasets\so101_sector_train` 폴더를 지우고 다시 실행 |
| 서보가 주사위를 못 찾아요 | `dice_live.py`로 확인. 조명이 어두우면 주사위가 잘 안 보여요 |

## 구성

```
setup.ps1                  처음 한 번 설치
patches/                   LeRobot 팔로워 보정 패치(연결 시 튀지 않게, 손목 회전 급변 차단)
autograsp/config/          rig.json(포트·카메라·자세), 녹화 계획, 안전 범위 예시
autograsp/plugin/          안전 필터가 들어간 팔로워(관절 범위·속도 제한·비상 정지)
autograsp/tools/           녹화·학습·평가·비주얼 서보 도구
```

LeRobot(Apache-2.0, Hugging Face)을 기반으로 합니다.
