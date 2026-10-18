"""Derive exact coupled-owned removal support and declared-settings checks."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;p=H/'stage_joint_power_native_r1.py';out=H/'stage_joint_power_native_r2.py';assert not out.exists()
s=p.read_text()
old="    r = read(recipe); parent = Path(r['parent_native_board_file'])"
new="""    r = read(recipe); declared_parent = Path(r['parent_native_board_file']);parent=H/'sbc-native-contract-r1/copy/board.kicad_pcb'
    assert sha(declared_parent)==sha(parent)
    frozen_sidecars=read(H/'io3-native-diagnostic-r2/inputs.json')
    for ext in ('.kicad_pro','.kicad_dru'):
        sidecar=parent.with_suffix(ext);assert sha(sidecar)==frozen_sidecars[str(sidecar.resolve())]"""
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("    inv = NC.C.inventory(parent.read_bytes()); added = []; ids = set()","""    inv = NC.C.inventory(parent.read_bytes()); added = []; ids = set();removed={}
    for row in r['native_existing_owned_Cu_delete_rows']:
        path=Path(row['chunk_file']);chunk=path.read_bytes();uid=row['uuid']
        assert sha(path)==row['chunk_sha256']==row['exact_original_chunk_sha256']
        assert uid not in removed and inv[4].get(uid)==chunk
        assert NC.C.pcbtext.chunk_kind(chunk)==row['kind'] and row['kind'] in ('segment','via')
        author=Path(row['authorizing_recipe_file']);assert sha(author)==row['authorizing_recipe_sha256']
        removed[uid]=chunk
    assert sum(NC.C.pcbtext.chunk_kind(x)=='segment' for x in removed.values())==r['exact_existing_native_deleted_segments']
    assert sum(NC.C.pcbtext.chunk_kind(x)=='via' for x in removed.values())==r['exact_existing_native_deleted_vias']""")
needle="    for row in rows:\n";assert s.count(needle)==1
s=s.replace(needle,"    pins[str(declared_parent.resolve())]=sha(declared_parent)\n    for row in r['native_existing_owned_Cu_delete_rows']:\n        for key in ('chunk_file','authorizing_recipe_file'):\n            path=Path(row[key]);pins[str(path.resolve())]=sha(path)\n"+needle)
s=s.replace("data = inv[0] + b''.join(inv[1]) + b''.join(added) + inv[2]","data = inv[0] + b''.join(ch for ch in inv[1] if NC.C.pcbtext.chunk_uuid(ch) not in removed) + b''.join(added) + inv[2]")
s=s.replace("assert all(after[3][uid] == chunk for uid, chunk in inv[3].items())","assert all(after[3].get(uid) == chunk for uid, chunk in inv[3].items() if uid not in removed)\n    assert not set(removed)&set(after[3])")
s=s.replace("via['board_sha256'] = sha(board)","via['board_sha256'] = sha(board);via['added_vias']=[row for row in via['added_vias'] if row['uuid'] not in removed]")
begin=s.index("    zones = []\n");end=s.index("    for path in (pgpath",begin)
block="""    zones = []
    for row in r['native_zone_rows']:
        d=row['declared_native_settings'];assert d['pad_connect_mode']=='FULL_SOLID'
        settings={'priority':int(d['priority']),'local_clearance_IU':iu(d['local_clearance_mm']),'minimum_thickness_IU':iu(d['min_thickness_mm']),'thermal_gap_IU':iu(d['thermal_gap_mm']),'thermal_spoke_IU':iu(d['thermal_bridge_width_mm']),'island_removal_mode':int(d['island_removal_mode'])}
        zones.append({'uuid':row['uuid'],'raw_net':row['raw_net'],'layer':row['layer'],'rings_IU':[row['outer_integer_nm']]+row['hole_integer_nm'],'declared_native_settings':settings})
    zone_spec = out/'expected-zones.json'; write(zone_spec,{'candidate_sha256':sha(board),'zones':zones})
    zone_origin=H/'native_declared_selected_zone_contract_r2.py';zone_helper=zone_origin
    zcmd=['C:/Program Files/Git/usr/bin/sh.exe','Z:/pcb-runs/claude-finish/tools/heavyt.sh','kicad','C:/Program Files/KiCad/10.0/bin/python.exe',str(zone_helper),str(zone_spec),str(board),str(out/'native-zones.json')]
"""
s=s[:begin]+block+s[end:]
s=s.replace("'all_parent_entities_header_tail_exact':True","'all_unlisted_parent_entities_header_tail_exact':True,'exact_owned_existing_Cu_deleted':sorted(removed),'owned_deletion_authorizers':r['existing_native_owned_Cu_removal_recipes']")
s=s.replace("'AO_recipe_included':False","'coupled_owned_recipes_included':r['existing_native_owned_Cu_removal_recipes'],'declared_perzone_settings_native_checked':True")
s=s.replace('and adds the final owned recipe once','and applies exact declared coupled-owned copper removals and adds the final owned recipe once')
compile(s,str(out),'exec');out.write_text(s)
r=H/'joint-native-stage-r2-derivation.json';assert not r.exists();r.write_text(json.dumps({'prior_script_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'derived_script_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'owned_removal_exact_source_chunk_and_authorizer_required':True,'all_unlisted_native_entities_original_zone_definitions_source_poses_exact':True,'matching_eedf_sidecar_copy_bound_to_completed_IO3_native_inputs':True,'perzone_declared_settings_and_allrings_native_checker':str(zone_origin) if False else str(H/'native_declared_selected_zone_contract_r2.py'),'all_fullboard_contact_current_refill_DRC_gates':'OPEN','existing_test_slot_only':True},indent=1)+'\n')
print(json.dumps({'script':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
