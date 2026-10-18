"""Construct and API-check one frozen power recipe on the exact native parent.

This writes an exploratory clone only. It preserves the entire parent inventory
and applies exact declared coupled-owned copper removals and adds the final owned recipe once, without appending interim plane previews.
Fresh fill, native continuity/DRC and electrical qualification remain separate.
"""
import ast, hashlib, json, os, re, shutil, subprocess, sys
from pathlib import Path
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import native_pose_signal_contract as NC
import native_translation_owned_contract_r2 as FP

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_bytes())
def write(p, value): Path(p).write_text(json.dumps(value, indent=1)+'\n', encoding='utf-8')

def main():
    assert len(sys.argv) == 3, 'recipe/receipt.json fresh_output_directory'
    recipe = Path(sys.argv[1]).resolve(); out = Path(sys.argv[2]).resolve()
    assert out.is_relative_to(H) and not out.exists()
    r = read(recipe); declared_parent = Path(r['parent_native_board_file']);parent=H/'sbc-native-contract-r1/copy/board.kicad_pcb'
    assert sha(declared_parent)==sha(parent)
    frozen_sidecars=read(H/'io3-native-diagnostic-r2/inputs.json')
    for ext in ('.kicad_pro','.kicad_dru'):
        sidecar=parent.with_suffix(ext);assert sha(sidecar)==frozen_sidecars[str(sidecar.resolve())]
    assert sha(parent) == r['parent_native_board_sha256'] == 'eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
    assert r['host_retained_relationships_pass'], 'Retained host contact gate must pass before native staging'
    assert r['old_zone_removals'] == r['old_zone_replacements'] == []
    model = Path(r['frozen_host_model_file']); audit = Path(r['full_original198b_and_dc936_contact_audit_file'])
    assert sha(model) == r['frozen_host_model_sha256'] and sha(audit) == r['full_original198b_and_dc936_contact_audit_sha256']
    inv = NC.C.inventory(parent.read_bytes()); added = []; ids = set();removed={}
    fp_rows=r.get('native_existing_owned_footprint_replacement_rows',[])
    replaced,fp_pins,fp_poses,fp_masks=FP.collect(fp_rows,inv)
    for row in r['native_existing_owned_Cu_delete_rows']:
        path=Path(row['chunk_file']);chunk=path.read_bytes();uid=row['uuid']
        assert sha(path)==row['chunk_sha256']==row['exact_original_chunk_sha256']
        assert uid not in removed and inv[4].get(uid)==chunk
        assert NC.C.pcbtext.chunk_kind(chunk)==row['kind'] and row['kind'] in ('segment','via')
        author=Path(row['authorizing_recipe_file']);assert sha(author)==row['authorizing_recipe_sha256']
        removed[uid]=chunk
    assert sum(NC.C.pcbtext.chunk_kind(x)=='segment' for x in removed.values())==r['exact_existing_native_deleted_segments']
    assert sum(NC.C.pcbtext.chunk_kind(x)=='via' for x in removed.values())==r['exact_existing_native_deleted_vias']
    rows = r['native_zone_rows'] + r['native_discrete_rows']
    pins = {str(p.resolve()): sha(p) for p in (Path(__file__), recipe, parent, parent.with_suffix('.kicad_pro'), parent.with_suffix('.kicad_dru'), model, audit)}
    pins[str(declared_parent.resolve())]=sha(declared_parent)
    pins.update(fp_pins);pins[str(Path(FP.__file__).resolve())]=sha(FP.__file__)
    for row in r['native_existing_owned_Cu_delete_rows']:
        for key in ('chunk_file','authorizing_recipe_file'):
            path=Path(row[key]);pins[str(path.resolve())]=sha(path)
    for row in rows:
        path = Path(row['chunk_file']); chunk = path.read_bytes()
        assert sha(path) == row['chunk_sha256']
        uid = NC.C.pcbtext.chunk_uuid(chunk)
        assert uid == row['uuid'] and uid not in inv[3] and uid not in ids
        assert NC.C.pcbtext.chunk_kind(chunk) == row.get('kind', 'zone')
        ids.add(uid); added.append(chunk); pins[str(path.resolve())] = sha(path)
    # PG is the separately native-tested, exact three-segment owned neck scope.
    pgpath = H/'sbc-power/PG-native-rule-proposal-r7/receipt.json'; pg = read(pgpath)
    assert sha(pgpath) == '468c0f1ccff701dce7954aa8fc17bd0db884cd3b02b9dbac1d200ce7832fe15c'
    area = Path(pg['area_chunk_file']); rule = Path(pg['rule_file'])
    assert sha(area) == pg['area_chunk_sha256'] and sha(rule) == pg['rule_sha256']
    area_uid = NC.C.pcbtext.chunk_uuid(area.read_bytes())
    assert area_uid not in ids and area_uid not in inv[3]
    added.append(area.read_bytes())
    data = inv[0] + b''.join(replaced.get(NC.C.pcbtext.chunk_uuid(ch),ch) for ch in inv[1] if NC.C.pcbtext.chunk_uuid(ch) not in removed) + b''.join(added) + inv[2]
    after = NC.C.inventory(data)
    assert after[0] == inv[0] and after[2] == inv[2]
    assert all(after[3].get(uid) == chunk for uid, chunk in inv[3].items() if uid not in removed and uid not in replaced)
    assert not set(removed)&set(after[3])
    assert all(after[3][uid]==chunk for uid,chunk in replaced.items()) and not set(removed)&set(replaced)
    out.mkdir(); copy = out/'copy'; copy.mkdir(); board = copy/'board.kicad_pcb'; board.write_bytes(data)
    shutil.copy2(parent.with_suffix('.kicad_pro'), board.with_suffix('.kicad_pro'))
    board.with_suffix('.kicad_dru').write_bytes(parent.with_suffix('.kicad_dru').read_bytes()+b'\n'+rule.read_bytes())
    command = read(H/'field-power-native-trial-r1/invocation.json')['command']
    parser = Path(command[8]); tree = ast.parse(parser.read_text(encoding='utf-8')); ns = {'re': re}
    decl = [n for n in tree.body if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id == 'TOKEN' or isinstance(n, ast.FunctionDef) and n.name in ('sexpr_parse','child','children','atom','norm')]
    exec(compile(ast.Module(body=decl,type_ignores=[]),'frozen-net-parser','exec'),ns)
    parse, child = ns['sexpr_parse'], ns['child']; iu = lambda v: int(round(float(v)*1000000))
    copper = {}; via = read(H/'field-power-native-trial-r1/native-via-spec.json'); via['board_sha256'] = sha(board);via['added_vias']=[row for row in via['added_vias'] if row['uuid'] not in removed]
    for uid, chunk in after[4].items():
        root = parse(chunk.decode()); kind = root[0]; net = child(root,'net')
        row = {'kind': kind, 'raw_net': net[1] if net else '', 'chunk_sha256': hashlib.sha256(chunk).hexdigest()}
        if kind == 'via':
            row.update(at_IU=list(map(iu,child(root,'at')[1:3])),drill_IU=iu(child(root,'drill')[1]),diameters_IU={l:iu(child(root,'size')[1]) for l in ('F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu')})
            if uid in ids:
                via['added_vias'].append({'uuid':uid,'net':row['raw_net'].replace('{slash}','/'),'net_raw':row['raw_net'],'at':[float(v) for v in child(root,'at')[1:3]],'d':float(child(root,'size')[1]),'drill':float(child(root,'drill')[1])})
        elif kind == 'segment':
            row.update(start_IU=list(map(iu,child(root,'start')[1:3])),end_IU=list(map(iu,child(root,'end')[1:3])),width_IU=iu(child(root,'width')[1]),layer=child(root,'layer')[1])
        else: raise ValueError('Unexpected copper kind '+kind)
        copper[uid] = row
    expected = out/'all-copper-expected.json'; write(expected,{'board_path':str(board),'board_sha256':sha(board),'copper':copper})
    via_path = out/'native-via-spec.json'; write(via_path,via)
    # Extend both native pose and exact SMD/text contracts before helper wrapping.
    if fp_rows:
        for arg in(command[6],command[7]):
            path=Path(arg);pins[str(path.resolve())]=sha(path)
        pose=read(command[7]);mask=read(command[6])
        assert not {x['ref']for x in fp_poses}&{x['ref']for x in pose['rows']}
        assert not {x['ref']for x in fp_masks}&{x['ref']for x in mask['footprints']}
        pose['rows'].extend(fp_poses);mask['footprints'].extend(fp_masks)
        pose['explicit_additional_owned_translation_rows']=len(fp_poses)
        mask['explicit_additional_owned_translation_rows']=len(fp_masks)
        pose_path=out/'native-owned-pose-ledger.json';mask_path=out/'native-owned-mask-text-ledger.json'
        write(pose_path,pose);write(mask_path,mask)
        for path in(pose_path,mask_path):pins[str(path.resolve())]=sha(path)
        command[7]=str(pose_path);command[6]=str(mask_path)
    command[9] = str(via_path); command[10] = str(board); command[-1] = str(out/'native-parity.json')
    original_helper = command[4]; command[4:5] = [str(H/'native_all_copper_contract_r1.py'),original_helper,str(expected)]
    zones = []
    for row in r['native_zone_rows']:
        d=row['declared_native_settings'];assert d['pad_connect_mode']=='FULL_SOLID'
        settings={'priority':int(d['priority']),'local_clearance_IU':iu(d['local_clearance_mm']),'minimum_thickness_IU':iu(d['min_thickness_mm']),'thermal_gap_IU':iu(d['thermal_gap_mm']),'thermal_spoke_IU':iu(d['thermal_bridge_width_mm']),'island_removal_mode':int(d['island_removal_mode'])}
        zones.append({'uuid':row['uuid'],'raw_net':row['raw_net'],'layer':row['layer'],'rings_IU':[row['outer_integer_nm']]+row['hole_integer_nm'],'declared_native_settings':settings})
    zone_spec = out/'expected-zones.json'; write(zone_spec,{'candidate_sha256':sha(board),'zones':zones})
    zone_origin=H/'native_declared_selected_zone_contract_r2.py';zone_helper=zone_origin
    zcmd=['C:/Program Files/Git/usr/bin/sh.exe','Z:/pcb-runs/claude-finish/tools/heavyt.sh','kicad','C:/Program Files/KiCad/10.0/bin/python.exe',str(zone_helper),str(zone_spec),str(board),str(out/'native-zones.json')]
    for path in (pgpath,area,rule,board,board.with_suffix('.kicad_pro'),board.with_suffix('.kicad_dru'),expected,via_path,zone_spec,zone_origin,zone_helper): pins[str(path.resolve())] = sha(path)
    for arg in command+zcmd:
        path = Path(arg)
        if path.is_file(): pins[str(path.resolve())] = sha(path)
    write(out/'inputs.json',pins)
    write(out/'construction.json',{'parent_sha256':sha(parent),'candidate_sha256':sha(board),'all_unlisted_parent_entities_header_tail_exact':True,'exact_owned_existing_Cu_deleted':sorted(removed),'exact_owned_footprint_translation_UUIDs':sorted(replaced),'owned_footprint_translation_rows':fp_rows,'owned_deletion_authorizers':r['existing_native_owned_Cu_removal_recipes'],'added_segments':r['new_segments'],'added_vias':r['new_vias'],'added_zone_chunks':len(zones),'original_zone_outlines_exact':True,'separate_PG_area':area_uid,'original_rule_bytes_exact_prefix':True,'host_all_supply_rooted':r['host_all_supply_pad_and_proposed_components_rooted'],'coupled_owned_recipes_included':r['existing_native_owned_Cu_removal_recipes'],'declared_perzone_settings_native_checked':True,'adopted':False})
    write(out/'invocation.json',{'source_all_Cu_command':command,'all_new_zone_command':zcmd,'existing_slot':'test-only1','new_heavy_slots':0})
    env = os.environ.copy(); env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']; runs=[]
    for name, cmd in [('source-all-Cu',command),('all-new-zones',zcmd)]:
        with (out/(name+'.log')).open('w',encoding='utf-8') as log: run=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
        runs.append({'name':name,'exit_code':run.returncode})
        if run.returncode: break
    assert all(sha(path)==digest for path,digest in pins.items())
    api=read(out/'native-parity.json') if (out/'native-parity.json').exists() else {}; zr=read(out/'native-zones.json') if (out/'native-zones.json').exists() else {}
    ok=len(runs)==2 and all(x['exit_code']==0 for x in runs) and api.get('all_discrete_copper_exact_native_contract',{}).get('verdict')=='PASS' and zr.get('native_zones_checked')==len(zones) and not zr.get('errors')
    receipt={'verdict':'PASS_JOINT_POWER_SOURCE_ALL_CU_ALL_NEW_ZONES_API_ONLY' if ok else 'FAIL_JOINT_POWER_NATIVE_API','candidate_sha256':sha(board),'candidate_path':str(board),'runs':runs,'source_API_summary':api.get('summary'),'all_native_discrete':api.get('all_discrete_copper_exact_native_contract'),'native_zone_count':zr.get('native_zones_checked'),'native_holes':zr.get('native_holes_checked'),'host_all_supply_rooted':r['host_all_supply_pad_and_proposed_components_rooted'],'full_refill_DRC_unchanged_relationships_actual_flash_current_thermal_transient_qualification':'OPEN','adopted':False}
    write(out/'receipt.json',receipt); print(json.dumps(receipt),flush=True)
    return 0 if ok else 1

if __name__=='__main__': raise SystemExit(main())
