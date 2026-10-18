"""Stage exactly the native-roundtripped single-outer fragments as a held candidate."""
import os,sys
sys.dont_write_bytecode=True
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import runpy,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;S=runpy.run_path(str(H/'restage_CORE69_DIR7_negative_on_stage3_r2.py'));K=S['K'];SOURCE=S['SOURCE']
PROBE=H/'CORE60-single-outer-native-roundtrip-r2';PRIOR=H/'coupled-CORE60-preserved-fragments-stage3-candidate-r1';OUT=H/'coupled-CORE60-single-outer-stage3-native-candidate-r2'
UID='60c95fa7-e6df-530f-a3d3-00d3f96e46bc';LG=S['LG']
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
digest=lambda b:hashlib.sha256(b).hexdigest()
def write(n,v):
    f=OUT/n;f.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8');return sha(f)
def main():
    assert not OUT.exists();assert sha(SOURCE)==S['EXPECTED'];d=json.loads((PROBE/'input.json').read_bytes());rr=json.loads((PROBE/'native-roundtrip-receipt.json').read_bytes());prior=json.loads((PRIOR/'receipt.json').read_bytes())
    assert rr['status']=='ALL_TWO_SINGLE_OUTER_CORE60_NATIVE_INTEGER_CONTOURS_HOLE_OWNERSHIP_LOAD_SAVE_RELOAD_PASS_NO_FILL'
    assert sha(rr['native_saved_output'])==rr['native_saved_output_SHA256']and rr['all_Cu_cache_empty_before_after']
    raw=SOURCE.read_bytes();a=K.C.inventory(raw);native=K.C.inventory(Path(rr['native_saved_output']).read_bytes());child=d['deterministic_child_UUID']
    assert set(native[3])=={UID,child}and child not in a[3]
    for u in(UID,child):
        q=native[3][u]if u==UID else native[3][u].replace(('(uuid "'+child+'")').encode(),('(uuid "'+UID+'")').encode(),1)
        assert S['profile'](q)==S['profile'](a[3][UID])
        assert len(S['polys'](native[3][u]))==1
    result=raw.replace(a[3][UID],native[3][UID]+native[3][child],1);b=K.C.inventory(result)
    assert set(b[3])==set(a[3])|{child}and a[0]==b[0]and a[2]==b[2]
    assert all(b[3][u]==v for u,v in a[3].items()if u!=UID)and b[3][LG]==a[3][LG]
    OUT.mkdir();(OUT/'candidate').mkdir();board=OUT/'candidate/board.kicad_pcb';board.write_bytes(result);ops=[]
    oldfile=OUT/(UID+'-exact-stage3-before.zone-chunk');oldfile.write_bytes(a[3][UID])
    for i,u in enumerate((UID,child)):
        f=OUT/(u+'-native-roundtripped-after.zone-chunk');f.write_bytes(native[3][u]);ops.append({'action':'replace_exact_owned_zone'if i==0 else'add_deterministic_same_profile_child_zone','UUID':u,'family_original_UUID':UID,'file':str(f),'SHA256':sha(f),'before_file':str(oldfile)if i==0 else None,'before_SHA256':sha(oldfile)if i==0 else None,'physical_native_intent_fragment':prior['operations'][0]['all_retained_real_intent_fragments'][i],'old_profile_after_child_UUID_mapping_exact_numeric':True,'one_outer_zero_holes_native_load_save_reload_proven':True,'stale_owned_fill_cache_cleared_not_credited_as_actual':True})
    manifest=write('reviewable-native-negative-packet.json',{'status':'REAL_NATIVE_SINGLE_OUTER_NEGATIVE_FAMILY_PACKET_ACTUAL_AFTER_CURRENT_REFERENCE_OPEN','baseline':str(SOURCE),'baseline_SHA256':sha(SOURCE),'candidate':str(board),'candidate_SHA256':sha(board),'operations':ops,'all_other_original_native_chunks_header_tail_exact':True,'new_child_zone_count':1,'original_CORE60_UUID_retained_on_largest_real_piece':True,'all_real_fragments_preserved_no_area_discard_or_annulus_caps':True,'aggregate_intent_strict_negative_subset_per_edge_proof':str(PRIOR/'per-component-per-edge-exact-native-IU-subset-proof.json'),'aggregate_intent_strict_negative_subset_per_edge_proof_SHA256':sha(PRIOR/'per-component-per-edge-exact-native-IU-subset-proof.json'),'native_roundtrip_receipt_SHA256':sha(PROBE/'native-roundtrip-receipt.json'),'whole_LG_source_zone_chunk_SHA256':digest(a[3][LG]),'whole_LG_source_zone_literal_retained':True,'native_load_save_roundtrip_is_only_isolated_fixture_not_full_CPP_fill':True,'CORE69_other_packet_not_included':True,'adopted':False})
    retention=H/'CORE1V2-conservative-whole-record-retention-r1/receipt.json';rp=json.loads(retention.read_bytes())
    rec={'status':'NATIVE_ROUNDTRIPPED_TWO_ZONE_CORE60_NEGATIVE_FAMILY_STAGE3_CANDIDATE_ALL_ACTUAL_AFTER_CURRENT_REFERENCE_GATES_OPEN','manifest_SHA256':manifest,'candidate_SHA256':sha(board),'operations':ops,'cut_guard_IU':prior['operations'][0]['native_cut_guard_IU'],'source_backed_guard_terms_IU':prior['source_backed_guard_terms_IU'],'explicit_owned_negative_region':prior['operations'][0]['removed_native_intent'],'explicit_sub_nm_inward_vertex_snaps_and_oblique_edge_negative_tapers':prior['explicit_inward_serialization_snaps_or_reserves'],'no_claim_negative_region_stays_strictly_inside_rectangular_cutters':True,'old_actual_CORE_host_source_contacts_partitions_scope':rp['trials'][1],'old_actual_CORE_host_receipt_SHA256':sha(retention),'old_actual_host_retention_is_not_stage3_new_native_physical_pass':True,'source_ground_reference_authority':'Original LG In4 c1d27 intent/profile untouched; no GND fill fabricated or credited','coverage':'CORE60 shadows at DIR7 components1/2 and RGB_DRIVER_18 component0 only; fresh native fill must demonstrate any actual gain','fresh_CPP_fill_all9sources_all_original_physical_partitions_directcontacts_allbank_oldbodies_positivepours_fullsignalbody_masks_actual109rules':'OPEN_REQUIRED','CORE_signed_load_current_IR_minwidth_voltage_drop_thermal_barrel':'OPEN_REQUIRED','all433_parent_reference_failures':'HELD_NO_CLOSURE_CLAIM','held_failed_multiple_outer_packet':str(PRIOR),'held_multiple_outer_native_parser_observation_SHA256':sha(PROBE/'held-legacy-multiple-polygon-native-parser-observation.json'),'adopted':False,'input_SHA256':{str(f):sha(f)for f in(Path(__file__),SOURCE,PROBE/'input.json',PROBE/'native-roundtrip-receipt.json',Path(rr['native_saved_output']),PRIOR/'receipt.json',PRIOR/'per-component-per-edge-exact-native-IU-subset-proof.json',retention)}}
    write('receipt.json',rec);assert sha(SOURCE)==S['EXPECTED'];print(json.dumps({'candidate_SHA256':sha(board),'manifest_SHA256':manifest,'receipt_SHA256':sha(OUT/'receipt.json'),'child_UUID':child}))
if __name__=='__main__':main()
