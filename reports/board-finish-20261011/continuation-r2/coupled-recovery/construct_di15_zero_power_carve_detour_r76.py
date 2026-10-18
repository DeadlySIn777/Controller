"""Correct physical In2 path around unchanged native field boundaries.

Potential new In1 ground keeps every original and proposed power plane hard;
it is a constructor search region, never source/ref/current qualification.
"""
import sys,json,pickle,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import fast_contacts as F
import tri_route as T
import construct_di6_direct_source_escape_r5 as K
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
C=A.C;GND='/LOGIC_GND';NET='/motherboard_di/DI15_LOGIC';RELEASE=set()
def main():
 started=time.monotonic();out=HERE/'di15-original-boundary-detour-r76.json';assert not out.exists();A.read(__file__);rp=HERE/'di15-safe-root-r22-DI6-bind-r62.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='a8234fa46de66b43eeefcf2bfbdb3d8563bf862a2ce60c46212b17e77ea314be';raw=A.read(r['model_path']);assert C.sha(raw)==r['model_sha256'];cur=pickle.loads(raw);h=cur['h'];ref=cur['source_planes']['In1.Cu'];domain=h['domains_normalized'];win=box(110,81,137,123);rec,trees=F.build({**h,'zones':[]});obs=[]
 for i in trees['In1.Cu'].query(win.buffer(1),predicate='intersects'):
  q=rec['In1.Cu'][int(i)];n=L.norm(q['net'])
  if n==GND:continue
  gap=max(.15 if domain.get(n)==domain.get(GND) else .6,.25)+.025;obs.append(q['shape'].buffer(gap,quad_segs=128))
 for k in('vias','pads'):
  for q in h[k]:
   if k=='vias':holes=[Point(q['x'],q['y']).buffer(q['drill']/2,quad_segs=128)]
   else:holes=L.poly(q.get('hole') or [])
   for sh in holes:
    if sh.distance(win)>1:continue
    obs.append(sh if L.norm(q['net'])==GND else sh.buffer(.275,quad_segs=128))
 for z in cur['zones']:
  n=L.norm(z['net'])
  if z['layer']!='In1.Cu' or n==GND or z['uuid'] in RELEASE or z['shape'].distance(win)>1:continue
  gap=max(.15 if domain.get(n)==domain.get(GND) else .6,.25,float(z.get('clearance_mm',.15)))+.025;obs.append(z['shape'].buffer(gap,quad_segs=128))
 # Original filled Cu of every foreign net remains hard, including the
 # explicit FIELD_B_0V native In1 cross-domain piece. No stale void credit.
 original_rows=[];owned_ids={z['uuid'] for z in cur['zones']}
 for z in cur['after']['zones']:
  n=L.norm(z['net'])
  if n==GND or z['uuid'] in owned_ids:continue
  for sh in L.poly(z['fills'].get('In1.Cu',[])):
   if sh.distance(win)>1:continue
   gap=max(.15 if domain.get(n)==domain.get(GND) else .6,.25,float(z.get('clearance_mm',.15)))+.025;obs.append(sh.buffer(gap,quad_segs=128));original_rows.append({'UUID':z['uuid'],'net':z['net'],'local_mm':float(z.get('clearance_mm',.15)),'required_mm':gap,'WKB_sha256':C.sha(sh.wkb)})
 for z in h['rule_areas']:
  if 'In1.Cu' in z['layers'] and z.get('no_zones'):obs.extend(sh.buffer(.025,quad_segs=128) for sh in L.poly(z['outline']))
 reserve,exempt=A.reservations()
 for z in reserve['keepouts']:
  if 'In1.Cu' in z['layers'] and GND not in exempt.get(z['name'],set()):obs.extend(sh.buffer(.025,quad_segs=128) for sh in L.poly(z['outline']))
 legal=win.difference(unary_union(obs));potential_reference=ref.intersection(win).union(legal)
 r44=json.loads(A.read(HERE/'di15-hybrid-transport-nomination-r44.json'));localraw=A.read(r44['saved_local_geometry']);assert C.sha(localraw)==r44['saved_local_geometry_sha256'];loc=pickle.loads(localraw);physical=loc['free'][NET,'In2.Cu'];allowed=physical.intersection(potential_reference.buffer(-.105,quad_segs=128));r48=json.loads(A.read(HERE/'di15-In2-physical-reference-diagnostic-r48.json'));sites=r48['physical_paths_reference_not_qualified'][0]['signal_sites'];parts=[p for p in K.pieces(allowed) if all(p.covers(Point(s)) for s in sites)];print('DI15_R76_ORIGINAL_BOUNDARY_AVOIDING_COMPONENTS',len(parts),flush=True);pts=[];search={};gap=None
 if parts:
  pts,search=T.route(parts[0],tuple(sites[0]),tuple(sites[1]));pts=[[round(x,6),round(y,6)] for x,y in pts]
  if len(pts)>=2:
   body=unary_union([A.shape({'kind':'segment','a':a,'b':b,'w':.2}) for a,b in zip(pts,pts[1:])]);gap=body.difference(potential_reference)
 cache=HERE/'di15-original-boundary-detour-r76-geometry.pkl';assert not cache.exists();cache.write_bytes(pickle.dumps({'potential_reference':potential_reference,'reference_only_new_ground_legal':legal,'allowed_In2_center_region':allowed,'physical_In2_center_region':physical,'current_actual_In1_reference':ref.intersection(win),'current_model_sha256':r['model_sha256']},protocol=5));report={'verdict':'DI15_ZERO_POWER_CARVE_IN2_PATH_NOMINATED_SOURCE_REFERENCE_CONSTRUCTION_OPEN' if len(pts)>=2 and gap.area<1e-10 else'DI15_ZERO_POWER_CARVE_SAVED_TWO_SITE_DETOUR_INCOMPLETE','R62_receipt_sha256':C.sha(A.read(rp)),'source_model_sha256':r['model_sha256'],'signal_sites':sites,'In2_points_mm':pts,'width_mm':.2,'length_mm':LineString(pts).length if len(pts)>=2 else None,'full_body_potential_reference_gap_mm2':gap.area if gap is not None else None,'actual_existing_ground_not_eroded_or_expanded':True,'new_ground_local_clearance_mm':.25,'owned_positive_planes_only_release_for_nomination':sorted(RELEASE),'source_contact_signed_load_current_peer_rebuild_native_SI':'OPEN','R56_R64_incomplete_masks_preserved_not_adopted':True,'all_original_foreign_fill_boundaries_preserved_hard':original_rows,'search':search,'saved_geometry':str(cache),'saved_geometry_sha256':C.sha(cache.read_bytes()),'native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':report['verdict'],'points':pts,'gap':report['full_body_potential_reference_gap_mm2'],'search':search}),flush=True)
if __name__=='__main__':main()
