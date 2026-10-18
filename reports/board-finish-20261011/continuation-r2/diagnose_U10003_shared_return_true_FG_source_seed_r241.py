"""Bind the failed direct source seed before nominating any real source bridge."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;source=H/'nominate_U10003_shared_return_actual_source_planes_r240.py';code=source.read_text();at=code.index("seedrows={");prefix=code[:at].replace('nomination-r240','source-seed-diagnosis-r241');exec(compile(prefix,str(source),'exec'))
from shapely.ops import nearest_points
from shapely.geometry import Point
rows=[]
for layer,ref in oldref.items():
 (OUT/(layer+'-actual-J3-source-reference.wkb')).write_bytes(ref.wkb)
 for name,v in [('shared_new',central),('old_A_return',oldret),('previous_unadopted_primary',next(v for v in h['vias']if v['uuid']==central['uuid']))]:
  centre=point(v);near,_=nearest_points(ref,centre);interior=ref.buffer(-.1,quad_segs=128);inside,_=nearest_points(interior,centre);rows.append({'layer':layer,'role':name,'UUID':v['uuid'],'xy_mm':[v['x'],v['y']],'actual_root_layer_key':('via',v['uuid'],layer)in rootkeys,'actual_source_annulus_overlap_mm2':ref.intersection(ann(v)).area,'source_boundary_distance_mm':ref.distance(centre),'nearest_actual_source_boundary_mm':[near.x,near.y],'nearest_100um_source_interior_mm':[inside.x,inside.y]})
result={'verdict':'SHARED_NEW_FG_RETURN_DIRECT_IN1_SOURCE_SEED_FAILED_REAL_SOURCE_BRIDGE_REQUIRED','base_model_sha256':sha(mp),'joint_receipt_sha256':sha(rp),'source_net':FG,'source_root':'J11003.2','actual_source_group_retained_keys':len(rootkeys),'rows':rows,'native_all_hole_source_refs_without_two_failed_FG_plane_records':True,'R240_assertion_failure_no_plane_packet_or_model_emitted':True,'no_union_of_unrooted_annulus_used_as_source_authority':True,'native_jobs':0,'adopted':False,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n');print('R241_SOURCE_SEEDS',json.dumps(rows),sha(OUT/'receipt.json'),flush=True)
