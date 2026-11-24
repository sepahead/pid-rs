"""Draw two fixed parameter sweeps from bounded rational moment evaluations."""
import argparse
from fractions import Fraction as Q
from math import comb
from pathlib import Path
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
INK="#2C3E50"; LAPIS="#1F3F60"; TEAL="#1F6968"; BRONZE="#916400"
MINERAL="#D2E0E2"; PAPER="#FFFFFF"; RED="#743E37"
N=20

def require(ok, message):
    if not ok:raise ValueError(message)

def joint(a,b):
    r=abs(a)+abs(b)
    require(Q(0)<r<1,"positive density")
    x,y=abs(a)/r,abs(b)/r
    atom=tail=Q(0)
    for j in range(1,N+1):
        k=Q(comb(2*j,j),4**j*2*j*(2*j-1))
        h=2*(2*j+1)*Q(1,4)**j-(j+1)*Q(4,9)**j
        mass=sum((comb(j,i)*x**i*y**(j-i))**2 for i in range(j+1))
        power=k*r**(2*j)
        atom+=power*(mass-(1-h)*x**(2*j))
        if j>4:tail+=power*mass
    j=N+1
    k=Q(comb(2*j,j),4**j*2*j*(2*j-1))
    e=k*r**(2*j)/(1-r*r)
    return (atom-3*e,atom+3*e),(tail,tail+e)

def divide(pos,den):
    require(den[0]>0 and pos[0]>0,"positive plotted interval")
    return pos[0]/den[1],pos[1]/den[0]

def samples():
    radius=Q(3,10)
    ax,tx=joint(radius,0)
    ex=divide(tx,ax)
    left=[];right=[];widths=[]
    def centre(iv):
        widths.append(iv[1]-iv[0])
        return (iv[0]+iv[1])/2
    for i in range(51):
        x=Q(i,50)
        atom,tail=joint(radius*x,radius*(1-x))
        left.append((x,centre(divide(tail,tx)),centre(divide(divide(tail,atom),ex))))
    for i in range(61):
        r=Q(1,5)+Q(i,400)
        atom,tail=joint(r,0)
        e=divide(tail,atom)
        right.append((r,centre((10**6*e[0],10**6*e[1]))))
    require(max(widths)<Q(1,10**10),"interval widths before plot rounding")
    return left,right

