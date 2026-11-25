"""Draw the two angular decisions from the stated rational inputs."""
from pathlib import Path
from fractions import Fraction as F
import argparse
from xml.sax.saxutils import escape

INK,BLUE,TEAL,RED,GOLD,LIGHT="#2C3E50","#1F3F60","#1F6968","#743E37","#916400","#D2E0E2"

def build():
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="365" viewBox="0 0 960 365" role="img" aria-labelledby="title description">',
         '<title id="title">Two distinct amplitude thresholds for four moments</title>',
         '<desc id="description">The first threshold is about 0.292039. Below it every direction passes. The second threshold is about 0.340315. At and above it no direction passes. In between, the direction changes the decision. At one millionth relative error equality fails the strict test.</desc>',
         '<rect width="960" height="365" fill="white"/><g font-family="DejaVu Sans, sans-serif">']
    def line(a,y,b,z,col=LIGHT,width=2,dash=None):
        attr=f' stroke-dasharray="{dash}"' if dash else ''
        out.append(f'<path d="M{a} {y} L{b} {z}" stroke="{col}" stroke-width="{width}" fill="none"{attr}/>')
    def label(x,y,t,size=18,col=INK,align="start",bold=False):
        wt='bold' if bold else 'normal'
        out.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{wt}" fill="{col}" text-anchor="{align}">{escape(t)}</text>')
    def circle(x,y,c,filled):
        fill=c if filled else 'white'
        out.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{fill}" stroke="{c}" stroke-width="2.2"/>')
    def x(t):
        return round(302+600*float((F(t)-F(28,100))/F(7,100)),4)
    alpha=x('0.2920386087761345'); rho=x('0.3403151687255')
    label(38,42,'Four even joint moments at a fixed common radian scale',25,BLUE,bold=True)
    label(38,73,'A direction passes if the relative error is strictly below one part per million.',17)
    line(38,91,920,91)
    for y,yname in [(135,'Every direction passes'),(184,'Some pass, some fail'),(233,'No direction passes')]:
        label(43,y+5,yname,18,INK,bold=True)
    line(x('.28'),135,alpha,135,TEAL,4);circle(alpha,135,TEAL,False)
    line(alpha,184,rho,184,GOLD,4);circle(alpha,184,GOLD,True);circle(rho,184,GOLD,False)
    line(rho,233,x('.35'),233,RED,4);circle(rho,233,RED,True)
    for v in (alpha,rho):line(v,104,v,252,LIGHT,1.5,'3 5')
    line(x('.28'),259,x('.35'),259,INK,2)
    for t in range(28,36):
        v=x(F(t,100));line(v,259,v,266,INK);label(v,287,format(t/100,'.2f'),15,align='middle')
    label(610,315,'Sum of the two absolute amplitudes',17,BLUE,'middle',True)
    label(43,347,'Open circle excludes equality. Filled circle includes the endpoint shown.',16)
    out.extend(['</g>','</svg>'])
    return '\n'.join(out)+'\n'


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.write_text(build(),encoding='utf-8')
