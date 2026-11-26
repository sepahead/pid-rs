"""Draw the two finite joint count tables used in the copy-target example."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


PANEL_SHA = "61030c1132d88c21808351a845fcdb0080578d2c8e75137b8fa95c3d4071a36c"
NAVY = "#1F3F60"
TEAL = "#1F6968"
INK = "#2C3E50"
LIGHT = "#D2E0E2"
WINE = "#743E37"


def add(parent, tag, attributes, label=None):
    node = ET.SubElement(parent, tag, {key: str(value) for key, value in attributes.items()})
    node.text = label
    return node


def label(group, x, y, value, size=14, anchor="start", color=INK, bold=False):
    return add(group, "text", {
        "x": x, "y": y, "fill": color, "font-size": size, "text-anchor": anchor,
        "font-weight": 600 if bold else 400,
    }, str(value))


def panel(group, x, name, counts, mass_factor):
    label(group, x, 45, name, 16, color=TEAL, bold=True)
    label(group, x, 69, "Row X", 13)
    label(group, x + 119, 69, "Column W", 13, "middle")
    for col in range(3):
        label(group, x + 70 + col * 50, 88, col + 1, 13, "middle")
    for row, cells in enumerate(counts):
        label(group, x + 18, 112 + row * 30, row + 1, 13, "middle")
        for col, count in enumerate(cells):
            left, top = x + 45 + col * 50, 93 + row * 30
            both_shared = (count > 0 and sum(v > 0 for v in cells) > 1
                           and sum(line[col] > 0 for line in counts) > 1)
            add(group, "rect", {
                "x": left + 1, "y": top + 1, "width": 48, "height": 28,
                "fill": LIGHT if count else "#FFFFFF",
                "stroke": WINE if both_shared else "#8396A0",
                "stroke-width": 2.5 if both_shared else 0.7,
            })
            if both_shared:
                add(group, "rect", {
                    "x": left + 4, "y": top + 4, "width": 42, "height": 22,
                    "fill": "none", "stroke": WINE, "stroke-width": 1,
                })
            label(group, left + 25, top + 20, count, 15, "middle", bold=bool(count))
    label(group, x, 204, "Mass factor exp(4M) = " + mass_factor, 14, color=NAVY, bold=True)


def draw(raw):
    if hashlib.sha256(raw).hexdigest() != PANEL_SHA:
        raise ValueError("the count figure requires the two published exact tables")
    report = json.loads(raw)
    root = ET.Element("svg", {
        "xmlns": "http://www.w3.org/2000/svg", "width": "700", "height": "265",
        "viewBox": "0 0 700 265", "role": "img", "aria-labelledby": "title description",
    })
    add(root, "title", {"id": "title"}, "Two four-observation tables with the same entropies")
    add(root, "desc", {"id": "description"},
        "The first table has rows 100, 011 and 010. The second has rows 010, 101 and 010. "
        "A double outline marks the first table’s central occupied cell. Its row and column "
        "both have another occupied cell. The second table has no such cell. Both tables have "
        "the same row and column counts. M is measured in nats. It sums the absolute values of the five signed mean atoms for which every source group contains source three. The target copies X and source two is constant.")
    add(root, "rect", {"x": 0, "y": 0, "width": 700, "height": 265, "fill": "#FFFFFF"})
    group = add(root, "g", {"font-family": "DejaVu Sans, sans-serif"})
    label(group, 14, 20, "First source X, middle source constant, third source W, target X. Four observations per table.", 15, color=NAVY)
    for x, name, table, key in zip((38, 385), ("First table", "Second table"), report["counts"], ("first", "second")):
        panel(group, x, name, table, report[key]["exp_four_M"])
    label(group, 14, 229, "M is the sum of the absolute values of the five signed mean atoms whose groups all contain W.", 13)
    label(group, 14, 251, "M is in nats. A double outline marks a 1 that shares both its row and its column.", 13)
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.write_bytes(draw(args.data.read_bytes()))


if __name__ == "__main__":
    main()
