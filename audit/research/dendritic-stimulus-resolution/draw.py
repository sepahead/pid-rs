"""Draw labelled scientific SVGs directly from the checked data and results."""
import argparse
from fractions import Fraction
from hashlib import sha256
import json
import math
import os
import subprocess
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
INK, LAPIS, TEAL, MINERAL = "#2C3E50", "#1F3F60", "#1F6968", "#D2E0E2"
IVORY, BRONZE, SAFFRON, RED = "#F7F3E9", "#916400", "#B28218", "#743E37"
GREY = "#596A73"
class Plate:
    def __init__(self,height,title,desc):
        self.h=height
        self.parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="512pt" height="{height}pt" viewBox="0 0 512 {height}" role="img" aria-labelledby="title desc">',
          f'<title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc>',
          '<g font-family="Source Sans Pro, Arial, sans-serif">']
        self.rect(0,0,512,height,"#FFFFFF")
        self.rect(14,10,2.5,8,SAFFRON)
        self.text(22,17,title,8.1,BRONZE,bold=True)
    def rect(self,x,y,w,h,fill,stroke="none",sw=.55):
        self.parts.append(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    def line(self,x,y,xx,yy,color=MINERAL,w=.65,dash=""):
        dotted=f' stroke-dasharray="{dash}"' if dash else ''
        self.parts.append(f'<line x1="{x:g}" y1="{y:g}" x2="{xx:g}" y2="{yy:g}" stroke="{color}" stroke-width="{w}"{dotted}/>')
    def text(self,x,y,s,size=8,fill=INK,anchor="start",bold=False):
        attrs=' font-weight="700"' if bold else ''
        self.parts.append(f'<text x="{x:g}" y="{y:g}" font-size="{size}" text-anchor="{anchor}" fill="{fill}"{attrs}>{escape(str(s))}</text>')
    def dot(self,x,y,r,fill):
        self.parts.append(f'<circle cx="{x:g}" cy="{y:g}" r="{r:g}" fill="{fill}"/>')
    def diamond(self,x,y,r):
        self.parts.append(f'<path d="M {x-r:g},{y:g} L {x:g},{y-r:g} L {x+r:g},{y:g} L {x:g},{y+r:g} Z" fill="white" stroke="{LAPIS}" stroke-width="1.1"/>')
    def flush(self,dest):
        dest.write_text("\n".join(self.parts+["</g></svg>"])+"\n",encoding="utf-8")

def draw_settings(raw,folder):
    observed=[[int(Fraction(v)) for v in s.split()] for s in raw.decode("ascii").splitlines()]
    if len(observed)!=31 or any(len(row)!=21 or any(n<0 or n>4 for n in row) for row in observed):raise ValueError("input")
    p=Plate(265,"WHAT THE NEURON MODEL RECORDED",
         "Every square is one published input setting. Basal input varies horizontally and tuft input vertically. The symbols show three spike-count classes. The new bit depends only on the two input settings.")
    p.text(18,37,"Spike counts at 651 input settings",13,LAPIS,bold=True)
    p.text(18,51,"Tuft input setting",8.7,GREY)
    l,top,d=42,60,7.35
    fills=["#FFFFFF","#C6DDDB",LAPIS]
    for i,r in enumerate(observed):
        for j,n in enumerate(r):
            x,y=l+d*i,top+d*(20-j)
            k=0 if n==0 else 1 if n<=2 else 2
            p.rect(x,y,d-.18,d-.18,fills[k],"#AFBEC2",.24)
            if k==1:p.dot(x+d/2,y+d/2,.92,TEAL)
    for v in (0,100,200,300):
        x=l+d*(v/10+.5)
        p.line(x,top+21*d,x,top+21*d+2.5,INK)
        p.text(x,top+21*d+11,v,7.8,anchor="middle")
    for v in (0,100,200):
        y=top+d*(20-v/10+.5)
        p.line(l-2.5,y,l,y,INK)
        p.text(l-5,y+2.4,v,7.8,anchor="end")
    for j in (10,20,30):
        x=l+d*j
        p.line(x,top,x,top+21*d,"#8A7344",.78,"2 2")
    for j in (10,20):
        y=top+d*(21-j)
        p.line(l,y,l+31*d,y,"#8A7344",.78,"2 2")
    p.text(l+15.5*d,top+21*d+23,"Basal input setting",9,LAPIS,anchor="middle",bold=True)
    p.line(288,57,288,234,MINERAL)
    p.text(301,70,"One setting, one stored output",10.8,LAPIS,bold=True)
    for k,text in enumerate(("Zero spikes  ·  163 settings","One or two spikes  ·  192 settings","Three or four spikes  ·  296 settings")):
        y=83+18*k
        p.rect(302,y,10,10,fills[k],GREY,.6)
        if k==1:p.dot(307,y+5,1.2,TEAL)
        p.text(319,y+8,text,8.8)
    p.text(301,155,"What the extra bit records",10.8,LAPIS,bold=True)
    p.text(301,171,"1 when the basal setting exceeds the tuft setting.",8.4)
    p.text(301,185,"0 when it is smaller or equal.",8.4)
    p.text(301,207,"Dashed lines separate the 100-count ranges.",8.4)
    p.text(301,221,"Some pairs of ranges contain both bit values.",8.4)
    p.line(15,246,497,246,MINERAL)
    p.text(15,258,"Shai et al. (2015), ModelDB 180373  ·  control simulation  ·  each nominal input setting receives weight 1/651",7.45,GREY)
    p.flush(folder/"stimulus-settings.svg")

def draw_atoms(brief,folder):
    q=brief["widths"]["100"]
    p=Plate(248,"WHAT THE EXTRA BIT CONTRIBUTES",
           "Five signed Makkeh–Gutknecht–Wibral categorical shared-exclusions contributions at the 100-count recording width. The flag-alone term is negative. Four positive terms offset it. The Williams–Beer comparison places the whole gain at the three-input position.")
    p.text(15,37,"The same total can have different contributions",14,LAPIS,bold=True)
    p.text(15,52,"Width 100 in nominal input counts. The bit records basal > tuft. Values are nats per setting.",9)
    left,right,lo,hi=180,355,-.065,.045
    xp=lambda v:left+(v-lo)*(right-left)/(hi-lo)
    zero=xp(0)
    p.text(15,73,"Source rule for the atom",8.5,TEAL,bold=True)
    p.text(408,73,"MGW",8.5,TEAL,"end",True)
    p.text(493,73,"Williams–Beer",8.5,TEAL,"end",True)
    for v in (-.06,-.03,0,.03):
        x=xp(v);p.line(x,79,x,181,INK if not v else MINERAL,1 if not v else .55)
        p.text(x,193,f"{v:.2f}" if v else "0",7.4,GREY,"middle")
    rows=[("04","Flag alone"),("05","Basal with flag"),("06","Tuft with flag"),("05+06","Shared by the two input–flag pairs"),("07","All three together")]
    for j,(key,label) in enumerate(rows):
        y=90+j*20
        v=q["signed_five"][key];other=q["imin_five"][key]
        p.text(15,y+2,label,9.1,LAPIS,bold=(j==0))
        p.rect(min(zero,xp(v)),y-4,abs(xp(v)-zero),6,RED if v<0 else TEAL)
        p.diamond(xp(other),y+4,2.6)
        p.text(408,y+2,f"{v:+.5f}",8.7,RED if v<0 else INK,"end")
        p.text(493,y+2,"0 (exact)" if other==0 else f"{other:+.5f}",8.7,INK,"end")
    p.rect(16,204,17,5,TEAL);p.text(38,210,"Bar: Makkeh–Gutknecht–Wibral (MGW)",8.2)
    p.diamond(245,207,3);p.text(253,210,"Diamond: minimum specific information (Williams–Beer)",8.2)
    p.line(15,221,497,221,MINERAL)
    p.text(15,237,"Sum under either method: +0.01155 nats. Best three-class decisions with or without the bit: 486 of 651 correct.",8.7,LAPIS,bold=True)
    p.flush(folder/"five-contributions.svg")

def draw_scores(brief,folder):
    p=Plate(204,"HELD-LEVEL FORECAST SCORES",
        "Gains in mean held-out logarithmic loss have different signs at widths 50 and 100. Positive values favour using the flag. At width 10 both fitted predictors use a uniform fallback on the held-out settings.")
    p.text(15,38,"Withhold one complete input level at a time",14,LAPIS,bold=True)
    p.text(15,54,"Widths count nominal stimulus inputs. Forecasts add one training count per spike class.",9)
    labels=[("10","basal"),("10","tuft"),("50","basal"),("50","tuft"),("100","basal"),("100","tuft")]
    left,right=173,375;xp=lambda v: left+(v+.014)*(right-left)/.017
    for v in (-.012,-.008,-.004,0,.002):
        p.line(xp(v),70,xp(v),158,INK if v==0 else MINERAL,1 if v==0 else .6)
        p.text(xp(v),170,"0" if not v else f"{v:+.3f}",7.3,GREY,"middle")
    p.text(15,70,"Width  ·  omitted level",8,TEAL,bold=True)
    p.text(490,70,"Gain (nats)",8,TEAL,"end",True)
    for j,(w,axis) in enumerate(labels):
        h=brief["widths"][w]["held_levels"][axis]
        v=h["3"]["mean_log_loss"]-h["6"]["mean_log_loss"]
        y=82+j*14
        p.text(16,y+2,f"{w}  ·  {axis}",8.7)
        if v==0:p.dot(xp(v),y,2.1,INK)
        else:p.rect(min(xp(v),xp(0)),y-2.4,abs(xp(v)-xp(0)),4.8,TEAL if v>0 else RED)
        p.text(490,y+2,"0" if v==0 else f"{v:+.5f}",8.6,INK,"end")
    p.line(15,181,497,181,MINERAL)
    p.text(15,195,"Gain = mean loss without the bit minus mean loss with it. Positive values favour recording the bit for this task.",8.4,LAPIS)
    p.flush(folder/"prediction-gain.svg")

def main():
    ap=argparse.ArgumentParser();ap.add_argument("data",type=Path);ap.add_argument("out",type=Path);ap.add_argument("--pdf",action="store_true",help="also render the three vector PDF figures with rsvg-convert");ap.add_argument("--assets-root",type=Path,default=HERE.parents[2],help="repository with the shared Source Sans fonts");args=ap.parse_args()
    raw=args.data.read_bytes()
    if sha256(raw).hexdigest()!="718e40b0509f077d8d667187c22d3fe7df7746f5489dc40bd983742a4bcbb467":raise ValueError("control data")
    summary=HERE/"results.json"
    if sha256(summary.read_bytes()).hexdigest()!="274bbc92cb6662b8a033f896566eac3f0e2688b6739be494402165bea699f1d9":raise ValueError("analysis return")
    args.out.mkdir(parents=True,exist_ok=True)
    brief=json.loads(summary.read_bytes())
    draw_settings(raw,args.out);draw_atoms(brief,args.out);draw_scores(brief,args.out)
    if args.pdf:
        fonts = (args.assets_root/"audit/formal/latex/source-coupling-compression/fonts").resolve()
        if not all((fonts/name).is_file() for name in ("SourceSansPro-Regular.otf","SourceSansPro-Semibold.otf")):
            raise ValueError("missing repository fonts")
        with tempfile.TemporaryDirectory(prefix="stimulus-figure-fonts-") as temp:
            conf = Path(temp)/"fonts.conf"
            conf.write_text("<fontconfig><dir>" + escape(str(fonts)) + "</dir><cachedir>"
                            + escape(str(Path(temp)/"cache")) + "</cachedir></fontconfig>\n")
            env = dict(os.environ,SOURCE_DATE_EPOCH="1795651200",LC_ALL="C",TZ="UTC",
                       FONTCONFIG_FILE=str(conf),PANGOCAIRO_BACKEND="fc")
            for name in ("stimulus-settings","five-contributions","prediction-gain"):
                subprocess.run(["rsvg-convert","--format","pdf","--output",
                                str(args.out/(name+".pdf")),str(args.out/(name+".svg"))],
                               check=True,env=env)
if __name__=="__main__":main()
