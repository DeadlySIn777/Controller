"""Construct and API-check one frozen power recipe on the exact native parent.

This writes an exploratory clone only. It preserves the entire parent inventory
and adds the final owned recipe once, without appending interim plane previews.
Fresh fill, native continuity/DRC and electrical qualification remain separate.
"""
import ast, hashlib, json, os, re, shutil, subprocess, sys
from pathlib import Path
H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import native_pose_signal_contract as NC

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_bytes())
def write(p, value): Path(p).write_text(json.dumps(value, indent=1)+'\n', encoding='utf-8')

def main():
    assert len(sys.argv) == 3, 'recipe/receipt.json fresh_output_directory'
    recipe = Path(sys.argv[1]).resolve(); out = Path(sys.argv[2]).resolve()
    assert out.is_relative_to(H) and not out.exists()
    r = read(recipe); parent = Path(r['parent_native_board_file'])
    assert sha(parent) == r['parent_native_board_sha256'] == 'eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
    assert r['host_retained_relationships_pass'], 'Retained host contact gate must pass before native staging'
    assert r['old_zone_removals'] == r['old_zone_replacements'] == []
    model = Path(r['frozen_host_model_file']); audit = Path(r['full_original198b_and_dc936_contact_audit_file'])
    assert sha(model) == r['frozen_host_model_sha256'] and sha(audit) == r['full_original198b_and_dc936_contact_audit_sha256']
    inv = NC.C.inventory(parent.read_bytes()); added = []; ids = set()
    rows = r['native_zone_rows'] + r['native_discrete_rows']
    pins = {str(p.resolve()): sha(p) for p in (Path(__file__), recipe, parent, parent.with_suffix('.kicad_pro'), parent.with_suffix('.kicad_dru'), model, audit)}
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
    data = inv[0] + b''.join(inv[1]) + b''.join(added) + inv[2]
    after = NC.C.inventory(data)
    assert after[0] == inv[0] and after[2] == inv[2]
    assert all(after[3][uid] == chunk for uid, chunk in inv[3].items())
    out.mkdir(); copy = out/'copy'; copy.mkdir(); board = copy/'board.kicad_pcb'; board.write_bytes(data)
    shutil.copy2(parent.with_suffix('.kicad_pro'), board.with_suffix('.kicad_pro'))
    board.with_suffix('.kicad_dru').write_bytes(parent.with_suffix('.kicad_dru').read_bytes()+b'\n'+rule.read_bytes())
    command = read(H/'field-power-native-trial-r1/invocation.json')['command']
    parser = Path(command[8]); tree = ast.parse(parser.read_text(encoding='utf-8')); ns = {'re': re}
    decl = [n for n in tree.body if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id == 'TOKEN' or isinstance(n, ast.FunctionDef) and n.name in ('sexpr_parse','child','children','atom','norm')]
    exec(compile(ast.Module(body=decl,type_ignores=[]),'frozen-net-parser','exec'),ns)
    parse, child = ns['sexpr_parse'], ns['child']; iu = lambda v: int(round(float(v)*1000000))
    copper = {}; via = read(H/'field-power-native-trial-r1/native-via-spec.json'); via['board_sha256'] = sha(board)
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
    command[9] = str(via_path); command[10] = str(board); command[-1] = str(out/'native-parity.json')
    original_helper = command[4]; command[4:5] = [str(H/'native_all_copper_contract_r1.py'),original_helper,str(expected)]
    zones = []
    for row in r['native_zone_rows']:
        zones.append({'uuid':row['uuid'],'raw_net':row['raw_net'],'layer':row['layer'],'rings_IU':[row['outer_integer_nm']]+row['hole_integer_nm']})
    zone_spec = out/'expected-zones.json'; write(zone_spec,{'candidate_sha256':sha(board),'zones':zones})
    zone_origin = H/'field-zone-native-contract-r2-layer-sets/native_field_zone_layer_sets_r2.py'
    zone_helper = out/'native_joint_zone_contract.py'; code = zone_origin.read_text(encoding='utf-8')
    anchor = 'PASS_NATIVE_41_FIELD_ZONES_ALL_RINGS_SETTINGS_RAW_NETS'; assert code.count(anchor) == 1
    zone_helper.write_text(code.replace(anchor,'PASS_NATIVE_JOINT_POWER_ZONES_ALL_RINGS_SETTINGS_RAW_NETS'),encoding='utf-8')
    zcmd = read(H/'field-zone-native-contract-r2-layer-sets/invocation.json')['command']
    zcmd[4:] = [str(zone_helper),str(zone_spec),str(board),str(out/'native-zones.json')]
    for path in (pgpath,area,rule,board,board.with_suffix('.kicad_pro'),board.with_suffix('.kicad_dru'),expected,via_path,zone_spec,zone_origin,zone_helper): pins[str(path.resolve())] = sha(path)
    for arg in command+zcmd:
        path = Path(arg)
        if path.is_file(): pins[str(path.resolve())] = sha(path)
    write(out/'inputs.json',pins)
    write(out/'construction.json',{'parent_sha256':sha(parent),'candidate_sha256':sha(board),'all_parent_entities_header_tail_exact':True,'added_segments':r['new_segments'],'added_vias':r['new_vias'],'added_zone_chunks':len(zones),'original_zone_outlines_exact':True,'separate_PG_area':area_uid,'original_rule_bytes_exact_prefix':True,'host_all_supply_rooted':r['host_all_supply_pad_and_proposed_components_rooted'],'AO_recipe_included':False,'adopted':False})
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
