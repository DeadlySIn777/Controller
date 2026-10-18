"""Bounded courtyard packing study; not a routing/fabrication release."""
from pathlib import Path
import json,random,math,time
R=Path(__file__).resolve().parent
geo=json.loads((R/'placement-geometry.json').read_text())
def transformed(ref,x,y,a):
 b=geo[ref]['courtyard'];rad=math.radians(a);c,s=math.cos(rad),math.sin(rad)
 pts=[(x+xx*c+yy*s,y-xx*s+yy*c) for xx,yy in ((b[0],b[1]),(b[2],b[1]),(b[2],b[3]),(b[0],b[3]))]
 return [min(t[0] for t in pts),min(t[1] for t in pts),max(t[0] for t in pts),max(t[1] for t in pts)]
def intersect(a,b):return a[0]<b[2]-1e-8 and a[2]>b[0]+1e-8 and a[1]<b[3]-1e-8 and a[3]>b[1]+1e-8
def cut(free,b):
 result=[]
 for f in free:
  if not intersect(f,b):result.append(f);continue
  if b[0]>f[0]:result.append([f[0],f[1],b[0],f[3]])
  if b[2]<f[2]:result.append([b[2],f[1],f[2],f[3]])
  if b[1]>f[1]:result.append([f[0],f[1],f[2],b[1]])
  if b[3]<f[3]:result.append([f[0],b[3],f[2],f[3]])
 result=[f for f in result if f[2]-f[0]>.1 and f[3]-f[1]>.1]
 return [f for i,f in enumerate(result) if not any(i!=j and g[0]<=f[0]+1e-9 and g[1]<=f[1]+1e-9 and g[2]>=f[2]-1e-9 and g[3]>=f[3]-1e-9 and (g!=f or j<i) for j,g in enumerate(result))]
random.seed(261006);results=[];started=time.time()
for height,tries in [(50,100),(60,300)]:
 fixed={'J1':[1.27,1.27,0,'bottom'],'J2':[13.97,3.81,0,'bottom'],
 'J3':[6.35,3.3,-90,'top'],'SW1':[7.62,height-10.35,0,'top'],'J4':[2.5,height-3.95,0,'top']}
 strips=[[0,0,2.37,20.15],[12.87,2.71,15.24,20.15]]
 basefree=[[.25,.25,14.99,height-.25]]
 for b in strips+[transformed(n,*v[:3]) for n,v in fixed.items() if v[3]=='top']:basefree=cut(basefree,b)
 refs=[n for n in geo if n not in fixed]
 best=None
 for trial in range(tries):
  # Native footprint envelopes are retained, with a further0.025mm gap.
  order=sorted(refs,key=lambda n:-(geo[n]['area_mm2']*(random.uniform(.65,1.35) if trial else 1)))
  free=[f[:] for f in basefree];placed=dict(fixed);failed=[]
  for ref in order:
   options=[]
   for a in [0,90]:
    b=transformed(ref,0,0,a);w,h=b[2]-b[0],b[3]-b[1]
    for f in free:
     fw,fh=f[2]-f[0],f[3]-f[1]
     if w+.025<=fw and h+.025<=fh:
      score=(min(fw-w,fh-h),max(fw-w,fh-h),f[1])
      options.append((score,f[0]-b[0]+.0125,f[1]-b[1]+.0125,a,w,h))
   if not options:failed.append(ref);continue
   _,x,y,a,w,h=min(options)
   placed[ref]=[round(x,5),round(y,5),a,'top']
   b=transformed(ref,x,y,a);free=cut(free,[b[0]-.0125,b[1]-.0125,b[2]+.0125,b[3]+.0125])
  if best is None or len(failed)<len(best['unplaced']):best={'board_mm':[15.24,height],'layers':2,'parts':placed,'unplaced':failed,'trial':trial,'header_top_service_strips':strips}
  if not failed:break
 best['status']='Courtyard packing only; electrical clustering/routing and host fit NOT PROVEN'
 best['native_erc_drc_performed']=False
 best['manufacturing_ready']=False
 best['algorithm']='Bounded MaxRects packing with native courtyard envelopes; largest-first varied order; no courtyard shrinking'
 best['attempts']=trial+1
 (R/f'placement-packing-{height}mm.json').write_text(json.dumps(best,indent=2)+'\n')
 results.append({'height':height,'unplaced':best['unplaced'],'attempts':best['attempts']})
print(json.dumps({'elapsed_seconds':time.time()-started,'results':results}))
