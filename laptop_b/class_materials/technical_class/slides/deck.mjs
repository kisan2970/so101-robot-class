const C = {
  bg: "#F4F7F5", paper: "#FFFFFF", ink: "#132522", muted: "#60706C",
  green: "#087F6C", greenSoft: "#DFF2ED", yellow: "#F2B944", yellowSoft: "#FFF2D1",
  red: "#CE5142", redSoft: "#FCEBE8", line: "#D8E1DE", code: "#14231F", white: "#FFFFFF",
};

function rect(ctx, slide, x, y, w, h, fill, line = C.line, width = 1, geometry = "rect") {
  return ctx.addShape(slide, { x, y, w, h, geometry, fill, line: ctx.line(line, width) });
}

function text(ctx, slide, x, y, w, h, value, size = 20, color = C.ink, bold = false, align = "left", face = "Malgun Gothic") {
  return ctx.addText(slide, { x, y, w, h, text: value, fontSize: size, color, bold, align, typeface: face,
    insets: { left: 0, right: 0, top: 0, bottom: 0 } });
}

function base(ctx, slide, n, kicker, title, subtitle = "") {
  rect(ctx, slide, 0, 0, ctx.W, ctx.H, C.bg, C.bg, 0);
  text(ctx, slide, 68, 42, 500, 24, kicker, 14, C.green, true);
  rect(ctx, slide, 68, 75, 72, 4, C.yellow, C.yellow, 0);
  text(ctx, slide, 68, 98, 1080, 82, title, 36, C.ink, true);
  if (subtitle) text(ctx, slide, 70, 186, 1040, 52, subtitle, 18, C.muted);
  rect(ctx, slide, 68, 657, 1080, 1.5, C.line, C.line, 0);
  text(ctx, slide, 68, 667, 760, 18, "SO-101 · LeRobot · Windows Teleoperation", 10, C.muted);
  text(ctx, slide, 1100, 667, 48, 18, String(n).padStart(2, "0"), 11, C.green, true, "right", "Aptos");
}

function codeBox(ctx, slide, x, y, w, h, code, size = 14) {
  rect(ctx, slide, x, y, w, h, C.code, C.code, 0);
  rect(ctx, slide, x, y, 5, h, C.green, C.green, 0);
  text(ctx, slide, x + 22, y + 17, w - 42, h - 30, code, size, "#E9F5F1", true, "left", "Consolas");
}

function card(ctx, slide, x, y, w, h, title, body, accent = C.green, fill = C.paper) {
  rect(ctx, slide, x, y, w, h, fill, C.line, 1);
  rect(ctx, slide, x, y, 7, h, accent, accent, 0);
  text(ctx, slide, x + 22, y + 18, w - 42, 30, title, 19, C.ink, true);
  text(ctx, slide, x + 22, y + 55, w - 42, h - 70, body, 15, C.muted);
}

function badge(ctx, slide, x, y, n, label, color = C.green) {
  rect(ctx, slide, x, y, 48, 48, color, color, 0, "ellipse");
  text(ctx, slide, x, y + 8, 48, 30, String(n), 21, C.white, true, "center", "Aptos");
  text(ctx, slide, x - 30, y + 58, 108, 46, label, 14, C.ink, true, "center");
}

function arrow(ctx, slide, x, y, label = "→") {
  text(ctx, slide, x, y, 50, 42, label, 28, C.green, true, "center");
}

function pill(ctx, slide, x, y, w, label, fill = C.greenSoft, color = C.green) {
  rect(ctx, slide, x, y, w, 40, fill, fill, 0);
  text(ctx, slide, x + 10, y + 9, w - 20, 22, label, 14, color, true, "center");
}

