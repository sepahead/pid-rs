"""Render the registered interval at its true position on both linear scales."""

import argparse
from fractions import Fraction
import json
from pathlib import Path
from xml.sax.saxutils import escape

BASE = Path(__file__).resolve().parent
LAPIS = "#1F3F60"
TURQUOISE = "#1F6968"
INK = "#2C3E50"
MINERAL = "#D2E0E2"
IVORY = "#F7F3E9"
BRONZE = "#916400"
POMEGRANATE = "#743E37"


def illustration(certificate):
    lower, upper = (
        Fraction(certificate[key], 4096) for key in ("lower_index", "upper_index")
    )
    width = upper - lower
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="840" height="440" viewBox="0 0 840 440" role="img" aria-labelledby="title desc">',
        '<title id="title">Four even moments on the angular model</title>',
        '<desc id="desc">Two linear axes show the amplitude radius. On the whole interval from zero to one half, the threshold lies just above one quarter. On an expanded scale the circle marks the all-directions guarantee through '
        + str(lower)
        + ". The diamond marks a violation at "
        + str(upper)
        + " with a equal to the radius and b equal to zero. The unresolved width is "
        + str(width)
        + ". At zero the relative error is undefined.</desc>",
        '<rect width="840" height="440" rx="0" fill="' + IVORY + '"/>',
        '<g font-family="Source Sans Pro, Source Sans 3, Arial, sans-serif" fill="'
        + INK
        + '">',
    ]

    def label(x, y, s, size=20, fill=INK, bold=False, align="start"):
        out.append(
            f'<text x="{x:.2f}" y="{y}" text-anchor="{align}" font-size="{size}" fill="{fill}" font-weight="{600 if bold else 400}">{escape(s)}</text>'
        )

    def line(x1, y1, x2, y2, color, width=2, more=""):
        out.append(
            f'<line x1="{x1:.2f}" x2="{x2:.2f}" y1="{y1}" y2="{y2}" stroke="{color}" stroke-width="{width}" {more}/>'
        )

    def circle(x, y, size, color, fill):
        out.append(
            f'<circle cx="{x:.2f}" cy="{y}" r="{size}" stroke="{color}" fill="{fill}" stroke-width="2.2"/>'
        )

    def diamond(x, y, size, color):
        out.append(
            f'<path d="M{x:.2f} {y - size} l{size} {size} l-{size} {size} l-{size} -{size} z" fill="{color}"/>'
        )

    def pos(value, start, end):
        return 64 + 712 * float((value - start) / (end - start))

    def tick(x, y, s, align="middle"):
        line(x, y - 4, x, y + 7, INK, 1.5)
        label(x, y + 29, s, 17, align=align)

    label(42, 43, "Four even moments on the angular model", 32, LAPIS, True)
    label(
        42,
        73,
        "Relative error tolerance 1 in 1,000,000. The amplitude radius is r = |a| + |b|.",
        20,
    )
    line(42, 88, 798, 88, MINERAL, 1)
    label(42, 115, "Full study range", 20, TURQUOISE, True)
    lo = Fraction(0)
    hi = Fraction(1, 2)
    y = 139
    x0, x1 = pos(lower, lo, hi), pos(upper, lo, hi)
    line(64, y, 776, y, INK, 2)
    line(65, y, x0, y, TURQUOISE, 5)
    line(x0, y, x1, y, BRONZE, 7)
    for value, word in [(lo, "0"), (Fraction(1, 4), "1/4"), (hi, "1/2")]:
        tick(pos(value, lo, hi), y, word)
    circle(64, y, 5, INK, IVORY)
    label(42, 194, "Expanded scale", 20, TURQUOISE, True)
    label(191, 194, "The marked endpoints bracket the unknown threshold.", 18)
    lo = Fraction(27, 100)
    hi = Fraction(31, 100)
    y = 230
    x0, x1 = pos(lower, lo, hi), pos(upper, lo, hi)
    line(64, y, 776, y, INK, 2)
    line(64, y, x0, y, TURQUOISE, 6)
    line(x0, y, x1, y, BRONZE, 6, 'stroke-dasharray="4,4"')
    for k in range(27, 32):
        tick(pos(Fraction(k, 100), lo, hi), y, f"0.{k}")
    circle(x0, y, 7, TURQUOISE, IVORY)
    diamond(x1, y, 9, POMEGRANATE)
    label(
        420, 292, "Unresolved interval width  " + str(width), 20, BRONZE, True, "middle"
    )
    line(42, 307, 798, 307, MINERAL, 1)
    circle(56, 333, 7, TURQUOISE, IVORY)
    label(76, 340, "All amplitude directions", 23, LAPIS, True)
    diamond(438, 333, 9, POMEGRANATE)
    label(458, 340, "One failing direction", 23, LAPIS, True)
    label(50, 371, "Through r = " + str(lower), 20)
    label(431, 371, "At r = " + str(upper) + ", a = r and b = 0", 20)
    label(50, 398, "Relative error is below tolerance.", 18)
    label(431, 398, "Actual relative error exceeds tolerance.", 18)
    label(
        50,
        427,
        "At r = 0 the relative error is undefined. All three proper terms are kept exact.",
        16,
    )
    out.extend(["</g>", "</svg>"])
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    arg = argparse.ArgumentParser(description=__doc__)
    arg.add_argument("--output", type=Path, required=True)
    a = arg.parse_args()
    a.output.write_text(
        illustration(json.loads((BASE.parent / "certificate.json").read_bytes())),
        encoding="utf-8",
    )
