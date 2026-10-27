# SO-101 작업 정리 — 노트북 B (wotjr)

> 이 폴더는 **노트북 B에서 한 SO-101 / LeRobot 작업 전부**를 모은 것입니다.
> `main` 브랜치(노트북 A의 `autograsp` 주사위 실습)와 합치기 전에 비교·검토하려고 `laptop-b-work` 브랜치에 올렸습니다.
> 작성일: 2026-10-27. 원본 위치: `OneDrive\문서\...`, `~\.cache\huggingface\lerobot\calibration`

---

## 1. 한눈에 보기

| 분야 | 상태 | 위치 |
|---|---|---|
| 설치·모터 ID·캘리브레이션 수업자료 (PPT, HTML, Codex 프롬프트) | 완료, 여러 버전 있음 | `class_materials/` |
| 다른 PC로 옮기는 패키지 (설치·캘리브레이션 복사·텔레오퍼레이션 스크립트) | 완료 (6월) | `transfer_package/` |
| 모터 진단·안전 텔레오퍼레이션 Python 스크립트 | 사용 중, 마지막 수정 10/23 | `scripts/` |
| 캘리브레이션 파일 (팔 5쌍 분량) | 최신 파일은 10/24 | `calibration/` |
| 학생용 웹 가이드 (Vercel 정적 페이지) | 6월 버전 | `class_web_guide/` |
| 손목 카메라 마운트 | 부품 다시 출력해야 함 (아래 4절) | `wrist_cam_mount/` |
| 모방학습 (데이터 수집·학습·평가) | **노트북 B에는 없음**. `main`의 `autograsp/`만 있음 | — |

---

## 2. 날짜별 진행 순서 (파일 수정 날짜 기준)

| 날짜 | 한 일 | 근거 파일 |
|---|---|---|
| 05/10–05/13 | LeRobot 설치, 첫 리더·팔로워 캘리브레이션 (COM7 리더 / COM8 팔로워). 팔로워 ID 5·6(wrist_roll, gripper)이 제대로 움직이지 않아 진단함. 1~4번 관절만 움직이는 안전 텔레오퍼레이션을 따로 만듦 | `scripts/safe_teleop_so101_1_4_only.py`, `test_so101_follower_456_direct.py`, `test_so101_follower_56_raw.py`, `status_so101_follower_56.py`, `watch_so101_leader_456.py`, `calibration/*/my_so101_*.json` |
| 06/05 | SO-101 설치 소개 PPT (9장) | `class_materials/setup_intro_deck/` |
| 06/12 | 두 번째 팔 쌍 캘리브레이션 (`_2`). 다른 PC로 옮기는 패키지 제작 | `transfer_package/`, `calibration/*/my_so101_*_2.json` |
| 06/19 | 학생용 웹 가이드 (Vercel 배포용) | `class_web_guide/` |
| 07/10 | 하드웨어 조립 가이드 PPT, 기술 수업 PPT | `class_materials/hardware_assembly/`, `technical_class/` |
| 08/26–08/27 | 모터 ID·캘리브레이션 2시간 수업 PPT (전체본·축약본), 수업 시작 HTML, Codex 프롬프트 | `class_materials/motor_calibration_2h/` |
| 08/28 | 아무것도 설치되지 않은 노트북용 수업 (설치 스크립트 `.ps1` 포함). 학생 배포용 V2 ZIP 구성 | `class_materials/fresh_install/`, `student_dist_v2/` |
| 09/18 | 로봇팔 실습 가이드 PPT (27장) + 실습 명령어 모음 | `class_materials/class_guide/` |
| 10/02 | "왜 설정할까 — 텔레오퍼레이션 개념 설명" PPT (20장). 키보드로 팔로워 조작하는 스크립트. 팔 쌍 캘리브레이션 (COM12 리더 / COM13 팔로워) | `class_materials/concepts/`, `scripts/keyboard_teleop_so101.py`, `calibration/*/com1*` |
| 10/14 | 손목 카메라 마운트 체결 문제 → 일체형 마운트 STL 확보 | `wrist_cam_mount/` |
| 10/23 | 팔로워 ID3(elbow_flex) 진단. 캘리브레이션 없이 상대 위치로 움직이는 텔레오퍼레이션 작성. 새 쌍 캘리브레이션 (COM9 리더 / COM12 팔로워) | `scripts/check_follower_motor3.py`, `scripts/teleop_so101_no_calibration.py`, `calibration/*/com9_leader.json`, `com12_follower.json` |
| 10/24 | `so101_follower` / `so101_leader` ID로 다시 캘리브레이션. `main` README가 쓰는 ID와 같음 | `calibration/*/so101_*.json` |

---

## 3. 파일별 설명

