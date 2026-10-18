"""Test continuous saved endpoint regions against exact zero-power-carve transport.

This nomination does not reuse a failed rounded/source reference claim or
qualify saved physical masks against final current/native source geometry.
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
 started=time.monotonic();out=HERE/'di15-zero-power-carve-continuous-regions-r78.json';assert not out.exists();A.read(__file__)
 p76=HERE/'di15-original-boundary-detour-r76.json';r76=json.loads(A.read(p76));assert C.sha(A.read(p76))=='b9b5d7bcf8939e409fb4dc69400a049cd2cb5fdf5d822ddf42c8aeeb6ed3d70c';b76=A.read(r76['saved_geometry']);assert C.sha(b76)==r76['saved_geometry_sha256'];z=pickle.loads(b76);assert r76['owned_positive_planes_only_release_for_nomination']==[]
 p44=HERE/'di15-hybrid-transport-nomination-r44.json';r44=json.loads(A.read(p44));b44=A.read(r44['saved_local_geometry']);assert C.sha(b44)=='6f8cf2264bbec115ac0c3e7b357d41d4a34c7586ee8b74d35b679dd3119af2b7';saved=pickle.loads(b44)
 free=saved['free'];via=saved['via'];src=saved['sourcepad'];dst=saved['targetpad'];attachments=[]
 for pad in(src,dst):
  sp=K.sites(pad.buffer(-.075).intersection(free[NET,'F.Cu']),list(pad.centroid.coords)[0],4)
  f=unary_union([q for q in K.pieces(free[NET,'F.Cu']) if any(q.covers(Point(s['at_mm'])) for s in sp)])
  attachments.append(via[NET].intersection(f).intersection(Point(pad.centroid).buffer(5,quad_segs=128)))
 rows=[];nominees=[]
 for i,part in enumerate(K.pieces(z['allowed_In2_center_region'])):
  a,b=[q.intersection(part) for q in attachments]
  if a.is_empty and b.is_empty:continue
  row={'component':i,'bounds_mm':part.bounds,'source_region_mm2':a.area,'target_region_mm2':b.area,'same_component':not a.is_empty and not b.is_empty};rows.append(row)
  if a.is_empty or b.is_empty:continue
  for sa,sb in zip(K.sites(a,[118.45,90.75],2),K.sites(b,[131.25,112.35],2)):
   pts,search=T.route(part,tuple(sa['at_mm']),tuple(sb['at_mm']));pts=[[round(x,6),round(y,6)] for x,y in pts]
   if len(pts)<2:continue
   body=unary_union([A.shape({'kind':'segment','a':x,'b':y,'w':.2}) for x,y in zip(pts,pts[1:])]);gap=body.difference(z['potential_reference']);nominees.append({'signal_sites':[sa['at_mm'],sb['at_mm']],'In2_points_mm':pts,'width_mm':.2,'length_mm':LineString(pts).length,'potential_full_body_reference_gap_mm2':gap.area,'search':search})
   if gap.is_empty:break
  if nominees:break
 report={'verdict':'DI15_ZERO_POWER_CARVE_CONTINUOUS_PATH_NOMINATED_UNQUALIFIED' if nominees else 'DI15_SAVED_CONTINUOUS_ENDPOINT_REGIONS_SPLIT_WITH_ALL_POWER_HARD','R76_receipt_sha256':C.sha(A.read(p76)),'R76_geometry_sha256':C.sha(b76),'saved_physical_mask_authority_R44_sha256':C.sha(b44),'current_R22_DI6_model_sha256':r76['source_model_sha256'],'source_target_saved_region_areas_mm2':[p.area for p in attachments],'components':rows,'nominees':nominees,'power_planes_released':[],'no_global_impossibility_claim':True,'paired_returns_new_signal_holes_final_actual_source_and_full_body_contact_reference_native_current':'OPEN','max_layer_segments':3,'native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':report['verdict'],'components':rows,'nominees':nominees}),flush=True)
if __name__=='__main__':main()
