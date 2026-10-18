"""Native field-zone refill experiment; final SBC and field completion remain open."""
import hashlib,json,os,runpy,shutil,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
import native_pose_signal_contract as N
C=N.C;STAGE=H/'field-power-native-trial-r1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
    if STAGE.exists():raise ValueError('Fresh field-power native trial required')
    field=H/'field-zone-native-contract-r1/copy/board.kicad_pcb';field_api=H/'field-zone-source-api-r2-bound-hash/receipt.json';field_geo=H/'field-zone-native-contract-r2-layer-sets/receipt.json'
    api=json.loads(field_api.read_bytes());geo=json.loads(field_geo.read_bytes())
    if api['verdict']!='PASS_FIELD_ZONES_SOURCE_API_26_POSES_68_VIAS_23_SMD_MASKS_AND_FIELDS' or not geo['verdict'].startswith('PASS_') or sha(field)!=api['candidate_sha256'] or sha(field)!=geo['candidate_sha256']:raise ValueError('Exact field source/API/geometry gate rejected')
    pg=H/'sbc-power/PG-native-rule-proposal-r7/receipt.json';p=json.loads(pg.read_bytes());area=Path(p['area_chunk_file']);rule=Path(p['rule_file']);scope=H/'pg-native-rule-scope-r1/receipt.json'
    if sha(pg)!='468c0f1ccff701dce7954aa8fc17bd0db884cd3b02b9dbac1d200ce7832fe15c' or sha(area)!=p['area_chunk_sha256'] or sha(rule)!=p['rule_sha256'] or json.loads(scope.read_bytes())['errors']:raise ValueError('Exact scoped PG fine-rule gate rejected')
    inv=C.inventory(field.read_bytes());uid=C.pcbtext.chunk_uuid(area.read_bytes())
    if uid in inv[3] or C.pcbtext.chunk_kind(area.read_bytes())!='zone' or b'(keepout' not in area.read_bytes():raise ValueError('Exact PG area contract differs')
    data=inv[0]+b''.join(inv[1])+area.read_bytes()+inv[2];after=C.inventory(data)
    if after[4]!=inv[4] or any(after[3].get(u)!=ch for u,ch in inv[3].items()):raise ValueError('PG scoped area changed unowned entity')
    STAGE.mkdir();copy=STAGE/'copy';copy.mkdir();candidate=STAGE/'field-power-native-trial.kicad_pcb';candidate.write_bytes(data);shutil.copy2(candidate,copy/'board.kicad_pcb')
    shutil.copy2(field.with_suffix('.kicad_pro'),copy/'board.kicad_pro');original_rule=field.with_suffix('.kicad_dru');dru=copy/'board.kicad_dru';dru.write_bytes(original_rule.read_bytes()+b'\n'+rule.read_bytes())
    prior=H/'field-zone-source-api-r2-bound-hash';command=json.loads((prior/'invocation.json').read_bytes())['command'];old_spec=prior/'native-via-spec.json';via=json.loads(old_spec.read_bytes());via['board_sha256']=sha(candidate);via_path=STAGE/'native-via-spec.json';write(via_path,via)
    changes={str(old_spec.resolve()):str(via_path.resolve()),str(field.resolve()):str((copy/'board.kicad_pcb').resolve()),str((prior/'native-parity.json').resolve()):str((STAGE/'native-parity.json').resolve())}
    for old,new in changes.items():
        if command.count(old)!=1:raise ValueError('Exact native API argument differs: '+old)
        command[command.index(old)]=new
    pins=json.loads((prior/'inputs.json').read_bytes())
    frozen=[Path(__file__),field,field_api,field_geo,pg,area,rule,scope,candidate,copy/'board.kicad_pcb',copy/'board.kicad_pro',dru,via_path]
    for path in frozen:pins[str(path.resolve())]=sha(path)
    write(STAGE/'construction.json',{'parent_field_sha256':sha(field),'candidate_sha256':sha(candidate),'all41_field_zones_exact':True,'all_old_copper_FPs_and_original_zone_outlines_settings_retained_from_eedf':True,'new_rule_area':uid,'original_DRC_rule_bytes_exact_prefix':True,'only_appended_rule_sha256':sha(rule),'PG_fine_3_owned_segments_cumulative_limit_mm':p['cumulative_owned_limit_mm'],'PG_rule_exact_scope_native_coupon_PASS':True,'CM_future_controlled_profile_installed':False,'SBC_CORE_IO3_final_mutual_planes':'OPEN','remaining_field_ground_supply_completion':'OPEN','adopted':False})
    write(STAGE/'inputs.json',pins);write(STAGE/'invocation.json',{'command':command,'existing_slot':'test-only1','no_save_refill_DRC_in_API_phase':True,'new_heavy_slots':0})
    env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
    with (STAGE/'native.log').open('w',encoding='utf-8') as log:run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
    for path,digest in pins.items():
        if sha(path)!=digest:raise ValueError('Frozen field trial input changed: '+path)
    report=json.loads((STAGE/'native-parity.json').read_bytes()) if (STAGE/'native-parity.json').exists() else {}
    passed=run.returncode==0 and report.get('summary',{}).get('parity_defects')==0 and report.get('native_field_pose_diagnostic',{}).get('verdict')=='PASS'
    verdict='PASS_SOURCE_NATIVE_API_26_POSES_68_VIAS_AND_FIELD_ZONES_WITH_PG_AREA' if passed else 'FAIL_FIELD_TRIAL_SOURCE_API'
    write(STAGE/'receipt.json',{'verdict':verdict,'candidate_sha256':sha(candidate),'native_exit_code':run.returncode,'source_API_summary':report.get('summary'),'adopted':False,'field_final_SBC_analog_and_current_qualification':'OPEN'})
    print(json.dumps({'phase':'FIELD_TRIAL_SOURCE_API','verdict':verdict}),flush=True)
    if not passed:raise ValueError('Final exact field trial source/API rejected')
    source=H/'measure_combined_reset_cm_r5.py';target=H/'measure_field_power_native_backend_r1.py';code=source.read_text(encoding='utf-8')
    if target.exists():raise ValueError('Fresh native field measurement backend required')
    replacements={"STAGE=HERE/'combined-reset-cm-native-r5-cache-refresh'":"STAGE=HERE/'field-power-native-trial-r1'","PASS_SOURCE_NATIVE_API_19_POSES_19_VIAS":verdict,"candidate=STAGE/'combined-reset-cm-cache-refreshed.kicad_pcb'":"candidate=STAGE/'field-power-native-trial.kicad_pcb'","'original_DRC_rules_unchanged':True":"'original_DRC_rules_exact_prefix_with_only_scoped_PG_rule_appended':True"}
    for old,new in replacements.items():
        if code.count(old)!=1:raise ValueError('Exact native measurement derivation anchor differs: '+old)
        code=code.replace(old,new)
    anchor="    baselines={\n"
    if code.count(anchor)!=1:raise ValueError('Exact baseline anchor differs')
    code=code.replace(anchor,anchor+"      '1beb':(HERE/'combined-reset-cm-native-r5-cache-refresh/combined-reset-cm-cache-refreshed.kicad_pcb',HERE/'combined-reset-cm-native-r5-cache-refresh/measure/partitions.json'),\n")
    target.write_text(code,encoding='utf-8');write(STAGE/'measure-backend-derivation.json',{'source_sha256':sha(source),'derived_sha256':sha(target),'replacements':replacements,'additional_measured_guard':'1beb full unchanged-original pad relationships','all_refill_DRC_source_matching_stem_and_old_pad_relationship_checks_unchanged':True,'native_measure_is_exploratory_field_only_not_final_SBC_completion':True})
    runpy.run_path(str(target),run_name='__main__')
if __name__=='__main__':main()
