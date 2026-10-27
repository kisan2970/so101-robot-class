import { C, addBase, addFooter, callout } from "./deck_helpers.mjs";

export async function slide07(presentation, ctx) {
  const slide = presentation.slides.add();
  addBase(slide, ctx, "CALIBRATION", "캘리브레이션은 로봇팔에게 안전한 움직임 범위를 알려주는 과정이다", "관절의 기준 위치와 최소/최대 범위를 천천히 확인한다.");
  ctx.addShape(slide, { x: 170, y: 390, w: 810, h: 18, fill: C.line });
  ctx.addShape(slide, { x: 170, y: 390, w: 215, h: 18, fill: C.red });
  ctx.addShape(slide, { x: 385, y: 390, w: 380, h: 18, fill: C.teal });
  ctx.addShape(slide, { x: 765, y: 390, w: 215, h: 18, fill: C.red });
  [["최소 범위", 145], ["안전한 움직임", 485], ["최대 범위", 850]].forEach(([t, x]) => {
    ctx.addText(slide, {
      x, y: 425, w: 160, h: 30, text: t,
      fontSize: 17, bold: true, color: C.ink, typeface: "Malgun Gothic",
      align: "center", insets: { left: 0, right: 0, top: 0, bottom: 0 },
    });
  });
  callout(slide, ctx, 255, 510, 700, "힘으로 끝까지 밀지 않고, 부드럽게 움직이는 범위만 알려준다");
  addFooter(slide, ctx, 7);
  return slide;
}
