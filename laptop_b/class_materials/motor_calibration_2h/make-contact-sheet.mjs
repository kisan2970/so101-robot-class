import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";

const root=path.dirname(fileURLToPath(import.meta.url));
const previewName=process.argv[2]||"preview";
const previewDir=path.join(root,previewName);
const files=(await fs.readdir(previewDir)).filter(x=>/^slide-\d+\.png$/.test(x)).sort();
const tw=320,th=180,label=28,cols=4,rows=Math.ceil(files.length/cols);
const comps=[];
for(let i=0;i<files.length;i++){
  const img=await sharp(path.join(previewDir,files[i])).resize(tw,th,{fit:"contain",background:"white"}).png().toBuffer();
  const svg=Buffer.from(`<svg width="${tw}" height="${label}" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="#1d2825"/><text x="12" y="20" font-family="Arial" font-size="14" fill="white">${files[i]}</text></svg>`);
  const tile=await sharp({create:{width:tw,height:th+label,channels:3,background:"white"}}).composite([{input:img,left:0,top:0},{input:svg,left:0,top:th}]).png().toBuffer();
  comps.push({input:tile,left:(i%cols)*tw,top:Math.floor(i/cols)*(th+label)});
}
await sharp({create:{width:cols*tw,height:rows*(th+label),channels:3,background:"#dfe3e1"}}).composite(comps).png().toFile(path.join(previewDir,"contact-sheet.png"));
