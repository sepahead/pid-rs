"""Render the two concrete byte words from one set of text and line coordinates."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FONTS = Path("audit/formal/latex/source-coupling-compression/fonts")
PAL = {"ink":"2C3E50", "lapis":"1F3F60", "blue":"1F6968", "wine":"743E37", "line":"A7B6B8", "white":"FFFFFF"}
WIDTH, HEIGHT = 850, 294


def drawing():
    marks = []
    def text(x,y,value,size=17,color="ink",bold=False,center=False):
        marks.append(("text",x,y,value,size,color,bold,center))
    def line(x,y,X,Y,color="line",width=1):
        marks.append(("line",x,y,X,Y,color,width))
    text(18,27,"Read one quoted token",26,"lapis",True)
    text(832,27,"Decimal byte values",16,"ink",False,False)
    text(18,65,"Accepted",20,"blue",True)
    good=[(173,34,"open"),(270,65,"A"),(351,49,"1"),(443,34,"close"),(572,44,"comma"),(705,255,"byte 255")]
    for x,n,label in good:
        text(x,69,str(n),25,"ink",True,True)
        text(x,95,label,16,"ink",False,True)
    line(142,107,474,107,"blue",3)
    line(142,101,142,112,"blue",2)
    line(474,101,474,112,"blue",2)
    text(308,132,"Consumed word",18,"blue",True,True)
    line(524,107,757,107,"lapis",3)
    line(524,101,524,112,"lapis",2)
    line(757,101,757,112,"lapis",2)
    text(641,132,"Untouched suffix",18,"lapis",True,True)
    line(18,154,820,154)
    text(18,191,"Rejected",20,"wine",True)
    bad=[(173,34,"open"),(270,65,"A"),(351,44,"comma"),(443,49,"1"),(572,34,"quote")]
    for x,n,label in bad:
        col="wine" if n==44 else "ink"
        text(x,194,str(n),25,col,True,True)
        text(x,220,label,16,col,False,True)
    line(322,231,380,231,"wine",3)
    text(18,263,"Byte 44 stops the scan. The reader needs byte 34 at that position and refuses this word.",18,"ink")
    return marks


def svg(marks):
    root=ET.Element("svg",{"xmlns":"http://www.w3.org/2000/svg","width":str(WIDTH),"height":str(HEIGHT),
                            "viewBox":f"0 0 {WIDTH} {HEIGHT}","role":"img","aria-labelledby":"title desc"})
    ET.SubElement(root,"title",id="title").text="Reading one quoted state token"
    ET.SubElement(root,"desc",id="desc").text=(
        "The accepted word starts with bytes 34, 65, 49, 34. It returns token A1 and leaves bytes 44 and 255. "
        "The second word has byte 44 where the closing quote is required and fails.")
    ET.SubElement(root,"rect",width=str(WIDTH),height=str(HEIGHT),fill="#FFFFFF")
    for kind,*a in marks:
        if kind=="line":
            x,y,X,Y,col,width=a
            ET.SubElement(root,"line",{"x1":str(x),"y1":str(y),"x2":str(X),"y2":str(Y),"stroke":"#"+PAL[col],"stroke-width":str(width)})
        else:
            x,y,v,size,col,bold,center=a
            anchor="middle" if center else "end" if x>820 else "start"
            ET.SubElement(root,"text",{"x":str(x),"y":str(y),"fill":"#"+PAL[col],"font-family":"Source Sans Pro, sans-serif",
                                      "font-size":str(size),"font-weight":"600" if bold else "400","text-anchor":anchor}).text=v
    ET.indent(root,space="  ")
    return ET.tostring(root,encoding="utf-8",xml_declaration=True)+b"\n"


def tex(marks):
    body=[]
    for kind,*a in marks:
        if kind=="line":
            x,y,X,Y,col,width=a
            body.append(rf"\draw[{col},line width={.75*width}bp] ({x},{y}) -- ({X},{Y});")
        else:
            x,y,v,size,col,bold,center=a
            anchor="base" if center else "base east" if x>820 else "base west"
            weight=r"\bfseries" if bold else r"\mdseries"
            body.append(rf"\node[anchor={anchor},inner sep=0pt,outer sep=0pt,text={col},font=\fontsize{{{.75*size}bp}}{{{.9*size}bp}}\selectfont{weight}] at ({x},{y}) {{{v}}};")
    palette=[rf"\definecolor{{{name}}}{{HTML}}{{{value}}}" for name,value in PAL.items()]
    return "\n".join([r"\documentclass[tikz,border=0pt]{standalone}",r"\usepackage{fontspec}",
        r"\setmainfont[Path=fonts/,BoldFont=SourceSansPro-Semibold.otf]{SourceSansPro-Regular.otf}",
        r"\pdfvariable minorversion=4",r"\pdfvariable suppressoptionalinfo=767",
        r"\pdfextension info { /Title (Reading one quoted state token) /Author (Sepehr Mahmoudian) }",*palette,
        r"\begin{document}",r"\begin{tikzpicture}[x=0.75bp,y=-0.75bp]",
        rf"\fill[white] (0,0) rectangle ({WIDTH},{HEIGHT});",*body,r"\end{tikzpicture}",r"\end{document}",""])


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--write-svg",action="store_true")
    cli.add_argument("--output",type=Path)
    cli.add_argument("--assets-root",type=Path,default=ROOT)
    args=cli.parse_args()
    if not(args.output or args.write_svg): cli.error("select --write-svg, --output, or both")
    marks=drawing()
    vector=svg(marks)
    path=HERE/"quoted-token-boundaries.svg"
    if args.write_svg:path.write_bytes(vector)
    if args.output:
        if path.read_bytes()!=vector:raise ValueError("source diagram differs from the drawing")
        with tempfile.TemporaryDirectory(prefix="categorical-token-diagram-") as tmp:
            work=Path(tmp);(work/"fonts").mkdir()
            for f in ("SourceSansPro-Regular.otf","SourceSansPro-Semibold.otf"):
                shutil.copyfile(args.assets_root.resolve()/FONTS/f,work/"fonts"/f)
            (work/"figure.tex").write_text(tex(marks),encoding="utf-8")
            result=subprocess.run(["lualatex","-no-shell-escape","-halt-on-error","-interaction=nonstopmode","figure.tex"],
                                  cwd=work,capture_output=True,env=dict(os.environ,SOURCE_DATE_EPOCH="1795478400",TZ="UTC",LC_ALL="C"))
            if result.returncode:raise ValueError(result.stdout.decode(errors="replace")[-2000:])
            args.output.write_bytes((work/"figure.pdf").read_bytes())


if __name__=="__main__":
    main()
