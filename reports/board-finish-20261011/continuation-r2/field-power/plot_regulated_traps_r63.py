"""Local physical-wall figures for the unresolved small regulated pins."""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle
from pathlib import Path
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as Patch
from shapely.geometry import box
from shapely.ops import unary_union
import contact_layout as C
import fast_contacts as F
HERE=Path(__file__).resolve().parent;OUT=HERE/'regulated-pin-wall-figures-r63'
def polys(s):return [s] if s.geom_type=='Polygon' else [q for q in getattr(s,'geoms',[]) if q.geom_type=='Polygon']
def main():
 assert not OUT.exists();OUT.mkdir();_,h,_,_,_=pickle.loads((HERE/'regulated-outer-source-joins-r51/base-model.pkl').read_bytes());rec,trees=F.build({**h,'zones':[]},layers={'F.Cu','B.Cu'});oldids={q['uuid'] for kind in ('vias','tracks') for q in pickle.loads((HERE/'native-bound-field-base-r5/geometry.pkl').read_bytes())[kind]} if (HERE/'native-bound-field-base-r5/geometry.pkl').exists() else set()
 targets=[('U9004','10'),('U9003','10'),('U10009','4'),('U19008','10'),('U10017','4'),('U10022','4'),('U11017','5')]
 fig,axes=plt.subplots(3,3,figsize=(15,15))
 for ax,(ref,pin) in zip(axes.flat,targets):
  pad=next(q for q in h['pads'] if q['ref']==ref and q['num']==pin);l=next(l for l in ('F.Cu','B.Cu') if l in pad['layers']);shape=unary_union(C.poly(pad['layers'][l]));x,y=shape.representative_point().coords[0];win=box(x-3,y-3,x+3,y+3)
  for i in trees[l].query(win,predicate='intersects'):
   q=rec[l][int(i)];color='#16a085' if q['net']==pad['net'] else '#d98825' if 'GND' in q['net'] or '0V' in q['net'] else '#4766a8'
   for sh in polys(q['shape'].intersection(win)):
    ax.add_patch(Patch(list(sh.exterior.coords),facecolor=color,edgecolor='black',linewidth=.4,alpha=.7))
   center=q['shape'].representative_point();label=(q.get('ref','')+'.'+q.get('pin','')).strip('.') if q['kind']=='pad' else q['uuid'][:8]
   if win.contains(center):ax.text(center.x,center.y,label,fontsize=5,ha='center',va='center')
  ax.set_xlim(x-3,x+3);ax.set_ylim(y+3,y-3);ax.set_aspect('equal');ax.set_title(ref+'.'+pin+' '+l);ax.grid(alpha=.2)
 for ax in list(axes.flat)[len(targets):]:ax.axis('off')
 fig.tight_layout();fig.savefig(OUT/'physical-walls.png',dpi=180);print(OUT/'physical-walls.png',flush=True)
if __name__=='__main__':main()
