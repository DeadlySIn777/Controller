"""Inspect saved actual/native and prospective host geometry; this is no fabrication output."""
import os
for n in('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[n]='2'
import hashlib,json,pickle,sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path as MP
from matplotlib.patches import PathPatch,Circle
from matplotlib.collections import LineCollection
from shapely.geometry import box
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
folder=H/'joint-positive-head-signal-reference-mask-proposal-r83';r=json.loads((folder/'receipt.json').read_bytes());mp=folder/'model.pkl';assert sha(mp)==r['model_sha256'];g,h,b,z,current=pickle.loads(mp.read_bytes());groups=pickle.loads((folder/'source-groups.pkl').read_bytes())['/CORE_1V2'];roi=box(145,72,250,108);fig,ax=plt.subplots(figsize=(17,6));ax.set_aspect('equal')
def draw(shape,color,alpha,label=None):
 sh=shape.intersection(roi)
 if sh.is_empty:return
 parts=[sh]if sh.geom_type=='Polygon'else[q for q in getattr(sh,'geoms',[])if q.geom_type=='Polygon']
 for i,p in enumerate(parts):
  vertices=[];codes=[]
  for ring in[p.exterior,*p.interiors]:
   points=list(ring.coords);vertices+=points;codes +=[MP.MOVETO]+[MP.LINETO]*(len(points)-2)+[MP.CLOSEPOLY]
  ax.add_patch(PathPatch(MP(vertices,codes),facecolor=color,edgecolor=color,lw=.2,alpha=alpha,label=label if i==0 else None))
for q in z:
 if q['layer']!='In3.Cu' or q['net']=='/CORE_1V2':continue
 draw(q['shape'],'#62a77c'if C.norm(q['net'])=='/LOGIC_GND'else'#df7558',.38)
for xs in groups:
 source=any(q['kind']=='pad'and(q['ref'],q['pin'])==('L2001','2')for q in xs);color='#204cbb'if source else'#579bea'
 for q in xs:
  if q['layer']=='In3.Cu':draw(q['shape'],color,.72)
segments=[];widths=[]
for t in h['tracks']:
 if t['layer']!='In3.Cu' or C.norm(t['net'])=='/CORE_1V2':continue
 if max(t['a'][0],t['b'][0])<145 or min(t['a'][0],t['b'][0])>250 or max(t['a'][1],t['b'][1])<72 or min(t['a'][1],t['b'][1])>108:continue
 segments.append([t['a'],t['b']]);widths.append(max(.25,t['w']*3.3))
ax.add_collection(LineCollection(segments,colors='#9e3c37',linewidths=widths,alpha=.8))
for v in h['vias']:
 if 'In3.Cu'not in v['flashed']or not(145<=v['x']<=250 and 72<=v['y']<=108):continue
 color='#204cbb'if v['net']=='/CORE_1V2'else'#873e35';ax.add_patch(Circle((v['x'],v['y']),v['d']/2,color=color,alpha=.8));ax.add_patch(Circle((v['x'],v['y']),v['drill']/2,color='white'))
for uid,label in[('f6ad6a15-3a41-4605-9ad5-72f4ba7d5d92','Actual source barrel'),('13ace114-2da3-479c-9c70-bee7d15da004','Main group landing')]:
 v=next(q for q in h['vias']if q['uuid']==uid);ax.annotate(label,(v['x'],v['y']),xytext=(v['x']-12,v['y']+9),fontsize=9,arrowprops={'arrowstyle':'->','color':'#152f60'},color='#152f60')
ax.set(xlim=(145,250),ylim=(108,72),xlabel='Board x (mm)',ylabel='Board y (mm)',title='In3 host routing inspection: source (dark blue), detached main copper (light blue)\nNew owned ground (green); other owned power and retained discrete copper (red). Native fill remains unqualified.');ax.grid(alpha=.15);fig.tight_layout();out=H/'CORE-In3-source-corridor-inspection-r88';assert not out.exists();out.mkdir();png=out/'host-In3-source-corridor.png';fig.savefig(png,dpi=130);plt.close(fig);(out/'receipt.json').write_text(json.dumps({'verdict':'READ_ONLY_HOST_GEOMETRY_INSPECTION_FIGURE','model_sha256':sha(mp),'figure_sha256':sha(png),'layer':'In3.Cu','ROI_mm':[145,72,250,108],'clearance_and_source_qualification_by_figure':'NOT_GRANTED','old_native_Cu_and_prospective_owned_planes_distinct_from_final_actual_native_fill':True,'native_jobs':0,'board_written':False,'adopted':False},indent=1)+'\n');print(png.resolve())
