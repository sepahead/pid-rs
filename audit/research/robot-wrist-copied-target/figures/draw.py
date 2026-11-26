"""Draw the observed LP4 count table and its two nonzero added-source signed means."""

import argparse
from decimal import Decimal
from html import escape
import json
import os
from pathlib import Path
import runpy
import subprocess


FIG = Path(__file__).resolve().parent
STUDY = FIG.parent
LAPIS = "#1F3F60"
TURQUOISE = "#1F6968"
INK = "#2C3E50"
BLUE = "#D2E0E2"
SAFFRON = "#B28218"
LIGHT = "#E4E7E8"


def render(support, lattice):
    audits = runpy.run_path(str(STUDY/"audit_results.py"))
    result = audits["load_checked"](support, lattice)
    matrix = json.loads(support.read_bytes())["count_matrix_negative_zero_positive"]
    mag = Decimal(result["per_nonzero_magnitude_nats"])
    rounded = format(mag, ".6f")
    width = float(mag / Decimal("0.25") * 113)
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 828 376" width="828" height="376" role="img" aria-labelledby="title desc">',
           '<title id="title">Force and torque trends produce two cancelling signed means</title>',
           '<desc id="desc">In 117 LP4 robot wrist episodes the target is a software copy of the force trend. Force and torque trend counts are 52 down/down, 25 down/up, 23 up/down, and 17 up/up; no flat trends occurred. Each occupied cell shares both a row and a column with another. In nats per episode the torque-only signed atom is minus 0.244337 and the force–torque signed atom is plus 0.244337. Three other added-source atom means are zero. Force predicts 117 of 117 copies perfectly and conditional mutual information from torque is zero.</desc>',
           '<rect width="828" height="376" fill="#FFFFFF"/>']
    def label(x,y,txt,size=15,colour=INK,bold=False,align="start"):
        svg.append(f'<text x="{x}" y="{y}" fill="{colour}" font-family="Liberation Sans,Arial,sans-serif" font-size="{size}" font-weight="{"bold" if bold else "normal"}" text-anchor="{align}">{escape(str(txt))}</text>')
    def line(x1,y1,x2,y2,colour=LIGHT,weight=1):
        svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{colour}" stroke-width="{weight}"/>')
    def box(x,y,w,h,fill,stroke="none",width=1):
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')
    label(14,29,"Force and torque trends in 117 wrist episodes",24,LAPIS,True)
    label(15,52,"The target copies the force trend. The middle source is constant.",16)
    line(14,66,814,66,BLUE,1.4)
    label(15,92,"Observed episode counts",19,TURQUOISE,True)
    label(180,115,"Torque trend",15,LAPIS,True,align="middle")
    label(16,141,"Force trend",15,LAPIS,True)
    x0, y0, cw, ch = 106,151,61,29
    names = ("Down","Flat","Up")
    for j,n in enumerate(names):
        label(x0+(j+0.5)*cw,141,n,15,align="middle")
    label(325,141,"Total",15,LAPIS,True,"middle")
    for i,values in enumerate(matrix):
        y = y0+i*ch
        label(16,y+21,names[i],15)
        for j,v in enumerate(values):
            x=x0+j*cw
            box(x,y,cw-4,ch-3,BLUE if v else "#FFFFFF",LAPIS if v else LIGHT)
            if v: box(x+3,y+3,cw-10,ch-9,"none",LAPIS)
            label(x+(cw-4)/2,y+19,v,16,INK,bool(v),"middle")
        label(325,y+20,sum(values),15,align="middle")
    label(16,262,"Total",15,LAPIS,True)
    for j in range(3):label(x0+(j+0.5)*cw-2,262,sum(row[j] for row in matrix),15,INK,True,"middle")
    label(325,262,result["episodes"],15,LAPIS,True,"middle")
    label(16,286,"All four occupied cells share their row and",14)
    label(16,304,"their column with other occupied cells.",14)
    line(390,85,390,304,BLUE)
    label(410,92,"Signed atom means",19,TURQUOISE,True)
    label(410,115,"Nats per episode",15)
    base=623
    line(base,138,base,236,INK,1)
    label(410,143,"Torque alone",16,LAPIS,True)
    box(base-width,154,width,11,LAPIS)
    label(797,166,"−"+rounded,17,LAPIS,True,"end")
    label(410,196,"Force and torque together",16,TURQUOISE,True)
    box(base,207,width,11,"#FFFFFF",TURQUOISE,2)
    label(797,232,"+"+rounded,17,TURQUOISE,True,"end")
    line(base-113,246,base+113,246,INK)
    for coord,name in [(base-113,"−0.25"),(base,"0"),(base+113,"+0.25")]:
        line(coord,242,coord,250,INK)
        label(coord,266,name,13,align="middle")
    label(410,286,"The other three added-source means are zero.",14)
    label(410,304,"The two nonzero signed means sum to zero.",14)
    line(14,318,814,318,BLUE,1.4)
    label(15,341,"Force reproduces 117 of 117 copied targets.",16,LAPIS,True)
    label(15,364,"After force is known, the conditional mutual information from torque is exactly 0 nats.",15)
    return ("\n".join(svg)+"\n</svg>\n").encode()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--support",type=Path,default=STUDY/"checked/support-ordinary.json")
    p.add_argument("--lattice",type=Path,default=STUDY/"checked/lattice-ordinary.json")
    p.add_argument("--output",type=Path,required=True,help="destination directory for the two vector files")
    args=p.parse_args()
    svg=render(args.support,args.lattice)
    process=subprocess.run(["rsvg-convert","--format","pdf"],input=svg,capture_output=True,timeout=30,check=True,
                           env={**os.environ,"SOURCE_DATE_EPOCH":"1795651200","TZ":"UTC","LC_ALL":"C"})
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/"force-copy-atoms.svg").write_bytes(svg)
    (args.output/"force-copy-atoms.pdf").write_bytes(process.stdout)


if __name__=="__main__":
    main()
