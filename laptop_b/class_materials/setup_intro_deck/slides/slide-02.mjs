import { C, addBase, addFooter, card } from "./deck_helpers.mjs";

export async function slide02(presentation, ctx) {
  const slide = presentation.slides.add();
  addBase(slide, ctx, "STARTING POINT", "로봇팔은 USB만 꽂는다고 바로 움직이지 않는다", "먼저 컴퓨터가 장치를 알아보고, 모터와 움직임 범위를 확인해야 한다.");
  card(slide, ctx, 90, 330, 310, 170, "인식", "컴퓨터가 로봇팔을 연결된 장치로 확인하는 단계", C.teal);
  card(slide, ctx, 485, 330, 310, 170, "설정", "모터 번호와 통신 조건이 맞는지 확인하는 단계", C.yellow);
  card(slide, ctx, 880, 330, 310, 170, "안전", "움직일 수 있는 범위를 알려주고 조종을 시험하는 단계", C.red);
  addFooter(slide, ctx, 2);
  return slide;
}
