"""Derive transparent R20 auditor for R28 on the actual full R299 cache."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
H=ROOT/'reports/board-finish-20261011/continuation-r2/coupled-recovery'
CACHE=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
PARENT=H/'audit_AO1_MON3_VREF_b177_5V_source_complete_r20.generated.py'
OUT=HERE/'AO1-R28-actual-full-R299-requalification-r1'
SCRIPT=HERE/'audit_AO1_R28_actual_full_R299_r1.generated.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    assert not SCRIPT.exists() and not OUT.exists()
    original=PARENT.read_text()
    assert 'def main()' in original and "if __name__=='__main__':main()" in original
    changes=[]
    def change(old,new):
        nonlocal original
        assert original.count(old)==1,(old,original.count(old))
        original=original.replace(old,new)
        changes.append({'old':old,'new':new})
    change('from pathlib import Path\nimport sys,json,pickle,hashlib,time,math,copy',
           "from pathlib import Path\nimport os\nfor variable in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[variable]='2'\nimport psutil\npsutil.Process().cpu_affinity(list(range(16,28)))\nimport sys,json,pickle,hashlib,time,math,copy")
    change('H=Path(__file__).resolve().parent;ROOT=H.parent',f'H=Path({str(H)!r});ROOT=H.parent')
    change("OUT=H/'AO1-MON3-VREF-b177-5V-source-complete-independent-host-audit-r20'",f'OUT=Path({str(OUT)!r})')
    change("ROOT/'field-power/R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763/actual-full-R157-before-model.pkl','dbeba66691d45ee12206f77e5060b4c845681014d19b3d9e633e9aed08a2b0c2'",f"Path({str(CACHE/'actual-combined-full-after-model.pkl')!r}),{sha(CACHE/'actual-combined-full-after-model.pkl')!r}")
    change("bp.parent/'actual-full-R157-before-all-net-groups.pkl','d808a9bbe54bb24d6232baf4bddddb260db7a82a891c6b50ca6355ed79e6482a'",f"bp.parent/'actual-combined-full-after-all-net-groups.pkl',{sha(CACHE/'actual-combined-full-after-all-net-groups.pkl')!r}")
    old="nt=p['tracks'];nv=p['vias'];removed=set(p['deleted_original_chunks']);assert len(removed)==4 and len(nt)==14 and len(nv)==2"
    new="gp=pin(H/'AO1-COM-seven-only-NEW-ground-tracks-local-inside-margin-repair-and-widths-r656/only-seven-NEW-COM-ground-tracks-inside-margin-repaired-widths-NOMINEE.pkl','cb36851a8df37c5e197cea6c8a4de7720ed7e8ec19543ba9a03a5c3b17f1b1b3');ground_packet=pickle.loads(gp.read_bytes());assert not ground_packet['vias'] and not ground_packet['original_deletes'];p={**p,'tracks':p['tracks']+ground_packet['tracks'],'exact_new_chunks':{**p['exact_new_chunks'],**ground_packet['exact_new_chunks']}};nt=p['tracks'];nv=p['vias'];removed=set(p['deleted_original_chunks']);assert len(removed)==4 and len(nt)==21 and len(nv)==2"
    change(old,new)
    change("'exact_full_R753_AFTER_native_source_fills_and_all_new_actual_masks':'OPEN; host scope anchored actual FULL R157 before only'","'exact_full_R753_AFTER_native_source_fills_and_all_new_actual_masks':'ACTUAL_FULL_R299_BEFORE; prospective R28 additions still require native AFTER'")
    change("'SCOPED_AO1_MON3_VREF_b177_5V_ALL_HOST_SOURCE_CONTACT_REFERENCE_PASS_FULL_CURRENT_NATIVE_ANALOG_SI_OPEN'if passed else'SCOPED_AO1_MON3_VREF_b177_5V_RAW_HOST_REPAIR_REQUIRED'","'R28_ACTUAL_FULL_R299_HOST_SOURCE_CONTACT_REFERENCE_PASS_NATIVE_CURRENT_ANALOG_SI_OPEN'if passed else'R28_ACTUAL_FULL_R299_RAW_HOST_REPAIR_REQUIRED'")
    SCRIPT.write_text(original)
    receipt={'derivation':'R20 exact audit with R28 seven-ground additive packet and actual full R299 model/groups. No other implementation or gate changed.','original_script':str(PARENT),'original_script_sha256':sha(PARENT),'derived_script':str(SCRIPT),'derived_script_sha256':sha(SCRIPT),'actual_graph_cache_receipt':str(CACHE/'actual-graph-cache-receipt.json'),'actual_graph_cache_receipt_sha256':sha(CACHE/'actual-graph-cache-receipt.json'),'exact_edits':changes,'new_tracks':21,'new_vias':2,'retired_original_tracks':4,'native_jobs':0,'board_written':False,'adopted':False}
    (HERE/'AO1-R28-actual-full-R299-audit-derivation-r1.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'script':str(SCRIPT),'sha256':sha(SCRIPT),'edits':len(changes)}))

if __name__=='__main__':main()
