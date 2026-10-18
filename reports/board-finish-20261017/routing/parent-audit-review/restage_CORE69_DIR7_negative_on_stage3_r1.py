"""Apply an already-proven exact negative zone chunk to an immutable stage3 copy."""
import os,sys
sys.dont_write_bytecode=True
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
from pathlib import Path
import json,hashlib,time
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3]
OLD=PROJECT/'reports/board-finish-20261011/continuation-r2'
for d in(OLD,OLD/'field-power',OLD/'sbc-power',OLD/'coupled-recovery'):sys.path.insert(0,str(d))
import R157_native_selected_actual_conversion_r673 as N
K=N.K
PACKET=HERE/'coupled-CORE1V2-DIR7-return-window-candidate-r2'
SOURCE=PROJECT/'reports/board-finish-20261017/combined-route-stage-r3/native/board.kicad_pcb'
OUT=HERE/'coupled-CORE1V2-DIR7-stage3-native-candidate-r1'
EXPECTED='653077ad9ca97e6d69f5ad1c2d90bf7bf1f73cf890b6f05ada882ec83552fbca'
UID='69c62b44-c4ad-55f0-bf91-575b93a0b295'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
def main():
    t=time.monotonic();assert not OUT.exists()
    receipt=PACKET/'receipt.json';r=json.loads(receipt.read_bytes());op=r['operations'][0]
    assert r['status']=='REAL_NATIVE_COUPLED_CORE1V2_NEGATIVE_WINDOWS_HOST_RETENTION_PRECHECK_PASS_ACTUAL_REFILL_CURRENT_OPEN'
    assert op['UUID']==UID and len(r['operations'])==1
    old=Path(op['old_chunk_file']);new=Path(op['new_chunk_file'])
    assert sha(old)==op['old_chunk_SHA256']and sha(new)==op['new_chunk_SHA256']
    assert sha(SOURCE)==EXPECTED
    raw=SOURCE.read_bytes();a=K.C.inventory(raw);assert a[3][UID]==old.read_bytes()
    result=raw.replace(old.read_bytes(),new.read_bytes(),1);b=K.C.inventory(result)
    assert set(a[3])==set(b[3]) and a[0]==b[0]and a[2]==b[2]
    assert all(b[3][u]==v for u,v in a[3].items()if u!=UID)
    assert b[3][UID]==new.read_bytes()
    OUT.mkdir();(OUT/'candidate').mkdir();board=OUT/'candidate/board.kicad_pcb';board.write_bytes(result)
    assert sha(SOURCE)==EXPECTED
    out={'status':'REAL_STAGE3_NATIVE_SAME_UUID_NEGATIVE_CHUNK_HOST_PRECHECK_ONLY_NATIVE_REFILL_ALL_PHYSICAL_CURRENT_REFERENCE_GATES_OPEN','input_stage3':str(SOURCE),'input_stage3_SHA256':EXPECTED,'candidate':str(board),'candidate_SHA256':sha(board),'changed_UUIDs':[UID],'unchanged_native_chunk_count':len(a[3])-1,'all_other_native_chunks_header_tail_exact':True,'stage3_source_zone_byteexact_to_R299_packet_before':True,'negative_CORE_native_intent_only_no_ground_cap_or_new_reference_authority':True,'native_cut_guard_IU':r['native_cut_guard_IU'],'exact_native_IU_rational_subset_proof':op['exact_native_IU_rational_subset_proof'],'negative_native_intent_area_mm2':op['explicit_owned_native_intent_removed']['area_mm2'],'scope':r['coverage'],'prior_R299_cache_whole_record_retention_proof_is_not_a_stage3_physical_pass':True,'fresh_native_CPP_fill_all9_sources_all_original_physical_relationships_contacts_oldbody_positivepour_masks_actual109_rules_current_minwidth_IR_thermal_barrel_gates':'OPEN_REQUIRED','all433_parent_reference_losses':'HELD_NO_CLOSURE_CLAIM','native_fill_or_save_calls':0,'adopted':False,'input_SHA256':{str(f):sha(f)for f in(Path(__file__),SOURCE,receipt,old,new)},'elapsed_seconds':time.monotonic()-t}
    (OUT/'receipt.json').write_text(json.dumps(out,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({'candidate_SHA256':sha(board),'receipt_SHA256':sha(OUT/'receipt.json')}))
if __name__=='__main__':main()
