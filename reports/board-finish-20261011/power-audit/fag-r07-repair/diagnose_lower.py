"""Read-only bounded diagnostic for the one withheld FAG network."""
import json
import math
import time
from pathlib import Path
import plan_repair as P
from shapely.geometry import Point,LineString
from shapely.ops import unary_union

def main():
 rows,_=P.I.own_additions();g,_,_=P.R.overlay_and_targets()
 reservations,exempt=P.exemptions();model=P.S.Model(g,reservations,exempt)
 vias={v['uuid']:v for v in g['vias']}
 removed=set(P.REMOVED_VIAS)|{u for n in P.NETWORKS for u in n['remove']}
 kept={u:r for u,r in rows.items() if u not in removed}
 own={u:{'uuid':u,'net':P.NET,'x':r['at'][0],'y':r['at'][1],'d':r['d'],'drill':r['drill']} for u,r in kept.items() if r['kind']=='via'}
 n=P.NETWORKS[1];original=unary_union([P.centre(rows[u]) for u in n['remove']])
 a,b=n['anchors'];out=[]
 for grow in (8,10,12):
  window=original.envelope.buffer(grow,cap_style=3).envelope
  f=P.free(model,.3,window,vias,own,set())
  components=list(getattr(f,'geoms',[f]))
  info={'grow_mm':grow,'window':list(window.bounds),'components':len(components),
        'anchor_components':[[{'index':i,'area':c.area,'bounds':list(c.bounds)} for i,c in enumerate(components) if c.covers(Point(p))] for p in(a,b)]}
  path,search=P.exact_path(model,a,b,.3,vias,own,set(),window)
  info.update(path=path,search=search);out.append(info);print(json.dumps(info),flush=True)
  if path:break
 nearby=[]
 direct=LineString([a,b]);window=direct.envelope.buffer(3,cap_style=3).envelope
 for i in model.trees['In3.Cu'].query(window,predicate='intersects'):
  rec=model.records['In3.Cu'][i]
  if rec['kind']!='hole' and rec['net']==P.NET:continue
  gap=.25 if rec['kind']=='hole' else .15 if rec.get('domain')==P.DOMAIN else .6
  expanded=rec['shape'].buffer(gap+.15+.025)
  if not expanded.intersects(direct):continue
  nearby.append({k:rec[k] for k in('kind','uuid','net','domain') if k in rec}|{'bounds':list(rec['shape'].bounds),'inflated_bounds':list(expanded.bounds)})
 for rec in model.hard['In3.Cu']:
  if P.NET not in rec['exempt'] and rec['shape'].buffer(.175).intersects(window):
   nearby.append({k:rec[k] for k in('kind','name')}|{'bounds':list(rec['shape'].bounds)})
 result={'source_only':True,'network':n,'windows':out,'direct_line_obstacles':nearby,'native_jobs':0,'board_emitted':False}
 destination=P.HERE/'lower-diagnosis.json'
 if destination.exists():raise ValueError('Distinct receipt required')
 destination.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({'direct_obstacles':nearby},indent=1),flush=True)

if __name__=='__main__':main()
