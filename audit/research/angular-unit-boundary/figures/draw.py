"""Write a vector of the four-moment radius results and the two unit-axis decisions."""

import argparse
from fractions import Fraction
import json
from pathlib import Path
import xml.etree.ElementTree as ET


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
LAPIS = "#1F3F60"
TEAL = "#1F6968"
INK = "#2C3E50"
GREY = "#D2E0E2"
RED = "#743E37"
PAPER = "#FFFFFF"
SVG = "http://www.w3.org/2000/svg"


def build(output, assets):
    order_record = json.loads((HERE.parent / "certificate.json").read_bytes())
    old_record = assets / "audit/research/angular-truncation-extremum/certificate.json"
    root_record = json.loads(old_record.read_bytes())["critical_radius"]
    root_lo, root_hi = [Fraction(n, root_record["grid"]) for n in root_record["endpoints"]]
    scale = order_record["scale"]
    order = order_record["order"]
    previous = [Fraction(value * 10**12, scale) for value in order_record["previous"]]
    current = [Fraction(value * 10**12, scale) for value in order_record["current"]]
    second, outer = Fraction(3, 10), Fraction(39, 100)
    k5, c5 = Fraction(7, 2560), Fraction(63, 256)
    if not (0 < root_lo < root_hi < second < outer < 1):
        raise ValueError("the plotted radius results require three ordered locations")
    if not 4 * k5 * second**8 / (1 - second**2) < Fraction(1, 10**6) < 3 * k5 * c5 * outer**8:
        raise ValueError("the two four-moment tests give invalid signs")
    if not (-20 < current[0] < current[1] < 0 < previous[0] < previous[1] < 20):
        raise ValueError("the signed width or scale changed")
    if order != 7278 or scale != 10**18 or max(current[1] - current[0], previous[1] - previous[0]) > Fraction(1, 10**6):
        raise ValueError("expected the two checked unit orders and their signed widths")

    def x_radius(radius):
        return 57 + float((radius - Fraction(27, 100)) / Fraction(15, 100)) * 350

    def x_margin(value):
        return 535 + float((value + 20) / 40) * 316

    def rounded_label(lo, hi):
        # Round the mid-interval value to the nearest 0.01 on the drawing scale.
        sign = "+" if lo > 0 else "-"
        cents = round(abs((lo + hi) / 2) * 100)
        return f"{sign}{cents // 100}.{cents % 100:02d}"

    ET.register_namespace("", SVG)
    svg = ET.Element("svg", xmlns=SVG, width="900", height="420",
                     viewBox="0 0 900 420", role="img", attrib={"aria-labelledby": "title desc"})
    ET.SubElement(svg, "title", id="title").text = "Radius and order decisions for the angular population"
    ET.SubElement(svg, "desc", id="desc").text = (
        "Left, with four even joint moments and exact proper terms, all directions pass at positive radii below the "
        "interior root near 0.292039, the two axes differ at radius 0.30, and all directions fail "
        "from radius 0.39 to 1. This panel shows the original sufficient bound. Right, at unit radius on the first "
        "harmonic axis the signed excess over one millionth of the exact atom is positive at "
        "7,277 moments and negative at 7,278 moments. Values are in trillionths of a nat."
    )
    ET.SubElement(svg, "rect", width="900", height="420", fill=PAPER)

    def line(x0, y0, x1, y1, stroke=INK, width=1.3, dash=None):
        attrs = {"x1": f"{x0:.3f}", "y1": str(y0), "x2": f"{x1:.3f}", "y2": str(y1),
                 "stroke": stroke, "stroke-width": str(width)}
        if dash:
            attrs["stroke-dasharray"] = dash
        ET.SubElement(svg, "line", attrs)

    def label(x, y, words, size=17, fill=INK, anchor="start", bold=False):
        attrs = {"x": f"{x:.3f}", "y": str(y), "font-family": "Source Sans Pro, sans-serif",
                 "font-size": str(size), "fill": fill, "text-anchor": anchor,
                 "font-weight": "600" if bold else "400"}
        ET.SubElement(svg, "text", attrs).text = words

    def circle(x, y, radius, fill, stroke):
        ET.SubElement(svg, "circle", cx=f"{x:.3f}", cy=str(y), r=str(radius), fill=fill,
                      stroke=stroke, attrib={"stroke-width": "2.4"})

    def diamond(x, y, size, fill):
        ET.SubElement(svg, "path", d=f"M{x:.3f} {y-size} l{size} {size} l-{size} {size} l-{size} -{size} z", fill=fill)

    label(35, 47, "Four moments across directions", 25, LAPIS, bold=True)
    label(35, 75, "Strict error below one part per million", 17)
    label(472, 47, "Two adjacent orders at unit radius", 25, LAPIS, bold=True)
    label(472, 75, "b = 0, |a| = 1, exact proper terms", 17)
    line(447, 27, 447, 391, GREY)
    label(47, 123, "Every direction passes", 19, TEAL, bold=True)
    x_cut = x_radius((root_lo + root_hi) / 2)
    line(x_radius(Fraction(27, 100)), 145, x_cut, 145, TEAL, 4)
    circle(x_cut, 145, 5, PAPER, TEAL)
    label(x_cut + 12, 151, "root near 0.292039", 16)
    label(47, 196, "The two axes differ", 19, INK, bold=True)
    circle(x_radius(second), 218, 5, INK, INK)
    label(x_radius(second) + 13, 224, "radius 0.30", 16)
    label(47, 268, "Sufficient range for all to fail", 19, RED, bold=True)
    line(x_radius(outer), 289, x_radius(Fraction(42, 100)), 289, RED, 4, "8,5")
    diamond(x_radius(outer), 289, 6, RED)
    label(x_radius(outer) - 12, 295, "0.39 through 1", 16, anchor="end")
    line(57, 326, 407, 326)
    for hundredths in (27, 30, 33, 36, 39, 42):
        x = x_radius(Fraction(hundredths, 100))
        line(x, 326, x, 332)
        label(x, 351, f"0.{hundredths:02d}", 15, anchor="middle")
    label(232, 382, "Amplitude radius", 19, LAPIS, "middle", True)

    line(x_margin(0), 133, x_margin(0), 326, INK, 1.3, "4,4")
    for y, count, interval, result, tint in (
        (158, order - 1, previous, "fails", RED), (263, order, current, "passes", TEAL)
    ):
        label(493, y - 35, f"{count:,} moments", 19, tint, bold=True)
        center = x_margin(sum(interval) / 2)
        line(x_margin(0), y, center, y, tint, 3)
        if interval[0] > 0:
            diamond(center, y, 6, tint)
        else:
            circle(center, y, 5, PAPER, tint)
        label(493, y + 26, rounded_label(*interval) + "  " + result, 17, tint)
    line(535, 326, 851, 326)
    for signed_tick in (-20, -10, 0, 10, 20):
        x = x_margin(Fraction(signed_tick))
        line(x, 326, x, 332)
        label(x, 351, str(signed_tick), 15, anchor="middle")
    label(693, 382, "Signed excess, trillionths of a nat", 19, LAPIS, "middle", True)

    ET.indent(svg)
    output.write_bytes(ET.tostring(svg, encoding="utf-8", xml_declaration=True) + b"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--assets-root", type=Path, default=ROOT)
    args = parser.parse_args()
    build(args.output, args.assets_root)