### 3-1. `scripts/` — 모터 진단·제어 (원본: `OneDrive\문서\lerobot-so101`)
Windows 전용입니다. 키 입력에 `msvcrt`를 쓰고, `lerobot.motors.feetech.FeetechMotorsBus`로 모터를 직접 다룹니다.

| 파일 | 하는 일 | 안전장치 |
|---|---|---|
| `teleop_so101_no_calibration.py` | 리더·팔로워의 **엔코더 원시값 차이**만 따라 움직이는 텔레오퍼레이션. 캘리브레이션 파일을 쓰거나 고치지 않음 | 몸체 ±20°, 집게 ±20% 범위 제한. 모터에 저장된 Min/Max 한계 준수. `--run` 없이 실행하면 읽기만 함. `--exclude-elbow`, `--exclude-wrist-roll`, `--recover-near-limit`(5° 이내 자동 복귀) 옵션 |
| `keyboard_teleop_so101.py` | 팔로워만 키보드로 조작 (1–6 관절 선택, A/D로 ±1°) | 저장된 캘리브레이션 중 맞는 파일을 자동으로 찾음. 범위를 벗어나면 시작하지 않음 |
| `check_follower_motor3.py` | ID3(팔꿈치)을 약 5°만 움직여 보고 부하·전류·전압·온도 확인 | 에러 상태이거나 범위 밖이면 움직이지 않음 |
| `safe_teleop_so101_1_4_only.py` | 1~4번 관절만 따라 움직이는 텔레오퍼레이션 (5·6번 제외), 20초 | 한 번에 최대 3°씩 |
| `test_so101_follower_456_direct.py` / `_56_raw.py` | 4·5·6번 모터를 하나씩 조금만 움직여 봄 (raw 버전은 Torque_Limit 350) | Enter를 눌러야 움직임 |
| `status_so101_follower_56.py` | 5·6번 레지스터 덤프 (모드, 토크, 부하, 전압, 온도, Status) | 읽기만 함 |
| `watch_so101_leader_456.py` | 리더 4·5·6번 위치를 실시간 출력 | 읽기만 함 |

> 주의: COM 포트 번호가 스크립트에 고정된 것이 있습니다 (COM7/8/12/13). 실행 전에 확인하세요.

### 3-2. `calibration/` — LeRobot 캘리브레이션 JSON
`~\.cache\huggingface\lerobot\calibration`를 그대로 복사했습니다. 다른 PC에서는 같은 위치에 넣으면 됩니다.

| ID | 만든 날짜 | 비고 |
|---|---|---|
| `my_so101_follower` / `my_so101_leader` | 05/13 | 첫 번째 쌍 |
| `my_so101_follower_2` / `my_so101_leader_2` | 06/12 | 옮기기 패키지에 들어 있는 쌍 |
| `com13_follower` / `com12_leader` | 10/02 | |
| `com12_follower` / `com9_leader` | 10/23 | |
| `so101_follower` / `so101_leader` | 10/24 | **`main` README와 같은 ID**. 합치면 이 파일을 쓰면 됨 |

### 3-3. `transfer_package/`
캘리브레이션이 끝난 팔 한 쌍(`_2`)을 다른 Windows PC에서 쓰기 위한 패키지입니다. 스크립트 01 설치 → 02 캘리브레이션 복사 → 03 포트 찾기 → 04 안전 텔레오퍼레이션 10초 → 05 일반 텔레오퍼레이션 순서입니다. 자세한 내용은 `README_설명서.txt`에 있습니다.

### 3-4. `class_materials/` — 수업자료
PPT는 Codex에서 `.mjs` 빌드 스크립트로 만들었습니다. 빌드 스크립트도 함께 넣었습니다.

| 폴더 | 내용 |
|---|---|
| `setup_intro_deck/` | SO-101 설치 소개 9장 (06/05) |
| `technical_class/` | 기술 수업 가이드 16장 (07/10) |
| `hardware_assembly/` | 조립 가이드 **빌드 스크립트와 출처 노트만** 있음 (아래 6절 참고) |
| `motor_calibration_2h/` | 모터 ID·캘리브레이션 2시간 수업 (전체본 9MB, 축약본), 수업 시작 HTML, Codex 프롬프트 |
| `fresh_install/` | 새 노트북 → 설치 → 캘리브레이션 2시간 수업, `SO101_처음설치.ps1` |
| `student_dist_v2/` | 학생에게 나눠 주는 ZIP 구성 (01 HTML → 02 설치 ps1 → 03 Codex 프롬프트 → 04 안내) |
| `class_guide/` | 로봇팔 실습 가이드 27장 (일반본, 수업용) + `SO101_실습_명령어.txt` |
| `concepts/` | "왜 설정할까" 텔레오퍼레이션 개념 설명 20장 |

