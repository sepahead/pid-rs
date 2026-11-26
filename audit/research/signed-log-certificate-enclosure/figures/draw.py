"""Draw exact partial sums, rounded bounds and a failed producer-containment example."""
import argparse
from fractions import Fraction
from pathlib import Path
from xml.etree.ElementTree import Element, ElementTree, SubElement, indent


INK = "#2C3E50"
BLUE = "#1F3F60"
TEAL = "#1F6968"
GRAY = "#D2E0E2"
RED = "#743E37"
WHITE = "#FFFFFF"


def draw(output):
    root = Element("svg", xmlns="http://www.w3.org/2000/svg", width="960", height="415",
                   viewBox="0 0 960 415", role="img", attrib={"aria-labelledby": "title desc"})
    SubElement(root, "title", id="title").text = "Two roles of outward logarithm bounds"
    SubElement(root, "desc", id="desc").text = (
        "Left: for x=1/3 at four internal bits, rounded partial-sum intervals in units of 1/16 "
        "are [10,12], [10,14] and [10,15]. Circles show the exact scaled finite sums. The "
        "one-unit tail allowance extends the third interval to [10,16]. Right: at Q=1+2^-2048, "
        "N=1 and p=2048, the producer interval covers zero to one and the independent verifier "
        "interval covers zero to two, in units of 2^-2048 nats. Both contain the true value.")
    SubElement(root, "rect", x="0", y="0", width="960", height="415", fill=WHITE)
    group = SubElement(root, "g", attrib={"font-family": "Source Sans Pro, sans-serif"})

    def line(x1, y1, x2, y2, color=INK, width=1, dashed=False):
        attributes = dict(x1=str(x1), y1=str(y1), x2=str(x2), y2=str(y2), stroke=color)
        attributes["stroke-width"] = str(width)
        if dashed:
            attributes["stroke-dasharray"] = "6,4"
        SubElement(group, "line", attributes)

    def label(x, y, value, size=16, color=INK, anchor="start", weight="400"):
        SubElement(group, "text", x=str(x), y=str(y),
                   attrib={"text-anchor": anchor, "font-size": str(size),
                           "fill": color, "font-weight": weight}).text = value

    def bar(x, lo, hi):
        y1, y2 = yvalue(lo), yvalue(hi)
        line(x, y1, x, y2, BLUE, 3)
        line(x-8, y1, x+8, y1, BLUE, 3)
        line(x-8, y2, x+8, y2, BLUE, 3)

    def yvalue(y):
        return round(304 - 23 * (float(y) - 8), 4)

    def endpoint(x1, x2, y, ink, dashed=False):
        line(x1, y, x2, y, ink, 4, dashed)
        for x in (x1, x2):
            line(x, y-6, x, y+6, ink, 3)

    label(26, 32, "Rounding at each term", 24, BLUE, weight="600")
    label(26, 60, "Argument x = 1/3, internal scale = 16", 17)
    label(26, 88, "Value in units of 1/16", 15)
    line(480, 16, 480, 399, GRAY, 2)
    for tick in (8, 10, 12, 14, 16):
        y = yvalue(tick)
        line(62, y, 447, y, GRAY)
        label(51, y+5, str(tick), 15, anchor="end")
    line(62, yvalue(8), 62, yvalue(16), INK)
    line(62, yvalue(8), 447, yvalue(8), INK)
    x = Fraction(1, 3)
    low, high = 5, 6
    lower_sum = upper_sum = 0
    exact = Fraction()
    for j, xpos in enumerate((119, 241, 363)):
        odd = 2*j + 1
        lower_sum += 2*low//odd
        upper_sum += -((-2*high)//odd)
        exact += 32*x**odd/odd
        low, high = low//16, -((-3*high)//16)
        bar(xpos, lower_sum, upper_sum)
        SubElement(group, "circle", cx=str(xpos), cy=str(yvalue(exact)), r="5.5", fill=TEAL)
        label(xpos, 325, str(j+1), 16, anchor="middle")
    if (lower_sum, upper_sum) != (10, 15) or exact != Fraction(13472, 1215):
        raise ValueError("three exact sums and final rounded endpoints")
    line(363, yvalue(15), 363, yvalue(16), RED, 3, True)
    line(355, yvalue(16), 371, yvalue(16), RED, 3)
    label(249, 348, "Number of included terms", 16, anchor="middle")
    label(26, 377, "Circle = exact partial sum. Bar = rounded partial sum.", 15)
    label(26, 400, "Dashed extension = one upper unit for the real remainder.", 15)
    label(505, 32, "Two intervals can both be correct", 23, BLUE, weight="600")
    label(505, 60, "Product Q = 1 + 2⁻²⁰⁴⁸, total N = 1", 17)
    label(505, 85, "Output precision p = 2048 bits", 17)
    first, middle, last = 580, 740, 900
    for xpos in (first, middle, last):
        line(xpos, 118, xpos, 289, GRAY)
    label(505, 140, "Producer", 16, BLUE, weight="600")
    endpoint(first, middle, 163, BLUE)
    label(505, 211, "Verifier", 16, RED, weight="600")
    endpoint(first, last, 234, RED, True)
    line(first, 289, last, 289, INK)
    for i, xpos in enumerate((first, middle, last)):
        line(xpos, 285, xpos, 293, INK)
        label(xpos, 313, str(i), 16, anchor="middle")
    label(737, 347, "Value in units of 2⁻²⁰⁴⁸ nats", 16, anchor="middle")
    label(505, 377, "The true value is strictly between grid points 0 and 1.", 15)
    label(505, 400, "The producer interval excludes the verifier endpoint 2.", 15)
    indent(root)
    with output.open("wb") as stream:
        ElementTree(root).write(stream, encoding="utf-8", xml_declaration=True)
        stream.write(b"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    draw(parser.parse_args().output)
