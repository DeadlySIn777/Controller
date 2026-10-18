"""Exact continuous connectivity and physical separator for A output return."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,math
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely import set_precision
from contact_layout import HERE,load,build,poly,norm,identity,O
from power_groups import N,ROOTS
from inventory import sha
OUT=HERE/'return-obstruction-r1'

def main():
 if OUT.exists():raise ValueError('Frozen screen exists')
 OUT.mkdir();g,b=load();rec,trees=build(g,layers={'In1.Cu','In2.Cu','In3.Cu','In4.Cu'})
 prior=pickle.loads((HERE/'variable-return-r2/prospective-copper.pkl').read_bytes())
 for q in prior:rec[q['layer']].append(q)
 groups=pickle.loads((HERE/'power-groups-r1.pkl').read_bytes());net=N['FAG'];dom=g['domains_normalized'][net];pad=next(p for p in g['pads'] if (p['ref'],p['num'])==ROOTS['FAG']);goal=groups['FAG'][38];outline=unary_union(poly(g['outline']));rows=[]
 for layer in ['In1.Cu','In4.Cu','In2.Cu','In3.Cu']:
  obs=[]
  for r in rec[layer]:
   if norm(r['net'])==net or r['kind']=='fill':continue
   obs.append((r['shape'].buffer((.15 if r['domain']==dom else .6)+.03),identity(r)))
  for p in g['pads']:
   if norm(p['net'])!=net:
    for q in poly(p.get('hole') or []):obs.append((q.buffer(.275),{'kind':'pad_hole','ref':p['ref'],'pin':p['num'],'uuid':p['uuid'],'net':p['net']}))
  for v in g['vias']:
   if norm(v['net'])!=net:obs.append((Point(v['x'],v['y']).buffer(v['drill']/2+.275),{'kind':'via_hole','uuid':v['uuid'],'net':v['net']}))
  for a in g['rule_areas']:
   if a.get('no_zones') and layer in a['layers']:
    for q in poly(a['outline']):obs.append((q.buffer(.025),{'kind':'native_zone_barrier','uuid':a['uuid'],'name':a['name']}))
  blocked=set_precision(unary_union([q for q,r in obs]),.000001)
  source=unary_union(poly(pad['layers'][layer]));target=unary_union([r['shape'] for r in goal if r['layer']==layer])
  for w in [2.,1.,.5]:
   free=set_precision(outline.buffer(-.5-w/2-.026),.000001).difference(blocked.buffer(w/2+.001));pieces=[free] if free.geom_type=='Polygon' else [q for q in free.geoms if q.geom_type=='Polygon'];src=[q for q in pieces if q.intersection(source).area>1e-8];dst=[q for q in pieces if q.intersection(target).area>1e-8];ss=unary_union(src);tt=unary_union(dst);joined=any(q.intersection(target).area>1e-8 for q in src);row={'layer':layer,'core_width_mm':w,'root_component_count':len(src),'target_component_count':len(dst),'root_connected_to_JD09_A_return_group38_continuously':joined,'zone_specific_frozen_rules':True}
   if not ss.is_empty and not tt.is_empty and not joined:
    a,bb=nearest_points(ss,tt);gap=LineString([a,bb]);hits=[r|{'distance_to_gap_mm':q.distance(gap)} for q,r in obs if q.buffer(w/2+.001).intersects(gap.buffer(.0001))];row.update(closest_component_gap_mm=gap.length,gap_points_mm=list(gap.coords),blocking_original_items=hits)
   elif joined:
    rootpiece=next(q for q in src if q.intersection(target).area>1e-8);p=OUT/(layer+'-'+str(w)+'.free.wkb');p.write_bytes(rootpiece.wkb);row.update(source_root_connected_free_component_file=str(p.resolve()),component_sha256=sha(p),component_area_mm2=rootpiece.area)
   rows.append(row);print(layer,w,joined,row.get('closest_component_gap_mm'),[(x.get('kind'),x.get('ref'),x.get('pin')) for x in row.get('blocking_original_items',[])][:15],flush=True)
   (OUT/'checkpoint.json').write_text(json.dumps(rows,indent=1)+'\n',encoding='utf-8')
 (OUT/'receipt.json').write_text(json.dumps({'board_sha256':g['sha256'],'prior_bridge_receipt_sha256':sha(HERE/'variable-return-r2/receipt.json'),'native_jobs':0,'board_written':False,'rows':rows,'capacity_qualified':False},indent=1)+'\n',encoding='utf-8')

if __name__=='__main__':main()
