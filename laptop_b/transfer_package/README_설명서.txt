SO-101 로봇팔 다른 컴퓨터에서 실행하기
=====================================

이 압축 파일은 이미 캘리브레이션이 끝난 SO-101 로봇팔 한 쌍을
다른 Windows 컴퓨터에서도 사용할 수 있게 준비한 패키지입니다.

포함된 것
---------
1. 캘리브레이션 파일
   - follower arm: my_so101_follower_2.json
   - leader arm: my_so101_leader_2.json

2. PowerShell 스크립트
   - scripts\01_install_lerobot_env.ps1
   - scripts\02_install_calibration_files.ps1
   - scripts\03_find_ports.ps1
   - scripts\04_test_teleop_safe.ps1
   - scripts\05_teleop_normal.ps1


중요 개념
---------
모터 ID는 모터 안에 저장되어 있으므로 다른 컴퓨터로 옮겨도 유지됩니다.
하지만 캘리브레이션은 컴퓨터 파일로 저장되므로 새 컴퓨터에 복사해야 합니다.
COM 포트 번호는 컴퓨터마다 달라지므로 반드시 새 컴퓨터에서 다시 확인해야 합니다.


준비물
------
- Windows 노트북 또는 PC
- SO-101 leader arm
- SO-101 follower arm
- USB 데이터 케이블 2개
- 가능하면 USB 허브보다 PC 본체 USB 포트 사용


전체 순서
---------
1. 이 압축 파일을 원하는 위치에 압축 해제합니다.
2. PowerShell을 엽니다.
3. 압축 해제한 폴더로 이동합니다.
4. LeRobot 환경을 설치합니다.
5. 캘리브레이션 파일을 복사합니다.
6. leader/follower COM 포트를 확인합니다.
7. 안전 제한 teleop를 먼저 실행합니다.
8. 정상 동작하면 일반 teleop를 실행합니다.


0단계: PowerShell 실행 정책 문제 해결
-------------------------------------
스크립트 실행이 막히면 PowerShell에서 아래 명령을 한 번 실행합니다.

Set-ExecutionPolicy -Scope CurrentUser RemoteSigned


1단계: LeRobot 환경 설치
-----------------------
압축 해제한 폴더에서 실행합니다.

.\scripts\01_install_lerobot_env.ps1

이 스크립트는 현재 폴더에 lerobot-so101 폴더를 만들고,
Python 가상환경과 LeRobot을 설치합니다.


2단계: 캘리브레이션 파일 복사
----------------------------
압축 해제한 폴더에서 실행합니다.

.\scripts\02_install_calibration_files.ps1

이 스크립트는 캘리브레이션 파일을 현재 Windows 사용자 계정의
LeRobot calibration 폴더로 복사합니다.


3단계: COM 포트 확인
-------------------
leader arm과 follower arm을 USB로 연결한 뒤 실행합니다.

.\scripts\03_find_ports.ps1

출력에서 Bluetooth COM 포트는 무시합니다.
아래처럼 USB-Enhanced-SERIAL CH343으로 보이는 포트가 로봇팔입니다.

예시:
COM10  USB-Enhanced-SERIAL CH343
COM11  USB-Enhanced-SERIAL CH343

어느 포트가 leader인지 follower인지 모르면 한쪽 USB를 뽑았다가 다시 확인합니다.


4단계: 안전 제한 teleop 테스트
------------------------------
처음에는 반드시 안전 제한 테스트부터 합니다.

.\scripts\04_test_teleop_safe.ps1

스크립트가 leader 포트와 follower 포트를 물어봅니다.
예를 들어 leader가 COM10, follower가 COM11이면 그대로 입력합니다.

처음 실행할 때 확인할 것:
- 로봇 주변에 물건이 없는지
- 전원 스위치를 바로 끌 수 있는지
- 갑자기 튀지 않는지
- 방향이 맞는지
- 이상한 소리나 과부하가 없는지


5단계: 일반 teleop 실행
-----------------------
안전 테스트가 정상일 때만 실행합니다.

.\scripts\05_teleop_normal.ps1


문제 해결
---------
1. COM 포트가 안 보일 때
   - USB 케이블이 데이터 케이블인지 확인
   - USB 허브 말고 본체 포트에 직접 연결
   - CH343 드라이버 확인

2. Could not connect on port 오류
   - COM 번호가 맞는지 확인
   - FD 프로그램이 켜져 있으면 종료
   - USB를 뺐다 다시 꽂기

3. Missing motor IDs 오류
   - 모터 ID 1~6 설정이 잘못되었거나 케이블 연결 문제
   - FD 프로그램에서 1,2,3,4,5,6이 모두 보이는지 확인

4. 시작하자마자 크게 튀는 경우
   - 즉시 전원을 끔
   - 캘리브레이션 파일이 이 로봇팔과 맞는지 확인
   - 필요하면 해당 컴퓨터에서 다시 캘리브레이션

5. 방향이 이상한 경우
   - leader/follower 포트를 반대로 넣었는지 확인
   - 캘리브레이션을 다시 진행


사용하는 ID 이름
----------------
이 패키지는 아래 ID 이름을 사용합니다.

leader arm:
my_so101_leader_2

follower arm:
my_so101_follower_2

스크립트도 이 이름을 기준으로 작성되어 있습니다.

