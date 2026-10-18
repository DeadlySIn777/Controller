"""Derive exact selected IO3 API/fill evidence from the preserved AO driver."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
src=H/'stage_ao1_native_diagnostic_r2.py';dst=H/'stage_io3_native_diagnostic_r1.py';assert not dst.exists()
s=src.read_text(encoding='utf-8').replace("OUT=H/'ao1-native-diagnostic-r2'","OUT=H/'io3-native-diagnostic-r1'")
start=s.index("    recipe=H/'coupled-recovery/");end=s.index('    data=inv[0]',start)
s=s[:start]+'''    recipe=H/'sbc-power/owned-io3-native-recipe-r45/receipt.json';zones_recipe=H/'sbc-power/owned-io3-selected-native-zones-r46/receipt.json'
    assert sha(recipe)=='33f764e286538085341d130d7ede6f5d3d2a7330924605d9ee4d94eb52d5c0eb'
    assert sha(zones_recipe)=='9db1363bd9d90d6d2ec1c74db6443c95a90cf38d59e76c0d75b0907026073cb1'
    r=json.loads(recipe.read_bytes());zr=json.loads(zones_recipe.read_bytes());assert r['IO3_source_host_pass'] and r['protected_screen_PASS']
    stage=H/'field-power-native-trial-r1';parent=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb'
    assert sha(parent)==r['parent_native_board_sha256']==zr['parent_native_board_sha256']=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
    inv=NC.C.inventory(parent.read_bytes());removed={};new={};zone_ids=set();chunk_inputs=[]
    for row in r['delete_rows']:
        p=Path(row['chunk_path']);assert sha(p)==row['exact_original_chunk_sha256'];removed[row['uuid']]=p.read_bytes();chunk_inputs.append(p)
    for row in r['add_rows']:
        p=Path(row['chunk_path']);assert sha(p)==row['chunk_sha256'];new[row['uuid']]=p.read_bytes();chunk_inputs.append(p)
    for row in zr['native_zone_rows']:
        p=Path(row['chunk_file']);assert sha(p)==row['chunk_sha256'];new[row['uuid']]=p.read_bytes();zone_ids.add(row['uuid']);chunk_inputs.append(p)
    assert len(removed)==2 and len(new)==4 and len(zone_ids)==1
    assert all(inv[4][u]==ch for u,ch in removed.items()) and not set(new)&set(inv[3])
    assert hashlib.sha256(inv[4][r['exact_retained_CM_clock_uuid']]).hexdigest()==r['exact_retained_CM_clock_chunk_sha256']
''' + s[end:]
s=s.replace("in ('via','segment') for u,ch in new.items()", "in ('via','segment','zone') for u,ch in new.items()")
s=s.replace("str((H/'native_ao_com_scoped_refill_r1.py').resolve())","str((H/'native_io3_scoped_refill_r1.py').resolve())")
s=s.replace("(Path(__file__),recipe,independent,analytic,parent", "(Path(__file__),recipe,zones_recipe,*chunk_inputs,parent")
s=s.replace("'exact7_owned_Cu_deleted'", "'exact2_owned_Cu_deleted'").replace("'exact20_owned_Cu_added':sorted(new)", "'exact3_owned_Cu_added':sorted(set(new)-zone_ids),'selected_new_IO3_zone_added':sorted(zone_ids)")
anchor="    write(OUT/'inputs.json',pins);write(OUT/'invocation.json'"
insert='''    zspec=OUT/'expected-zones.json';write(zspec,{'candidate_sha256':sha(board),'zones':[{'uuid':q['uuid'],'raw_net':q['raw_net'],'layer':q['layer'],'rings_IU':q['outline_integer_nm']} for q in zr['native_zone_rows']]})
    zhelper=H/'native_io3_selected_zone_contract_r1.py'
    zcmd=['C:/Program Files/Git/usr/bin/sh.exe','Z:/pcb-runs/claude-finish/tools/heavyt.sh','kicad','C:/Program Files/KiCad/10.0/bin/python.exe',str(zhelper.resolve()),str(zspec.resolve()),str(board.resolve()),str((OUT/'native-zones.json').resolve())]
    pins[str(zspec.resolve())]=sha(zspec);pins[str(zhelper.resolve())]=sha(zhelper)
'''
assert anchor in s;s=s.replace(anchor,insert+anchor)
anchor2="    api=json.loads((OUT/'native-parity.json').read_bytes());assert api['all_discrete_copper_exact_native_contract']['verdict']=='PASS'"
assert anchor2 in s;s=s.replace(anchor2,anchor2+'''
    with (OUT/'native-zone.log').open('w',encoding='utf-8') as log:zone_run=subprocess.run(zcmd,env=env,stdout=log,stderr=subprocess.STDOUT)
    assert zone_run.returncode==0
    zone_native=json.loads((OUT/'native-zones.json').read_bytes());assert not zone_native['errors'] and zone_native['native_zones_checked']==1
''')
s=s.replace("AO_", "IO3_").replace("AO_SOURCE", "IO3_SOURCE").replace("AO1_COM", "IO3").replace("selected_AO_COM_fill_command", "selected_IO3_fill_command").replace("COM_REFILL", "IO3_REFILL").replace("72_VIA", "69_VIA")
s=s.replace("'reference_gate':'OPEN; no cache healing credit'", "'source_contact_and_F_In1_actual_flash_gate':'OPEN; independent selected fresh fill review required'")
s=s.replace("'scope'", "'scope'")
s=s.replace("'whole_board_refill_DRC_reference_current_analog_SI_and_final_power_composition':'OPEN'", "'whole_board_refill_DRC_retained_contacts_current_and_final_power_composition':'OPEN','selected_trial_scope':'eedf plus exact2-owned-track replacement and one IO3 plane only; other R38 power proposals excluded'")
dst.write_text(s,encoding='utf-8');compile(s,str(dst),'exec')
fsource=H/'native_ao_com_scoped_refill_r1.py';fdest=H/'native_io3_scoped_refill_r1.py';assert not fdest.exists()
f=fsource.read_text(encoding='utf-8').replace("raw='/motherboard_analog_output{slash}AO1_COM'","raw='/IO_3V3'").replace('AO1_COM','IO3').replace('AO1_COM','IO3').replace('AO1_COM','IO3');fdest.write_text(f,encoding='utf-8');compile(f,str(fdest),'exec')
zsource=H/'corrected-local-native-contract-r1/native_local_zone_contract.py';zdest=H/'native_io3_selected_zone_contract_r1.py';assert not zdest.exists()
z=zsource.read_text(encoding='utf-8').replace('PASS_NATIVE_52_CORRECTED_LOCAL_ZONES_ALL_RINGS_SETTINGS_RAW_NETS','PASS_NATIVE_SELECTED_IO3_ZONE_ALL_RINGS_SETTINGS_RAW_NETS');zdest.write_text(z,encoding='utf-8');compile(z,str(zdest),'exec')
(H/'io3-native-diagnostic-r1-derivation.json').write_text(json.dumps({'source_scripts':{str(p.resolve()):sha(p) for p in (src,fsource,zsource)},'derived_scripts':{str(p.resolve()):sha(p) for p in (dst,fdest,zdest)},'scope':'eedf plus IO3 R45 exact2owned track delete/1via2segment add and selected R46 In1 zone; no other R38 power geometry','existing_test_slot':1,'new_heavy_slots':0,'whole_board_and_independent_contacts_current_gates':'OPEN','adopted':False},indent=1)+'\n',encoding='utf-8')
print(sha(dst))
