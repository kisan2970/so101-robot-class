import { C, addBase, addFooter, node, arrow, card } from "./deck_helpers.mjs";

export async function slide08(presentation, ctx) {
  const slide = presentation.slides.add();
  addBase(slide, ctx, "TELEOPERATION", "조종 테스트는 명령이 실제 움직임으로 이어지는지 확인하는 단계다", "사람이 leader arm을 움직이면 follower arm이 따라 움직이는지 확인한다.");
  node(slide, ctx, 140, 345, 250, 110, "Leader arm", "사람이 손으로 움직이는 조종용 팔", "#FFF1CF");
  arrow(slide, ctx, 430, 380);
  node(slide, ctx, 515, 345, 250, 110, "Follower arm", "명령을 받아 실제로 움직이는 팔", C.teal2);
  card(slide, ctx, 865, 322, 285, 160, "확인할 것", "방향이 맞는가?\n갑자기 튀지 않는가?\n이상한 소리나 과부하가 없는가?", C.teal);
  addFooter(slide, ctx, 8);
  return slide;
}
