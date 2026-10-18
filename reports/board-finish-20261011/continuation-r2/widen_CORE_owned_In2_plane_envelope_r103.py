"""Widen only the newly nominated CORE plane; retain route/core and exact legal region."""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='2'
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
 base=H/'CORE-bounded-owned-FAG-In2-notch-feed-proposal-r98';assert sha(base/'receipt.json')=='77e2d358f3a177854b3b2aaa4863430e36967e4eb06520f91a501742f054e4cd';rows=pickle.loads((base/'proposed-route-and-zone.pkl').read_bytes());assert len(rows)==1;row=rows[0];q=row['zone'];assert q['uuid']=='b0453302-df03-561f-9bc4-0560bc66658a';legal=from_wkb((base/'In2.Cu-legal.wkb').read_bytes());replays=[]
 for role in('shape','zone_outline_shape'):
  old=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert q[role].wkb==old;replays.append({'only_documented_NEW_CORE_UUID':q['uuid'],'role':role,'WKB_unchanged':True,'grid_mm':1e-6,'WKB_sha256':digest(q[role])})
 points=row['source_to_main_points'];line=LineString(points);core=N.bounded_buffer(line,.5);assert legal.covers(core)
 mp=H/'joint-positive-head-signal-reference-mask-proposal-r83/model.pkl';assert sha(mp)=='e9d67e30fd34bf5e42db2faa23b8c4c32ea11e8be9b8e414b8f8e5419fd2bd2c';g,h,b,z,current=pickle.loads(mp.read_bytes());d=pickle.loads((base/'proposed-discrete.pkl').read_bytes());assert len(d['vias'])==2 and not d['tracks'];ownholes=unary_union([N.bounded_disk(v,v['drill']/2)for v in h['vias']+d['vias']if v['net']=='/CORE_1V2']+[shape for p in h['pads']if p['net']=='/CORE_1V2'for shape in C.poly(p.get('hole')or[])])
 native=set_precision(unary_union([p for p in parts(N.bounded_buffer(line,2.).intersection(legal))if p.intersection(core).area>0]),1e-6);native=set_precision(unary_union([q['zone_outline_shape'],native]),1e-6);assert legal.covers(native),'expanded original-route union escaped unchanged legal region';physical=native.difference(ownholes);assert native.is_valid and physical.is_valid;assert q['zone_outline_shape'].difference(native).is_empty,'wider envelope unexpectedly lost prior intended path';assert q['shape'].difference(physical).is_empty,'wider envelope lost prior physical Cu';updated={**q,'zone_outline_shape':native,'shape':physical,'label':'Widened CORE In2 envelope R102, minimum original1mm core preserved'};newrow={**row,'zone':updated,'maximum_new_nominal_envelope_radius_mm':2.,'old_radius_mm':1.,'minimum_original_route_core_mm':1.,'actual_old_native_foreign_power_IO3_antipads_and_only_declared_new_FAG_e2fe_notch':'ALL_GATES_OPEN'}
 out=H/'CORE-wider-owned-FAG-In2-notch-feed-proposal-r103';assert not out.exists();out.mkdir();(out/'proposed-route-and-zone.pkl').write_bytes(pickle.dumps([newrow],protocol=5));(out/'proposed-discrete.pkl').write_bytes((base/'proposed-discrete.pkl').read_bytes());r=json.loads((base/'receipt.json').read_bytes());r.update({'verdict':'CORE_WIDER_ONLY_NEW_OWNED_IN2_ENVELOPE_NOMINATION_ALL_GATES_OPEN','old_route_receipt_sha256':sha(base/'receipt.json'),'exact_legal_region_sha256':sha(base/'In2.Cu-legal.wkb'),'old_physical_WKB_sha256':digest(q['shape']),'new_physical_WKB_sha256':digest(physical),'old_intended_WKB_sha256':digest(q['zone_outline_shape']),'new_intended_WKB_sha256':digest(native),'old_actual_physical_area_mm2':q['shape'].area,'new_actual_physical_area_mm2':physical.area,'old_route_core_and_ordinary_barrel_geometries_unchanged':True,'new_nominal_envelope_radius_mm':2.,'full_CORE_0_8A_IO3_2A_voltages_preserved':True,'new_affected_FAG_return_notch_all77_source_native_guard_body_reference_full_current_mesh':'OPEN','only_generated_old_plane_tags_replayed_WKB_exact':replays,'failed_R102_overlay_without_tag_replay_rejected_before_model':True})
 r['routes'][0]['physical_WKB_sha256']=digest(physical);(out/'receipt.json').write_text(json.dumps(r,indent=1)+'\n');print('R103_CORE_NEW_ENVELOPE_ONLY',q['shape'].area,physical.area,sha(out/'receipt.json'),digest(physical),flush=True)
if __name__=='__main__':main()
