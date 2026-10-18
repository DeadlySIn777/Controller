"""Exact local starting pockets and straight-path blockers; no route waiver."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,re
from pathlib import Path
from shapely.geometry import box,Point,LineString
from shapely.ops import unary_union,nearest_points
from shapely import STRtree
import contact_layout as C
import fast_contacts as F
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import guarded_power_projection_r44 as P
O=H/'seven-regulated-local-wall-diagnostic-r128'
def parts(s):return [s] if s.geom_type=='Polygon' else [p for q in getattr(s,'geoms',[]) for p in parts(q)]
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();base=H/'regulated-source-contact-reference-audit-r116';g,h,b,z,after=pickle.loads((base/'model.pkl').read_bytes());groups=pickle.loads((base/'groups.pkl').read_bytes());rows=json.loads((H/'regulated-source-synchronized-local-nominees-r125/receipt.json').read_text())['remaining'];rec,trees=F.build({**h,'zones':[]},layers={'F.Cu','B.Cu'});vmap={q['uuid']:q for q in h['vias']};tmap={q['uuid']:q for q in h['tracks']};outline=unary_union(C.poly(h['outline'])).buffer(-.526);reserved=json.loads((C.BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text());adapter=H/'moved-supply-escape-rule-adapter-r122/proposed.kicad_dru';exceptions={}
 for line in adapter.read_text().splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
  if m:exceptions[m[1]]={C.norm(x) for x in re.findall(r"A.NetName != '([^']*)'",m[2])}
 out=[]
 for row in rows:
  ident=row['physical_pads'][0];net=C.norm(ident['net']);l=ident['layer'];target=next(q for q in rec[l] if q['kind']=='pad' and q['uuid']==ident['uuid']);sh=target['shape'];center=sh.representative_point();win=box(center.x-5,center.y-5,center.x+5,center.y+5);dom=h['domains_normalized'][net];walls=[];wallrows=[]
  def gap(other):return .15 if h['domains_normalized'].get(C.norm(other))==dom else .6
  def add(uid,kind,raw,body,clear,**meta):
   cut=P.bounded_buffer(body,clear);walls.append(cut);wallrows.append({'uuid':uid,'kind':kind,'raw_net':raw,'actual_body_gap_to_target_mm':body.distance(sh),'required_guarded_gap_mm':clear,'guarded_cut_target_overlap_mm2':cut.intersection(sh).area,'bounds':list(body.bounds),**meta})
  for j in trees[l].query(win.buffer(.627),predicate='intersects'):
   q=rec[l][int(j)]
   if C.norm(q['net'])==net:continue
   body=q['shape']
   if q['kind']=='via':v=vmap[q['uuid']];body=P.bounded_disk(v,v['d']/2)
   if q['kind']=='track':t=tmap[q['uuid']];body=P.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2)
   add(q['uuid'],q['kind'],q['net'],body,gap(q['net'])+.025,ref=q.get('ref'),pin=q.get('pin'))
  for q in z:
   if q['layer']==l and C.norm(q['net'])!=net and q['shape'].intersects(win.buffer(.627)):add(q['uuid'],'new_plane',q['net'],q['shape'],max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025)
  for a in h['rule_areas']:
   if a.get('no_tracks') and l in a['layers']:
    for sh0 in C.poly(a['outline']):
     if sh0.intersects(win):add(a.get('uuid','rule-area'),'native_no_tracks','',sh0,.025)
  for a in reserved['keepouts']:
   if l in a['layers'] and net not in exceptions.get(a['name'],set()):
    for sh0 in C.poly(a['outline']):
     if sh0.intersects(win):add(a['name'],'declared_reservation','',sh0,.025)
  free=win.intersection(outline).difference(unary_union(walls));pockets=[p for p in parts(free.buffer(-.105)) if p.intersection(sh).area>1e-9];rootref,rootpin=next((r,p) for bank,n,r,p,pol in __import__('regulated_outer_joins_r51').PORTS if n==net);gs=groups[net];ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(rootref,rootpin) for q in xs));source=unary_union([q['shape'] for q in gs[ri] if q['layer']==l]);a,bb=nearest_points(sh,source);line=LineString([a.coords[0],bb.coords[0]]);body=P.bounded_buffer(line,.1);blockers=[]
  for wall,w in zip(walls,wallrows):
   if wall.intersects(body):blockers.append({**w,'straight_nominee_cut_overlap_mm2':wall.intersection(body).area})
  result={'target':ident,'absolute_pad_bounds':list(sh.bounds),'start_pocket_count_for_0p20_with_0p005_search_reserve':len(pockets),'start_pocket_bounds':[list(p.bounds) for p in pockets],'target_body_remaining_in_local_free_mm2':sh.intersection(free).area,'target_body_total_mm2':sh.area,'nearest_source':rootref+'.'+rootpin,'nearest_source_points_mm':[list(a.coords[0]),list(bb.coords[0])],'nearest_source_gap_mm':a.distance(bb),'local_guarded_walls_overlapping_target':[w for w in wallrows if w['guarded_cut_target_overlap_mm2']>1e-9],'straight_line_blockers_are_diagnostic_only':blockers};out.append(result);print(ident['ref'],ident['pin'],'pockets',len(pockets),'pad-wall-overlaps',len(result['local_guarded_walls_overlapping_target']),flush=True)
  write(O/'checkpoint.json',out)
 write(O/'detail.json',out);write(O/'receipt.json',{'verdict':'EXACT_LOCAL_WALL_DIAGNOSIS_ONLY','R116_model_sha256':sha(base/'model.pkl'),'R125_receipt_sha256':sha(H/'regulated-source-synchronized-local-nominees-r125/receipt.json'),'source_rule_adapter_SHA256':sha(adapter),'detail_sha256':sha(O/'detail.json'),'no_path_or_removal_acceptance':True,'geometry_changed':False,'board_written':False,'native_jobs':0});print('R128',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
