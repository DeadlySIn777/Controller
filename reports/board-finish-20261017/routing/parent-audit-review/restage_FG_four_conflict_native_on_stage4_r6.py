"""Restage owned FG negative boundary only; immutable-path host proof is conditional."""
import os,sys
sys.dont_write_bytecode=True
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
from pathlib import Path
import runpy,json,hashlib
from shapely import from_wkb
H=Path(__file__).resolve().parent;ROOT=H.parents[3];S=runpy.run_path(str(H/'restage_CORE69_DIR7_negative_on_stage3_r2.py'));K=S['K'];R=S['R']
OLD=H/'owned-FG-negative-four-conflicts-intent-only-r4';PROOF=H/'FG-local-immutable-path-retention-r3';SOURCE=ROOT/'reports/board-finish-20261017/combined-route-stage-r4/native/board.kicad_pcb';OUT=H/'FG-four-conflict-stage4-native-packet-r6';UID='ff5ffe1e-111b-5951-957a-dfd8894ca90c'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
digest=lambda b:hashlib.sha256(b).hexdigest()
def put(n,v):
 f=OUT/n;f.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8');return sha(f)
def main():
 assert not OUT.exists();expected='ce8aa2cd5bb9c2128733618d5241a10acebdd637e4a0b5f726fea40801444c55';assert sha(SOURCE)==expected
 rec=json.loads((OLD/'receipt.json').read_bytes());op=rec['trials'][0];proposed=Path(op['chunk_file']);assert sha(proposed)==op['chunk_SHA256']
 proof=json.loads((PROOF/'receipt.json').read_bytes());assert proof['old_retained_physical_layer_keys']==808
 raw=SOURCE.read_bytes();a=K.C.inventory(raw);old=a[3][UID];newproposal=proposed.read_bytes();before=S['shape'](old);after=S['shape'](newproposal)
 assert S['profile'](old)==S['profile'](newproposal)
 bound=from_wkb((OLD/'guard-600001-after-intended.wkb').read_bytes());assert S['canonical_ring'](after)==S['canonical_ring'](R['integer_shape'](bound))
 from shapely.geometry import Polygon
 coords=[]
 for xy in after.exterior.coords:
  if not coords or xy!=coords[-1]:coords.append(xy)
 assert not after.interiors
 exact=S['detailed_subset'](before,Polygon(coords));exact['zero_length_native_edges_trivially_inside_ignored_for_predicate_only']=len(after.exterior.coords)-len(coords)
 oldspans=S['polys'](old);newspans=S['polys'](newproposal);assert len(oldspans)==len(newspans)==1
 lo,hi,oldpolygon=oldspans[0];newpolygon=newspans[0][2];new=old[:lo]+newpolygon+old[hi:]
 assert S['literal_nonpolygon'](old)==S['literal_nonpolygon'](new)
 result=raw.replace(old,new,1);b=K.C.inventory(result);assert set(a[3])==set(b[3])and a[0]==b[0]and a[2]==b[2]
 assert all(b[3][u]==v for u,v in a[3].items()if u!=UID)
 OUT.mkdir();(OUT/'candidate').mkdir();board=OUT/'candidate/board.kicad_pcb';board.write_bytes(result)
 for n,data in(('exact-stage4-before.zone-chunk',old),('exact-stage4-after.zone-chunk',new),('exact-stage4-before.polygon-chunk',oldpolygon),('exact-stage4-after.polygon-chunk',newpolygon)):(OUT/n).write_bytes(data)
 exactsha=put('per-edge-native-IU-negative-subset-proof.json',exact)
 operation={'action':'replace_exact_native_polygon_subchunk_in_same_UUID_zone','UUID':UID,'old_zone_chunk_file':str(OUT/'exact-stage4-before.zone-chunk'),'old_zone_chunk_SHA256':digest(old),'new_zone_chunk_file':str(OUT/'exact-stage4-after.zone-chunk'),'new_zone_chunk_SHA256':digest(new),'old_native_polygon_byte_guard_SHA256':digest(oldpolygon),'new_native_polygon_SHA256':digest(newpolygon),'all_current_zone_nonpolygon_bytes_including_stale_fills_retained':True,'all_original_profile_name_priority_UUID_net_layer_island_minwidth_parameters_exact':True,'strict_native_IU_negative_subset_per_edge_proof_SHA256':exactsha,'native_guard_mm':op['guard_mm'],'raw_negative_scope':op['explicit_negative']}
 mf=put('reviewable-native-negative-packet.json',{'status':'REAL_FG_FOUR_CONFLICT_STAGE4_NEGATIVE_ONLY_PACKET_CONDITIONAL_HOST_GRAPH_PASS_ALL_NATIVE_CURRENT_REFERENCE_OPEN','baseline':str(SOURCE),'baseline_SHA256':expected,'candidate':str(board),'candidate_SHA256':sha(board),'operations':[operation],'all_other_native_chunks_header_tail_exact':True,'conditional_old_R299_808_key_immutable_path_proof_SHA256':sha(PROOF/'receipt.json'),'exact_immutable_path_endpoints_and_segments_SHA256':sha(PROOF/'exact-interior-immutable-Cu-path-and-positive-endpoint-proof.json'),'actual_stage4_or_new_native_physical_graph_reference_current_pass':False,'adopted':False})
 put('receipt.json',{'status':'REAL_STAGE4_NEGATIVE_FG_BOUNDARY_WITH_EXACT_NATIVE_SUBSET_AND_CONDITIONAL_IMMUTABLE_R299_PATH_PROOF_ALL_NATIVE_AFTER_OPEN','manifest_SHA256':mf,'candidate_SHA256':sha(board),'operation':operation,'host_conditional_808_partition_retention':proof,'no_projected_fill_or_ground_cap_created_or_credited':True,'scope':'Only four original LG retained raw-loss tracks942659fe/028ef3d3/2598f69f/f9b50d70; neither oldref472 nor native-withdrawal433 nor any new reference gain is closed','fresh_native_CPP_all9sources_allphysicalgroups_contacts_masks_actual109rules_allbank_oldbody_positivepour_fullsignalbody':'OPEN_REQUIRED','FG_current_source_load_IR_minwidth_thermal_barrel_all_inherited_power_reference_and_voltage_budgets':'OPEN_REQUIRED','native_jobs':0,'adopted':False,'input_SHA256':{str(f):sha(f)for f in(Path(__file__),SOURCE,OLD/'receipt.json',proposed,OLD/'guard-600001-after-intended.wkb',PROOF/'receipt.json',PROOF/'exact-interior-immutable-Cu-path-and-positive-endpoint-proof.json')}})
 assert sha(SOURCE)==expected;print(json.dumps({'manifest_SHA256':mf,'candidate_SHA256':sha(board),'receipt_SHA256':sha(OUT/'receipt.json')}))
if __name__=='__main__':main()
