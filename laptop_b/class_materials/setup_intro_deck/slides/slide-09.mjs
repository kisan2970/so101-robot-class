import { C, addBase, addFooter, numbered, callout } from "./deck_helpers.mjs";

export async function slide09(presentation, ctx) {
  const slide = presentation.slides.add();
  addBase(slide, ctx, "SAFETY CHECK", "로봇팔 세팅의 마지막 기준은 정상 동작보다 안전한 동작이다", "오류가 보이면 계속 실행하지 않고 원인을 확인한다.");
  numbered(slide, ctx, 110, 315, 1, "모터 인식", "1번부터 6번까지 응답하는가?");
  numbered(slide, ctx, 110, 425, 2, "움직임 방향", "관절이 예상한 방향으로 움직이는가?");
  numbered(slide, ctx, 650, 315, 3, "캘리브레이션", "범위가 너무 좁거나 넓지 않은가?");
  numbered(slide, ctx, 650, 425, 4, "이상 신호", "과부하, 튐, 소음이 없는가?");
  callout(slide, ctx, 300, 560, 680, "환경 세팅은 로봇팔이 안전하게 통신하고 움직이도록 준비하는 과정이다");
  addFooter(slide, ctx, 9);
  return slide;
}
