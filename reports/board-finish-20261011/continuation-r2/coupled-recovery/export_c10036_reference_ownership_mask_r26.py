"""Exact scoped mask for peer-owned prospective R41 source feed revision."""
import sys,json,pickle
from pathlib import Path
HERE=Path(__file__).resolve().parent;FP=HERE.parent/'field-power';sys.path.insert(0,str(FP));import contact_layout as L
sys.path.insert(0,str(HERE));import audit_aux_exact_raw as A
from shapely import from_wkb
from shapely.ops import unary_union
def main():
 out=HERE/'c10036-peer-reference-mask-r26.json';assert not out.exists();rp=HERE/'c10036-r25-reference-bridge-recipe-r24.json';r=json.loads(A.read(rp));assert A.C.sha(A.read(rp))=='016762020a735b19c932b4f0dc7a1d36b07854844c207f65aba6965caf438f6e';d=pickle.loads(A.read(HERE/'c10036-joint-reference-bridge-diagnostic-r19.pkl'));rx=json.loads(A.read(HERE/'c10036-r41-reference-interaction-r23.json'));ids={q['native_old_track_uuid'] for q in rx['all_current_B_outer_tracks_prior_rooted_reference_touched_by_R41']}-{ '75409711-7adb-4e55-b9ea-c36978361c51'};rows=[];shapes=[]
 for t in d['g']['tracks']:
  if t['uuid'] not in ids:continue
  body=A.shape({'kind':'segment',**t});covered=body.intersection(d['planes']['In4.Cu']);shapes.append(covered);rows.append({'exact_native_UUID':t['uuid'],'exact_serialized_shape':t,'old_rooted_reference_area_mm2':covered.area,'mask_WKB_sha256':A.C.sha(covered.wkb)})
 zp=Path(r['new_zone_manifest']['geometry_WKB_path']);bridge=from_wkb(A.read(zp));assert A.C.sha(A.read(zp))==r['new_zone_manifest']['geometry_WKB_sha256'];shapes.append(bridge);mask=unary_union(shapes);path=HERE/'c10036-peer-reference-mask-r26.wkb';path.write_bytes(mask.wkb)
 report={'verdict':'EXACT_R25_CURRENT_REFERENCE_PLUS_NEW_C_BRIDGE_MASK_FOR_PROSPECTIVE_MESH_REVISION','source_recipe_SHA256':A.C.sha(A.read(rp)),'new_ground_reference_bridge_manifest':r['new_zone_manifest'],'retained_old_native_power_reference_masks':rows,'combined_mask_WKB_path':str(path),'combined_mask_WKB_sha256':A.C.sha(mask.wkb),'combined_mask_area_mm2':mask.area,'minimum_required_owned_foreign_mesh_body_distance_mm':.275,'mask_expansion_by_peer_required_mm':.275,'R41_native_priority_local_GND_clearance_and_full_final_contact_reference_current_capacity_gates':'OPEN','read_files_sha256':A.READS};out.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps(report),flush=True)
if __name__=='__main__':main()
