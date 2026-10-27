import { C, addFooter, callout, node, arrow } from "./deck_helpers.mjs";

export async function slide01(presentation, ctx) {
  const slide = presentation.slides.add();
  ctx.addShape(slide, { x: 0, y: 0, w: ctx.W, h: ctx.H, fill: C.bg });
  ctx.addShape(slide, { x: 0, y: 0, w: 34, h: ctx.H, fill: C.teal });
  ctx.addText(slide, {
    x: 78, y: 78, w: 760, h: 80, text: "SO-101 로봇팔 환경 세팅",
    fontSize: 45, bold: true, color: C.ink, typeface: "Malgun Gothic",
    insets: { left: 0, right: 0, top: 0, bottom: 0 },
  });
  ctx.addText(slide, {
    x: 82, y: 162, w: 740, h: 60,
    text: "컴퓨터와 로봇팔을 연결하고 안전하게 조종하기 위한 기본 과정",
    fontSize: 22, color: C.muted, typeface: "Malgun Gothic",
    insets: { left: 0, right: 0, top: 0, bottom: 0 },
  });
  node(slide, ctx, 120, 322, 180, 96, "컴퓨터", "제어 환경");
  arrow(slide, ctx, 315, 348);
  node(slide, ctx, 370, 322, 180, 96, "USB", "연결 통로", "#FFF1CF");
  arrow(slide, ctx, 565, 348);
  node(slide, ctx, 620, 322, 210, 96, "SO-101", "로봇팔");
  callout(slide, ctx, 880, 314, 270, "핵심: 바로 움직이기보다 먼저 확인한다");
  addFooter(slide, ctx, 1);
  return slide;
}
