"""Derive exact additive DI6 diagnostic using the existing native test-only slot."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=H/'stage_c10036_native_diagnostic_r1.py';out=H/'stage_di6_native_diagnostic_r1.py';fs=H/'native_c10036_scoped_refill_r1.py';fo=H/'native_di6_scoped_refill_r1.py';receipt=H/'di6-native-diagnostic-r1-derivation.json'
assert not out.exists() and not fo.exists() and not receipt.exists()
s=source.read_text();s=s.replace('Exact AO R18 operation on the source-bound field clone, API then scoped fill.','Exact DI6 eleven-item additive native clone, API then fresh LOGIC_GND-only fill.')
s=s.replace("OUT=H/'c10036-native-diagnostic-r1'","OUT=H/'di6-native-diagnostic-r1'")
start=s.index("    recipe=H/");end=s.index("    stage=H/",start)
s=s[:start]+"""    recipe=H/'coupled-recovery/di6-native-owned-ledger-r14/receipt.json'
    assert sha(recipe)=='6d7dcdc50a10393138761a0067fb73325eace8307800358d72723adcbb1afd79'
    r=json.loads(recipe.read_bytes());author=Path(r['host_independent_receipt'])
    assert sha(author)==r['host_independent_receipt_sha256']=='d6468fbf689a15f94e157318067358eec8c323eda202355194f9cde41879a8cb'
    assert r['exact_deleted_current_chunks']=={} and r['new_items_counts']=={'vias':2,'segments':9}
"""+s[end:]
start=s.index("    for row in r['rows']:");end=s.index("    assert all(inv[4]",start)
s=s[:start]+"""    for row in r['exact_new_chunk_files']:
        p=Path(row['chunk_file']);assert sha(p)==row['chunk_sha256'];chunk_inputs.append(p)
        uid=row['UUID'];assert uid not in new and row['kind'] in ('segment','via')
        new[uid]=p.read_bytes();assert NC.C.pcbtext.chunk_kind(new[uid])==row['kind']
    assert len(removed)==0 and len(new)==11 and len(zone_ids)==0
"""+s[end:]
s=s.replace("'native_c10036_scoped_refill_r1.py'","'native_di6_scoped_refill_r1.py'").replace('recipe,zones_recipe,*chunk_inputs','recipe,author,*chunk_inputs')
start=s.index("    zspec=OUT/");end=s.index("    write(OUT/'inputs.json'",start);s=s[:start]+s[end:]
start=s.index("    with (OUT/'native-zone.log')");end=s.index("    write(OUT/'receipt.json'",start);s=s[:start]+s[end:]
s=s.replace("'selected_C10036_COM_fill_command'","'selected_DI6_LOGIC_GND_fill_command'").replace("'exact6_owned_Cu_deleted'","'exact0_owned_Cu_deleted'").replace("'exact8_owned_Cu_added'","'exact11_owned_Cu_added'").replace("'selected_new_FBG_reference_zone_added'","'new_zones_added'")
s=s.replace('C10036','DI6').replace('F_B_In4_actual_flash_gate','F_In3_In1_In4_actual_flash_gate').replace('69_VIA','70_VIA')
s=s.replace('eedf plus exact6 owned track replacement, six tracks/two vias/one FBG reference zone; other power proposals excluded','eedf plus exact9 segments/2 vias; LOGIC_GND zones freshly filled only; other power proposals excluded')
needle="    for ext in ('.kicad_pro','.kicad_dru'):shutil.copy2(parent.with_suffix(ext),board.with_suffix(ext))";assert s.count(needle)==1
s=s.replace(needle,"    original_sidecar_pins=json.loads((H/'io3-native-diagnostic-r2/inputs.json').read_bytes())\n    for ext in ('.kicad_pro','.kicad_dru'):\n        sc=parent.with_suffix(ext);assert sha(sc)==original_sidecar_pins[str(sc.resolve())]\n        shutil.copy2(sc,board.with_suffix(ext))")
compile(s,str(out),'exec');out.write_text(s)
f=fs.read_text();f=f.replace("raw='/motherboard_do{slash}FIELD_B_0V'","raw='/LOGIC_GND'").replace('FBG','LOGIC_GND')
compile(f,str(fo),'exec');fo.write_text(f)
receipt.write_text(json.dumps({'source_stager_sha256':sha(source),'derived_stager_sha256':sha(out),'source_scoped_filler_sha256':sha(fs),'derived_scoped_filler_sha256':sha(fo),'exact_DI6_R14_11_additions_no_deletes_or_zones':True,'matching_eedf_project_rules_and_fresh_source_binding':True,'all_existing_and_new_native_Cu_raw_net_IU_all6_diameters_source_poses_checked':True,'selected_LOGIC_GND_zones_fresh_noSave_otherfills_unvalidated':True,'independent_signal_body_reference_paired_annuli_actual_source_and_retained_contacts_required_after_export':True,'final_R78_field_ground_C_AO_mutual_and_wholeboard_native_current_DRC_SI':'OPEN','existing_test_only_slot':True,'new_heavy_slots':0},indent=1)+'\n')
print(json.dumps({'stager':str(out),'sha256':sha(out),'scoped_filler_sha256':sha(fo)}))
