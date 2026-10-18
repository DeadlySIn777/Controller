"""Retain exact prior owned route and add only legal contained widening pieces."""
import os
for key in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='2'
import hashlib,json,pickle,sys
from pathlib import Path
from shapely import from_wkb,set_precision
from shapely.geometry import LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for folder in('field-power','sbc-power'):sys.path.insert(0,str(H/folder))
import guarded_declared_settings_projection_r58 as N
import contact_layout as C
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.wkb).hexdigest()
def parts(s):
 if s.is_empty:return[]
 if s.geom_type=='Polygon':return[s]
 return[p for q in getattr(s,'geoms',[])for p in parts(q)]
def main():
 base=H/'CORE-bounded-owned-FAG-In2-notch-feed-proposal-r98';assert sha(base/'receipt.json')=='77e2d358f3a177854b3b2aaa4863430e36967e4eb06520f91a501742f054e4cd';rows=pickle.loads((base/'proposed-route-and-zone.pkl').read_bytes());assert len(rows)==1;row=rows[0];q=row['zone'];replays=[]
 for role in('shape','zone_outline_shape'):
  original=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert q[role].wkb==original;replays.append({'only_generated_CORE_UUID':q['uuid'],'role':role,'WKB_unchanged':True,'WKB_sha256':digest(q[role]),'grid_mm':1e-6})
 legal=from_wkb((base/'In2.Cu-legal.wkb').read_bytes());w=legal.wkb;legal=set_precision(legal,1e-6,mode='pointwise');assert legal.wkb==w;line=LineString(row['source_to_main_points']);new_wide=N.bounded_buffer(line,2.);added=set_precision(new_wide.intersection(legal.buffer(-.000005)).difference(q['zone_outline_shape']),1e-6);fixes=[]
 for attempt in range(5):
  outside=added.difference(legal)
  if outside.is_empty:break
  cutter=N.bounded_buffer(outside,.000003);fixes.append({'only_new_widening_gain_sha256':digest(outside),'gain_mm2':outside.area,'local_cutter_sha256':digest(cutter)});added=set_precision(added.difference(cutter),1e-6)
 assert added.difference(legal).is_empty,'new-only widening escaped unchanged planner region';native=set_precision(unary_union([q['zone_outline_shape'],added]),1e-6);assert q['zone_outline_shape'].difference(native).is_empty,'new-only widening lost existing owned route'
 mp=H/'joint-positive-head-signal-reference-mask-proposal-r83/model.pkl';assert sha(mp)=='e9d67e30fd34bf5e42db2faa23b8c4c32ea11e8be9b8e5419fd2bd2c';g,h,b,z,current=pickle.loads(mp.read_bytes());d=pickle.loads((base/'proposed-discrete.pkl').read_bytes());holes=unary_union([N.bounded_disk(v,v['drill']/2)for v in h['vias']+d['vias']if v['net']=='/CORE_1V2']+[s for p in h['pads']if p['net']=='/CORE_1V2'for s in C.poly(p.get('hole')or[])]);physical=native.difference(holes);assert native.is_valid and physical.is_valid;assert q['shape'].difference(physical).is_empty
 out=H/'CORE-wider-new-only-legal-envelope-proposal-r105';assert not out.exists();out.mkdir();updated={**q,'shape':physical,'zone_outline_shape':native,'label':'CORE new-only legal envelope expansion R105; original1mm core preserved'};newrow={**row,'zone':updated,'old_nominal_envelope_radius_mm':1.,'new_nominal_envelope_radius_mm':2.,'only_NEW_added_region_required_inside_exact_same_legal_region':True,'all_true_geometry_native_guard_contact_reference_current_gates':'OPEN'};(out/'proposed-route-and-zone.pkl').write_bytes(pickle.dumps([newrow],protocol=5));(out/'proposed-discrete.pkl').write_bytes((base/'proposed-discrete.pkl').read_bytes());(out/'only-new-legal-expansion.wkb').write_bytes(added.wkb);oldoutside=q['zone_outline_shape'].difference(legal);newoutside=native.difference(legal);r=json.loads((base/'receipt.json').read_bytes());r.update({'verdict':'NEW_ONLY_LEGAL_CORE_WIDER_ENVELOPE_NOMINEE_ALL_ACTUAL_GATES_OPEN','old_R98_receipt_sha256':sha(base/'receipt.json'),'new_physical_WKB_sha256':digest(physical),'new_intended_WKB_sha256':digest(native),'old_actual_physical_mm2':q['shape'].area,'new_actual_physical_mm2':physical.area,'only_new_widening_added_mm2':added.area,'added_region_legal_coverage_exact':True,'minimum_original1mm_route_core_geometry_preserved':True,'exact_ordinary_via_geometry_unchanged':True,'generated_role_WKB_exact_tag_replays':replays,'only_new_local_legal_clips':fixes,'old_R98_planner_subset_diagnostic':{'old_baseline_outside_legal_mm2':oldoutside.area,'new_outside_legal_mm2':newoutside.area,'old_baseline_true_all6_Cu_geometry109_checks0_from_independent_R224':'unmodified separate evidence; no coverage-tolerance grant','wider_actualtrueCu_and_all_source_contact_reference_current_native_gates':'OPEN'},'strict_R224_reference_FAILURES_preserved':True});r['routes'][0]['physical_WKB_sha256']=digest(physical);(out/'receipt.json').write_text(json.dumps(r,indent=1)+'\n');print('R105_NEW_ONLY_LEGAL_CORE_WIDENING',q['shape'].area,physical.area,sha(out/'receipt.json'),digest(physical),flush=True)
if __name__=='__main__':main()
