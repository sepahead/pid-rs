"""Reproduce the table comparison and its SVG. Python 3.11 or later.
Usage: python3 example.py --check (or --write to regenerate the figure).
"""
import argparse
import json
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
SVG = HERE / "support-bounds.svg"
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)

def require(test, message):
    if not test:
        raise ValueError(message)

def read_tables(data):
    require(data["order"] == ["source_1", "source_2", "target"], "variable order")
    require(data["alphabet"] == [2, 2, 2], "binary alphabet")
    reference, changed = {}, {}
    for row in data["rows"]:
        cell = row["cell"]
        require(isinstance(cell, str) and len(cell) == 3 and set(cell) <= {"0", "1"}, "binary cell")
        require(cell not in reference, "duplicate cell")
        for name, table in (("reference", reference), ("changed", changed)):
            count = row[name]
            require(type(count) is int and count >= 0, "nonnegative integer count")
            table[cell] = count
    n, m = sum(reference.values()), sum(changed.values())
    require(n > 0 and m > 0, "nonempty tables")
    p = {c: Fraction(v, n) for c, v in reference.items()}
    q = {c: Fraction(v, m) for c, v in changed.items()}
    return p, q

def summary(p, q):
    keys = p.keys() | q.keys()
    s = {x for x in keys if p.get(x, 0) > 0}
    t = {x for x in keys if q.get(x, 0) > 0}
    require(s and t, "nonempty support")
    distance = sum(abs(p.get(x, 0) - q.get(x, 0)) for x in keys) / 2
    return s, t, min(p[x] for x in s), distance

def numbers(p, q, ks):
    s, t, pmin, eta = summary(p, q)
    require(len(ks) > 0 and all(type(k) is int and k >= len(s | t) and k >= 1 for k in ks),
            "K must cover the union support")
    if eta == 0:
        return Decimal(0), {k: Decimal(0) for k in ks}
    require(s == t and eta < pmin, "the local comparison needs common support and TV below p_min")
    require(all(k >= 2 for k in ks), "positive distance needs at least two cells")
    with localcontext() as ctx:
        ctx.prec = 60
        e = Decimal(eta.numerator) / Decimal(eta.denominator)
        p0 = Decimal(pmin.numerator) / Decimal(pmin.denominator)
        first = -(1 - e / p0).ln() - e + 2 * e * (1 / p0).ln()
        second = {k: e * (12 + Decimal(k*k // 4).ln() - 2*e.ln()) for k in ks}
        return first, second

def drawing(data, local, global_):
    lapis, teal, ink = "#1F3F60", "#1F6968", "#2C3E50"
    mineral, ivory, wine = "#D2E0E2", "#F7F3E9", "#743E37"
    root = ET.Element("{" + NS + "}svg", {"width": "800", "height": "306",
        "viewBox": "0 0 800 306", "role": "img", "aria-labelledby": "title desc"})
    def add(tag, **attrs):
        return ET.SubElement(root, "{" + NS + "}" + tag, {k.replace("_", "-"): str(v) for k,v in attrs.items()})
    add("title", id="title").text = "The same two tables give different bounds when the support limit changes"
    add("desc", id="desc").text = (
        "Reference counts in cells 000, 010, 100, 111 are 50 each. Changed counts are 1, 99, 50, 50. "
        "Total variation is 0.245. Bounds displayed to three decimal places are %.3f nats for K equal to four and %.3f for K equal to sixteen. "
        "The local bound rounds to %.3f nats. Smaller values give tighter bounds." % (global_[4], global_[16], local))
    add("rect", x=0,y=0,width=800,height=306, fill="white")
    def label(x,y,txt,sz=15, color=ink, bold=False, anchor="start"):
        add("text", x=x,y=y,fill=color, font_family="DejaVu Sans, Arial, sans-serif",font_size=sz,
            font_weight="bold" if bold else "normal",text_anchor=anchor).text=txt
    def line(x1,y1,x2,y2,color=ink,w=1):
        add("line",x1=x1,y1=y1,x2=x2,y2=y2,stroke=color,stroke_width=w)
    label(18,28,"Where the 49 counts move",19,lapis,True)
    label(372,28,"Upper bound on synergy change",19,lapis,True)
    label(372,51,"Bound values rounded to three decimal places",13,ink)
    line(345,16,345,277,mineral,1.5)
    add("rect",x=16,y=48,width=306,height=29,fill=ivory)
    label(27,68,"Cell",14,teal,True)
    label(129,68,"Reference",14,teal,True,"middle")
    label(251,68,"Changed",14,teal,True,"middle")
    for i,row in enumerate(data["rows"]):
        y=102+34*i
        label(27,y,row["cell"],16)
        label(129,y,str(row["reference"]),16,ink,False,"middle")
        label(251,y,str(row["changed"]),16,ink,False,"middle")
        line(19,y+11,319,y+11,mineral)
    label(27,246,"Each column totals 200.",14)
    label(27,269,"Total variation = 49/200.",14,teal,True)
    x0, span=516,221
    for tick in range(6):
        x=x0+span*tick/5
        line(x,61,x,216,mineral)
        label(x,235,str(tick),12,ink,False,"middle")
    line(x0,216,x0+span,216)
    label(x0+span/2,257,"Bound in nats",14,ink,False,"middle")
    lab=[("Global, K = 4",global_[4],teal),("Local, p = 1/4",local,wine),("Global, K = 16",global_[16],teal)]
    for i,(name,value,col) in enumerate(lab):
        y=91+49*i
        label(372,y+5,name,14,col,True)
        end=x0+span*float(value)/5
        line(x0,y,end,y,col,3)
        if i==1:
            add("circle",cx=end,cy=y,r=5,fill="white",stroke=col,stroke_width=2.4)
        else:
            add("rect",x=end-4,y=y-4,width=8,height=8,fill=col)
        label(785,y+5,f"{value:.3f}",14,ink,True,"end")
    label(18,294,"The tables fix the distance. K changes only the global upper bound.",14,lapis)
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n"

def main():
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = p.parse_args()
    data = json.loads((HERE/"counts.json").read_text())
    ref, changed = read_tables(data)
    local, global_ = numbers(ref, changed, data["support_bounds"])
    image = drawing(data, local, global_)
    if args.write:
        SVG.write_bytes(image)
    else:
        require(SVG.read_bytes() == image, "checked SVG differs from generated bytes")
    for name, value in (("Global, K=4",global_[4]),("Local",local),("Global, K=16",global_[16])):
        print(f"{name}: {value:.9f} nats (rounded to nine decimal places)")

if __name__ == "__main__":
    main()
