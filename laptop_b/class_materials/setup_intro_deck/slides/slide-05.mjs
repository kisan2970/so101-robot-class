import { C, addBase, addFooter, node, arrow, card } from "./deck_helpers.mjs";

export async function slide05(presentation, ctx) {
  const slide = presentation.slides.add();
  addBase(slide, ctx, "USB AND COM", "COM 포트는 컴퓨터가 로봇팔을 찾는 연결 주소다", "같은 로봇팔이라도 컴퓨터가 바뀌면 COM 번호가 달라질 수 있다.");
  node(slide, ctx, 95, 350, 190, 100, "노트북", "명령을 보내는 쪽");
  arrow(slide, ctx, 310, 380);
  node(slide, ctx, 380, 350, 190, 100, "COM 포트", "예: COM7, COM8", "#FFF1CF");
  arrow(slide, ctx, 595, 380);
  node(slide, ctx, 665, 350, 230, 100, "SO-101 보드", "명령을 받는 쪽");
  card(slide, ctx, 950, 316, 235, 170, "주의", "포트 번호는 외워서 쓰는 값이 아니라 현재 컴퓨터에서 직접 확인하는 값이다.", C.red);
  addFooter(slide, ctx, 5);
  return slide;
}
