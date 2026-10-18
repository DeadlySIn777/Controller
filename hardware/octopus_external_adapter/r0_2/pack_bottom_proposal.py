from pathlib import Path
import json, math, random, time
import numpy as np

ROOT=Path(__file__).resolve().parent
geo=json.loads((ROOT/'bottom-geometry.json').read_text())
layout=json.loads((ROOT/'placement.json').read_text())['parts']
extra={'R3','R4','R5','R22','C21'}
refs=[n for n,v in layout.items() if n not in ('J1','J2') and (v[3]=='bottom' or n in extra)]
preferred={
'Q1':[10.4,3.3,0],'R8':[10.4,1.3,0],'R11':[10.4,5.3,0],
'Q2':[10.4,8.8,0],'R9':[10.4,6.8,0],'R12':[10.4,10.8,0],
'Q3':[10.4,14.3,0],'R10':[10.4,12.3,0],'R13':[10.4,16.3,0],
'D1':[4.7,3.2,90],'R15':[4.7,7.3,90],'R3':[4.7,10,0],
'U1':[5.2,14.85,90],'C1':[4.7,11.7,0],'R4':[7.6,13,90],
'R5':[7.6,16.3,90],'R1':[5.2,18,0],'R2':[7.6,19.6,90],
'U2':[5.2,22.1,0],'C2':[5.2,24.1,0],'U3':[10,19.7,0],
'C3':[10,22.3,0],'U21':[10.3,29.75,0],'C25':[13.8,30,90],
'C26':[10.1,33,0],'R23':[7.0,30,90],'R24':[7.0,33.6,90],
'R25':[7.4,35.5,0],'D21':[1.8,23.5,90],'F20':[10.9,36,0],
'R20':[7.1,35.5,0],'R21':[4.7,19.7,0],'R22':[4.7,21.3,0],
'R6':[2,22.8,90],'R7':[2,25.2,90],'R14':[7.5,22,90],
'C21':[8.8,18.1,180]}

def bbox(ref,x,y,ang,flip=False):
    b=geo[ref]['courtyard'];pts=[]
    for xx,yy in [(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])]:
        if flip:xx=-xx
        a=math.radians(ang);pts.append((x+xx*math.cos(a)+yy*math.sin(a),y-xx*math.sin(a)+yy*math.cos(a)))
    return [min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts)]

obs=[bbox('J1',1.27,1.27,0,True),bbox('J2',13.97,3.81,0,True)]
for ref,x,y,ang in [('J3',7.3,3.1,-90),('J4',2.5,33.1,0),('SW1',7.62,26.5,0)]:
 for pad in geo[ref]['pads']:
  if pad['drill']<=0:continue
  b=pad['box'];pts=[]
  for xx,yy in [(b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3])]:
   a=math.radians(ang);pts.append((x+xx*math.cos(a)+yy*math.sin(a),y-xx*math.sin(a)+yy*math.cos(a)))
  obs.append([min(p[0] for p in pts)-.15,min(p[1] for p in pts)-.15,max(p[0] for p in pts)+.15,max(p[1] for p in pts)+.15])
obs=np.array(obs)
viaobs=np.array([[7.25,16.40,8.15,17.30],[9.75,16.55,10.65,17.45]])
cent=np.array([preferred[n][:2] for n in refs],float);angles=np.array([preferred[n][2] for n in refs])
sizes=np.array([[geo[n]['courtyard'][2]-geo[n]['courtyard'][0],geo[n]['courtyard'][3]-geo[n]['courtyard'][1]] for n in refs])
orig=cent.copy()
def boxes():
 wh=sizes.copy();wh[angles%180==90]=wh[angles%180==90,::-1]
 return np.column_stack((cent-wh/2,cent+wh/2))
