import { C, addBase, addFooter, numbered, callout } from "./deck_helpers.mjs";

export async function slide04(presentation, ctx) {
  const slide = presentation.slides.add();
  addBase(slide, ctx, "COMPUTER SETUP", "컴퓨터에는 로봇팔과 대화할 수 있는 실행 환경이 필요하다", "전용 작업 공간을 만들고 필요한 제어 도구를 설치하는 단계다.");
  numbered(slide, ctx, 105, 320, 1, "Python", "LeRobot을 실행하는 기본 언어");
  numbered(slide, ctx, 105, 430, 2, "가상환경", "이 프로젝트만의 깨끗한 실행 공간");
  numbered(slide, ctx, 650, 320, 3, "LeRobot", "SO-101을 제어하는 로봇 도구");
  numbered(slide, ctx, 650, 430, 4, "통신 패키지", "USB와 모터 통신을 가능하게 함");
  callout(slide, ctx, 350, 555, 580, "목표: 컴퓨터가 로봇팔 명령을 보낼 준비를 끝낸다");
  addFooter(slide, ctx, 4);
  return slide;
}
