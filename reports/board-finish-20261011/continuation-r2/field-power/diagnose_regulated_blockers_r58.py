"""Identify exact outer-pad trapping walls after frozen regulated feed proposals."""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle
from pathlib import Path
from shapely.geometry import box
from shapely.ops import unary_union
from inventory import sha
import contact_layout as C
import fast_contacts as F
HERE=Path(__file__).resolve().parent;OUT=HERE/'regulated-pad-blocker-diagnostic-r58'

def main():
 assert not OUT.exists();OUT.mkdir();bp=HERE/'regulated-outer-source-joins-r51';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'base-model.pkl')==br['base_model_sha256'];g,h,binding,zones,after=pickle.loads((bp/'base-model.pkl').read_bytes());rec,trees=F.build({**h,'zones':[]},layers={'F.Cu','B.Cu'});padbyid={q['uuid']:q for q in h['pads']};rows=[]
 for miss in br['remaining']:
  for ident in miss['physical_pads']:
   pad=padbyid[ident['uuid']];l=ident['layer'];shape=unary_union(C.poly(pad['layers'][l]));net=C.norm(pad['net']);dom=h['domains_normalized'][net];x0,y0,x1,y1=shape.bounds;win=box(x0-4,y0-4,x1+4,y1+4);walls=[];near=[]
   for i in trees[l].query(win,predicate='intersects'):
    q=rec[l][int(i)]
    if q['net']==pad['net']:continue
    gap=.15 if q['domain']==dom else .6;wall=q['shape'].buffer(gap+.025);walls.append(wall);d=shape.distance(q['shape'])
    if d<1.25:near.append(C.identity(q)|{'Cu_gap_to_target_mm':d,'required_track_Cu_gap_mm':gap+.025,'bounds_mm':list(q['shape'].bounds)})
   for q in zones:
    if q['layer']==l and q['net']!=pad['net'] and q['shape'].intersects(win):walls.append(q['shape'].buffer((.15 if h['domains_normalized'][C.norm(q['net'])]==dom else .6)+.025))
   for area in h['rule_areas']:
    if area.get('no_tracks') and l in area['layers']:walls.extend([s.buffer(.025) for s in C.poly(area['outline'])])
   legal=win.difference(unary_union(walls));free=legal.buffer(-.105);parts=[free] if free.geom_type=='Polygon' else [s for s in getattr(free,'geoms',[]) if s.geom_type=='Polygon'];attached=[s for s in parts if s.intersects(shape)];rows.append({'bank':miss['bank'],'group':miss['group'],'target_pad':ident,'target_native_Cu_bounds_mm':list(shape.bounds),'minimum_020_track_center_can_enter_pad':bool(attached),'local_reachable_component_areas_mm2':[s.area for s in attached],'nearest_source_mm':miss['nearest_source_mm'],'nearest_foreign_physical_items':sorted(near,key=lambda q:q['Cu_gap_to_target_mm'])[:18],'diagnostic_local_window_mm':list(win.bounds),'old_original_fill_retreat_permitted_for_tracks_but_new_proposals_hard':True})
   print(miss['bank'],ident['ref']+'.'+ident['pin'],'escape',bool(attached),'nearest',[(q.get('ref'),q.get('pin'),q['kind'],q['uuid'],round(q['Cu_gap_to_target_mm'],6)) for q in sorted(near,key=lambda q:q['Cu_gap_to_target_mm'])[:3]],flush=True)
 (OUT/'receipt.json').write_text(json.dumps({'verdict':'EXACT_REGULATED_PAD_WALL_DIAGNOSTIC_ONLY','input_R51_receipt_sha256':sha(bp/'receipt.json'),'rows':rows,'native_jobs':0,'board_written':False,'full_conservative_control_rate_output_limits_preserved':True},indent=1)+'\n',encoding='utf-8');print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
