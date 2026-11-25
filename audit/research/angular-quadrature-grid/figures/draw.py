"""Draw the two integer grids and the eight observed missing boundary points."""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
INK, BLUE, TEAL, RED, FAINT, WHITE = "#2C3E50", "#1F3F60", "#1F6968", "#743E37", "#D2E0E2", "#FFFFFF"

def draw(out):
    fixed = json.loads((HERE.parent / "quadrature-grid.json").read_bytes())
    old = json.loads((HERE.parent / "historical-grid.json").read_bytes())
    missing = [tuple(x) for x in old["missing"]]
    if (fixed["lower"]["pairs"], fixed["tail"]["pairs"], old["old_tail_count"]) != (2244,1860,1852):
        raise ValueError("unexpected numerical coverage")
    if len(set(missing)) != 8 or any(abs(i)+abs(j) != 30 for i,j in missing) or old["extra"]:
        raise ValueError("expected eight distinct missing points on ring 30")
    root = ET.Element("svg", xmlns="http://www.w3.org/2000/svg", width="900", height="420",
                      viewBox="0 0 900 420", role="img", attrib={"aria-labelledby":"title description"})
    ET.SubElement(root,"title",id="title").text = "The integer amplitude grid and its earlier omissions"
    ET.SubElement(root,"desc",id="description").text = (
        "A solid outer diamond encloses the nonzero grid through ring 33. A dashed inner diamond "
        "encloses the nonzero grid through ring 30. Eight open circles on the inner edge identify "
        "points omitted by the earlier floating-point filter. A cross marks the excluded origin."
    )
    ET.SubElement(root,"rect",width="900",height="420",fill=WHITE)
    def label(x,y,value,size=18,tint=INK,bold=False,anchor="start"):
        ET.SubElement(root,"text",x=str(x),y=str(y),fill=tint,attrib={
            "font-family":"Source Sans Pro, sans-serif","font-size":str(size),
            "font-weight":"600" if bold else "400","text-anchor":anchor}).text=value
    def line(x1,y1,x2,y2,tint=INK,size=1.5,dash=None):
        attr={"x1":str(x1),"y1":str(y1),"x2":str(x2),"y2":str(y2),"stroke":tint,"stroke-width":str(size)}
        if dash: attr["stroke-dasharray"]=dash
        ET.SubElement(root,"line",attr)
    def xy(i,j):
        return 225+4.3*i, 213-4.3*j
    def point(x,y):
        ET.SubElement(root,"circle",cx=f"{x:.3f}",cy=f"{y:.3f}",r="4.2",stroke=RED,fill=WHITE,
                      attrib={"stroke-width":"2.6"})
    label(30,34,"Integer amplitude indices",23,BLUE,True)
    line(58,213,397,213,FAINT,1.6)
    line(225,55,225,370,FAINT,1.6)
    for radius,tint,dash in ((33,BLUE,None),(30,TEAL,"6,4")):
        for p,q in zip(((radius,0),(0,radius),(-radius,0),(0,-radius)),
                       ((0,radius),(-radius,0),(0,-radius),(radius,0))):
            line(*xy(*p),*xy(*q),tint,2.7,dash)
    for i,j in missing:
        point(*xy(i,j))
    line(221,209,229,217,INK,2)
    line(221,217,229,209,INK,2)
    label(373,206,"i",19,BLUE,True)
    label(237,62,"j",19,BLUE,True)
    label(68,238,"-33",16,anchor="end")
    label(377,238,"33",16)
    label(236,359,"-33",16)
    label(213,78,"33",16,anchor="end")
    line(420,27,420,376,FAINT)
    label(452,42,"Pairs in each check",23,BLUE,True)
    line(454,81,502,81,BLUE,3)
    label(520,88,"Lower bound",20,BLUE,True)
    label(454,115,"Rings 1 to 33 give 2,244 pairs.")
    line(454,154,502,154,TEAL,3,"6,4")
    label(520,161,"Eight-moment remainder",20,TEAL,True)
    label(454,187,"Rings 1 to 30 give 1,860 pairs.")
    point(477,226)
    label(520,233,"Earlier omissions",20,RED,True)
    label(454,259,"Eight boundary pairs were lost.")
    line(473,291,481,299,INK,2)
    line(473,299,481,291,INK,2)
    label(520,302,"Origin",20,INK,True)
    label(454,329,"Both comparisons exclude ring zero.")
    label(33,397,"Each index step changes its amplitude by 0.03. Axes and ring numbers have no units.",17)
    ET.indent(root)
    out.write_bytes(ET.tostring(root,encoding="utf-8",xml_declaration=True)+b"\n")

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    draw(parser.parse_args().output)
