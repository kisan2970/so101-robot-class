const C = {
  bg: "#F7F4ED",
  ink: "#17212B",
  muted: "#5F6872",
  teal: "#0E7C86",
  teal2: "#DDF2F0",
  yellow: "#F2B84B",
  red: "#D85C4A",
  line: "#D6CEC2",
  white: "#FFFFFF",
};

export function addBase(slide, ctx, kicker, title, subtitle = "") {
  ctx.addShape(slide, { x: 0, y: 0, w: ctx.W, h: ctx.H, fill: C.bg });
  ctx.addText(slide, {
    x: 70, y: 45, w: 210, h: 28, text: kicker,
    fontSize: 15, bold: true, color: C.teal, typeface: "Malgun Gothic",
    insets: { left: 0, right: 0, top: 0, bottom: 0 },
  });
  ctx.addShape(slide, { x: 70, y: 80, w: 78, h: 4, fill: C.yellow });
  ctx.addText(slide, {
    x: 70, y: 108, w: 720, h: 92, text: title,
    fontSize: 36, bold: true, color: C.ink, typeface: "Malgun Gothic",
    insets: { left: 0, right: 0, top: 0, bottom: 0 },
  });
  if (subtitle) {
    ctx.addText(slide, {
      x: 72, y: 202, w: 710, h: 58, text: subtitle,
      fontSize: 20, color: C.muted, typeface: "Malgun Gothic",
      insets: { left: 0, right: 0, top: 0, bottom: 0 },
    });
  }
}

export function addFooter(slide, ctx, n) {
  ctx.addShape(slide, { x: 70, y: 650, w: 980, h: 1.5, fill: C.line });
  ctx.addText(slide, {
    x: 70, y: 660, w: 900, h: 20,
    text: "SO-101 로봇팔 환경 세팅 안내 | AI와 카메라 단계 제외",
    fontSize: 11, color: C.muted, typeface: "Malgun Gothic",
    insets: { left: 0, right: 0, top: 0, bottom: 0 },
  });
  ctx.addText(slide, {
    x: 1130, y: 660, w: 70, h: 20, text: String(n).padStart(2, "0"),
    fontSize: 12, bold: true, color: C.teal, typeface: "Aptos",
    align: "right", insets: { left: 0, right: 0, top: 0, bottom: 0 },
  });
}

export function card(slide, ctx, x, y, w, h, title, body, accent = C.teal) {
  ctx.addShape(slide, { x, y, w, h, fill: C.white, line: ctx.line(C.line, 1) });
  ctx.addShape(slide, { x, y, w: 8, h, fill: accent });
  ctx.addText(slide, {
    x: x + 24, y: y + 20, w: w - 44, h: 32, text: title,
    fontSize: 22, bold: true, color: C.ink, typeface: "Malgun Gothic",
    insets: { left: 0, right: 0, top: 0, bottom: 0 },
  });
  ctx.addText(slide, {
    x: x + 24, y: y + 62, w: w - 44, h: h - 78, text: body,
    fontSize: 17, color: C.muted, typeface: "Malgun Gothic",
    insets: { left: 0, right: 0, top: 0, bottom: 0 },
  });
}

export function node(slide, ctx, x, y, w, h, label, sub = "", fill = C.teal2) {
  ctx.addShape(slide, { x, y, w, h, fill, line: ctx.line(C.teal, 1.5) });
  ctx.addText(slide, {
    x: x + 10, y: y + 16, w: w - 20, h: 30, text: label,
    fontSize: 21, bold: true, color: C.ink, typeface: "Malgun Gothic",
    align: "center", insets: { left: 0, right: 0, top: 0, bottom: 0 },
  });
  if (sub) {
    ctx.addText(slide, {
      x: x + 12, y: y + 52, w: w - 24, h: 28, text: sub,
      fontSize: 14, color: C.muted, typeface: "Malgun Gothic",
      align: "center", insets: { left: 0, right: 0, top: 0, bottom: 0 },
    });
  }
}

export function arrow(slide, ctx, x, y, text = "→") {
  ctx.addText(slide, {
    x, y, w: 42, h: 40, text,
    fontSize: 28, bold: true, color: C.teal, typeface: "Malgun Gothic",
    align: "center", insets: { left: 0, right: 0, top: 0, bottom: 0 },
  });
}

export function numbered(slide, ctx, x, y, n, title, body) {
  ctx.addShape(slide, { x, y, w: 54, h: 54, geometry: "ellipse", fill: C.teal, line: ctx.line(C.teal, 0) });
  ctx.addText(slide, {
    x, y: y + 8, w: 54, h: 34, text: String(n),
    fontSize: 24, bold: true, color: C.white, typeface: "Aptos",
    align: "center", insets: { left: 0, right: 0, top: 0, bottom: 0 },
  });
  ctx.addText(slide, {
    x: x + 72, y: y + 1, w: 300, h: 28, text: title,
    fontSize: 20, bold: true, color: C.ink, typeface: "Malgun Gothic",
    insets: { left: 0, right: 0, top: 0, bottom: 0 },
  });
  ctx.addText(slide, {
    x: x + 72, y: y + 31, w: 360, h: 42, text: body,
    fontSize: 15, color: C.muted, typeface: "Malgun Gothic",
    insets: { left: 0, right: 0, top: 0, bottom: 0 },
  });
}

export function callout(slide, ctx, x, y, w, text, accent = C.yellow) {
  ctx.addShape(slide, { x, y, w, h: 64, fill: accent, line: ctx.line(accent, 0) });
  ctx.addText(slide, {
    x: x + 18, y: y + 13, w: w - 36, h: 38, text,
    fontSize: 16, bold: true, color: C.ink, typeface: "Malgun Gothic",
    align: "center", insets: { left: 0, right: 0, top: 0, bottom: 0 },
  });
}

export { C };
