"""Draw nested source partitions and the exact lower product at each integer total."""
import argparse
from fractions import Fraction
from pathlib import Path
from xml.etree.ElementTree import Element,SubElement,ElementTree,indent

def draw(path):
    ns='http://www.w3.org/2000/svg'
    svg=Element('svg',xmlns=ns,width='960',height='415',viewBox='0 0 960 415',role='img',attrib={'aria-labelledby':'title desc'})
    SubElement(svg,'title',id='title').text='Nested source partitions and the smallest non-unit directed product'
    SubElement(svg,'desc',id='desc').text=('Left: successively record the first one, two and three bits of an eight-state value. '
        'The three keys that can carry nonzero atoms are 01+02+04, 02+04 and 04. Right: for each integer sample total from two through twelve, '
        'circles show the minimum possible product at a failed fine-to-coarse map for unrestricted finite alphabets; '
        'squares show the minimum with at most two fine labels. Each observation contributes its union-match count '
        'divided by its coarse-match count. A product of one means the map exists.')
    lapis='#1F3F60';teal='#1F6968';ink='#2C3E50';pale='#D2E0E2';red='#743E37'
    def rectangle(x,y,w,h,fill,stroke='none'):
        SubElement(svg,'rect',x=str(x),y=str(y),width=str(w),height=str(h),fill=fill,stroke=stroke)
    def line(x1,y1,x2,y2,col,width=1,dash=''):
        attr=dict(x1=str(x1),y1=str(y1),x2=str(x2),y2=str(y2),stroke=col)
        attr['stroke-width']=str(width)
        if dash:attr['stroke-dasharray']=dash
        SubElement(svg,'line',attr)
    def label(x,y,txt,size=17,color=ink,weight=400,anchor='start'):
        SubElement(svg,'text',x=str(x),y=str(y),fill=color,attrib={'font-family':'Source Sans Pro, sans-serif','font-weight':str(weight),'font-size':str(size),'text-anchor':anchor}).text=txt
    rectangle(0,0,960,415,'#FFFFFF');line(480,25,480,383,pale,1.5)
    label(20,40,'Three nested readings',24,lapis,600);label(20,68,'Eight possible finest readings, grouped by bit prefix',16)
    start=100;span=338
    for j in (1,2,3):
        cells=2**j;y=100+(j-1)*82;width=span/cells
        label(18,y+22,('Coarse','Middle','Fine')[j-1],16,ink,600)
        for i in range(cells):
            rectangle(start+i*width,y,width,32,'#F7F3E9' if i%2==0 else '#FFFFFF',lapis)
            label(start+(i+.5)*width,y+22,format(i,'0'+str(j)+'b'),15,ink,400,'middle')
        mask=('01+02+04','02+04','04')[j-1]
        label(start,y+53,'Possible nonzero atom at key '+mask,15,teal)
    label(20,359,'The other 15 nodes have zero in all three atom components.',15,ink)
    label(20,386,'Key masks name sources. 01 is coarse, 02 middle and 04 fine.',15,ink)
    label(505,40,'Smallest positive departure',24,lapis,600)
    label(505,67,'Minimum directed product G at a failed map',16)
    label(505,89,'At N = 4 the circle gives 9/4 and the square gives 8/3.',14)
    def xp(n):return 569+(n-2)*33
    def yp(v):return float(317-(v-1)*70)
    for y in range(1,5):
        line(562,yp(y),910,yp(y),pale)
        label(549,yp(y)+5,str(y),15,ink,400,'end')
    line(562,93,562,319,ink);line(562,319,910,319,ink)
    for n in range(2,13):
        value=Fraction(2*n,n-1)
        rectangle(xp(n)-5.6,round(yp(value)-5.6,3),11.2,11.2,'#FFFFFF',lapis)
    for n in range(2,13):
        a,b=n//2,n-n//2;v=Fraction((a+1)*(b+1),a*b)
        SubElement(svg,'circle',cx=str(xp(n)),cy=f'{yp(v):.3f}',r='5',fill=red)
        if n%2==0:label(xp(n),342,str(n),15,ink,400,'middle')
    line(562,317,909,317,teal,2,'6,4')
    label(740,365,'Total number of observations',16,ink,400,'middle')
    SubElement(svg,'circle',cx='518',cy='383',r='5',fill=red)
    label(530,388,'Any finite alphabets',15,ink)
    rectangle(692,377.5,11,11,'#FFFFFF',lapis)
    label(710,388,'At most two fine labels',15,ink)
    line(512,403,536,403,teal,2,'6,4');label(545,408,'Unit product for a valid map',15,ink)
    indent(svg)
    with path.open('wb') as f:ElementTree(svg).write(f,encoding='utf-8',xml_declaration=True);f.write(b'\n')
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);draw(parser.parse_args().output)
