"""Draw both conditional gains and the corresponding known-table modal comparison."""
from argparse import ArgumentParser
from fractions import Fraction
import json
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
LAPIS,TURQUOISE,INK,MINERAL,IVORY,POMEGRANATE = "#1F3F60","#1F6968","#2C3E50","#D2E0E2","#F7F3E9","#743E37"

def graphic(report):
    tasks=report["tasks"]
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="840" height="440" viewBox="0 0 840 440" role="img" aria-labelledby="title desc">',
           '<title id="title">Information and correct class choices after detection</title>',
           '<desc id="desc">For LP1 through LP5, two conditional information gains are plotted on one scale in millinats. Both are positive in every task. Exact correct counts for the better single sign and both signs are 38 and 42 of 88, 21 and 22 of 47, 24 and 24 of 47, 72 and 72 of 117, and 49 and 52 of 164. These are same-table decisions.</desc>',
           f'<rect width="840" height="440" fill="{IVORY}"/>',
           '<g font-family="Source Sans Pro, Source Sans 3, Arial, sans-serif">']
    def label(x,y,text,size=19,fill=INK,bold=False,anchor="start"):
        parts.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" fill="{fill}" font-weight="{600 if bold else 400}">{escape(str(text))}</text>')
    def line(x,y,x2,y2,fill=MINERAL,width=1):
        parts.append(f'<line x1="{x}" y1="{y}" x2="{x2}" y2="{y2}" stroke="{fill}" stroke-width="{width}"/>')
    def circle(x,y):
        parts.append(f'<circle cx="{x:.2f}" cy="{y}" r="4" stroke="{TURQUOISE}" fill="{IVORY}" stroke-width="2.4"/>')
    def diamond(x,y):
        parts.append(f'<path d="M{x:.2f} {y-5} l5 5 l-5 5 l-5 -5 z" fill="{POMEGRANATE}"/>')
    def position(v):
        return 97+float(v)*1.65
    def value(task,key):
        v=task["nanonat_intervals"][key]
        lo,hi=v["lower_nanonats"],v["upper_nanonats"]
        low,high=(lo+50000)//100000,(hi+50000)//100000
        if v["sign"]!=1 or low!=high:
            raise ValueError("display requires unambiguous one-decimal millinat rounding")
        return Fraction(lo+hi,2000000),f"{low//10}.{low%10}"
    label(31,42,"Information and correct class choices after detection",31,LAPIS,True)
    label(32,70,"Five robot tasks. Each direction uses the same 15 readings of an axial channel.",20)
    line(32,85,808,85)
    label(32,115,"Added class information",23,TURQUOISE,True)
    label(548,115,"Correct class choices",23,TURQUOISE,True)
    circle(39,141);label(52,147,"Torque given force",17)
    diamond(227,141);label(241,147,"Force given torque",17)
    label(548,146,"Best single sign and both signs",17)
    label(32,180,"Task",16,LAPIS,True)
    label(410,180,"Torque",16,LAPIS,True,"middle")
    label(477,180,"Force",16,LAPIS,True,"middle")
    for x,k in ((591,"Single"),(679,"Both"),(770,"Episodes")):label(x,180,k,16,LAPIS,True,"middle")
    for tick in (0,40,80,120,160):
        x=position(tick);line(x,186,x,333,MINERAL,1)
        label(f"{x:.2f}",179,tick,14,INK,False,"middle")
    for i,task in enumerate(tasks):
        y=205+i*30
        label(32,y+6,task["id"],19,LAPIS,True)
        torque,ts=value(task,"cmi_q_given_f");force,fs=value(task,"cmi_f_given_q")
        a,b=position(torque),position(force)
        line(f"{min(a,b):.2f}",y,f"{max(a,b):.2f}",y,INK,1.4)
        circle(a,y);diamond(b,y)
        label(410,y+6,ts,19,TURQUOISE,True,"middle")
        label(477,y+6,fs,19,POMEGRANATE,True,"middle")
        counts=task["modal_correct"]
        for x,num in ((591,max(counts[1:3])),(679,counts[3]),(770,task["n"])):
            label(x,y+6,num,19,INK,False,"middle")
    line(520,157,520,337)
    line(32,347,808,347)
    label(32,375,"Information is in millinats. 1,000 millinats equal one nat.",19)
    label(32,402,"LP4 retains positive gains in both directions. Each modal rule gets 72 of 117 correct.",19,LAPIS,True)
    label(32,427,"Classes and frequencies come from the same recorded task. UCI Robot Execution Failures.",17)
    return "\n".join([*parts,"</g>","</svg>",""])

if __name__=="__main__":
    p=ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    args.output.write_text(graphic(json.loads((HERE.parent/"results.json").read_bytes())),encoding="utf-8")
