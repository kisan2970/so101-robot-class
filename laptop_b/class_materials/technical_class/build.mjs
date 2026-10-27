import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const workspace = path.dirname(fileURLToPath(import.meta.url));
const slidesDir = path.join(workspace, "slides");
const previewDir = path.join(workspace, "preview");
const outputDir = path.join(workspace, "output");
const artifactPath = path.resolve(workspace, "../../../manual-so101-ppt/presentations/so101-setup/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs");

const artifact = await import(pathToFileURL(artifactPath).href);
const { Presentation, PresentationFile } = artifact;

function frame(o) {
  return { left: o.x, top: o.y, width: o.w, height: o.h };
}

const ctx = {
  W: 1280,
  H: 720,
  line(fill = "#00000000", width = 0, style = "solid") {
    return { style, fill, width };
  },
  addShape(slide, options) {
    const { geometry = "rect", fill = "#00000000", line = { style: "solid", fill: "#00000000", width: 0 }, name, ...rest } = options;
    return slide.shapes.add({ geometry, name, position: frame(rest), fill, line });
  },
  addText(slide, options) {
    const { text = "", fontSize = 24, color = "#111827", bold = false, typeface = "Malgun Gothic", align = "left", valign = "top", insets = { left: 0, right: 0, top: 0, bottom: 0 }, fill = "#00000000", line = { style: "solid", fill: "#00000000", width: 0 }, name, ...rest } = options;
    const shape = slide.shapes.add({ geometry: "rect", name, position: frame(rest), fill, line });
    shape.text = text;
    shape.text.fontSize = fontSize;
    shape.text.color = color;
    shape.text.bold = Boolean(bold);
    shape.text.typeface = typeface;
    shape.text.alignment = align;
    shape.text.verticalAlignment = valign;
    shape.text.insets = insets;
    return shape;
  },
};

await fs.mkdir(previewDir, { recursive: true });
await fs.mkdir(outputDir, { recursive: true });

const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const slides = [];

for (let index = 1; index <= 16; index += 1) {
  const modulePath = path.join(slidesDir, `slide-${String(index).padStart(2, "0")}.mjs`);
  const module = await import(`${pathToFileURL(modulePath).href}?v=${Date.now()}-${index}`);
  const fn = module[`slide${String(index).padStart(2, "0")}`];
  slides.push(await fn(presentation, ctx));
}

for (let index = 0; index < slides.length; index += 1) {
  const png = await presentation.export({ slide: slides[index], format: "png", scale: 1 });
  await fs.writeFile(path.join(previewDir, `slide-${String(index + 1).padStart(2, "0")}.png`), Buffer.from(await png.arrayBuffer()));
  const layout = await presentation.export({ slide: slides[index], format: "layout" });
  await fs.writeFile(path.join(previewDir, `slide-${String(index + 1).padStart(2, "0")}.layout.json`), await layout.text(), "utf8");
}

const pptx = await PresentationFile.exportPptx(presentation);
const outputPath = path.join(outputDir, "SO101_technical_class_guide.pptx");
await pptx.save(outputPath);
console.log(JSON.stringify({ outputPath, slideCount: slides.length }, null, 2));



