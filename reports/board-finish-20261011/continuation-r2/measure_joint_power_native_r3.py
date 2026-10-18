"""Run the established full native measurement on an API-passed joint clone.

The existing queued slot wrapper, uncapped partitions, matching source export,
all-baseline guards and DRC options are retained exactly. No adoption is made.
"""
import hashlib,json,runpy,sys
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    assert len(sys.argv)==2,'API-passed stage directory'
    stage=Path(sys.argv[1]).resolve();assert stage.is_relative_to(H)
    receipt=json.loads((stage/'receipt.json').read_bytes())
    verdict='PASS_JOINT_POWER_SOURCE_ALL_CU_ALL_NEW_ZONES_API_ONLY'
    assert receipt['verdict']==verdict
    candidate=stage/'copy/board.kicad_pcb';assert sha(candidate)==receipt['candidate_sha256']
    source=H/'measure_field_power_native_backend_r1.py'
    target=H/('measure_joint_power_backend_r3_'+stage.name.replace('-','_')+'.py')
    assert not target.exists() and not (stage/'measure').exists()
    code=source.read_text(encoding='utf-8')
    replacements={"STAGE=HERE/'field-power-native-trial-r1';OUT=STAGE/'measure'":"STAGE=Path("+repr(str(stage))+");OUT=STAGE/'measure'","PASS_SOURCE_NATIVE_API_26_POSES_68_VIAS_AND_FIELD_ZONES_WITH_PG_AREA":verdict,"candidate=STAGE/'field-power-native-trial.kicad_pcb'":"candidate=STAGE/'copy/board.kicad_pcb'"}
    for old,new in replacements.items():
        assert code.count(old)==1,old
        code=code.replace(old,new)
    anchor="    baselines={\n";assert code.count(anchor)==1
    added="      'dc936':(HERE/'field-power-native-trial-r1/field-power-native-trial.kicad_pcb',HERE/'field-power-native-trial-r1/measure/partitions.json'),\n"
    code=code.replace(anchor,anchor+added)
    postfill=stage/'native-postfill-via-obligations.json'
    assert sha(postfill)==receipt['native_postfill_via_obligations_sha256']
    actual_helper=H/'native_final_partitions_contract_r2.py'
    original_step=Path('Z:/pcb-runs/claude-finish/tools/step_measure.sh')
    step=stage/'step_measure_all_native_r3.sh';assert not step.exists()
    ss=original_step.read_text();needle='"$T/net_partitions.py"'
    replacement='"'+actual_helper.resolve().as_posix()+'" "Z:/pcb-runs/claude-finish/tools/net_partitions.py" "'+postfill.resolve().as_posix()+'"'
    assert ss.count(needle)==1;ss=ss.replace(needle,replacement);step.write_text(ss,newline='\n')
    a="    step=Path('Z:/pcb-runs/claude-finish/tools/step_measure.sh')"
    assert code.count(a)==1;code=code.replace(a,"    step=Path("+repr(str(step))+ ")")
    a="    for bp,pp in baselines.values():pinned.extend([bp,pp])"
    extra="    pinned.extend([Path("+repr(str(actual_helper))+"),Path("+repr(str(postfill))+"),Path("+repr(str(original_step))+")])\n"
    assert code.count(a)==1;code=code.replace(a,extra+a)
    a="    summary=json.loads((OUT/'summary.json').read_bytes());after=json.loads((OUT/'partitions.json').read_bytes())"
    extra="    actual_contract=json.loads((OUT/'actual-full-refill-contract.json').read_bytes())\n    if actual_contract['verdict']!='PASS_ACTUAL_FULL_NATIVE_FILL_ALL_CU_AND_EXPLICIT_FLASH_CONTRACT' or actual_contract['postfill_Cu_or_flash_errors']:raise ValueError('Actual full native Cu/flash contract failed')\n    if actual_contract['candidate_sha256']!=sha(candidate):raise ValueError('Actual full native geometry belongs to a different candidate')\n"
    assert code.count(a)==1;code=code.replace(a,extra+a)
    a="'candidate_sha256':sha(candidate),'summary':summary"
    extra="'candidate_sha256':sha(candidate),'actual_full_refill_contract':actual_contract,'actual_full_refill_contract_sha256':sha(OUT/'actual-full-refill-contract.json'),'actual_full_refill_geometry_sha256':sha(OUT/'actual-full-refill-geometry.json'),'actual_full_refill_via_flashes_sha256':sha(OUT/'actual-full-refill-via-flashes.json'),'summary':summary"
    assert code.count(a)==1;code=code.replace(a,extra)
    compile(code,str(target),'exec')
    target.write_text(code,encoding='utf-8')
    (stage/'measure-backend-derivation.json').write_text(json.dumps({'source_file':str(source),'source_sha256':sha(source),'derived_backend_file':str(target),'derived_backend_sha256':sha(target),'replacements':replacements,'additional_native_baseline':'dc936 uncapped fresh refill partitions','original_source_stem_parity14changed_pads_uncapped_partitions_all_original_relationship_guards_and_DRC_options_retained':True,'existing_queued_slots_only':True,'new_heavy_slots':0,'adopted':False},indent=1)+'\n',encoding='utf-8')
    runpy.run_path(str(target),run_name='__main__')
if __name__=='__main__':main()