def svg():
    root=ET.Element("svg",{"xmlns":"http://www.w3.org/2000/svg","width":"900","height":"465","viewBox":"0 0 900 465","role":"img","aria-labelledby":"title desc"})
    ET.SubElement(root,"title",id="title").text="Direction and radius of four-moment truncation error"
    ET.SubElement(root,"desc",id="desc").text="Both panels retain four even moments. At fixed radius 0.30 both pure harmonics maximize absolute error; only the first maximizes relative error. On the first-harmonic axis, relative error crosses one part per million at radius 0.292038608776134 to 0.292038608776135."
    def point(n):return f"{float(n):.3f}"
    def line(x,y,X,Y,col,width=1,dash=None):
        a={"x1":point(x),"y1":point(y),"x2":point(X),"y2":point(Y),"stroke":col,"stroke-width":str(width)}
        if dash:a["stroke-dasharray"]=dash
        ET.SubElement(root,"line",a)
    def label(x,y,s,size=16,anchor="start",col=INK,bold=False):
        ET.SubElement(root,"text",{"x":point(x),"y":point(y),"font-family":"Source Sans Pro, sans-serif","font-size":str(size),
         "font-weight":"600" if bold else "400","text-anchor":anchor,"fill":col}).text=s
    def dot(x,y,r,col,fill):
        ET.SubElement(root,"circle",{"cx":point(x),"cy":point(y),"r":str(r),"stroke":col,"fill":fill,"stroke-width":"1.6"})
    def curve(points,col,dash=None):
        a={"points":" ".join(point(x)+","+point(y) for x,y in points),"stroke":col,"stroke-width":"2.8","fill":"none","stroke-linejoin":"round"}
        if dash:a["stroke-dasharray"]=dash
        ET.SubElement(root,"polyline",a)
    ET.SubElement(root,"rect",{"width":"900","height":"465","fill":PAPER})
    left,right=samples()
    label(22,28,"Mix the two harmonics",22,col=LAPIS,bold=True)
    label(478,28,"Increase the radius",22,col=LAPIS,bold=True)
    label(22,56,"Four even moments, radius 0.30",17,col=TEAL)
    label(478,56,"Four even moments, first harmonic alone",17,col=TEAL)
    label(22,88,"Fraction of the largest error",16)
    label(478,88,"Relative error in parts per million",16)
    ytop,ybottom=109,310
    def Y(v,maxvalue):return ybottom-(ybottom-ytop)*v/maxvalue
    def X(v,x0,x1,lo,hi):return x0+(v-lo)*(x1-x0)/(hi-lo)
    for x0,x1,yvalues,maximum in [(73,419,[Q(i,4) for i in range(5)],1),(530,873,list(range(6)),5)]:
        for v in yvalues:
            y=Y(v,maximum)
            line(x0,y,x1,y,MINERAL)
            s=f"{float(v):.2f}".rstrip("0").rstrip(".") if v else "0"
            label(x0-9,y+5,s,15,"end")
        line(x0,ytop,x0,ybottom,INK,1.3);line(x0,ybottom,x1,ybottom,INK,1.3)
    for v,s in [(Q(0),"0"),(Q(1,4),"0.25"),(Q(1,2),"0.50"),(Q(3,4),"0.75"),(Q(1),"1")]:
        x=X(v,73,419,0,1);line(x,310,x,316,INK);label(x,337,s,15,"middle")
    for v in [Q(1,5),Q(1,4),Q(3,10),Q(7,20)]:
        x=X(v,530,873,Q(1,5),Q(7,20));line(x,310,x,316,INK);label(x,337,f"{float(v):.2f}",15,"middle")
    label(246,366,"Share of amplitude in the first harmonic",17,"middle")
    label(700,366,"Amplitude radius",17,"middle")
    for idx,col,dash in [(1,BRONZE,"8,5"),(2,TEAL,None)]:
        pts=[(X(cell[0],73,419,0,1),Y(cell[idx],1)) for cell in left]
        require(all(ytop-0.01<=float(y)<=ybottom+0.01 for _,y in pts),"first panel in range")
        curve(pts,col,dash)
        for x,y in pts[::10]:dot(x,y,4 if idx==1 else 2.6,col,PAPER if idx==1 else col)
    pts=[(X(r,530,873,Q(1,5),Q(7,20)),Y(v,5)) for r,v in right]
    require(all(ytop<=float(y)<=ybottom for _,y in pts),"second panel in range")
    curve(pts,TEAL)
    for x,y in pts[::10]:dot(x,y,2.7,TEAL,TEAL)
    root_low=Q(292038608776134,10**15)
    rx=X(root_low,530,873,Q(1,5),Q(7,20));ry=Y(1,5)
    line(530,ry,873,ry,RED,1.3,"4,4");line(rx,ry,rx,310,RED,1.3,"4,4");dot(rx,ry,4,RED,PAPER)
    line(22,399,65,399,BRONZE,2.5,"8,5");dot(44,399,4,BRONZE,PAPER);label(76,405,"Absolute error",17)
    line(218,399,262,399,TEAL,2.5);dot(240,399,2.6,TEAL,TEAL);label(273,405,"Relative error",17)
    line(481,399,518,399,RED,1.3,"4,4");dot(499,399,4,RED,PAPER);label(532,405,"One part per million",17)
    label(22,443,"Two separate maxima set the scales in the left panel.",15,col=LAPIS)
    label(478,443,"Crossing radius 0.292038608776134 to 0.292038608776135",15,col=LAPIS)
    ET.indent(root)
    return ET.tostring(root,encoding="utf-8",xml_declaration=True)+b"\n"

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args();args.output.write_bytes(svg())