function robot(ctx, slide, x, y, label, mirrored = false) {
  rect(ctx, slide, x + 35, y + 145, 90, 24, C.ink, C.ink, 0);
  rect(ctx, slide, x + 70, y + 83, 18, 80, mirrored ? C.green : C.yellow, mirrored ? C.green : C.yellow, 0);
  rect(ctx, slide, x + 62, y + 75, 34, 34, C.paper, C.ink, 8, "ellipse");
  rect(ctx, slide, x + 74, y + 17, 18, 75, mirrored ? C.yellow : C.green, mirrored ? C.yellow : C.green, 0);
  rect(ctx, slide, x + 66, y + 8, 34, 34, C.paper, C.ink, 8, "ellipse");
  rect(ctx, slide, x + 24, y + 4, 48, 28, C.ink, C.ink, 0);
  text(ctx, slide, x, y + 183, 160, 28, label, 15, C.green, true, "center");
}

function slide01(presentation, ctx) {
  const s = presentation.slides.add();
  rect(ctx, s, 0, 0, ctx.W, ctx.H, C.bg, C.bg, 0);
  rect(ctx, s, 0, 0, 30, ctx.H, C.green, C.green, 0);
  text(ctx, s, 75, 70, 900, 34, "SO-101 CLASSROOM GUIDE", 15, C.green, true, "left", "Aptos");
  text(ctx, s, 75, 126, 690, 150, "SO-101 로봇팔은\n어떻게 움직일까?", 50, C.ink, true);
  text(ctx, s, 78, 298, 620, 80, "환경 설치부터 모터 통신, 캘리브레이션,\nTeleoperation까지 이해하는 기술 수업", 21, C.muted);
  robot(ctx, s, 825, 145, "LEADER ARM", false);
  arrow(ctx, s, 1000, 235);
  robot(ctx, s, 1060, 145, "FOLLOWER ARM", true);
  rect(ctx, s, 75, 490, 1080, 94, C.paper, C.line, 1);
  text(ctx, s, 100, 510, 230, 22, "오늘의 핵심 질문", 15, C.green, true);
  text(ctx, s, 100, 542, 1010, 30, "컴퓨터는 어떻게 12개의 모터를 구분하고 같은 움직임을 전달할까?", 23, C.ink, true);
  text(ctx, s, 75, 665, 600, 20, "Windows · Hugging Face LeRobot · Feetech STS3215", 11, C.muted);
  return s;
}

function slide02(presentation, ctx) {
  const s = presentation.slides.add(); base(ctx, s, 2, "SYSTEM OVERVIEW", "두 로봇팔은 컴퓨터를 통해 위치 정보를 주고받는다", "리더암과 팔로워암이 직접 연결되는 것이 아니라, LeRobot이 가운데에서 데이터를 전달한다.");
  const nodes = [[85,"Leader\nSTS3215"],[315,"CH343\nCOM 포트"],[545,"LeRobot\nPython"],[775,"CH343\nCOM 포트"],[1005,"Follower\nSTS3215"]];
  nodes.forEach(([x,l],i)=>{ rect(ctx,s,x,330,150,110,i===2?C.yellowSoft:C.greenSoft,C.green,1.5); text(ctx,s,x+12,354,126,60,l,18,C.ink,true,"center"); if(i<nodes.length-1) arrow(ctx,s,x+166,365); });
  text(ctx,s,85,490,1070,45,"사람의 손 → 현재 위치 읽기 → 각도로 변환 → 목표 위치 전송 → 모터 이동",20,C.ink,true,"center");
  return s;
}

function slide03(presentation, ctx) {
  const s = presentation.slides.add(); base(ctx,s,3,"SOFTWARE STACK","여러 프로그램이 층층이 역할을 나누어 로봇팔을 제어한다","각 도구의 이름보다 어떤 역할을 맡는지 이해하는 것이 중요하다.");
  const rows=[
    ["LeRobot","모터 설정 · 캘리브레이션 · Teleoperation",C.yellowSoft],
    ["Python + pyserial","명령 실행 · Windows COM 통신",C.greenSoft],
    ["가상환경 .venv","이 프로젝트만의 독립된 패키지 공간",C.paper],
    ["Windows + CH343","USB 장치를 COM 포트로 연결",C.paper]
  ];
  rows.forEach((r,i)=>{const y=292+i*75; rect(ctx,s,190,y,900,58,r[2],C.line,1); text(ctx,s,218,y+15,230,28,r[0],19,C.ink,true); text(ctx,s,470,y+15,590,28,r[1],17,C.muted);});
  return s;
}

