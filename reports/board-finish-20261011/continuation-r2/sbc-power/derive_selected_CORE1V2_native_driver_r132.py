"""Derive one frozen selected-native trial on the existing test-only1 slot."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent.parent
src=H/'stage_io3_native_diagnostic_r2.py';dst=H/'stage_core1v2_native_diagnostic_r132.py';assert not dst.exists()
s=src.read_text()
s=s.replace("OUT=H/'io3-native-diagnostic-r2'","OUT=H/'core1v2-native-diagnostic-r132'")
start=s.index("    recipe=H/'sbc-power/");end=s.index('    data=inv[0]',start)
s=s[:start]+'''    recipe=H/'sbc-power/selected-CORE1V2-native-recipe-r130/receipt.json';analytic=H/'sbc-power/selected-CORE1V2-strict-geometry-r131/receipt.json'
    assert sha(recipe)=='d778d6118245f0846575f49bdb4e44bffa2b14437c9025bff62c07ab49e34c2c'
    assert sha(analytic)=='f2c85f9a08c763487647ed512bb0ef4d3051268730f1ef3b821ff0982431e471'
    r=json.loads(recipe.read_bytes());zr=r;ar=json.loads(analytic.read_bytes());assert not ar['errors'] and ar['all_strict_no_gap_or_area_tolerance']
    stage=H/'field-power-native-trial-r1';parent=Path(r['parent_native_board_file'])
    assert sha(parent)==r['parent_native_board_sha256']=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
    inv=NC.C.inventory(parent.read_bytes());removed={};new={};zone_ids=set();chunk_inputs=[]
    for row in r['native_discrete_rows']+r['native_zone_rows']:
        p=Path(row['chunk_file']);assert sha(p)==row['chunk_sha256'];new[row['uuid']]=p.read_bytes();chunk_inputs.append(p)
        if row in r['native_zone_rows']:zone_ids.add(row['uuid'])
    assert not removed and len(new)==2 and len(zone_ids)==1 and not set(new)&set(inv[3])
''' + s[end:]
s=s.replace("Path(__file__),recipe,zones_recipe,*chunk_inputs", "Path(__file__),recipe,analytic,*chunk_inputs")
s=s.replace("str((H/'native_io3_scoped_refill_r1.py').resolve())", "str((H/'native_core1v2_scoped_refill_r132.py').resolve())")
s=s.replace("str(zhelper.resolve())", "str(zhelper.resolve())")
s=s.replace("zhelper=H/'native_io3_selected_zone_contract_r1.py'", "zhelper=H/'native_declared_selected_zone_contract_r2.py'")
start=s.index("    zspec=OUT/'expected-zones.json';");end=s.index("    zhelper=",start)
s=s[:start]+'''    declared=[]
    for q in zr['native_zone_rows']:
        d=q['declared_native_settings'];assert d['pad_connect_mode']=='FULL_SOLID'
        settings={'priority':int(d['priority']),'local_clearance_IU':iu(d['local_clearance_mm']),'minimum_thickness_IU':iu(d['min_thickness_mm']),'thermal_gap_IU':iu(d['thermal_gap_mm']),'thermal_spoke_IU':iu(d['thermal_bridge_width_mm']),'island_removal_mode':int(d['island_removal_mode'])}
        declared.append({'uuid':q['uuid'],'raw_net':q['raw_net'],'layer':q['layer'],'rings_IU':[q['outer_integer_nm']]+q['hole_integer_nm'],'declared_native_settings':settings})
    zspec=OUT/'expected-zones.json';write(zspec,{'candidate_sha256':sha(board),'zones':declared})
''' + s[end:]
s=s.replace("'exact2_owned_Cu_deleted'", "'exact0_owned_Cu_deleted'").replace("'exact3_owned_Cu_added'", "'exact1_owned_Cu_added'").replace("'selected_new_IO3_zone_added'", "'selected_new_CORE1V2_zone_added'")
s=s.replace("'source_contact_and_F_In1_actual_flash_gate'", "'source_contact_and_original_F_In3_plus_fresh_In4_actual_flash_gate'")
s=s.replace("eedf plus exact2-owned-track replacement and one IO3 plane only; other R38 power proposals excluded", "eedf plus exact J7 .20 F track and one In4 CORE1V2 plane only; complete CORE c7 and other power proposals excluded")
s=s.replace('IO3_', 'CORE1V2_').replace('selected_IO3_COM_fill_command','selected_CORE1V2_fill_command').replace('69_VIA','68_VIA')
dst.write_text(s);compile(s,str(dst),'exec')
fs=H/'native_io3_scoped_refill_r1.py';fd=H/'native_core1v2_scoped_refill_r132.py';assert not fd.exists()
f=fs.read_text().replace("raw='/IO_3V3'","raw='/CORE_1V2'").replace('IO3','CORE1V2')
fd.write_text(f);compile(f,str(fd),'exec')
der=H/'sbc-power/core1v2-selected-native-driver-derivation-r132.json'
der.write_text(json.dumps({'sources':{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in (src,fs)},'derived':{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in (dst,fd)},'authorizing_root_message':'Run selected R130 immutable nativecopy/declaredzone+J7track probe on existing test-only1 slot after strict analytic geometry.','new_heavy_slots':0,'no_native_board_save':'Fresh in-memory selected fill only; stage clone stores exact owned chunk append.','wholeboard_contact_reference_current_native_final':'OPEN'},indent=1)+'\n')
print('CORE1V2_SELECTED_NATIVE_DRIVER_DERIVED',hashlib.sha256(dst.read_bytes()).hexdigest())
