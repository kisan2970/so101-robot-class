import { C, addBase, addFooter } from "./deck_helpers.mjs";

function motor(slide, ctx, x, y, n, label, color) {
  ctx.addShape(slide, { x, y, w: 74, h: 74, geometry: "ellipse", fill: color, line: ctx.line(color, 0) });
  ctx.addText(slide, {
    x, y: y + 12, w: 74, h: 36, text: String(n),
    fontSize: 27, bold: true, color: C.white, typeface: "Aptos",
    align: "center", insets: { left: 0, right: 0, top: 0, bottom: 0 },
  });
  ctx.addText(slide, {
    x: x - 35, y: y + 82, w: 145, h: 44, text: label,
    fontSize: 16, bold: true, color: C.ink, typeface: "Malgun Gothic",
    align: "center", insets: { left: 0, right: 0, top: 0, bottom: 0 },
  });
}

export async function slide06(presentation, ctx) {
  const slide = presentation.slides.add();
  addBase(slide, ctx, "MOTOR ID", "모터 ID는 각 관절의 이름표 역할을 한다", "컴퓨터는 ID를 보고 어느 관절에 명령을 보낼지 결정한다.");
  ctx.addShape(slide, { x: 130, y: 370, w: 880, h: 10, fill: C.line });
  const xs = [130, 285, 440, 595, 750, 905];
  const labels = ["어깨 좌우", "어깨 위아래", "팔꿈치", "손목 굽힘", "손목 회전", "집게"];
  xs.forEach((x, i) => motor(slide, ctx, x, 325, i + 1, labels[i], i < 4 ? C.teal : C.yellow));
  ctx.addText(slide, {
    x: 155, y: 520, w: 940, h: 56,
    text: "ID가 틀리면 원하는 관절이 아니라 다른 관절이 움직이거나, 일부 모터가 응답하지 않을 수 있다.",
    fontSize: 21, bold: true, color: C.ink, typeface: "Malgun Gothic",
    align: "center", insets: { left: 0, right: 0, top: 0, bottom: 0 },
  });
  addFooter(slide, ctx, 6);
  return slide;
}
