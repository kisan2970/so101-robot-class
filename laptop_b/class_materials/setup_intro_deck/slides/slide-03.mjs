import { C, addBase, addFooter, node, arrow, callout } from "./deck_helpers.mjs";

export async function slide03(presentation, ctx) {
  const slide = presentation.slides.add();
  addBase(slide, ctx, "PROCESS", "전체 세팅은 작은 확인 단계를 순서대로 통과하는 과정이다", "앞 단계가 안정적이어야 다음 단계에서 로봇팔이 예측 가능하게 움직인다.");
  const items = [
    ["환경 준비", "제어 도구"],
    ["USB 연결", "물리 연결"],
    ["COM 포트", "연결 주소"],
    ["모터 ID", "관절 번호"],
    ["캘리브레이션", "움직임 범위"],
    ["조종 테스트", "따라 움직임"],
  ];
  items.forEach(([label, sub], i) => {
    const x = 72 + i * 194;
    node(slide, ctx, x, 335, 145, 92, label, sub, i % 2 ? "#FFF1CF" : C.teal2);
    if (i < items.length - 1) arrow(slide, ctx, x + 150, 360);
  });
  callout(slide, ctx, 330, 505, 620, "설정은 설치가 아니라 안전한 움직임을 준비하는 절차다");
  addFooter(slide, ctx, 3);
  return slide;
}
