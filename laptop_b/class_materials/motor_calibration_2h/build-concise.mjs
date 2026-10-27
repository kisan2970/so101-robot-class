import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const root=path.dirname(fileURLToPath(import.meta.url));
const outDir=path.join(root,"output-concise"), preview=path.join(root,"preview-concise");
const W=1280,H=720,F="Malgun Gothic";
const C={white:"#FFFFFF",ink:"#151A18",muted:"#5D6663",line:"#B9C0BD",panel:"#EEF0EF",green:"#117A65",green2:"#E3F2ED",blue:"#3D8DFF",red:"#B62D32",red2:"#FDE7E8",dark:"#1D2825"};
const hf="https://huggingface.co/docs/lerobot/en/so101",seeed="https://wiki.seeedstudio.com/lerobot_so100m_new/";

function text(s,t,x,y,w,h,z=22,c=C.ink,b=false,a="left",font=F){const q=s.shapes.add({geometry:"textbox",position:{left:x,top:y,width:w,height:h},fill:"none",line:{style:"solid",fill:"none",width:0}});q.text=t;q.text.style={fontSize:z,color:c,bold:b,typeface:font,alignment:a};q.text.verticalAlignment="middle";q.text.insets={left:0,right:0,top:0,bottom:0};return q}
function box(s,x,y,w,h,fill=C.panel,line=C.line,lw=1){return s.shapes.add({geometry:"rect",position:{left:x,top:y,width:w,height:h},fill,line:{style:"solid",fill:line,width:lw}})}
function line(s,x,y,w,c=C.line,lw=1){box(s,x,y,w,lw,c,c,0)}
function head(s,n,title,sub=""){s.background.fill=C.white;text(s,title,72,55,1136,62,38,C.ink,true);if(sub)text(s,sub,72,125,1136,36,17,C.muted);line(s,72,185,1136,C.ink,1);text(s,String(n).padStart(2,"0"),1155,675,53,20,11,C.muted,true,"right","Arial")}
function notes(s,src=""){s.speakerNotes.textFrame.setText(src?`[Sources]\n${src}`:"[Sources]\nClassroom instructions authored for this deck.");s.speakerNotes.setVisible(true)}
function code(s,t,y=235,h=210){box(s,72,y,1136,h,C.dark,C.dark,0);text(s,t,96,y+18,1088,h-36,17,"#ECF7F3",false,"left","Consolas")}
function bullets(s,items,x=95,y=235,w=1080,gap=64,size=20){items.forEach((v,i)=>{text(s,"•",x,y+i*gap,30,44,size,C.green,true,"center");text(s,v,x+45,y+i*gap,w-45,44,size,C.ink,false)})}
function row(s,y,a,b,accent=false){box(s,78,y,1124,55,accent?C.green2:C.white,C.line,.5);text(s,a,95,y,350,55,17,accent?C.green:C.ink,true);text(s,b,465,y,700,55,17,C.muted)}

