"""Draw a six-observation attaining example from the exact count certificate."""

import argparse
from decimal import Decimal, localcontext
from fractions import Fraction
import json
from pathlib import Path
import xml.etree.ElementTree as ET

INK = "#2C3E50"
NAVY = "#1F3F60"
TEAL = "#1F6968"
WINE = "#743E37"
PALE = "#D2E0E2"


def element(parent, tag, attributes, content=None):
    child = ET.SubElement(parent, tag, {k: str(v) for k, v in attributes.items()})
    child.text = content
    return child


def text(canvas, x, y, value, size=13, colour=INK, weight=400, anchor="start"):
    return element(
        canvas,
        "text",
        {
            "x": x,
            "y": y,
            "font-size": size,
            "fill": colour,
            "font-weight": weight,
            "text-anchor": anchor,
        },
        str(value),
    )


def rule(canvas, x, y, x2, y2, colour=PALE, width=1):
    return element(
        canvas,
        "line",
        {"x1": x, "y1": y, "x2": x2, "y2": y2, "stroke": colour, "stroke-width": width},
    )


def rect(canvas, x, y, width, height, fill, stroke="none"):
    return element(
        canvas,
        "rect",
        {
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "fill": fill,
            "stroke": stroke,
        },
    )


def draw(result):
    with localcontext() as context:
        context.prec = 45
        values = {}
        for row in result["sharp_witnesses"]:
            if row["N"] == 6:
                factor = Fraction(row["exp_N_gap"])
                values[row["ell"]] = (
                    Decimal(factor.numerator).ln() - Decimal(factor.denominator).ln()
                ) / 6
    if set(values) != set(range(2, 7)) or result["sharp_witness_count"] != 123:
        raise ValueError("incomplete empirical certificate")
    root = ET.Element(
        "svg",
        {
            "xmlns": "http://www.w3.org/2000/svg",
            "viewBox": "0 0 750 318",
            "width": "750",
            "height": "318",
            "role": "img",
            "aria-labelledby": "fig-title fig-desc",
        },
    )
    element(
        root,
        "title",
        {"id": "fig-title"},
        "The smallest positive third-source budget gap for six observations",
    )
    element(
        root,
        "desc",
        {"id": "fig-desc"},
        "At left, the first source is copied to the target and the second source is constant. The first-source groups have third-source counts [1,1], [2,0], and [0,2]. At right, the exact least positive gap increases from 0.192 to 0.462 nats as the number of occupied third labels rises from two to six. Each marker fixes only the total count and the number of occupied third labels. The other source and target alphabets can vary.",
    )
    rect(root, 0, 0, 750, 318, "white")
    g = element(root, "g", {"font-family": "DejaVu Sans, sans-serif"})
    text(g, 16, 23, "The smallest positive gap for six observations", 18, NAVY, 650)
    text(
        g,
        16,
        43,
        "A is the entropy of source 3 given sources 1 and 2. B also conditions on the target. The gap is A + B − M in nats.",
        12,
    )
    text(
        g,
        16,
        61,
        "M sums the absolute values of the five signed mean atoms whose every source group contains source 3.",
        12,
    )
    g = element(g, "g", {"transform": "translate(0,18)"})
    rule(g, 16, 56, 732, 56)
    text(g, 16, 83, "One table that attains the minimum", 15, TEAL, 650)
    text(g, 16, 102, "The target copies source 1. Source 2 is constant.", 12)
    text(g, 16, 134, "Source 1", 12, NAVY, 650)
    text(g, 157, 118, "Source 3", 12, NAVY, 650, "middle")
    for x, label in ((137, "a"), (178, "b")):
        text(g, x, 135, label, 12, INK, 600, "middle")
    counts = ((1, 1), (2, 0), (0, 2))
    for i, (label, row) in enumerate(
        zip(("shared", "only a", "only b"), counts, strict=True)
    ):
        y = 143 + 27 * i
        text(g, 17, y + 17, label, 13, INK, 600 if i == 0 else 400)
        for j, count in enumerate(row):
            rect(
                g,
                115 + 42 * j,
                y,
                42,
                27,
                TEAL if i == 0 else "white",
                "white" if i == 0 else PALE,
            )
            text(
                g,
                136 + 42 * j,
                y + 18,
                count,
                13,
                "white" if i == 0 else INK,
                600 if count else 400,
                "middle",
            )
    text(g, 212, 157, "Two labels occur", 12)
    text(g, 212, 174, "in the shared row.", 12)
    text(g, 16, 252, "Both third labels have total count 3.", 12)
    text(g, 16, 274, "Gap = ln(256/81)/6 ≈ 0.192 nats.", 13, NAVY, 650)
    rule(g, 345, 75, 345, 282)
    text(g, 364, 83, "What changes with more third labels?", 15, TEAL, 650)
    text(g, 364, 104, "Least positive gap (nats)", 12)
    x0, x1, y0, y1 = 401, 708, 235, 126
    yplot = lambda z: y0 - (y0 - y1) * float(z) / 0.5
    for val in (0, 0.1, 0.2, 0.3, 0.4, 0.5):
        ypos = yplot(val)
        rule(g, x0, ypos, x1, ypos, PALE, 0.8)
        text(
            g, x0 - 8, ypos + 4, format(val, ".1f") if val else "0", 11, INK, 400, "end"
        )
    rule(g, x0, y0, x1, y0, NAVY, 1.2)
    rule(g, x0, y0, x0, y1, NAVY, 1.2)
    for label, value in sorted(values.items()):
        xpos = x0 + (x1 - x0) * (label - 2) / 4
        ypos = yplot(value)
        rule(g, xpos, y0, xpos, ypos, TEAL, 2)
        element(g, "circle", {"cx": xpos, "cy": f"{ypos:.3f}", "r": 4, "fill": WINE})
        text(
            g,
            xpos + 9 if label == 2 else xpos - 3 if label == 6 else xpos,
            ypos - 10,
            f"{value:.3f}",
            10.5,
            WINE,
            600,
            "middle",
        )
        text(g, xpos, y0 + 17, label, 12, INK, 400, "middle")
    text(
        g,
        (x0 + x1) / 2,
        273,
        "Number of occupied source 3 labels",
        12,
        NAVY,
        500,
        "middle",
    )
    text(g, 16, 293, "Each point fixes only the total and the number of occupied third labels. Other source and target alphabets can vary.", 12)
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_bytes(draw(json.loads(args.data.read_bytes())))