function slide04(presentation, ctx) {
  const s = presentation.slides.add(); base(ctx,s,4,"ENVIRONMENT SETUP","가상환경을 만들고 SO-101 통신 패키지를 설치한다","PowerShell 명령을 순서대로 실행하면 프로젝트 전용 실행 환경이 준비된다.");
  codeBox(ctx,s,100,285,1080,250,'py -3.12 -m venv .venv\n.\\.venv\\Scripts\\python.exe -m pip install --upgrade pip\n.\\.venv\\Scripts\\pip.exe install "lerobot[feetech]" opencv-python pyserial',17);
  pill(ctx,s,165,565,250,"venv = 독립된 작업실"); pill(ctx,s,515,565,250,"feetech = 모터 통신"); pill(ctx,s,865,565,250,"pyserial = COM 통신");
  return s;
}

function slide05(presentation, ctx) {
  const s = presentation.slides.add(); base(ctx,s,5,"USB SERIAL","COM 포트는 컴퓨터가 로봇팔을 찾는 연결 주소다","CH343 칩은 USB 데이터를 모터가 사용하는 직렬 통신으로 변환한다.");
  card(ctx,s,85,285,340,210,"USB-Enhanced-SERIAL CH343","USB-직렬 변환 장치\n\nVID:PID = 1A86:55D3",C.green,C.paper);
  card(ctx,s,470,285,340,210,"COM10 / COM11","Windows가 장치에 붙이는 주소\n\nUSB 위치에 따라 변경 가능",C.yellow,C.paper);
  card(ctx,s,855,285,340,210,"Bluetooth COM은 제외","포트 목록에 보여도 SO-101 장치가 아님\n\nCH343 설명을 확인",C.red,C.paper);
  codeBox(ctx,s,270,540,740,62,'.\\.venv\\Scripts\\python.exe -m serial.tools.list_ports -v',15);
  return s;
}

function slide06(presentation, ctx) {
  const s = presentation.slides.add(); base(ctx,s,6,"MOTOR BUS","여섯 모터는 같은 통신선을 공유하는 직렬 버스로 연결된다","같은 선을 사용하므로 각 모터는 고유한 ID로 구분되어야 한다.");
  text(ctx,s,80,275,260,28,"Feetech STS3215",20,C.green,true);
  text(ctx,s,80,310,260,55,"통신 속도\n1,000,000 baud",18,C.ink,true);
  for(let i=0;i<6;i++){const x=330+i*135; badge(ctx,s,x,340,i+1,`Motor ${i+1}`,i<4?C.green:C.yellow); if(i<5) arrow(ctx,s,x+68,345);}
  rect(ctx,s,120,515,1040,72,C.yellowSoft,C.yellowSoft,0);
  text(ctx,s,145,535,990,32,"baudrate는 1초에 전송하는 비트 수이며, 모든 모터가 같은 통신 속도를 사용해야 한다.",18,C.ink,true,"center");
  return s;
}

function slide07(presentation, ctx) {
  const s = presentation.slides.add(); base(ctx,s,7,"MOTOR ID MAP","모터 ID는 각 관절에 붙이는 디지털 이름표다","Leader와 Follower는 서로 다른 COM 포트이므로 양쪽 모두 ID 1~6을 사용할 수 있다.");
  const names=["shoulder_pan\n베이스 좌우","shoulder_lift\n어깨 위아래","elbow_flex\n팔꿈치","wrist_flex\n손목 굽힘","wrist_roll\n손목 회전","gripper\n집게"];
  names.forEach((name,i)=>{const x=65+i*196; rect(ctx,s,x,305,170,190,C.paper,C.line,1); badge(ctx,s,x+61,330,i+1,"",i<4?C.green:C.yellow); text(ctx,s,x+14,415,142,60,name,15,C.ink,true,"center");});
  text(ctx,s,120,545,1040,35,"잘못된 ID → 다른 관절이 움직이거나, 두 모터가 동시에 응답하거나, 모터가 보이지 않는다.",19,C.red,true,"center");
  return s;
}

