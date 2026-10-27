import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
import sharp from 'sharp';
const root=path.dirname(fileURLToPath(import.meta.url));
const work=path.join(root,'class-guide'), preview=path.join(work,'preview');
const skill='C:/Users/wotjr/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations';
const python='C:/Users/wotjr/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe';
const source='https://huggingface.co/docs/lerobot/so101';
const install='https://huggingface.co/docs/lerobot/main/en/installation';
const project="$Project = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'lerobot-so101'";
const deck=[
{title:'SO-101 로봇팔 실습',sub:'Windows 설치부터 모터 번호 지정, 캘리브레이션까지',lines:['조립을 마친 리더암과 팔로워암 한 쌍','2시간 수업 / 명령어는 PowerShell에서 실행'],note:'본 수업의 필수 목표는 양쪽 팔의 캘리브레이션 저장이다. 텔레오피는 교사 확인 후 선택 실습으로 진행한다.'},
{title:'수업 순서',lines:['00~10분   장비와 안전 확인','10~40분   Python과 LeRobot 설치','40~55분   USB 연결과 COM 포트 확인','55~90분   리더·팔로워 모터 ID 지정','90~120분   중간 자세 설정, 범위 기록, 저장'],note:'시간은 수업 운영 예시다. 다운로드와 오류 해결 시간을 고려해 교사는 설치를 사전 점검한다.'},
{title:'리더암과 팔로워암',lines:['리더암: 사람이 손으로 움직이는 조종용 팔','팔로워암: 명령을 받아 모터로 움직이는 팔','COM 포트: 컴퓨터가 USB 장치를 구분하는 연결 번호','모터 ID: 한 팔 안에서 각 관절을 구분하는 번호'],note:'COM 번호와 모터 ID는 다르다. 두 팔 모두 ID 1~6을 쓰지만, 서로 다른 제어 보드와 COM 포트에 연결한다.'},
{title:'준비물과 모터 구분',lines:['Windows 노트북, 인터넷, 충전기','조립된 팔 한 쌍, 제어 보드, 데이터 통신 USB 케이블','모터 정격에 맞는 전원 어댑터와 팔 고정 장치','모터 라벨의 전압·기어비와 키트 부품표 확인','같은 STS3215라도 사양이 다를 수 있음'],callout:'모터를 강한 것·약한 것으로만 나누지 말고 관절별 사양 확인',note:'사용자 사례에서는 서로 다른 사양의 모터가 섞였다. 공식 SO-101 구성과 판매 키트 구성이 다를 수 있으므로 판매처 부품표를 우선 대조한다. 외형만으로 전압이나 기어비를 판단하지 않는다.'},
{title:'전원과 케이블',lines:['팔을 책상에 고정하고 주변 물건을 치운다.','모터 케이블을 교체할 때는 모터 전원을 끈다.','배선을 확인한 다음 전원을 켠다.','관절과 집게 사이에 손가락을 넣지 않는다.','멈춤·이상 소음·과부하가 발생하면 실습을 중단한다.'],callout:'전원을 끄면 팔이 내려올 수 있으므로 안전한 받침 준비',note:'소프트웨어 종료가 실패하면 토크가 남아 있을 수 있다. 위험 시 물리 전원을 차단한다. 작동 중인 팔을 손으로 붙잡아 억지로 멈추지 않는다.'},
{title:'PowerShell 사용법',lines:['시작 메뉴에서 PowerShell을 검색해 연다.','명령어만 복사한다. 앞의 PS C:\\...> 표시는 복사하지 않는다.','한 단계가 끝나고 입력 표시가 돌아오면 다음 단계를 실행한다.','오류가 나오면 마지막 오류 문장을 확인한다.'],callout:'이 자료의 명령어는 줄 끝에 역슬래시를 붙이지 않음',note:'Linux 문법의 줄 연속 문자 \\를 PowerShell에 붙이면 60\\ 같은 인수 오류가 생길 수 있다. 각 코드 블록을 그대로 사용한다.'},
{title:'Python 설치',code:'winget install --id Python.Python.3.12 -e --source winget\n\n# 설치 후 PowerShell을 다시 열고 확인\npy -3.12 --version',lines:['Python 3.12.x가 나오면 다음 단계로 진행'],callout:'winget이 없으면 python.org에서 Python 3.12 설치',note:'Python 공식 Windows 설치 파일을 사용한다. 설치 권한 제한이나 학교 네트워크 차단은 교사에게 알린다.',src:install},
{title:'작업 폴더와 가상환경',code:project+'\nNew-Item -ItemType Directory -Force -Path $Project | Out-Null\nSet-Location -LiteralPath $Project\npy -3.12 -m venv .venv',lines:['문서 폴더에 lerobot-so101을 만든다.','.venv는 이 실습에서 사용할 Python 공간이다.'],note:'실제 문서 위치를 조회하므로 OneDrive와 한글 문서 폴더에서도 사용할 수 있다. 이후 .venv 내부 실행 파일을 직접 호출하므로 Activate.ps1 실행이 필요 없다.',src:install},
{title:'LeRobot 설치',code:'.\\.venv\\Scripts\\python.exe -m pip install --upgrade pip\n\n.\\.venv\\Scripts\\python.exe -m pip install "lerobot[core_scripts,feetech]" pyserial',lines:['다운로드와 설치가 끝날 때까지 기다린다.','에러가 나오면 다음 명령어를 실행하지 않는다.'],note:'새 Windows에서 실제 설치 성공은 교사가 동일 노트북 환경에서 사전 점검해야 한다. 이 자료 생성 과정에서 학생 기기에 설치를 실행하지 않았다. 카메라 실습은 없으므로 별도 OpenCV 설치 단계는 생략한다.',src:install},
{title:'설치 확인과 다시 접속',code:project+'\nSet-Location -LiteralPath $Project\n.\\.venv\\Scripts\\python.exe -m pip show lerobot\n.\\.venv\\Scripts\\lerobot-calibrate.exe --help',lines:['LeRobot 정보와 도움말이 나오면 설치 확인 완료','PowerShell을 새로 열었을 때도 위의 첫 두 줄부터 실행'],note:'명령어를 찾을 수 없으면 작업 폴더와 .venv 설치 여부를 먼저 확인한다.',src:install},
{title:'USB 포트 확인',code:'.\\.venv\\Scripts\\python.exe -m serial.tools.list_ports -v',lines:['팔을 한 개씩 연결해 새로 나타나는 COM 번호를 찾는다.','USB Serial / CH343 등의 장치 이름을 확인한다.','Bluetooth 직렬 포트는 로봇팔 포트가 아니다.'],callout:'리더: COM____     팔로워: COM____',note:'USB를 뺐다 연결해 비교한다. 허브나 USB 단자를 바꾸면 번호가 달라질 수 있다. 장치 관리자에서 포트(COM 및 LPT)도 확인 가능하다.'},
{title:'이후 명령어에서 사용할 포트',code:"$LeaderPort = 'COM10'\n$FollowerPort = 'COM11'",lines:['COM10과 COM11은 예시다. 실제로 찾은 번호로 바꾼다.','한 PowerShell 창에서 계속 진행한다.','창을 새로 열면 작업 폴더 이동과 포트 변수 설정을 다시 한다.'],note:'리더만 연결한 상태라면 리더 포트부터 확인한다. 팔로워 연결 후 해당 변수도 실제 번호로 지정한다.'},
{title:'모터 ID와 관절 이름',lines:['1   shoulder_pan       밑부분 좌우 회전','2   shoulder_lift        어깨 올리고 내리기','3   elbow_flex           팔꿈치 굽히기','4   wrist_flex             손목 굽히기','5   wrist_roll             손목 돌리기','6   gripper                 집게 열고 닫기'],note:'리더암 6번은 집게 조종 손잡이에 대응한다. 두 팔 각각 1~6을 지정한다.'},
{title:'ID 지정 때의 연결',lines:['제어 보드에 대상 모터 한 개만 연결한다.','그 모터 뒤에 다른 모터가 연결되어 있으면 안 된다.','화면에 나온 관절 이름을 확인한다.','연결 확인 후 전원을 켜고 Enter를 누른다.','설정 완료를 확인하고 전원을 끈 뒤 다음 모터로 바꾼다.'],callout:'화면 안내 순서에 따라 진행 / 보통 집게 6번부터 시작',note:'모터 전원만 끄고 USB는 유지한다. 전원 차단 시 COM 포트도 사라지는 보드라면 교사가 연결 방법을 확인한다. setup 명령은 ID와 통신 속도를 설정한다.'},
{title:'리더암 모터 ID 지정',code:'.\\.venv\\Scripts\\lerobot-setup-motors.exe --teleop.type=so101_leader --teleop.port=$LeaderPort',lines:["gripper motor id set to 6: 집게 번호 설정 완료",'다음 관절 이름이 나오면 전원을 끄고 모터를 교체한다.','6개 모두 완료하면 명령어가 끝난다.'],note:'입력 대기 문구를 읽고 그때 요구하는 관절만 연결한다. 이미 ID가 설정된 중고 모터도 단독 연결로 설정한다.'},
{title:'팔로워암 모터 ID 지정',code:'.\\.venv\\Scripts\\lerobot-setup-motors.exe --robot.type=so101_follower --robot.port=$FollowerPort',lines:['리더암과 같은 방법으로 6개를 설정한다.','완료 후 전원을 끄고 모터 케이블을 모두 연결한다.','제어 보드에서 각 모터로 이어지는 연결을 확인한다.'],note:'팔로워 전원과 모터 정격을 확인한다. 두 팔의 부품을 섞지 않는다.'},
{title:'캘리브레이션의 의미',lines:['관절의 기준 위치와 움직일 범위를 맞추는 작업','모터 ID 지정이 끝난 다음 진행','리더와 팔로워를 각각 측정','새 팔에 이전 팔의 보정 파일을 그대로 재사용하지 않음'],note:'calibration JSON이 저장됐다는 사실만으로 정상 구동이 보장되지는 않는다. 센서 위치 읽기와 모터 구동은 별도로 확인한다.'},
{title:'처음 잡는 자세',lines:['관절마다 움직일 수 있는 범위의 중간에 둔다.','팔꿈치나 어깨를 끝까지 펴거나 접지 않는다.','집게는 중간 정도 열고 손목 케이블에 여유를 둔다.','리더와 팔로워의 대응 관절 방향을 비슷하게 맞춘다.'],callout:'중간 자세를 만든 뒤 화면 안내에 따라 Enter',note:'교사가 실물로 자세를 보여준다. 관절 축과 링크 방향을 기준으로 비교한다. 기준이 크게 어긋나면 구동 시작 시 큰 위치 차이가 생길 수 있다.'},
{title:'팔로워암 캘리브레이션',code:'.\\.venv\\Scripts\\lerobot-calibrate.exe --robot.type=so101_follower --robot.port=$FollowerPort --robot.id=student_follower',lines:['기존 보정 파일 사용 질문이 나오면 c 입력 후 Enter','중간 자세 확인 질문에서 자세를 잡고 Enter'],note:'student_follower는 이 팔의 보정 파일 이름이다. 다른 팔에는 다른 ID를 사용한다. 기존 파일 질문에서 Enter만 누르면 재측정하지 않고 파일을 사용한다.'},
{title:'움직임 범위 기록',lines:['각 관절을 손으로 천천히 한 개씩 움직인다.','충돌하지 않는 사용 범위 양쪽 끝까지 움직인다.','MIN은 최솟값, POS는 현재값, MAX는 최댓값이다.','측정할 관절의 MIN과 MAX가 바뀌는지 확인한다.','완료 후 Enter를 누르고 저장 메시지를 확인한다.'],callout:'Calibration saved to ...json',note:'토크가 풀린 상태에서도 무리한 힘을 주지 않는다. 기본 SO follower 코드의 wrist_roll은 범위 측정에서 빠지고 0~4095로 설정된다. 실제 안내 문구를 따른다.'},
{title:'5번 손목과 위치값 경계',lines:['기본 설정에서는 wrist_roll이 범위 기록 표에서 빠질 수 있다.','표에 없다는 이유만으로 5번 모터 고장으로 판단하지 않는다.','원시 위치값 4095 다음이 0으로 바뀌는 것은 한 회전의 경계다.','사용 범위에서 값이 크게 튀면 교사에게 확인받고 재측정한다.'],callout:'기록 제외를 임의로 해제하거나 파일 숫자를 직접 고치지 않음',note:'현재 설치된 so_follower.py는 wrist_roll을 제외한 관절을 측정한 뒤 wrist_roll 범위를 0과 4095로 저장한다. 경계 통과 자체만으로 고장은 아니지만 잘못된 기준 자세와 범위는 불연속 명령으로 이어질 수 있다. 리더·팔로워 중간 자세와 조립 방향을 점검한다.'},
{title:'리더암 캘리브레이션',code:'.\\.venv\\Scripts\\lerobot-calibrate.exe --teleop.type=so101_leader --teleop.port=$LeaderPort --teleop.id=student_leader',lines:['리더암도 중간 자세와 움직임 범위를 측정한다.','다시 측정할 때는 c 입력 후 Enter','Calibration saved to 메시지가 나오는지 확인'],note:'팔로워 측정 때와 대응되는 관절 방향을 확인한다. 손잡이를 무리하게 꺾지 않는다.'},
{title:'연결 오류 확인',lines:['Could not connect / Access denied','COM 번호 확인. FD와 같은 포트를 쓰는 프로그램 종료.','Missing motor IDs / No status packet','전원을 끄고 해당 모터 케이블·전원·ID 확인.','ClearCommError / Incorrect status packet','실습 중단. USB 케이블·허브·전원을 확인하고 포트 재검색.'],note:'교사는 오류 전체와 마지막 문장을 함께 확인한다. 통신이 끊긴 상태에서는 토크 해제 명령도 실패할 수 있다. 허브 없이 직접 연결하여 비교하는 것도 진단 방법이다.'},
{title:'멈춤·과부하·큰 움직임',lines:['Overload: 구동을 멈추고 전원을 끈다.','간섭, 모터 사양, 정격 전압, 부하를 교사와 확인한다.','펌웨어 불일치: 교사가 모델에 맞는 공식 절차로 처리한다.','시작할 때 크게 움직임: 중간 자세와 보정 파일을 확인한다.','손으로 움직일 때 값이 변해도 구동이 정상이라는 뜻은 아니다.'],callout:'과부하 보호를 끄거나 토크를 높여 억지로 진행하지 않음',note:'사용자 대화의 실제 오류 유형을 일반화한 점검 항목이다. 이 메시지만으로 부품 고장을 단정하지 않는다. 캘리브레이션 반복만으로 전기·기계 문제가 해결되지는 않는다.'},
{title:'수업 완료 확인',lines:['리더·팔로워 COM 번호를 기록했는가?','두 팔의 모터 ID 1~6을 설정했는가?','양쪽 캘리브레이션 저장 메시지를 확인했는가?','사용한 robot.id와 teleop.id를 기록했는가?','안전한 받침 위에 팔을 두고 전원을 껐는가?'],note:'JSON 경로는 저장 메시지에서 확인한다. 같은 팔을 다른 PC에서 사용할 때 보정 파일도 함께 옮기거나 다시 캘리브레이션한다. 여기까지가 2시간 필수 수업이다.'},
{title:'선택 실습: 텔레오피 준비',lines:['교사가 6개 관절의 구동 상태와 보정값을 확인한다.','두 팔을 비슷한 자세로 놓고 주변 공간을 비운다.','한 사람이 리더를 조작하고 다른 사람은 전원 차단을 준비한다.','처음에는 작은 범위에서 한 관절씩 확인한다.'],callout:'오류나 갑작스러운 움직임이 있으면 바로 중단',note:'선택 실습은 필수 2시간 분량 이후 또는 시간이 남을 때 진행한다. 카메라나 AI 학습을 포함하지 않는다.'},
{title:'선택 실습: 1분 텔레오피',code:'.\\.venv\\Scripts\\lerobot-teleoperate.exe --robot.type=so101_follower --robot.port=$FollowerPort --robot.id=student_follower --teleop.type=so101_leader --teleop.port=$LeaderPort --teleop.id=student_leader --fps=15 --teleop_time_s=60 --robot.max_relative_target=3',lines:['Ctrl+C로 중단 / 60초가 지나면 자동 종료','종료 시 토크가 풀려 팔이 내려올 수 있음'],note:'max_relative_target은 한 제어 주기의 목표 위치 차이를 제한한다. 정확한 속도 제한이나 충돌 방지 기능은 아니다. 단위는 관절 정규화 설정에 따라 다르다. 통신 장애 시 소프트웨어 종료만으로 토크 해제를 보장하지 못한다.'}
];
await fs.mkdir(preview,{recursive:true});await fs.mkdir(path.join(work,'output'),{recursive:true});
const p=Presentation.create({slideSize:{width:1280,height:720}});
function t(s,str,x,y,w,h,size=27,color='#222827',bold=false,font='Malgun Gothic'){const q=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});q.text=str;q.text.style={fontSize:size,color,bold,typeface:font};q.text.insets={left:0,right:0,top:0,bottom:0};return q;}
for(let i=0;i<deck.length;i++){
 const d=deck[i],s=p.slides.add();s.background.fill='#FFFFFF';
 t(s,d.title,70,55,1140,80,i===0?52:38,'#183B32',true);
 if(d.sub)t(s,d.sub,72,170,1120,70,29);
 if(d.code){const formatted=d.code.split('\n').flatMap(line=>{const parts=[];while(line.length>86){const cut=line.lastIndexOf(' ',84);if(cut<1)break;parts.push(line.slice(0,cut)+' `');line='  '+line.slice(cut+1);}parts.push(line);return parts;}).join('\n');t(s,formatted,72,185,1136,280,21,'#174C75',false,'Consolas');d.lines.forEach((v,j)=>t(s,v,72,470+j*50,1130,44,25));}
 else {const y=i===0?300:180;const gap=d.lines.length===6?66:76;d.lines.forEach((v,j)=>t(s,v,72,y+j*gap,1130,58,27));}
 if(d.callout)t(s,d.callout,72,625,1120,40,21,'#A33832',true);
 t(s,String(i+1).padStart(2,'0'),1170,677,45,22,14,'#777777');
 s.speakerNotes.textFrame.setText(d.note+'\n\n[Sources]\n'+(d.src||source)+'\nUser-provided classroom workflow and troubleshooting logs.');
 const png=await p.export({slide:s,format:'png',scale:1});await fs.writeFile(path.join(preview,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
}
const candidate=path.join(work,'candidate.pptx');await(await PresentationFile.exportPptx(p)).save(candidate);
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const final=path.join(work,'output','SO101_로봇팔_실습_가이드_수업용.pptx');
await finalizePresentation({workspaceDir:work,candidatePath:candidate,finalPath:final,pythonExecutable:python,integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],fontPolicy:{basis:'design',families:['Malgun Gothic','Consolas']},verifyArtifactToolImport:true,receiptPath:path.join(work,'validation-classroom.json')});
await fs.writeFile(path.join(work,'output','SO101_실습_명령어.txt'),deck.filter(d=>d.code).map(d=>d.title+'\n\n'+d.code+'\n\n'+d.lines.join('\n')).join('\n\n----------------------------------------\n\n'),'utf8');
for(let start=0;start<deck.length;start+=9){const items=[];for(let j=start;j<Math.min(start+9,deck.length);j++){items.push({input:await sharp(path.join(preview,`slide-${String(j+1).padStart(2,'0')}.png`)).resize(640,360).png().toBuffer(),left:((j-start)%3)*640,top:Math.floor((j-start)/3)*360});}await sharp({create:{width:1920,height:1080,channels:3,background:'white'}}).composite(items).png().toFile(path.join(preview,`sheet-${start}.png`));}
console.log(final);

