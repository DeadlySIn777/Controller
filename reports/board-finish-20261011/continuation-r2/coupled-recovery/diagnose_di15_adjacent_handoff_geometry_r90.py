"""Check if a concrete adjacent-ground handoff could avoid any power carve.

Union is used for nomination only. Actual per-body source coverage, finite
both-plane annular handoff and fully projected contact/current/native proof
are mandatory before a recipe; union itself supplies no reference credit.
"""
import sys,json,pickle,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import construct_di6_direct_source_escape_r5 as K
import tri_route as T
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
C=A.C;NET='/motherboard_di/DI15_LOGIC'
def main():
 started=time.monotonic();out=HERE/'di15-adjacent-reference-handoff-geometric-nomination-r90.json';assert not out.exists();A.read(__file__);models={};pins={}
 for tag,sha in[(76,'b9b5d7bcf8939e409fb4dc69400a049cd2cb5fdf5d822ddf42c8aeeb6ed3d70c'),(80,'7676af5a9fa3b96e966a378a0edbbdac1711dc3158f14d606a5fe84f1bc4f720')]:
  rp=HERE/f'di15-original-boundary-detour-r{tag}.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))==sha;assert not r['owned_positive_planes_only_release_for_nomination'];raw=A.read(r['saved_geometry']);assert C.sha(raw)==r['saved_geometry_sha256'];models[tag]=pickle.loads(raw);pins[tag]={'receipt_sha256':sha,'geometry_sha256':C.sha(raw)}
 p44=HERE/'di15-hybrid-transport-nomination-r44.json';r44=json.loads(A.read(p44));raw=A.read(r44['saved_local_geometry']);assert C.sha(raw)=='6f8cf2264bbec115ac0c3e7b357d41d4a34c7586ee8b74d35b679dd3119af2b7';saved=pickle.loads(raw);free=saved['free'];attachments=[]
 for pad in(saved['sourcepad'],saved['targetpad']):
  sp=K.sites(pad.buffer(-.075).intersection(free[NET,'F.Cu']),list(pad.centroid.coords)[0],4);f=unary_union([q for q in K.pieces(free[NET,'F.Cu']) if any(q.covers(Point(s['at_mm'])) for s in sp)]);attachments.append(saved['via'][NET].intersection(f).intersection(Point(pad.centroid).buffer(5,quad_segs=128)))
 potential={l:models[t]['potential_reference'] for l,t in[('In1.Cu',76),('In3.Cu',80)]};allowed=models[76]['physical_In2_center_region'].intersection(unary_union(list(potential.values())).buffer(-.105,quad_segs=128));rows=[];nominees=[]
 for i,part in enumerate(K.pieces(allowed)):
  a,b=[p.intersection(part) for p in attachments]
  if a.is_empty and b.is_empty:continue
  row={'component':i,'bounds_mm':part.bounds,'source_region_mm2':a.area,'target_region_mm2':b.area,'geometric_common_nomination_only':not a.is_empty and not b.is_empty};rows.append(row)
  if a.is_empty or b.is_empty:continue
  sa=K.sites(a,[118.45,90.75],1)[0]['at_mm'];sb=K.sites(b,[131.25,112.35],1)[0]['at_mm'];pts,search=T.route(part,tuple(sa),tuple(sb));pts=[[round(x,6),round(y,6)] for x,y in pts]
  if len(pts)<2:continue
  segments=[]
  for p,q in zip(pts,pts[1:]):
   body=A.shape({'kind':'segment','a':p,'b':q,'w':.2});segments.append({'a':p,'b':q,'full_body_missing_by_adjacent_reference_mm2':{l:body.difference(sh).area for l,sh in potential.items()},'missing_by_union_nomination_only_mm2':body.difference(unary_union(list(potential.values()))).area})
  nominees.append({'signal_sites':[sa,sb],'In2_points_mm':pts,'length_mm':LineString(pts).length,'width_mm':.2,'segment_nomination_diagnostics':segments,'search':search});break
 cache=HERE/'di15-adjacent-reference-handoff-r90-geometry.pkl';assert not cache.exists();cache.write_bytes(pickle.dumps({'allowed_In2_center_region':allowed,'potential_reference_by_layer':potential,'models':models,'saved_physical':saved},protocol=5));report={'verdict':'DI15_ZERO_CARVE_ADJACENT_HANDOFF_GEOMETRIC_PATH_ONLY_NOMINATED' if nominees else'DI15_ZERO_CARVE_ADJACENT_HANDOFF_BOUNDED_GEOMETRY_SPLIT','frozen_inputs':pins,'current_R22_DI6_model_sha256':models[76]['current_model_sha256'],'source_target_region_components':rows,'nominees':nominees,'union_grants_no_reference_credit':True,'required_before_recipe':['explicit per-body actual rooted reference coverage and overlap','real finite In1/In3 source annuli at every handoff','exact ordinary all6 handoff return clearance/drill/SMD/contact holes','full current/r06/r07 pad/Cu/contact/neighbour reference','all supply source/current/mesh and actual native'], 'max_signal_layer_segments':3,'power_planes_released':[],'saved_geometry':str(cache),'saved_geometry_sha256':C.sha(cache.read_bytes()),'native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':report['verdict'],'components':rows,'nominees':nominees}),flush=True)
if __name__=='__main__':main()
