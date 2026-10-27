import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
const workspace=path.dirname(fileURLToPath(import.meta.url));
const previewDir=path.join(workspace,"preview-detailed"),outputDir=path.join(workspace,"output");
const artifactPath=path.resolve(workspace,"../../../manual-so101-ppt/presentations/so101-setup/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs");
const {Presentation,PresentationFile}=await import(pathToFileURL(artifactPath).href);
const {renderSlide}=await import("./deck-detailed.mjs");
const pos=o=>({left:o.x,top:o.y,width:o.w,height:o.h});
const ctx={W:1280,H:720,workspace,line:(fill="#00000000",width=0,style="solid")=>({style,fill,width}),
 addShape(slide,o){const{geometry="rect",fill="#00000000",line={style:"solid",fill:"#00000000",width:0},name,...r}=o;return slide.shapes.add({geometry,name,position:pos(r),fill,line});},
 addText(slide,o){const{text="",fontSize=24,color="#15201D",bold=false,typeface="Malgun Gothic",align="left",valign="top",insets={left:0,right:0,top:0,bottom:0},fill="#00000000",line={style:"solid",fill:"#00000000",width:0},name,...r}=o;const q=slide.shapes.add({geometry:"rect",name,position:pos(r),fill,line});q.text=text;q.text.fontSize=fontSize;q.text.color=color;q.text.bold=!!bold;q.text.typeface=typeface;q.text.alignment=align;q.text.verticalAlignment=valign;q.text.insets=insets;return q;},
 async addImage(slide,o){const b=await fs.readFile(o.path);return slide.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:o.path.endsWith(".png")?"image/png":"image/jpeg",alt:o.alt||"SO-101 assembly photo",fit:o.fit||"contain",position:pos(o)});}};
await fs.mkdir(previewDir,{recursive:true});await fs.mkdir(outputDir,{recursive:true});
const presentation=Presentation.create({slideSize:{width:1280,height:720}}),slides=[];
for(let i=1;i<=24;i++)slides.push(await renderSlide(presentation,ctx,i));
for(let i=0;i<slides.length;i++){const stem=`slide-${String(i+1).padStart(2,"0")}`;const png=await presentation.export({slide:slides[i],format:"png",scale:1});await fs.writeFile(path.join(previewDir,`${stem}.png`),Buffer.from(await png.arrayBuffer()));const layout=await presentation.export({slide:slides[i],format:"layout"});await fs.writeFile(path.join(previewDir,`${stem}.layout.json`),await layout.text(),"utf8");}
const out=path.join(outputDir,"SO101_hardware_assembly_detailed.pptx");const pptx=await PresentationFile.exportPptx(presentation);await pptx.save(out);console.log(JSON.stringify({outputPath:out,slideCount:slides.length}));
