"""Test exactly one generated zone's own-hole correction on an R9 copy."""
import copy,hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path
from shapely.geometry import Point,Polygon
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));sys.path.insert(0,str(H/'field-power'))
import native_pose_signal_contract as NC
from verify_source import parse,children,child,atom
OUT=H/'R9-R5051-single-own-hole-native-diagnostic-r123'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=1)+'\n')
def main():
    assert not OUT.exists();OUT.mkdir();src=H/'SAFE-exploratory-native-trial-r9/measure/copy';bp=src/'board.kicad_pcb';assert sha(bp)=='3b579aa7ea4cf4c070c22e36df8dca2fbfcdefccd0e3c2a874ebf337acda3919'
    delta=H/'R112-R5051-own-drill-intended-outline-only-correction-r122';assert sha(delta/'receipt.json')=='fb082ca4f5a96a06363c88ea3a8329b89290399c1574a2590214d2ab5ed69bf9'
    raw=bp.read_bytes();C=NC.C;inv=C.inventory(raw);uid='e309aa10-2546-5c29-a800-5351ac005bf5';old=inv[3][uid];ast=parse(old.decode());assert atom(ast,'net')=='/LOGIC_GND' and atom(ast,'layer')=='In3.Cu'
    polygons=children(ast,'polygon');assert len(polygons)==2
    rings=[[[int(round(float(v[1])*1e6)),int(round(float(v[2])*1e6))] for v in child(p,'pts')[1:]] for p in polygons]
    hole=Polygon([(x/1e6,y/1e6) for x,y in rings[1]]);assert hole.covers(Point(292,209.375)) and hole.bounds==(291.85,209.225,292.15,209.525)
    import shapely
    exact=shapely.from_wkb((delta/'exact-own-drill-void.wkb').read_bytes());assert hole.equals(exact)
    matches=list(re.finditer(rb'(?ms)^\t\t\(polygon\n.*?^\t\t\)\n',old));assert len(matches)==2
    hit=matches[1];new=old[:hit.start()]+old[hit.end():];newast=parse(new.decode());expected_ast=[x for x in ast if x is not polygons[1]];assert newast==expected_ast
    candidate=inv[0]+b''.join(new if C.pcbtext.chunk_uuid(ch)==uid else ch for ch in inv[1])+inv[2];current=C.inventory(candidate);assert current[0]==inv[0] and current[2]==inv[2] and set(current[3])==set(inv[3])
    assert [u for u in inv[3] if inv[3][u]!=current[3][u]]==[uid]
    copydir=OUT/'copy';shutil.copytree(src,copydir);board=copydir/'board.kicad_pcb';board.write_bytes(candidate)
    (OUT/'original-generated-zone-chunk').write_bytes(old);(OUT/'corrected-generated-zone-chunk').write_bytes(new)
    ledger=read_json= json.loads((H/'SAFE-exploratory-native-trial-r9/all-copper-expected.json').read_bytes());assert ledger['board_sha256']==sha(bp);ledger['board_sha256']=sha(board);write(OUT/'all-copper-expected.json',ledger)
    zone_spec=json.loads((H/'SAFE-exploratory-native-trial-r9/expected-zones.json').read_bytes());q=next(q for q in zone_spec['zones'] if q['uuid']==uid);assert q['rings_IU']==rings;q=copy.deepcopy(q);q['rings_IU']=rings[:1];write(OUT/'one-corrected-zone-expected.json',{'candidate_sha256':sha(board),'zones':[q]})
    source=H/'native_core1v2_scoped_refill_r132.py';helper=OUT/'native_R5051_one_zone_refill.py';code=source.read_text()
    needle="raw='/CORE_1V2'";assert code.count(needle)==1;code=code.replace(needle,"raw='/LOGIC_GND'")
    needle="str(z.GetNetname())==raw:";assert code.count(needle)==1;code=code.replace(needle,"str(z.GetNetname())==raw and str(z.m_Uuid.AsString())=='e309aa10-2546-5c29-a800-5351ac005bf5':")
    code=code.replace('CORE1V2','R5051_SINGLE_OWNED_LOGIC_ZONE').replace('CORE1V2 only','R5051 one owned LOGIC zone only');helper.write_text(code);compile(code,str(helper),'exec')
    wrapper=Path('Z:/pcb-runs/claude-finish/tools/heavyt.sh');api=Path('C:/Program Files/KiCad/10.0/bin/python.exe')
    check_script=H/'native_declared_selected_zone_contract_r2.py';check_report=OUT/'one-zone-native-API.json'
    prefix=['C:/Program Files/Git/usr/bin/sh.exe',str(wrapper),'kicad',str(api)]
    commands=[prefix+[str(check_script.resolve()),str((OUT/'one-corrected-zone-expected.json').resolve()),str(board.resolve()),str(check_report.resolve())],prefix+[str(helper.resolve()),str(board.resolve()),str((OUT/'all-copper-expected.json').resolve()),str((OUT/'scoped-fill').resolve())]]
    files=[Path(__file__),bp,delta/'receipt.json',delta/'exact-own-drill-void.wkb',source,helper,wrapper,api,check_script,board,board.with_suffix('.kicad_pro'),board.with_suffix('.kicad_dru'),OUT/'all-copper-expected.json',OUT/'one-corrected-zone-expected.json']
    pins={str(p.resolve()):sha(p) for p in files};write(OUT/'inputs.json',{'pins':pins,'commands':commands,'exact_only_changed_item_UUID':uid,'only_deleted_polygon_ring':rings[1],'unchanged_all_old_FP_discrete_native_zone_definitions_and_rules':True,'scope':'One new generated LOGIC zone fresh fill; other zone fills remain unvalidated. Not full candidate acceptance.','old_R9_full_native_flash_failure_and_three_old_relationship_losses_retained':True,'new_heavy_slots':0,'adopted':False})
    env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
    write(OUT/'status.json',{'phase':'EXACT_ONE_OWN_HOLE_NATIVE_ZONE_API_AND_SELECTED_REFILL_RUNNING','candidate_sha256':sha(board),'adopted':False});print('R123_NATIVE_ONE_OWNED_ZONE_START',sha(board),flush=True)
    for i,cmd in enumerate(commands):
        with (OUT/('native-'+str(i)+'.log')).open('w') as log:r=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
        assert r.returncode==0,('Native scoped test failed',i,r.returncode)
        for p,s in pins.items():assert sha(p)==s,p
    flashes=json.loads((OUT/'scoped-fill/actual-via-flashes.json').read_bytes())['vias'];actual=flashes['18701851-0390-4dc4-b03d-f8e1cd66c395']
    report={'verdict':'SCOPED_R5051_NATIVE_IN3_FLASH_PRESENT_FULL_CANDIDATE_GATES_OPEN' if 'In3.Cu' in actual else 'SCOPED_R5051_NATIVE_IN3_FLASH_STILL_FAILED','candidate_sha256':sha(board),'original_R9_board_sha256':sha(bp),'actual_same_serialized_existing_via_flashes':actual,'actual_fresh_scope_only_zone_UUID':uid,'all_original_Cu_and_FP_bytes_preserved':True,'only_exact_bound_own_drill_void_removed_from_new_generated_intended_zone':True,'physical_host_zone_unchanged':True,'full_fresh_refill_all_original_group_no_loss_full_DRC_current_and_reference':'MANDATORY_OPEN','inputs_sha256':sha(OUT/'inputs.json'),'scoped_native_fill_receipt_sha256':sha(OUT/'scoped-fill/receipt.json'),'native_copper_saved':False,'adopted':False}
    write(OUT/'receipt.json',report);write(OUT/'status.json',report);print(json.dumps(report),flush=True)
if __name__=='__main__':main()