B=boxes()
links=[('Q1','R8'),('Q1','R11'),('Q2','R9'),('Q2','R12'),('Q3','R10'),('Q3','R13'),('U1','C1'),('U2','C2'),('U3','C3'),('U21','C25'),('U21','C26'),('U21','R23'),('R23','R24'),('U1','R4'),('U1','R5')]
links=[(refs.index(a),refs.index(b)) for a,b in links]
def local_cost(i):
 b=B[i]
 other=np.concatenate((B[:i],B[i+1:],obs,viaobs if refs[i]!='C21' else np.zeros((0,4))))
 ix=np.minimum(b[2]+.025,other[:,2])-np.maximum(b[0]-.025,other[:,0])
 iy=np.minimum(b[3]+.025,other[:,3])-np.maximum(b[1]-.025,other[:,1])
 collision=np.maximum(ix,0)*np.maximum(iy,0)
 wall=sum(max(v,0)**2 for v in [.25-b[0],.25-b[1],b[2]-14.99,b[3]-37.85])
 soft=.012*np.sum((cent[i]-orig[i])**2)
 for a,c in links:
  if i in (a,c):soft+=.15*np.sum((cent[a]-cent[c])**2)
 
 for a,c in links:
  if i in (a,c) and (refs[a].startswith('Q') or refs[c].startswith('C') or refs[a]=='U21' or refs[a]=='R23'):wall+=max(0,np.linalg.norm(cent[a]-cent[c])-4)**2
 if refs[i]=='C21':wall+=sum((cent[i]-[8.8,18.1])**2)
 return 800*sum(collision)+800*wall+soft
def hard():
 total=0
 for i,b in enumerate(B):
  other=np.concatenate((B[i+1:],obs,viaobs if refs[i]!='C21' else np.zeros((0,4))))
  ix=np.minimum(b[2]+.025,other[:,2])-np.maximum(b[0]-.025,other[:,0]);iy=np.minimum(b[3]+.025,other[:,3])-np.maximum(b[1]-.025,other[:,1])
  total+=sum(np.maximum(ix,0)*np.maximum(iy,0))
  total+=sum(max(v,0)**2 for v in [.25-b[0],.25-b[1],b[2]-14.99,b[3]-37.85])
  if refs[i]=='C21':total+=sum((cent[i]-[8.8,18.1])**2)
 for a,c in links:
  if refs[a].startswith('Q') or refs[c].startswith('C') or refs[a]=='U21' or refs[a]=='R23':total+=max(0,np.linalg.norm(cent[a]-cent[c])-4)**2
 return total

random.seed(91624);best=None;besth=1e9;start=time.time()
for step in range(1200000):
 i=random.randrange(len(refs))
 if refs[i]=='C21':continue
 oldc=cent[i].copy();olda=angles[i];oldb=B[i].copy();oc=local_cost(i)
 phase=(step%80000)/80000;temp=max(.018,12*(1-phase)**3)
 if random.random()<.09:angles[i]=(angles[i]+90)%180
 else:
  span=.2 if phase>.8 else (1.1 if phase>.2 else 3)
  cent[i]+=np.array([round(random.gauss(0,span)/.05)*.05,round(random.gauss(0,span)/.05)*.05])
 wh=sizes[i] if angles[i]%180==0 else sizes[i][::-1];B[i]=[*list(cent[i]-wh/2),*list(cent[i]+wh/2)]
 dc=local_cost(i)-oc
 if dc>0 and random.random()>math.exp(-min(dc/temp,700)):cent[i]=oldc;angles[i]=olda;B[i]=oldb
 if step%1000==0:
  h=hard()
  if h<besth:besth=h;best=(cent.copy(),angles.copy(),B.copy())
  if h<1e-10 and step>40000:break
cent,angles,B=best
parts={n:[round(cent[i,0],3),round(cent[i,1],3),int(angles[i]),'bottom'] for i,n in enumerate(refs)}
out={'status':'bottom courtyard and through-pad clearance proposal; routing and full native DRC pending','fixed_th':{'J1':[1.27,1.27,0],'J2':[13.97,3.81,0],'J3':[7.3,3.1,-90],'J4':[2.5,33.1,0],'SW1':[7.62,26.5,0]},'board_mm':[15.24,38.1],'hard_overlap_score':besth,'parts':parts}
(ROOT/'bottom-placement-proposal.json').write_text(json.dumps(out,indent=2)+'\n')
print('seconds',time.time()-start,'steps',step,'overlap',besth)
print(json.dumps(parts,indent=2))
