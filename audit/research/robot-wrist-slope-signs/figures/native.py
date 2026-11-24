"""Build the companion vector PDF from the SVG using only the repository's portable fonts."""

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FONTS = Path("audit/formal/latex/source-coupling-compression/fonts")
UNIT = 0.75  # SVG CSS pixels to PDF big points.


def numeric(value):
    result = float(value)
    if not -1500 <= result <= 1500:
        raise ValueError("coordinate outside figure")
    return result


def color(value):
    if not re.fullmatch(r"#[0-9A-F]{6}", value):
        raise ValueError("unexpected SVG color")
    return "rgb" + value[1:]


def escaped_text(text):
    if not re.fullmatch(r"[A-Za-z0-9 .,=+/|-]+", text):
        raise ValueError("unexpected label character")
    return text.replace("|", r"\textbar{}")


def tikz_from_svg(path):
    root = ET.parse(path).getroot()
    items = []
    colors = set()
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        values = element.attrib
        if tag in ("svg", "g", "title", "desc"):
            continue
        for key in ("stroke", "fill"):
            if key in values:
                colors.add(values[key])
        if tag == "rect":
            items.append(
                rf"\fill[{color(values['fill'])}] (0,0) rectangle ({numeric(values['width'])},{numeric(values['height'])});"
            )
        elif tag == "line":
            style = [
                color(values["stroke"]),
                f"line width={numeric(values['stroke-width']) * UNIT}bp",
            ]
            if "stroke-dasharray" in values:
                on, off = map(numeric, values["stroke-dasharray"].split(","))
                style.append(f"dash pattern=on {on * UNIT}bp off {off * UNIT}bp")
            items.append(
                rf"\draw[{','.join(style)}] ({numeric(values['x1'])},{numeric(values['y1'])}) -- ({numeric(values['x2'])},{numeric(values['y2'])});"
            )
        elif tag == "circle":
            style = f"draw={color(values['stroke'])},fill={color(values['fill'])},line width={numeric(values['stroke-width']) * UNIT}bp"
            items.append(
                rf"\path[{style}] ({numeric(values['cx'])},{numeric(values['cy'])}) circle[radius={numeric(values['r']) * UNIT}bp];"
            )
        elif tag == "path":
            points = re.fullmatch(
                r"M([0-9.]+) ([0-9.]+) l([0-9]+) \3 l-\3 \3 l-\3 -\3 z", values["d"]
            )
            if not points:
                raise ValueError("unexpected SVG path shape")
            x, y, size = map(numeric, points.groups())
            polygon = [
                (x, y),
                (x + size, y + size),
                (x, y + 2 * size),
                (x - size, y + size),
            ]
            items.append(
                rf"\fill[{color(values['fill'])}] "
                + " -- ".join(f"({px},{py})" for px, py in polygon)
                + " -- cycle;"
            )
        elif tag == "text":
            anchor = {"start": "base west", "middle": "base", "end": "base east"}[
                values["text-anchor"]
            ]
            size = numeric(values["font-size"]) * UNIT
            weight = r"\bfseries" if values["font-weight"] == "600" else r"\mdseries"
            style = rf"anchor={anchor},inner sep=0pt,outer sep=0pt,text={color(values['fill'])},font=\fontsize{{{size}bp}}{{{size * 1.15}bp}}\selectfont{weight}"
            items.append(
                rf"\node[{style}] at ({numeric(values['x'])},{numeric(values['y'])}) {{{escaped_text(element.text)}}};"
            )
        else:
            raise ValueError(f"unsupported SVG element {tag}")
    definitions = "\n".join(
        rf"\definecolor{{{color(v)}}}{{HTML}}{{{v[1:]}}}" for v in sorted(colors)
    )
    return "\n".join(
        [
            r"\documentclass[tikz,border=0pt]{standalone}",
            r"\usepackage{fontspec}",
            r"\setmainfont[Path=fonts/,BoldFont=SourceSansPro-Semibold.otf]{SourceSansPro-Regular.otf}",
            r"\pdfvariable minorversion=4",
            r"\pdfvariable suppressoptionalinfo=767",
            r"\pdfextension info { /Title (Information and correct class choices after detection) /Author (Sepehr Mahmoudian) }",
            definitions,
            r"\begin{document}",
            r"\begin{tikzpicture}[x=0.75bp,y=-0.75bp]",
            r"\useasboundingbox (0,0) rectangle (840,440);",
            *items,
            r"\end{tikzpicture}",
            r"\end{document}",
            "",
        ]
    )


def build(output, assets):
    with tempfile.TemporaryDirectory(prefix="robot-sign-figure-") as temp:
        work = Path(temp)
        fonts = work / "fonts"
        fonts.mkdir()
        for name in ("SourceSansPro-Regular.otf", "SourceSansPro-Semibold.otf"):
            shutil.copyfile(assets / FONTS / name, fonts / name)
        (work / "figure.tex").write_text(
            tikz_from_svg(HERE / "information-and-decisions.svg"), encoding="utf-8"
        )
        proc = subprocess.run(
            [
                "lualatex",
                "-no-shell-escape",
                "-halt-on-error",
                "-interaction=nonstopmode",
                "figure.tex",
            ],
            cwd=work,
            capture_output=True,
            env=dict(os.environ, SOURCE_DATE_EPOCH="1795392000", TZ="UTC", LC_ALL="C"),
        )
        if proc.returncode:
            raise RuntimeError(proc.stdout.decode(errors="replace")[-3000:])
        output.write_bytes((work / "figure.pdf").read_bytes())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--assets-root", type=Path, default=ROOT)
    args = parser.parse_args()
    build(args.output, args.assets_root)
