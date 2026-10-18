"""Distinguish exact physical In2 transport from missing rooted reference."""
import sys,json,pickle,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import construct_di6_direct_source_escape_r5 as K
import tri_route as T
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
C=A.C;NET='/motherboard_di/DI15_LOGIC'
def main():
 started=time.monotonic();out=HERE/'di15-In2-physical-reference-diagnostic-r48.json';assert not out.exists();A.read(__file__)
 rp=HERE/'di15-hybrid-transport-nomination-r44.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='1f957becfd819b46b14075aff7aa62e676302cb27db62cfa2b2c2004d4101d09';raw=A.read(r['saved_local_geometry']);assert C.sha(raw)==r['saved_local_geometry_sha256'];physical=pickle.loads(raw)
 rp46=HERE/'di15-In2-three-segment-nomination-r46.json';r46=json.loads(A.read(rp46));assert C.sha(A.read(rp46))=='24b6078c1944cd8723393eaa730fa1697b835833b0ce8c53271fab297f47a63b';rr=A.read(r46['saved_local_geometry']);assert C.sha(rr)==r46['saved_local_geometry_sha256'];strict=pickle.loads(rr);free=physical['free'];via=strict['via'];refs=strict['refs'];src=strict['sourcepad'];dst=strict['targetpad'];sp=K.sites(src.buffer(-.075).intersection(free[NET,'F.Cu']),list(src.centroid.coords)[0],1)[0]['at_mm'];dp=K.sites(dst.buffer(-.075).intersection(free[NET,'F.Cu']),list(dst.centroid.coords)[0],1)[0]['at_mm'];sf=unary_union([p for p in K.pieces(free[NET,'F.Cu']) if p.covers(Point(sp))]);df=unary_union([p for p in K.pieces(free[NET,'F.Cu']) if p.covers(Point(dp))]);sr=via[NET].intersection(sf).intersection(Point(src.centroid).buffer(5,quad_segs=128));dr=via[NET].intersection(df).intersection(Point(dst.centroid).buffer(5,quad_segs=128));components=[];nomination=[]
 for i,part in enumerate(K.pieces(free[NET,'In2.Cu'])):
  a=sr.intersection(part);b=dr.intersection(part)
  if a.is_empty and b.is_empty:continue
  row={'component':i,'source_region_mm2':a.area,'target_region_mm2':b.area,'physical_transport_common':not a.is_empty and not b.is_empty};components.append(row)
  if a.is_empty or b.is_empty:continue
  sa=K.sites(a,[118.45,90.75],4);sb=K.sites(b,[131.25,112.35],4)
  for qa in sa[:2]:
   for qb in sb[:2]:
    pts,search=T.route(part,tuple(qa['at_mm']),tuple(qb['at_mm']));pts=[[round(x,6),round(y,6)] for x,y in pts]
    if len(pts)<2:continue
    body=unary_union([A.shape({'kind':'segment','a':x,'b':y,'w':.2}) for x,y in zip(pts,pts[1:])]);gap=body.difference(refs['In2.Cu']);p=HERE/('di15-In2-r48-reference-gap-'+str(len(nomination))+'.wkb');p.write_bytes(gap.wkb);newIn3=unary_union([z['shape'] for z in physical['reservation_shapes'] if z['layer']=='In3.Cu']);nomination.append({'signal_sites':[qa['at_mm'],qb['at_mm']],'In2_points_mm':pts,'width_mm':.2,'length_mm':LineString(pts).length,'full_body_old_rooted_In1_reference_gap_mm2':gap.area,'reference_gap_WKB_path':str(p),'reference_gap_WKB_sha256':C.sha(gap.wkb),'gap_bounds_mm':gap.bounds if not gap.is_empty else None,'R18_In3_shape_overlap_mm2_nomination_only':newIn3.intersection(gap).area,'R18_In3_uncovered_gap_mm2_nomination_only':gap.difference(newIn3).area,'R18_no_reference_credit':True,'search':search})
 result={'verdict':'DI15_PHYSICAL_IN2_REFERENCE_CORRIDOR_DIAGNOSED' if nomination else'DI15_PHYSICAL_IN2_TRANSPORT_BARRIER_DIAGNOSED','R44_sha256':C.sha(A.read(rp)),'R46_sha256':C.sha(A.read(rp46)),'current_ROOT_R11_model_sha256':r['exact_current_ROOT_R11_model_sha256'],'R18_hard_snapshot_sha256':r['LG_R18_hard_snapshot_sha256'],'components':components,'physical_paths_reference_not_qualified':nomination,'current_source_contact_return_current_r06_r07_native_DRC_SI':'OPEN','strict_max_three_layer_segments':True,'all_current_FAULT9_DI6_oldCu_and_source_poses_preserved':True,'native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(result,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':result['verdict'],'components':components,'paths':nomination}),flush=True)
if __name__=='__main__':main()
