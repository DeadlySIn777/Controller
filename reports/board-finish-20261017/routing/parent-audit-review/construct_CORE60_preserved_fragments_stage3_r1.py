"""Keep every real native intent fragment when opening guarded LG return windows."""
import os,sys
sys.dont_write_bytecode=True
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
from pathlib import Path
import json,hashlib,time,runpy,math
from fractions import Fraction as Q
from shapely import from_wkb
from shapely.geometry import box
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3]
S=runpy.run_path(str(HERE/'restage_CORE69_DIR7_negative_on_stage3_r2.py'))
R=S['R'];K=S['K'];SOURCE=S['SOURCE'];EXPECTED=S['EXPECTED'];LG=S['LG']
UID='60c95fa7-e6df-530f-a3d3-00d3f96e46bc'
OUT=HERE/'coupled-CORE60-preserved-fragments-stage3-candidate-r1'
WITNESSES=['6e8d51b6-4181-4dc1-bfc7-c0482d7736b9','b95e2244-59ed-40df-b39a-7f9a04a8ac8d']
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
digest=lambda v:hashlib.sha256(v).hexdigest()
def write(n,v):
    p=OUT/n;p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8');return sha(p)
def main():
    t=time.monotonic();assert not OUT.exists();assert sha(SOURCE)==EXPECTED
    raw=SOURCE.read_bytes();a=K.C.inventory(raw);old=a[3][UID];before=S['shape'](old)
    seed=K.C.inventory(R['SOURCE'].read_bytes())[3][UID]
    assert S['canonical_ring'](before)==S['canonical_ring'](S['shape'](seed))and S['profile'](old)==S['profile'](seed)
    guard=375001;cutters=[];descriptors=[];inputs=[Path(__file__),HERE/'restage_CORE69_DIR7_negative_on_stage3_r2.py',HERE/'construct_coupled_CORE1V2_DIR7_return_window_r2.py',SOURCE,R['SOURCE']]
    for uid in WITNESSES:
        f=R['P']/('oldref-'+uid+'.wkb');inputs.append(f)
        for i,part in enumerate(R['parts'](from_wkb(f.read_bytes()))):
            b=part.bounds;bounds=[math.floor(Q(b[0])*1000000)-guard,math.floor(Q(b[1])*1000000)-guard,math.ceil(Q(b[2])*1000000)+guard,math.ceil(Q(b[3])*1000000)+guard]
            cutters.append(box(*bounds));descriptors.append({'track_UUID':uid,'component':i,'raw_WKB_SHA256':sha(f),'raw_bounds_mm':list(b),'outward_native_IU_cut_bounds':bounds})
    cut=unary_union(cutters);after,snaps=R['snap_native_negative'](before.difference(cut),before,cut);pieces=R['parts'](after)
    assert len(pieces)==2 and all(not p.interiors for p in pieces)
    assert after.difference(before).is_empty and after.relate(cut)[0]=='F'
    # No fragment is discarded or silently merged into another electrical role.
    proofs=[S['detailed_subset'](before,part)for part in pieces]
    oldspans=S['polys'](old);assert len(oldspans)==1;lo,hi,oldpolygon=oldspans[0]
    # Adjacent closed/open S-expressions are unambiguous, and avoid inserting
    # whitespace outside the replacement polygon expressions.
    newpolygons=b''.join(R['render_ring'](part.exterior).strip()for part in pieces)
    new=old[:lo]+newpolygons+old[hi:]
    assert S['literal_nonpolygon'](old)==S['literal_nonpolygon'](new)
    assert S['profile'](old)==S['profile'](new)
    assert len(S['polys'](new))==2
    result=raw.replace(old,new,1);b=K.C.inventory(result)
    assert set(a[3])==set(b[3])and a[0]==b[0]and a[2]==b[2]
    assert all(b[3][u]==v for u,v in a[3].items()if u!=UID)and b[3][LG]==a[3][LG]
    retention=HERE/'CORE1V2-conservative-whole-record-retention-r1/receipt.json';inputs.append(retention);rr=json.loads(retention.read_bytes());trial=rr['trials'][1]
    assert UID in trial['removed_native_zone_actual_fill_record_UUIDs']and not trial['old_CORE1V2_group_relationship_losses']and not trial['old_CORE1V2_source_layer_key_losses']and not trial['old_CORE1V2_direct_fill_contact_losses']
    OUT.mkdir();(OUT/'candidate').mkdir();board=OUT/'candidate/board.kicad_pcb';board.write_bytes(result)
    for n,v in(('exact-stage3-before.zone-chunk',old),('exact-stage3-after.zone-chunk',new),('exact-stage3-before-native.polygon-chunk',oldpolygon),('exact-stage3-after-two-native-polygons.chunk',newpolygons),('exact-negative-native-IU-cutters.wkb',cut.wkb),('exact-retained-fragments-native-IU.wkb',after.wkb),('exact-owned-negative-native-IU.wkb',before.difference(after).wkb)):(OUT/n).write_bytes(v)
    proofsha=write('per-component-per-edge-exact-native-IU-subset-proof.json',{'before_single_no_hole_native_polygon':True,'all_fragments_kept':True,'components':proofs})
    fragments=[R['info'](v)for v in pieces]
    op={'action':'replace_exact_native_polygon_subchunk_with_two_preserved_same_UUID_outlines','UUID':UID,'old_zone_chunk_file':str(OUT/'exact-stage3-before.zone-chunk'),'old_zone_chunk_SHA256':digest(old),'new_zone_chunk_file':str(OUT/'exact-stage3-after.zone-chunk'),'new_zone_chunk_SHA256':digest(new),'old_polygon_byte_guard_SHA256':digest(oldpolygon),'new_polygon_subchunks_SHA256':digest(newpolygons),'all_current_zone_nonpolygon_bytes_including_stale_fill_retained':True,'same_profile_name_UUID_net_layer_priority_island_parameters_exact':True,'negative_only_no_new_Cu':True,'all_retained_real_intent_fragments':fragments,'no_small_fragment_discarded':True,'removed_native_intent':R['info'](before.difference(after)),'exact_per_edge_subset_proof_SHA256':proofsha,'native_cut_guard_IU':guard,'native_parser_support_for_multiple_outlines':'PENDING_READ_ONLY_API_PROBE'}
    mf=write('reviewable-native-negative-packet.json',{'status':'HOST_EXACT_NEGATIVE_PRESERVED_FRAGMENTS_PACKET_NATIVE_PARSER_AND_AFTER_REQUIRED','baseline':str(SOURCE),'baseline_SHA256':EXPECTED,'candidate':str(board),'candidate_SHA256':sha(board),'operations':[op],'all_other_native_chunks_header_tail_exact':True,'LG_source_entire_chunk_SHA256':digest(a[3][LG]),'all_LG_source_intent_and_profile_literal_retained':True,'CORE69_other_negative_packet_not_included':True,'adopted':False})
    write('receipt.json',{'status':'REAL_CORE60_NEGATIVE_INTENT_WITH_BOTH_REAL_FRAGMENTS_KEPT_HOST_PRECHECK_ONLY','manifest_SHA256':mf,'candidate_SHA256':sha(board),'operations':[op],'source_backed_guard_terms_IU':{'actual_LG_source_clearance':250000,'half_actual_LG_minimum_fill_width':100000,'unchanged_planning_margin':25000,'native_construction_guard':1},'windows':descriptors,'explicit_inward_serialization_snaps_or_reserves':snaps,'CORE_host_stronger_entire_record_removal_scope':trial,'stronger_entire_record_removal_receipt_SHA256':sha(retention),'host_retention_is_not_a_stage3_or_new_native_physical_pass':True,'native_parser_multiple_outline_support':'OPEN_REQUIRED','fresh_native_CPP_all9source_relationships_directcontacts_oldbody_positivepour_fullsignalbody_masks_actual109rules':'OPEN_REQUIRED','CORE_load_current_IR_minwidth_voltage_drop_thermal_barrel':'OPEN_REQUIRED','all433_reference_losses':'HELD_NO_CLOSURE_CLAIM','native_fill_save_calls':0,'adopted':False,'input_SHA256':{str(f):sha(f)for f in inputs},'elapsed_seconds':time.monotonic()-t})
    assert sha(SOURCE)==EXPECTED
    print(json.dumps({'candidate_SHA256':sha(board),'manifest_SHA256':mf,'receipt_SHA256':sha(OUT/'receipt.json'),'fragment_areas_mm2':[v['area_mm2']for v in fragments]}))
if __name__=='__main__':main()
