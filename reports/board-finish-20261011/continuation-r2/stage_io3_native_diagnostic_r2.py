"""Exact AO R18 operation on the source-bound field clone, API then scoped fill."""
import ast,hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;OUT=H/'io3-native-diagnostic-r2'
sys.path.insert(0,str(H));import native_pose_signal_contract as NC
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
    assert not OUT.exists()
    recipe=H/'sbc-power/owned-io3-native-recipe-r45/receipt.json';zones_recipe=H/'sbc-power/owned-io3-selected-native-zones-r46/receipt.json'
    assert sha(recipe)=='33f764e286538085341d130d7ede6f5d3d2a7330924605d9ee4d94eb52d5c0eb'
    assert sha(zones_recipe)=='9db1363bd9d90d6d2ec1c74db6443c95a90cf38d59e76c0d75b0907026073cb1'
    r=json.loads(recipe.read_bytes());zr=json.loads(zones_recipe.read_bytes());assert r['IO3_source_host_pass'] and r['protected_screen_PASS']
    stage=H/'field-power-native-trial-r1';parent=H/'sbc-native-contract-r1/copy/board.kicad_pcb'
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
    data=inv[0]+b''.join(ch for ch in inv[1] if NC.C.pcbtext.chunk_uuid(ch) not in removed)+b''.join(new.values())+inv[2];after=NC.C.inventory(data)
    assert after[0]==inv[0] and after[2]==inv[2] and all(after[3].get(u)==ch for u,ch in inv[3].items() if u not in removed)
    assert all(NC.C.pcbtext.chunk_uuid(ch)==u and NC.C.pcbtext.chunk_kind(ch) in ('via','segment','zone') for u,ch in new.items())
    OUT.mkdir();copy=OUT/'copy';copy.mkdir();board=copy/'board.kicad_pcb';board.write_bytes(data)
    for ext in ('.kicad_pro','.kicad_dru'):shutil.copy2(parent.with_suffix(ext),board.with_suffix(ext))
    command=json.loads((stage/'invocation.json').read_bytes())['command'];parser=Path(command[8]);tree=ast.parse(parser.read_text());ns={'re':re};decl=[n for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='TOKEN' or isinstance(n,ast.FunctionDef) and n.name in ('sexpr_parse','child','children','atom','norm')];exec(compile(ast.Module(body=decl,type_ignores=[]),'frozen-parser','exec'),ns);parse,child=ns['sexpr_parse'],ns['child'];iu=lambda v:int(round(float(v)*1000000));copper={};via=json.loads((stage/'native-via-spec.json').read_bytes());via['board_sha256']=sha(board)
    for uid,ch in after[4].items():
        root=parse(ch.decode());kind=root[0];net=child(root,'net');row={'kind':kind,'raw_net':net[1] if net else '','chunk_sha256':hashlib.sha256(ch).hexdigest()}
        if kind=='via':
            row.update(at_IU=list(map(iu,child(root,'at')[1:3])),drill_IU=iu(child(root,'drill')[1]),diameters_IU={l:iu(child(root,'size')[1]) for l in ('F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu')})
            if uid in new:via['added_vias'].append({'uuid':uid,'net':row['raw_net'].replace('{slash}','/'),'net_raw':row['raw_net'],'at':[float(x) for x in child(root,'at')[1:3]],'d':float(child(root,'size')[1]),'drill':float(child(root,'drill')[1])})
        elif kind=='segment':row.update(start_IU=list(map(iu,child(root,'start')[1:3])),end_IU=list(map(iu,child(root,'end')[1:3])),width_IU=iu(child(root,'width')[1]),layer=child(root,'layer')[1])
        else:raise ValueError('Unsupported copper kind')
        copper[uid]=row
    expected=OUT/'expected-Cu.json';write(expected,{'board_path':str(board.resolve()),'board_sha256':sha(board),'copper':copper});via_path=OUT/'native-via-spec.json';write(via_path,via)
    command[9]=str(via_path.resolve());command[10]=str(board.resolve());command[-1]=str((OUT/'native-parity.json').resolve());original_helper=command[4];command[4:5]=[str((H/'native_all_copper_contract_r1.py').resolve()),original_helper,str(expected.resolve())]
    fill_command=['C:/Program Files/Git/usr/bin/sh.exe','Z:/pcb-runs/claude-finish/tools/heavyt.sh','kicad','C:/Program Files/KiCad/10.0/bin/python.exe',str((H/'native_io3_scoped_refill_r1.py').resolve()),str(board.resolve()),str(expected.resolve()),str((OUT/'scoped-native-fill').resolve())]
    pins={str(p.resolve()):sha(p) for p in (Path(__file__),recipe,zones_recipe,*chunk_inputs,parent,parent.with_suffix('.kicad_pro'),parent.with_suffix('.kicad_dru'),board,board.with_suffix('.kicad_pro'),board.with_suffix('.kicad_dru'),expected,via_path)}
    for arg in command+fill_command:
        p=Path(arg)
        if p.is_file():pins[str(p.resolve())]=sha(p)
    zspec=OUT/'expected-zones.json';write(zspec,{'candidate_sha256':sha(board),'zones':[{'uuid':q['uuid'],'raw_net':q['raw_net'],'layer':q['layer'],'rings_IU':q['outline_integer_nm']} for q in zr['native_zone_rows']]})
    zhelper=H/'native_io3_selected_zone_contract_r1.py'
    zcmd=['C:/Program Files/Git/usr/bin/sh.exe','Z:/pcb-runs/claude-finish/tools/heavyt.sh','kicad','C:/Program Files/KiCad/10.0/bin/python.exe',str(zhelper.resolve()),str(zspec.resolve()),str(board.resolve()),str((OUT/'native-zones.json').resolve())]
    pins[str(zspec.resolve())]=sha(zspec);pins[str(zhelper.resolve())]=sha(zhelper)
    write(OUT/'inputs.json',pins);write(OUT/'invocation.json',{'source_all_Cu_API_command':command,'selected_IO3_COM_fill_command':fill_command,'existing_slot':'test-only1','new_heavy_slots':0})
    write(OUT/'construction.json',{'parent_sha256':sha(parent),'candidate_sha256':sha(board),'exact2_owned_Cu_deleted':sorted(removed),'exact3_owned_Cu_added':sorted(set(new)-zone_ids),'selected_new_IO3_zone_added':sorted(zone_ids),'all_unowned_entities_source_poses_zone_definitions_header_tail_unchanged':True,'all_reference_and_final_power_gates':'OPEN','adopted':False})
    env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
    with (OUT/'api.log').open('w',encoding='utf-8') as log:api_run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
    assert all(sha(p)==v for p,v in pins.items())
    if api_run.returncode:
        write(OUT/'receipt.json',{'verdict':'FAIL_IO3_NATIVE_API_BEFORE_REFILL','native_exit':api_run.returncode,'candidate_sha256':sha(board),'adopted':False});return api_run.returncode
    api=json.loads((OUT/'native-parity.json').read_bytes());assert api['all_discrete_copper_exact_native_contract']['verdict']=='PASS'
    with (OUT/'native-zone.log').open('w',encoding='utf-8') as log:zone_run=subprocess.run(zcmd,env=env,stdout=log,stderr=subprocess.STDOUT)
    assert zone_run.returncode==0
    zone_native=json.loads((OUT/'native-zones.json').read_bytes());assert not zone_native['errors'] and zone_native['native_zones_checked']==1

    write(OUT/'receipt.json',{'verdict':'PASS_IO3_SOURCE_POSE_69_VIA_ALL_CU_API_SCOPED_REFILL_RUNNING','candidate_sha256':sha(board),'source_API_summary':api['summary'],'all_native_discrete':api['all_discrete_copper_exact_native_contract'],'source_contact_and_F_In1_actual_flash_gate':'OPEN; independent selected fresh fill review required','adopted':False})
    print('IO3_SOURCE_API_ALL_CU_PASS_START_SELECTED_IO3_REFILL',flush=True)
    with (OUT/'scoped-fill.log').open('w',encoding='utf-8') as log:fill_run=subprocess.run(fill_command,env=env,stdout=log,stderr=subprocess.STDOUT)
    assert all(sha(p)==v for p,v in pins.items())
    fill=OUT/'scoped-native-fill/receipt.json'
    final={'verdict':'IO3_NATIVE_SELECTED_REFILL_COMPLETE_INDEPENDENT_REFERENCE_REVIEW_OPEN' if fill_run.returncode==0 else 'FAIL_IO3_SELECTED_NATIVE_REFILL','candidate_sha256':sha(board),'source_API_summary':api['summary'],'all_native_discrete':api['all_discrete_copper_exact_native_contract'],'scoped_fill_receipt_sha256':sha(fill) if fill.exists() else None,'native_fill_exit':fill_run.returncode,'whole_board_refill_DRC_retained_contacts_current_and_final_power_composition':'OPEN','selected_trial_scope':'eedf plus exact2-owned-track replacement and one IO3 plane only; other R38 power proposals excluded','adopted':False}
    write(OUT/'receipt.json',final);print(json.dumps({'verdict':final['verdict'],'native_fill_exit':fill_run.returncode}),flush=True);return fill_run.returncode
if __name__=='__main__':raise SystemExit(main())
