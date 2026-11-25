"""Render the two exact five-row panels as portable SVG with live text."""
from pathlib import Path
from xml.sax.saxutils import escape
import argparse

INK = "#2C3E50"
LAPIS = "#1F3F60"
TEAL = "#1F6968"
LIGHT = "#D2E0E2"
BRONZE = "#916400"
RED = "#743E37"


def build():
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="530" viewBox="0 0 1100 530" role="img" aria-labelledby="title desc">',
        '<title id="title">Strict counts and two-source distances at five rows and rank two</title>',
        '<desc id="desc">Left: all ten possible count pairs. The boundary-only exceptional pair is two, two. The two minima are three, four and four, three. Right: the four other rows have source scores and target differences (2,3), (5,10), (19,2) and (22,7). Row 2 fixes the radius ten. Only source arm one admits row 1 and only arm two admits row 2.</desc>',
        '<rect width="1100" height="530" fill="white"/>',
        '<g font-family="DejaVu Sans, Arial, sans-serif" fill="' + INK + '">',
    ]

    def label(x, y, value, size=16, anchor="start", bold=False, color=INK, transform=None):
        attr = f' transform="{transform}"' if transform else ""
        out.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}"'
                   f' font-weight="{"bold" if bold else "normal"}" fill="{color}"{attr}>{escape(value)}</text>')

    def line(x1, y1, x2, y2, color=LIGHT, width=1, dash=""):
        attr = f' stroke-dasharray="{dash}"' if dash else ""
        out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"{attr}/>')

    def circle(x, y, color=TEAL):
        out.append(f'<circle cx="{x}" cy="{y}" r="7" fill="{color}"/>')

    def square(x, y):
        out.append(f'<rect x="{x-7}" y="{y-7}" width="14" height="14" fill="{LAPIS}"/>')

    def diamond(x, y):
        out.append(f'<path d="M{x} {y-9} l9 9 -9 9 -9 -9 z" fill="white" stroke="{RED}" stroke-width="2.7"/>')

    label(42, 43, "One query row, five observations, rank two", 27, bold=True, color=LAPIS)
    line(42, 61, 1062, 61)
    label(55, 98, "Which counts are possible?", 20, bold=True, color=TEAL)
    label(548, 98, "Which rows enter the two strict counts?", 20, bold=True, color=TEAL)
    label(55, 124, "x and y each include the query row.", 15)
    label(548, 124, "Row 0 is the query row. Each point is another row.", 15)

    def cx(x): return 130 + (x-2)*89
    def cy(y): return 355 - (y-2)*59
    for value in range(2, 6):
        line(cx(value), cy(2), cx(value), cy(5))
        line(cx(2), cy(value), cx(5), cy(value))
        label(cx(value), 381, str(value), 15, "middle")
        label(109, cy(value)+5, str(value), 15, "end")
    line(cx(2), cy(2), cx(5)+12, cy(2), INK, 1.7)
    line(cx(2), cy(2), cx(2), cy(5)-10, INK, 1.7)
    line(cx(2), cy(5), cx(5), cy(2), BRONZE, 1.8, "6 5")
    for x in range(2, 6):
        for y in range(2, 6):
            if x+y <= 7:
                mark = diamond if (x,y) == (2,2) else square if abs(x-y)==1 and x+y==7 else circle
                mark(cx(x), cy(y))
    label(261, 407, "Source count x", 16, "middle")
    label(65, 269, "Target count y", 16, "middle", transform="rotate(-90 65 269)")
    circle(67, 439); label(84, 445, "Other open pairs", 15)
    square(250, 439); label(267, 445, "Minimum local term", 15)
    diamond(67, 470); label(84, 475, "Exceptional pair", 15)
    line(258, 469, 285, 469, BRONZE, 1.8, "6 5"); label(295, 475, "x + y = 7", 15)

    def px(x): return 621 + 15.2*x
    def py(y): return 355 - 12.1*y
    for value in range(0,26,5):
        line(px(value), py(0), px(value), py(15))
        label(px(value), 381, str(value), 15, "middle")
    for value in (0,5,10,15):
        line(px(0), py(value), px(25), py(value))
        label(605, py(value)+5, str(value), 15, "end")
    line(px(0), py(0), px(25)+8, py(0), INK, 1.7)
    line(px(0), py(0), px(0), py(15)-8, INK, 1.7)
    line(px(10), py(0), px(10), py(15), BRONZE, 2, "7 4")
    line(px(0), py(10), px(25), py(10), BRONZE, 2, "7 4")
    label(px(10)+8, py(15)+6, "S = 10", 14, color=BRONZE)
    label(px(24.9), py(10)-8, "T = 10", 14, "end", color=BRONZE)
    rows = [(2,3,1), (5,10,2), (19,2,3), (22,7,4)]
    for x, y, i in rows:
        if i==2:
            ax, ay = px(x), py(y)
            out.append(f'<path d="M{ax} {ay-9} l9 16 h-18 z" fill="{LAPIS}"/>')
        else: circle(px(x), py(y))
        label(px(x)+12, py(y)-8, "row "+str(i), 14, bold=True)
    label(806, 407, "Source score S (raw units)", 16, "middle")
    label(560, 265, "Target difference T (raw units)", 15, "middle", transform="rotate(-90 560 265)")
    label(550, 445, "Left of S = 10: rows 1 and 2, one per source arm.", 15)
    label(550, 474, "Below T = 10: rows 1, 3 and 4. Row 2 fixes the radius.", 15)
    line(42, 494, 1062, 494)
    label(42, 517, "At row 0 the two counts are (3, 4). Its exact local contribution is −1/4 nat.", 15, bold=True)
    out.extend(["</g>", "</svg>"])
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(build(), encoding="utf-8")
