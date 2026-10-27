import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const workspace = path.dirname(fileURLToPath(import.meta.url));
const previewDir = path.join(workspace, "preview");
const outputDir = path.join(workspace, "output");
const artifactPath = path.resolve(workspace, "../../../manual-so101-ppt/presentations/so101-setup/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs");
const { Presentation, PresentationFile } = await import(pathToFileURL(artifactPath).href);
const { renderSlide } = await import("./deck.mjs");

function position(o) { return { left: o.x, top: o.y, width: o.w, height: o.h }; }
const ctx = {
  W: 1280, H: 720, workspace,
  line(fill = "#00000000", width = 0, style = "solid") { return { style, fill, width }; },
  addShape(slide, options) {
    const { geometry = "rect", fill = "#00000000", line = { style: "solid", fill: "#00000000", width: 0 }, name, ...rest } = options;
    return slide.shapes.add({ geometry, name, position: position(rest), fill, line });
  },
  addText(slide, options) {
    const { text = "", fontSize = 24, color = "#15201D", bold = false, typeface = "Malgun Gothic", align = "left", valign = "top", insets = { left: 0, right: 0, top: 0, bottom: 0 }, fill = "#00000000", line = { style: "solid", fill: "#00000000", width: 0 }, name, ...rest } = options;
    const shape = slide.shapes.add({ geometry: "rect", name, position: position(rest), fill, line });
    shape.text = text; shape.text.fontSize = fontSize; shape.text.color = color; shape.text.bold = !!bold;
    shape.text.typeface = typeface; shape.text.alignment = align; shape.text.verticalAlignment = valign; shape.text.insets = insets;
    return shape;
  },
  async addImage(slide, options) {
    const bytes = await fs.readFile(options.path);
    return slide.images.add({ blob: bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), contentType: options.path.toLowerCase().endsWith(".png") ? "image/png" : "image/jpeg", alt: options.alt || "SO-101 assembly", fit: options.fit || "contain", position: position(options) });
  }
};

await fs.mkdir(previewDir, { recursive: true }); await fs.mkdir(outputDir, { recursive: true });
const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const slides = [];
for (let i = 1; i <= 16; i++) slides.push(await renderSlide(presentation, ctx, i));
for (let i = 0; i < slides.length; i++) {
  const stem = `slide-${String(i + 1).padStart(2, "0")}`;
  const png = await presentation.export({ slide: slides[i], format: "png", scale: 1 });
  await fs.writeFile(path.join(previewDir, `${stem}.png`), Buffer.from(await png.arrayBuffer()));
  const layout = await presentation.export({ slide: slides[i], format: "layout" });
  await fs.writeFile(path.join(previewDir, `${stem}.layout.json`), await layout.text(), "utf8");
}
const montage = await presentation.export({ format: "webp", montage: true, scale: 0.5 });
await fs.writeFile(path.join(previewDir, "montage.webp"), Buffer.from(await montage.arrayBuffer()));
const out = path.join(outputDir, "SO101_hardware_assembly_guide.pptx");
const pptx = await PresentationFile.exportPptx(presentation); await pptx.save(out);
console.log(JSON.stringify({ outputPath: out, slideCount: slides.length }));
