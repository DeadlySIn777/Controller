from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
H=ROOT/'reports/board-finish-20261011/continuation-r2/coupled-recovery'
PARENT=H/'audit_AO1_repaired_seven_ground_additions_joint_R20_current_r658.generated.py'
R20=HERE/'AO1-R20-actual-full-R299-requalification-r2/receipt.json'
OUT=HERE/'AO1-R658-ground-actual-full-R299-requalification-r3'
SCRIPT=HERE/'audit_AO1_ground_actual_full_R299_r3.generated.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    assert not SCRIPT.exists() and not OUT.exists()
    result=json.loads(R20.read_text())
    assert result['verdict']=='R20_ACTUAL_FULL_R299_HOST_SOURCE_CONTACT_REFERENCE_PASS_NATIVE_CURRENT_ANALOG_SI_OPEN'
    text=PARENT.read_text();changes=[]
    def change(old,new):
        nonlocal text
        assert text.count(old)==1,(old,text.count(old));text=text.replace(old,new);changes.append({'old':old,'new':new})
    change('from pathlib import Path\nimport sys,json,pickle,hashlib,time,math',"from pathlib import Path\nimport os\nfor variable in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[variable]='2'\nimport psutil\npsutil.Process().cpu_affinity(list(range(16,28)))\nimport sys,json,pickle,hashlib,time,math")
    change('H=Path(__file__).resolve().parent;ROOT=H.parent',f'H=Path({str(H)!r});ROOT=H.parent')
    change("OUT=H/'AO1-R656-seven-GROUND-additions-joint-R20-independent-source-geometry-r658'",f'OUT=Path({str(OUT)!r})')
    change("H/'AO1-MON3-VREF-b177-5V-source-complete-independent-host-audit-r20/receipt.json','8e1213a3a723bf7fd9c006183b9ba90d11e70420ea46bde4e0c268375fda8b58'",f"Path({str(R20)!r}),{sha(R20)!r}")
    change("parent['host_model_file'],'3605d85bb9c672bb2d8dc58b3a6d2c01b01c2e3412978c9941846ee5ad415b72'",f"parent['host_model_file'],{result['host_model_SHA256']!r}")
    change("mp.parent/'AO1-and-local-antipad-all-drilled-after-groups.pkl','4587bd3d6b32ba0cfac8f4c1dfcddd193184ef0bb8049ddac85419a9a9f191de'",f"mp.parent/'AO1-and-local-antipad-all-drilled-after-groups.pkl',{result['groups_SHA256']!r}")
    change("'SEVEN_ADDITIVE_GROUND_TRACKS_TRUE_GEOMETRY_SOURCE_CONTACT_OLDREF_SCOPED_PASS_NATIVE_CURRENT_SI_OPEN'if passed else'SEVEN_ADDITIVE_GROUND_TRACKS_RAW_SCOPE_REPAIR_REQUIRED'","'R658_GROUND_ACTUAL_R299_TRUE_GEOMETRY_SOURCE_CONTACT_OLDREF_PASS_NATIVE_CURRENT_SI_OPEN'if passed else'R658_GROUND_ACTUAL_R299_RAW_SCOPE_REPAIR_REQUIRED'")
    # Bind the loaded project-tool dependency closure before executing the gate.
    hook="""
def run_with_dependency_provenance():
 tool_files={str(Path(m.__file__).resolve()) for m in list(sys.modules.values()) if getattr(m,'__file__',None) and str(Path(m.__file__).resolve()).lower().endswith('.py') and ('controller' in str(Path(m.__file__).resolve()).lower() or 'pcb-runs' in str(Path(m.__file__).resolve()).lower())}
 dependency_sha256={p:sha(p) for p in sorted(tool_files)}
 main()
 assert all(sha(p)==v for p,v in dependency_sha256.items())
 (OUT/'loaded-tool-dependency-provenance.json').write_text(json.dumps({'input_sha256':dependency_sha256,'all_rehashed_after_unchanged':True,'derived_script_sha256':sha(__file__),'native_jobs':0,'adopted':False},indent=2)+'\\n')
"""
    change("if __name__=='__main__':main()",hook+"\nif __name__=='__main__':run_with_dependency_provenance()")
    SCRIPT.write_text(text)
    (HERE/'AO1-ground-actual-full-R299-derivation-r3.json').write_text(json.dumps({'original_script':str(PARENT),'original_script_sha256':sha(PARENT),'derived_script_sha256':sha(SCRIPT),'exact_edits':changes,'parent_R20_receipt_sha256':sha(R20),'scope':'Original R658 SOURCE/drill/foreign-fill/old-reference scope, with actual-full-R299 R20 host context; raw r1 self-reference gap screen retained.'},indent=2)+'\n')
    print(str(SCRIPT))
if __name__=='__main__':main()