function slide08(presentation, ctx) {
  const s = presentation.slides.add(); base(ctx,s,8,"ID ASSIGNMENT","ID를 바꿀 때는 반드시 모터 한 개만 연결한다","같은 기본 ID의 모터가 여러 개 연결되면 같은 명령에 동시에 응답하여 충돌할 수 있다.");
  rect(ctx,s,80,270,1120,72,C.redSoft,C.redSoft,0); text(ctx,s,110,290,1060,35,"주의: 안내된 모터 1개 연결 → Enter → 분리 → 다음 모터 연결",20,C.red,true,"center");
  text(ctx,s,85,375,250,24,"LEADER ARM",13,C.green,true,"left","Aptos");
  codeBox(ctx,s,85,410,1110,72,'.\\.venv\\Scripts\\lerobot-setup-motors.exe --teleop.type=so101_leader --teleop.port=COM10 --teleop.id=my_so101_leader',13);
  text(ctx,s,85,505,250,24,"FOLLOWER ARM",13,C.green,true,"left","Aptos");
  codeBox(ctx,s,85,540,1110,72,'.\\.venv\\Scripts\\lerobot-setup-motors.exe --robot.type=so101_follower --robot.port=COM11 --robot.id=my_so101_follower',13);
  return s;
}

function slide09(presentation, ctx) {
  const s = presentation.slides.add(); base(ctx,s,9,"CALIBRATION THEORY","캘리브레이션은 모터 숫자를 실제 관절 움직임으로 해석하는 과정이다","STS3215의 원시 위치값과 로봇팔의 기준 위치·안전 범위를 연결한다.");
  text(ctx,s,95,278,1090,30,"STS3215 Raw Position",18,C.green,true,"center");
  rect(ctx,s,140,350,1000,22,C.line,C.line,0); rect(ctx,s,140,350,500,22,C.green,C.green,0); rect(ctx,s,640,350,500,22,C.yellow,C.yellow,0);
  [[120,"0"],[600,"2048"],[1085,"4095 → 0"]].forEach(([x,l])=>text(ctx,s,x,390,120,26,l,18,C.ink,true,"center","Aptos"));
  card(ctx,s,100,465,310,130,"Homing offset","중간 자세를 기준 위치로 맞추는 보정값",C.green);
  card(ctx,s,485,465,310,130,"Range min / max","관절이 사용할 최소·최대 위치",C.yellow);
  card(ctx,s,870,465,310,130,"Drive mode","모터의 회전 방향을 맞추는 설정",C.red);
  return s;
}

function slide10(presentation, ctx) {
  const s = presentation.slides.add(); base(ctx,s,10,"CALIBRATION PRACTICE","중간 자세에서 시작해 각 관절의 실제 사용 범위를 기록한다","베이스 정면, 어깨 중간, 팔꿈치 약 90도, 손목 중간, 집게 반쯤 열린 자세가 좋다.");
  const labels=["베이스 정면","어깨 중간","팔꿈치 90°","집게 반쯤"];
  labels.forEach((l,i)=>{pill(ctx,s,80+i*285,270,220,l,i%2?C.yellowSoft:C.greenSoft,i%2?C.ink:C.green); if(i<3) arrow(ctx,s,305+i*285,271);});
  text(ctx,s,80,350,250,22,"FOLLOWER",13,C.green,true,"left","Aptos");
  codeBox(ctx,s,80,382,1120,70,'.\\.venv\\Scripts\\lerobot-calibrate.exe --robot.type=so101_follower --robot.port=COM11 --robot.id=my_so101_follower',13);
  text(ctx,s,80,478,250,22,"LEADER",13,C.green,true,"left","Aptos");
  codeBox(ctx,s,80,510,1120,70,'.\\.venv\\Scripts\\lerobot-calibrate.exe --teleop.type=so101_leader --teleop.port=COM10 --teleop.id=my_so101_leader',13);
  text(ctx,s,80,602,1120,25,"wrist_roll(ID 5)은 전체 회전 관절이라 일반 범위 기록표에서 제외될 수 있다.",16,C.muted,true,"center");
  return s;
}