async function build(){await fs.mkdir(outDir,{recursive:true});await fs.mkdir(preview,{recursive:true});const p=Presentation.create({slideSize:{width:W,height:H}});const slides=[];const add=()=>{const s=p.slides.add();slides.push(s);return s};

{const s=add();s.background.fill=C.white;text(s,"SO-101",72,65,300,38,17,C.green,true,"left","Arial");text(s,"모터 ID 지정과\n캘리브레이션",72,145,700,145,56,C.ink,true);text(s,"Windows · LeRobot · 리더암/팔로워암",72,335,650,40,21,C.muted);line(s,72,590,1136,C.ink,2);text(s,"2시간 실습 수업",72,620,400,35,18,C.green,true);notes(s,`${hf}\n${seeed}`)}
{const s=add();head(s,2,"수업 순서");const a=[["1","연결·포트 확인","20분"],["2","모터 ID 지정","55분"],["3","모터 인식 확인","15분"],["4","캘리브레이션","30분"]];a.forEach((r,i)=>{const x=78+i*285;text(s,r[0],x,245,60,60,34,C.green,true,"center","Arial");text(s,r[1],x,330,245,42,21,C.ink,true,"center");text(s,r[2],x,390,245,35,17,C.muted,false,"center")});text(s,"오늘 범위: AI 학습과 카메라는 진행하지 않음",160,530,960,45,20,C.red,true,"center");notes(s)}
{const s=add();head(s,3,"안전 수칙");bullets(s,["모터 ID 지정 시 대상 모터 한 개만 연결한다.","전원 어댑터의 전압을 확인한다.","손가락을 관절과 집게 사이에 넣지 않는다.","갑자기 움직이거나 Overload가 나오면 전원을 끈다.","FD 프로그램과 LeRobot을 동시에 같은 COM 포트에 연결하지 않는다."],95,220,1080,76,20);notes(s,seeed)}
{const s=add();head(s,4,"모터 번호와 관절");const a=[["1","shoulder_pan","바닥 좌우"],["2","shoulder_lift","어깨 위아래"],["3","elbow_flex","팔꿈치"],["4","wrist_flex","손목 위아래"],["5","wrist_roll","손목 회전"],["6","gripper","손잡이/집게"]];a.forEach((r,i)=>row(s,220+i*61,`${r[0]}번  ${r[1]}`,r[2],i===0));notes(s,hf)}
{const s=add();head(s,5,"학생용 Codex 사용 방법");text(s,"SO101_수업_시작.html",120,235,1040,65,31,C.blue,true,"center","Consolas");line(s,250,325,780,C.blue,3);bullets(s,["HTML 파일을 더블클릭한다.","작업 폴더와 실제 COM 포트를 입력한다.","현재 단계의 프롬프트 복사 버튼을 누른다.","Codex에 붙여넣고 한 단계씩 진행한다."],250,370,780,58,19);notes(s)}
{const s=add();head(s,6,"환경 확인");code(s,'cd "$env:USERPROFILE\\OneDrive\\문서\\lerobot-so101"\n.\\.venv\\Scripts\\python.exe --version\n.\\.venv\\Scripts\\python.exe -m pip show lerobot',235,200);text(s,"Python 버전과 LeRobot 패키지 정보가 출력되는지 확인",100,490,1080,45,20,C.green,true,"center");notes(s,hf)}
{const s=add();head(s,7,"COM 포트 확인");code(s,'cd "$env:USERPROFILE\\OneDrive\\문서\\lerobot-so101"\n.\\.venv\\Scripts\\python.exe -m serial.tools.list_ports -v',235,165);row(s,455,"사용할 포트","USB-Enhanced-SERIAL CH343(COM번호)",true);row(s,520,"사용하지 않을 포트","표준 Bluetooth에서 직렬 링크");text(s,"리더와 팔로워를 한 개씩 뺐다 연결해 각각의 COM 번호를 기록",90,605,1100,40,18,C.red,true,"center");notes(s,seeed)}
{const s=add();head(s,8,"모터 ID 지정 방법");bullets(s,["제어 보드 전원을 끈다.","ID를 지정할 모터 한 개만 연결한다.","전원과 USB를 연결하고 setup-motors를 실행한다.","안내에 따라 ID를 지정한다.","전원을 끄고 다음 모터로 교체한다."],110,220,1060,70,21);text(s,"리더와 팔로워 각각 ID 1~6을 반복",150,585,980,45,21,C.red,true,"center");notes(s,`${hf}\n${seeed}`)}
{const s=add();head(s,9,"리더암 모터 ID 지정");code(s,'cd "$env:USERPROFILE\\OneDrive\\문서\\lerobot-so101"\n.\\.venv\\Scripts\\lerobot-setup-motors.exe `\n  --teleop.type=so101_leader `\n  --teleop.port=COM10',225,245);text(s,"COM10을 실제 리더암 포트로 변경",150,515,980,45,21,C.red,true,"center");notes(s,hf)}
{const s=add();head(s,10,"팔로워암 모터 ID 지정");code(s,'cd "$env:USERPROFILE\\OneDrive\\문서\\lerobot-so101"\n.\\.venv\\Scripts\\lerobot-setup-motors.exe `\n  --robot.type=so101_follower `\n  --robot.port=COM11',225,245);text(s,"COM11을 실제 팔로워암 포트로 변경",150,515,980,45,21,C.red,true,"center");notes(s,hf)}
{const s=add();head(s,11,"모터 인식 확인");row(s,230,"정상","Found motor list에 1, 2, 3, 4, 5, 6이 모두 표시",true);row(s,305,"Missing motor ID","표시된 번호의 케이블·ID·전원 확인");row(s,380,"Could not connect","COM 번호와 포트 점유 프로그램 확인");row(s,455,"Different firmware","Feetech 프로그램에서 펌웨어 버전 통일");text(s,"모터가 빠져 있으면 캘리브레이션으로 넘어가지 않음",140,560,1000,45,20,C.red,true,"center");notes(s,hf)}
{const s=add();head(s,12,"캘리브레이션 준비");bullets(s,["팔을 책상과 부딪히지 않는 중간 자세에 둔다.","관절이 기계적인 끝에 닿지 않게 한다.","집게는 중간 정도 열어 둔다.","손목 케이블이 팽팽하지 않은지 확인한다.","전원 스위치에 바로 손이 닿게 한다."],100,220,1080,70,20);notes(s,`${hf}\n${seeed}`)}
{const s=add();head(s,13,"팔로워암 캘리브레이션");code(s,'cd "$env:USERPROFILE\\OneDrive\\문서\\lerobot-so101"\n.\\.venv\\Scripts\\lerobot-calibrate.exe `\n  --robot.type=so101_follower `\n  --robot.port=COM11 `\n  --robot.id=my_so101_follower',215,280);text(s,"기존 값을 다시 측정하려면 질문에서 c 입력",150,525,980,45,20,C.red,true,"center");notes(s,hf)}
{const s=add();head(s,14,"리더암 캘리브레이션");code(s,'cd "$env:USERPROFILE\\OneDrive\\문서\\lerobot-so101"\n.\\.venv\\Scripts\\lerobot-calibrate.exe `\n  --teleop.type=so101_leader `\n  --teleop.port=COM10 `\n  --teleop.id=my_so101_leader',215,280);text(s,"리더암도 같은 관절 순서로 범위를 기록",150,525,980,45,20,C.green,true,"center");notes(s,hf)}
{const s=add();head(s,15,"범위 기록 방법");bullets(s,["안내가 시작되면 관절을 하나씩 움직인다.","한쪽 끝에서 반대쪽 끝까지 천천히 이동한다.","기구 끝에서 힘으로 더 밀지 않는다.","표의 MIN과 MAX가 변하는지 확인한다.","끝나면 ENTER를 눌러 저장한다."],100,220,1080,70,20);text(s,"완료 메시지: Calibration saved to ...json",140,585,1000,45,20,C.blue,true,"center","Consolas");notes(s,hf)}
{const s=add();head(s,16,"최종 확인");const a=["리더·팔로워 COM 번호 기록","리더 ID 1~6 지정","팔로워 ID 1~6 지정","양쪽 모터 6개 인식","팔로워 calibration 저장","리더 calibration 저장"];a.forEach((v,i)=>{const x=80+(i%2)*570,y=225+Math.floor(i/2)*100;box(s,x,y,535,72,C.white,C.line,1);text(s,"□",98+(i%2)*570,y,50,72,23,C.green,true,"center");text(s,v,160+(i%2)*570,y,420,72,18,C.ink,true)});text(s,"완료 후 전원을 끄고 USB를 분리",160,560,960,45,20,C.red,true,"center");notes(s)}

for(let i=0;i<slides.length;i++){const stem=`slide-${String(i+1).padStart(2,"0")}`;const png=await p.export({slide:slides[i],format:"png",scale:1});await fs.writeFile(path.join(preview,`${stem}.png`),Buffer.from(await png.arrayBuffer()));const layout=await slides[i].export({format:"layout"});await fs.writeFile(path.join(preview,`${stem}.layout.json`),await layout.text(),"utf8")}
const out=path.join(outDir,"SO101_모터ID_캘리브레이션_수업용_축약본.pptx");const pptx=await PresentationFile.exportPptx(p);await pptx.save(out);console.log(JSON.stringify({outputPath:out,slideCount:slides.length}));}
build().catch(e=>{console.error(e);process.exitCode=1});