수업 방식: 학생이 **ChatGPT 무료 계정의 Codex**에 프롬프트를 붙여 넣고, 한 단계씩 PowerShell 명령을 받아 실행합니다. Python 3.12와 `.venv`를 쓰고 Conda는 쓰지 않습니다.

### 3-5. `class_web_guide/`
학생용 정적 웹 가이드입니다 (`index.html`, `app.js`, `style.css`). Vercel 프로젝트 `so101-class-guide`에 연결되어 있었지만, 연결 정보가 든 `.vercel/` 폴더는 넣지 않았습니다.

### 3-6. `wrist_cam_mount/`
- `Wrist_Cam_Mount_32x32_UVC_Module_SO101.stl`: TheRobotStudio 공식 저장소의 **일체형 마운트**입니다. Wrist Roll(고정 집게)을 통째로 대체합니다.
- `preview.png`: STL 미리보기. 공식 조립 사진 2장도 있습니다.

---

## 4. 현재 상황과 남은 문제

1. **손목 카메라 마운트**: 헥스너트 마운트(SO101_Wrist_Cam_Hex-Nut)는 Wrist Roll에 육각 홈이 있어야 하는데, 이 팔의 Wrist Roll은 **원형 구멍**이라 체결이 안 됐습니다. 일체형 마운트 STL로 다시 출력하기로 했고, **아직 출력·조립 전**입니다. `main`의 `autograsp`는 손목 카메라가 있다고 가정하므로, 이 부품이 비전·모방학습 실습의 선행 조건입니다.
2. **팔로워 모터 문제 (확인 필요)**:
   - 5월: ID 5·6 (wrist_roll, gripper) 동작 문제를 진단했습니다.
   - 10/23: ID 3 (elbow_flex) 진단 스크립트를 만들었고, 텔레오퍼레이션에 `--exclude-elbow`와 `--recover-near-limit` 옵션을 넣었습니다.
   - 진단 결과는 파일로 남아 있지 않습니다. 실제로 고쳤는지 다시 확인해야 합니다.
3. **COM 포트가 계속 바뀜**: COM7/8 → COM12/13 → COM9/12로 바뀌었습니다. CH343 드라이버를 쓰고, USB를 꽂는 위치에 따라 번호가 달라집니다. 포트 번호를 정해 두거나, 실행할 때마다 확인해야 합니다.
4. **LeRobot 버전이 서로 다름**: `OneDrive\문서\lerobot-so101\.venv`는 0.5.1(pip), `~\.venv`는 0.6.1(pip), `main`은 0.5.2-dev 특정 커밋에 `patches/lerobot_so_follower.patch`를 적용해서 씁니다. 합칠 때 **`main`의 `setup.ps1` 방식으로 통일**하는 것을 추천합니다. `scripts/`는 `FeetechMotorsBus` API만 쓰므로 버전 차이 영향은 작을 것으로 보지만, 확인은 해야 합니다.
5. **모방학습**: 노트북 B에는 데이터셋·학습 결과가 없습니다. 이 부분은 `main`의 `autograsp`(노트북 A)가 기준입니다.

---

## 5. `main`과 합칠 때 참고

- `main`과 파일이 겹치지 않도록 전부 `laptop_b/` 아래에 두었습니다. 그래서 `git merge laptop-b-work`를 해도 충돌이 나지 않습니다.
- 합친 뒤 정리 제안:
  - `laptop_b/scripts/` → `tools/motor_diag/` 등으로 옮기기 (`autograsp/tools`와 역할이 다름)
  - `laptop_b/calibration/` → 노트북마다 다른 파일이므로 `.gitignore`에 넣을지 결정
  - `laptop_b/class_materials/` → `docs/`로 옮기기. 중복 버전(`fresh_install`, `student_dist_v2`)은 하나로 합치기
- 노트북 A에도 비슷한 진단 스크립트가 있다면 `teleop_so101_no_calibration.py`와 비교해 보세요. 범위 제한과 한계 복귀 로직은 이 스크립트가 더 꼼꼼합니다.

## 6. 저장소에 넣지 않은 것 (OneDrive에만 있음)

| 항목 | 이유 | 원본 위치 |
|---|---|---|
| 하드웨어 조립 PPT 2개 (48MB, 21MB), 조립 사진 약 40장 (장당 약 2MB) | 크기가 너무 큼 | `OneDrive\문서\outputs\so101-hardware-class\presentations\so101-hardware\` |
| 슬라이드 미리보기 PNG, `layout.json`, `inspect.ndjson` | 빌드할 때 생기는 중간 파일 | `OneDrive\문서\outputs\*` |
| `.venv`, `node_modules` | 다시 설치하면 생김 | — |
| `.vercel/` | 배포 계정 연결 정보 | `OneDrive\문서\apps\so101-class-guide\.vercel` |