function slide11(presentation, ctx) {
  const s = presentation.slides.add(); base(ctx,s,11,"CONTROL LOOP","Teleoperation은 읽기와 전송을 초당 여러 번 반복하는 제어 루프다","Leader의 현재 위치가 Follower의 목표 위치로 바뀌어 전달된다.");
  const steps=[["1","Present_Position\n읽기"],["2","Calibration\n각도 변환"],["3","Goal_Position\n전송"],["4","Follower\n이동"]];
  steps.forEach((a,i)=>{const x=80+i*290; rect(ctx,s,x,320,220,145,i%2?C.yellowSoft:C.greenSoft,C.line,1); badge(ctx,s,x+86,340,a[0],"",i%2?C.yellow:C.green); text(ctx,s,x+20,410,180,55,a[1],17,C.ink,true,"center"); if(i<3) arrow(ctx,s,x+235,370);});
  rect(ctx,s,230,520,820,62,C.paper,C.green,1.5); text(ctx,s,255,538,770,30,"fps = 15  →  약 1초에 15번 위치를 읽고 전달",20,C.green,true,"center");
  return s;
}

function slide12(presentation, ctx) {
  const s = presentation.slides.add(); base(ctx,s,12,"SAFE TELEOP","처음에는 이동량·속도·시간을 제한해 위험을 줄인다","안전 테스트가 정상일 때만 일반 Teleoperation으로 넘어간다.");
  codeBox(ctx,s,70,270,1140,150,'.\\.venv\\Scripts\\lerobot-teleoperate.exe --robot.type=so101_follower --robot.port=COM11 --robot.id=my_so101_follower --robot.max_relative_target=3 --teleop.type=so101_leader --teleop.port=COM10 --teleop.id=my_so101_leader --fps=15 --teleop_time_s=10',12);
  card(ctx,s,70,455,260,135,"max_relative_target=3","한 번에 큰 위치 변화가 전달되지 않도록 제한",C.green);
  card(ctx,s,365,455,260,135,"fps=15","1초에 실행하는 제어 루프의 횟수",C.yellow);
  card(ctx,s,660,455,260,135,"teleop_time_s=10","10초 뒤 자동으로 프로그램 종료",C.green);
  card(ctx,s,955,455,260,135,"전원 스위치","통신이 끊기면 소프트웨어가 토크를 못 풀 수 있음",C.red);
  return s;
}

function slide13(presentation, ctx) {
  const s = presentation.slides.add(); base(ctx,s,13,"ERROR DIAGNOSIS","오류 메시지는 고장 위치를 알려주는 진단 정보다","메시지의 핵심 단어를 보고 포트·ID·전원·기구 문제를 나누어 확인한다.");
  const rows=[
    ["Missing motor IDs","ID · 케이블 · 전원"],
    ["Could not connect on port","COM 번호 · 다른 프로그램 점유"],
    ["Incorrect status packet","중복 ID · 접촉 불량"],
    ["There is no status packet","전원 · baudrate · 통신선"],
    ["Overload error","기구 간섭 · 과도한 토크"],
    ["ClearCommError / Access denied","USB 끊김 · 허브 · 절전 설정"]
  ];
  text(ctx,s,95,260,470,25,"오류 메시지",15,C.green,true); text(ctx,s,640,260,490,25,"먼저 확인할 것",15,C.green,true);
  rows.forEach((r,i)=>{const y=298+i*51; rect(ctx,s,80,y,1120,43,i%2?C.paper:C.greenSoft,C.line,0.5); text(ctx,s,100,y+10,500,24,r[0],15,i===4?C.red:C.ink,true,"left","Consolas"); text(ctx,s,650,y+10,500,24,r[1],15,C.muted,true);});
  rect(ctx,s,175,620,930,36,C.redSoft,C.redSoft,0); text(ctx,s,190,628,900,22,"이상한 움직임·소음·통신 끊김이 생기면 먼저 손을 떼고 전원을 끈다.",16,C.red,true,"center");
  return s;
}

