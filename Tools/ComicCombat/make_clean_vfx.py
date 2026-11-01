"""Original, code-authored vector silhouettes rendered into deterministic flipbooks.
No extracted commercial game assets. Each frame changes shape, not just alpha.
"""
from PIL import Image,ImageDraw
from pathlib import Path
import math,json
OUT=Path(__file__).resolve().parent/'CleanSheets';OUT.mkdir(exist_ok=True)
S=256;SS=2
PURPLE=(155,90,232,255);CREAM=(238,255,164,255)
def poly(d,pts,color):d.polygon([(int(x*S*SS),int(y*S*SS)) for x,y in pts],fill=color)
def point(a,r,c=(.5,.5)):return (c[0]+math.cos(a)*r,c[1]+math.sin(a)*r)
def frame(kind,i,n):
 im=Image.new('RGBA',(S*SS,S*SS));d=ImageDraw.Draw(im);p=i/(n-1)
 if i==n-1:return im.resize((S,S),Image.Resampling.LANCZOS)
 expand=1-math.exp(-p*12);tail=max(0,(p-.3)/.7);fade=1-tail
 if kind=='impact':
  # Six asymmetric wedges. Late frames open the centre into a broken ring.
  for j,a in enumerate([-.35,.62,1.6,2.25,3.35,4.62]):
   length=(.35+.07*math.sin(j*3.7))*expand
   r0=min(.015+.28*tail,length*.86);mid=(r0+length)*.54
   width=.24*fade
   pts=[point(a-width,r0),point(a-width*.85,mid),point(a,length),point(a+width*.8,mid),point(a+width,r0)]
   poly(d,pts,PURPLE)
   if p<.42:poly(d,[point(a-.11,r0),point(a,length*.78),point(a+.10,r0)],CREAM)
  if p<.28:
   poly(d,[point(j*math.pi/4,.08*expand if j%2 else .20*expand) for j in range(8)],(255,255,237,255))
 elif kind=='shock':
  # Broken elliptical shock ring, with three pointed expansions and empty core.
  r=(.12+.32*expand);width=.048*fade
  for j in range(3):
   a0=j*2.094+.20+p*.24;a1=a0+1.4*(1-tail*.7)
   pts=[]
   for k in range(24):
    a=a0+(a1-a0)*k/23;rr=r+(.10*fade if k==17 else 0)
    x,y=point(a,rr);pts.append((x,.5+(y-.5)*.74))
   for k in range(23,-1,-1):
    a=a0+(a1-a0)*k/23;x,y=point(a,r-width);pts.append((x,.5+(y-.5)*.74))
   poly(d,pts,PURPLE)
 elif kind=='electric':
  for j in range(2):
   x=.25+j*.35;off=.035*math.sin(i*2+j)
   pts=[(x-.06,.85),(x+.08+off,.52),(x-.02,.53),(x+.12,.15),(x+.03,.47),(x+.15+off,.43)]
   c=(.5,.5);scale=.8+.2*expand
   if p>.5:pts=[(x+(a-x)*fade*1.8,b) for a,b in pts]
   poly(d,pts,CREAM if j else PURPLE)
 elif kind=='ground':
  for j in range(3):
   y=.30+j*.20;length=(.68-j*.13)*expand;th=.065*fade
   poly(d,[(.1,y),(.1+length,y-.08-j*.018),(.1+length*.65,y),(.1+length*.94,y+th),(.1+length*.3,y+th)],PURPLE if j else CREAM)
 elif kind=='smoke':
  # Three detached angular puffs, almost neutral; no multicolour confetti.
  for j in range(3):
   c=(.28+j*.22,.64-p*.24+(.03 if j%2 else -.03));r=(.06+.11*expand)*fade
   pts=[point(k*math.pi/4,r*(1+.13*math.sin(k*2+j)),c) for k in range(8)]
   poly(d,pts,(165,174,185,255))
 return im.resize((S,S),Image.Resampling.LANCZOS)
manifest={}
for kind,n in [('impact',16),('shock',12),('electric',8),('ground',8),('smoke',12)]:
 atlas=Image.new('RGBA',(S*4,S*(n//4)))
 for i in range(n):atlas.paste(frame(kind,i,n),(i%4*S,i//4*S))
 atlas.save(OUT/('T_Clean_'+kind+'.png'));manifest[kind]={'frames':n,'columns':4,'rows':n//4}
 # Neutral checker-free presentation for easy shape review.
 preview=Image.new('RGB',atlas.size,(41,39,47));preview.paste(atlas,mask=atlas.getchannel('A'));preview.save(OUT/('preview_'+kind+'.png'))
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
print('CLEAN_VFX_GENERATED',OUT)
