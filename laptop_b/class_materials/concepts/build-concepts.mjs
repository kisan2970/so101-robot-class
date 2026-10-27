import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
import sharp from 'sharp';
const root=path.dirname(fileURLToPath(import.meta.url)),work=path.join(root,'concepts'),preview=path.join(work,'preview');
const skill='C:/Users/wotjr/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations';
const source='https://huggingface.co/docs/lerobot/so101';
const decks=[
['SO-101 로봇팔의 작동 원리','연결부터 텔레오피까지, 각 단계가 필요한 이유',['사람의 움직임을 다른 로봇팔에 전달하는 실습'], '시작 전에 리더의 집게 손잡이를 움직여 팔로워가 따라오는 모습을 짧게 시연한다. 오늘의 질문은 이것이 어떻게 가능한가이다.'],
['사람의 말을 움직임으로 바꾸기','우리가 원하는 동작: 집게를 조금 열기',['컴퓨터는 어느 모터를 움직일지 알아야 한다.','지금 위치와 목표 위치도 알아야 한다.','연결과 보정은 이 정보를 준비하는 과정이다.'],'학생에게 집게를 열라고 말하면 누구를 움직일지 바로 알지만 컴퓨터는 장치 번호와 목표값이 필요하다고 설명한다.'],
['리더암: 사람이 조종하는 팔','손으로 움직이면 센서가 관절 위치를 읽는다.',['조종 손잡이처럼 사람이 원하는 자세를 만든다.','컴퓨터는 관절마다 위치값을 받는다.'],'리더를 사람이 움직이고 센서는 위치를 읽는다. 리더가 팔로워를 기계적으로 끌어당기는 것은 아니다. 힘의 되먹임을 제공한다고 설명하지 않는다.','leader'],
['팔로워암: 움직임을 실행하는 팔','컴퓨터가 보내는 목표를 모터가 따라간다.',['모터가 팔을 움직이고 집게를 열거나 닫는다.','센서는 실제로 어디까지 움직였는지 알려준다.'],'팔로워는 적절한 전원으로 구동한다. 사진의 부품 배치와 실제 키트가 다를 수 있다.','follower'],
['USB와 전원선의 역할','대화하는 길과 움직일 에너지가 따로 필요하다.',['USB는 노트북과 제어 보드 사이에서 데이터를 전달한다.','전원 어댑터는 모터가 움직일 에너지를 공급한다.','USB 인식만으로 모터 전원까지 확인한 것은 아니다.'],'USB 연결 성공과 모터 구동 성공은 다르다. 모터 정격 전압과 어댑터를 확인하며 LED만으로 모든 전원이 정상이라고 단정하지 않는다.'],
['제어 보드와 프로그램','노트북과 모터 사이를 연결하는 역할',['제어 보드는 USB 데이터를 모터 통신으로 전달한다.','Python은 실습 프로그램을 실행한다.','LeRobot은 연결, 보정, 조종에 필요한 기능을 제공한다.'],'사람이 글을 쓰는 도구와 메시지를 전달하는 장치를 구분하듯 설명한다. 가상환경은 실습용 도구를 따로 모아 두는 공간이다. 설치 명령어는 기존 실습 가이드를 사용한다.'],
['COM 포트: 어느 팔과 연결할까','노트북이 연결된 장치를 구분하는 이름',['예: 리더는 COM10, 팔로워는 COM11','USB를 하나씩 뺐다 연결하면 어느 팔인지 찾을 수 있다.','다른 노트북에서는 COM 번호가 달라질 수 있다.'],'COM 번호는 예시이며 고정되지 않는다. 블루투스 직렬 포트와 구분한다. COM은 한 팔의 제어 보드 연결을 구분한다.'],
['모터 ID: 어느 관절을 움직일까','한 팔 안에서 사용하는 출석번호',['1번 밑부분 회전 / 2번 어깨 / 3번 팔꿈치','4번 손목 굽힘 / 5번 손목 회전 / 6번 집게','6번에 보낸 명령은 집게 모터가 받아야 한다.'],'COM 번호와 모터 ID를 대조한다. COM은 팔의 연결, ID는 그 팔 안의 관절이다. 리더의 6번은 조종 손잡이에 해당한다.'],
['한 개씩 번호를 지정하는 이유','같은 번호를 가진 모터가 여러 개면 구분하기 어렵다.',['새 모터들은 같은 초기 ID를 가질 수 있다.','설정할 모터 한 개만 연결하고 번호를 지정한다.','설정이 끝나면 각 모터를 다시 이어 연결한다.'],'출석번호가 모두 1번인 반을 예로 들고 한 명씩 이름을 확인해 번호를 붙이는 비유를 쓴다. 모터 케이블을 바꿀 때는 전원을 끈다.'],
['통신 속도와 펌웨어','대화 규칙과 모터 내부 프로그램',['Baudrate는 데이터를 주고받는 속도 설정이다.','연결된 모터와 제어 프로그램의 속도가 맞아야 한다.','펌웨어는 모터 안에서 동작하는 프로그램이다.'],'baudrate를 모터 회전 속도로 오해하지 않도록 한다. 버전이 섞여 연결 오류가 발생하면 교사가 공식 절차로 확인한다. 학생에게 무조건 최신 버전 업데이트를 요구하지 않는다.'],
['센서가 읽는 위치값','관절 위치를 숫자로 나타낸다.',['손으로 관절을 움직이면 센서값이 바뀐다.','컴퓨터는 이 숫자로 현재 자세를 확인한다.','숫자가 변해도 모터 구동까지 정상이라는 뜻은 아니다.'],'읽기와 움직이기를 구분한다. 모터 전원이나 토크 문제가 있어도 센서값을 읽을 수 있는 경우가 있다.'],
['캘리브레이션: 기준 맞추기','두 사람이 같은 자의 눈금을 쓰도록 맞추는 작업',['조립 상태가 다르면 같은 자세의 원시값도 다를 수 있다.','각 팔의 기준 위치와 움직임 범위를 확인한다.','컴퓨터가 두 팔의 위치값을 비교할 기준을 만든다.'],'캘리브레이션을 모터 성능 향상이나 고장 수리로 설명하지 않는다. 기준과 범위 설정으로 위치값 해석을 맞추는 과정이다.'],
['기준이 어긋난 경우','같은 숫자를 서로 다른 자세로 해석할 수 있다.',['설명 예: 리더는 수평인데 팔로워는 위쪽을 가리킨다.','실행하자마자 목표 자세로 크게 움직일 수 있다.','중간 자세를 잡고 양쪽 팔을 각각 보정한다.'],'숫자 예시를 실제 결과로 단정하지 않는다. 큰 움직임은 조립 방향, 보정 파일, 시작 자세 등의 문제로 발생할 수 있다. 학생에게 자신의 팔꿈치 기준 방향을 비교하게 한다.'],
['움직임 범위를 기록하는 이유','관절이 움직일 수 있는 양쪽 끝을 확인한다.',['MIN: 기록한 최솟값 / POS: 현재값 / MAX: 최댓값','관절을 천천히 움직이며 사용 범위를 측정한다.','끝에 닿았을 때 더 세게 밀면 부품이 손상될 수 있다.'],'사용 범위와 기계적 끝을 구분한다. 기본 wrist_roll은 별도 처리되어 범위 기록 표에서 빠질 수 있다. 범위 기록이 모든 충돌을 자동으로 막아주지는 않는다.'],
['위치값이 4095에서 0으로 바뀌는 이유','시계가 12시를 지나 1시가 되는 것과 비슷하다.',['한 회전의 위치를 0~4095로 나타내는 경우다.','경계를 지나면 숫자는 커지다가 다시 작아진다.','움직임이 조금인데 숫자 차이는 크게 보일 수 있다.'],'4095에서 0으로 넘어가는 현상 자체만으로 고장은 아니다. 자료의 비유는 순환하는 숫자의 개념을 설명한다. 소프트웨어 기준과 보정이 맞는지 확인해야 한다.'],
['텔레오피: 사람이 움직임을 결정','Teleoperation은 원격 조종이라는 뜻이다.',['1. 사람이 리더암을 움직인다.','2. 컴퓨터가 리더 관절 위치를 읽는다.','3. 대응하는 목표를 팔로워에 보낸다.','4. 팔로워 모터가 목표 자세를 따라간다.'],'카메라 없이 관절 위치값을 전달하는 실습이다. 로봇이 스스로 작업을 판단하는 단계로 설명하지 않는다. 프로그램은 이 과정을 반복한다.'],
['서보 모터의 목표와 현재 위치','센서값을 확인하며 목표에 가까워지도록 조절한다.',['설명 예: 현재 20도, 목표 30도','모터가 움직인 뒤 센서가 실제 위치를 다시 읽는다.','목표에 가까워지면 위치 오차가 작아진다.'],'예시 각도는 설명용이다. 모든 관절과 집게가 같은 단위나 같은 범위로 동작한다고 설명하지 않는다. 실제 지연, 힘의 한계, 오차가 있을 수 있다.'],
['처음에는 작게 움직이는 이유','연결과 기준이 맞는지 안전하게 확인한다.',['팔을 고정하고 관절 주변에 손을 넣지 않는다.','한 관절씩 작은 움직임으로 따라오는지 확인한다.','걸림, 이상 소음, 과부하가 생기면 즉시 멈춘다.'],'소프트웨어가 끊기면 모터 토크가 남을 수 있다. 교사가 전원 차단을 준비하고 팔이 떨어지지 않도록 안전한 받침을 확보한다. 속도나 목표 변화 제한은 충돌 방지 보장이 아니다.'],
['오늘의 확인 실험','리더 손목을 조금 움직이면 어느 모터가 따라올까?',['관절 번호를 먼저 예상하고 작은 범위에서 확인한다.','번호가 틀리면 다른 관절에 명령이 전달될 수 있다.','기준이 틀리면 대응하는 자세가 어긋날 수 있다.'],'교사가 정상 설정된 팔로 시연한다. 교육 목적의 잘못된 ID나 보정값을 실제로 쓰지 않는다. 학생이 원인을 말로 설명하게 한다.'],
['실습 단계마다 준비하는 정보','연결, 번호, 기준을 맞추면 조종을 확인할 수 있다.',['COM 포트 확인: 어떤 팔과 대화하는가','모터 ID 지정: 어느 관절에 명령을 보내는가','캘리브레이션: 위치값을 어떤 기준으로 해석하는가','텔레오피: 사람의 움직임을 다른 팔에 전달하기'],'마무리 질문: COM과 모터 ID는 어떻게 다른가? 같은 ID를 여러 모터가 가지면 무엇이 문제인가? 캘리브레이션을 끝내도 구동 확인을 왜 해야 하는가?']
];
await fs.mkdir(preview,{recursive:true});await fs.mkdir(path.join(work,'output'),{recursive:true});
const p=Presentation.create({slideSize:{width:1280,height:720}});
function text(s,str,x,y,w,h,size=29,color='#202626',bold=false){const q=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});q.text=str;q.text.style={typeface:'Malgun Gothic',fontSize:size,color,bold};q.text.insets={left:0,right:0,top:0,bottom:0};return q;}
for(let i=0;i<decks.length;i++){
 const [title,sub,lines,note,pic]=decks[i],s=p.slides.add();s.background.fill='#FFFFFF';
 text(s,title,72,52,1136,84,i===0?55:42,'#173F35',true);
 text(s,sub,72,165,pic?600:1120,94,31,'#24638D',true);
 lines.forEach((v,j)=>text(s,v,72,(i===0?380:310)+j*77,pic?600:1130,65,28));
 if(pic==='leader'){const b=await fs.readFile(path.join(root,pic+'-concept.webp'));s.images.add({blob:new Uint8Array(b),contentType:'image/webp',fit:'contain',alt:'SO-101 리더암',position:{left:730,top:180,width:470,height:425}});}
 if(pic==='follower'){text(s,'목표 위치',760,260,410,75,40,'#24638D',true);text(s,'실제 위치',760,420,410,75,40,'#173F35',true);text(s,'센서로 확인',760,510,410,55,26);}
 text(s,String(i+1).padStart(2,'0'),1170,680,50,20,14,'#777777');
 s.speakerNotes.textFrame.setText(note+'\n\n[Sources]\n'+source+(pic?'\nhttps://huggingface.co/datasets/huggingface/documentation-images/resolve/main/lerobot/SO101_'+(pic==='leader'?'Leader':'Follower')+'.webp':'')+'\n수업용 비유와 숫자 예시는 설명 목적으로 작성.');
 const png=await p.export({slide:s,format:'png',scale:1});await fs.writeFile(path.join(preview,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
}
const candidate=path.join(work,'candidate.pptx');await(await PresentationFile.exportPptx(p)).save(candidate);
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const final=path.join(work,'output','SO101_왜_설정할까_텔레오피_개념설명.pptx');
await finalizePresentation({workspaceDir:work,candidatePath:candidate,finalPath:final,pythonExecutable:'C:/Users/wotjr/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],fontPolicy:{basis:'design',families:['Malgun Gothic']},verifyArtifactToolImport:true,receiptPath:path.join(work,'validation.json')});
for(let start=0;start<decks.length;start+=8){const items=[];for(let j=start;j<Math.min(start+8,decks.length);j++)items.push({input:await sharp(path.join(preview,`slide-${String(j+1).padStart(2,'0')}.png`)).resize(640,360).png().toBuffer(),left:((j-start)%2)*640,top:Math.floor((j-start)/2)*360});await sharp({create:{width:1280,height:1440,channels:3,background:'white'}}).composite(items).png().toFile(path.join(preview,`sheet-${start}.png`));}
console.log(final);