function slide14(presentation, ctx) {
  const s = presentation.slides.add(); base(ctx,s,14,"FULL WORKFLOW","설치부터 조종까지는 여덟 번의 확인 과정으로 완성된다","각 단계가 정상일 때만 다음 단계로 넘어가면 문제 원인을 빠르게 찾을 수 있다.");
  const items=["Python 환경","LeRobot 설치","COM 포트","모터 ID","통신 확인","캘리브레이션","안전 Teleop","일반 Teleop"];
  items.forEach((l,i)=>{const row=i<4?0:1; const col=i%4; const x=85+col*290; const y=285+row*170; badge(ctx,s,x,y,i+1,"",i===7?C.yellow:C.green); text(ctx,s,x+60,y+10,200,30,l,17,C.ink,true); if(col<3) arrow(ctx,s,x+240,y+5);});
  rect(ctx,s,180,570,920,58,C.greenSoft,C.greenSoft,0); text(ctx,s,200,586,880,30,"성공 기준: 12개 모터 인식 · 방향 일치 · 과부하 없음 · USB 연결 안정",19,C.green,true,"center");
  return s;
}

function slide15(presentation, ctx) {
  const s = presentation.slides.add(); base(ctx,s,15,"APPENDIX A","수업용 핵심 명령어 모음","실제 COM 번호와 로봇 ID는 사용하는 컴퓨터와 장비에 맞게 바꾼다.");
  const cmds=[
    ["포트 확인",'.\\.venv\\Scripts\\python.exe -m serial.tools.list_ports -v'],
    ["Follower 캘리브레이션",'.\\.venv\\Scripts\\lerobot-calibrate.exe --robot.type=so101_follower --robot.port=COM11 --robot.id=my_so101_follower'],
    ["Leader 캘리브레이션",'.\\.venv\\Scripts\\lerobot-calibrate.exe --teleop.type=so101_leader --teleop.port=COM10 --teleop.id=my_so101_leader'],
    ["일반 Teleoperation",'.\\.venv\\Scripts\\lerobot-teleoperate.exe --robot.type=so101_follower --robot.port=COM11 --robot.id=my_so101_follower --teleop.type=so101_leader --teleop.port=COM10 --teleop.id=my_so101_leader']
  ];
  cmds.forEach((r,i)=>{const y=250+i*98; text(ctx,s,75,y,220,22,r[0],13,C.green,true); codeBox(ctx,s,280,y-5,920,70,r[1],i===3?10.5:11.5);});
  return s;
}

function slide16(presentation, ctx) {
  const s = presentation.slides.add(); base(ctx,s,16,"APPENDIX B","수업을 시작하기 전 이 체크리스트를 확인한다","하드웨어와 소프트웨어 상태를 먼저 확인하면 수업 중 갑작스러운 중단을 줄일 수 있다.");
  const checks=[
    ["전원","Leader와 Follower 전원 및 비상 OFF 위치"],
    ["USB","데이터 케이블 2개와 CH343 포트 확인"],
    ["모터","양쪽 팔에서 ID 1~6이 모두 응답"],
    ["펌웨어","각 팔의 모터 펌웨어 버전 통일"],
    ["캘리브레이션","올바른 robot.id와 calibration JSON 확인"],
    ["작업 공간","관절 이동 범위 안의 사람과 물건 제거"]
  ];
  checks.forEach((r,i)=>{const col=i%2,row=Math.floor(i/2); const x=85+col*580,y=260+row*115; rect(ctx,s,x,y,535,88,C.paper,C.line,1); rect(ctx,s,x+20,y+24,34,34,C.bg,C.green,2); text(ctx,s,x+75,y+17,170,25,r[0],18,C.ink,true); text(ctx,s,x+75,y+47,430,24,r[1],14,C.muted);});
  rect(ctx,s,230,610,820,44,C.yellowSoft,C.yellowSoft,0); text(ctx,s,250,620,780,24,"가장 중요한 장비는 오류를 발견했을 때 즉시 멈추는 사람의 판단이다.",17,C.ink,true,"center");
  return s;
}

const SLIDES=[slide01,slide02,slide03,slide04,slide05,slide06,slide07,slide08,slide09,slide10,slide11,slide12,slide13,slide14,slide15,slide16];
export async function renderSlide(presentation, ctx, index) { return SLIDES[index - 1](presentation, ctx); }

