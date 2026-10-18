"""Exact AO R18 operation on the source-bound field clone, API then scoped fill."""
import ast,hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;OUT=H/'core1v2-native-diagnostic-r132'
sys.path.insert(0,str(H));import native_pose_signal_contract as NC
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
    assert not OUT.exists()
    recipe=H/'sbc-power/selected-CORE1V2-native-recipe-r130/receipt.json';analytic=H/'sbc-power/selected-CORE1V2-strict-geometry-r131/receipt.json'
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
    fill_command=['C:/Program Files/Git/usr/bin/sh.exe','Z:/pcb-runs/claude-finish/tools/heavyt.sh','kicad','C:/Program Files/KiCad/10.0/bin/python.exe',str((H/'native_core1v2_scoped_refill_r132.py').resolve()),str(board.resolve()),str(expected.resolve()),str((OUT/'scoped-native-fill').resolve())]
    pins={str(p.resolve()):sha(p) for p in (Path(__file__),recipe,analytic,*chunk_inputs,parent,parent.with_suffix('.kicad_pro'),parent.with_suffix('.kicad_dru'),board,board.with_suffix('.kicad_pro'),board.with_suffix('.kicad_dru'),expected,via_path)}
    for arg in command+fill_command:
        p=Path(arg)
        if p.is_file():pins[str(p.resolve())]=sha(p)
    declared=[]
    for q in zr['native_zone_rows']:
        d=q['declared_native_settings'];assert d['pad_connect_mode']=='FULL_SOLID'
        settings={'priority':int(d['priority']),'local_clearance_IU':iu(d['local_clearance_mm']),'minimum_thickness_IU':iu(d['min_thickness_mm']),'thermal_gap_IU':iu(d['thermal_gap_mm']),'thermal_spoke_IU':iu(d['thermal_bridge_width_mm']),'island_removal_mode':int(d['island_removal_mode'])}
        declared.append({'uuid':q['uuid'],'raw_net':q['raw_net'],'layer':q['layer'],'rings_IU':[q['outer_integer_nm']]+q['hole_integer_nm'],'declared_native_settings':settings})
    zspec=OUT/'expected-zones.json';write(zspec,{'candidate_sha256':sha(board),'zones':declared})
    zhelper=H/'native_declared_selected_zone_contract_r2.py'
    zcmd=['C:/Program Files/Git/usr/bin/sh.exe','Z:/pcb-runs/claude-finish/tools/heavyt.sh','kicad','C:/Program Files/KiCad/10.0/bin/python.exe',str(zhelper.resolve()),str(zspec.resolve()),str(board.resolve()),str((OUT/'native-zones.json').resolve())]
    pins[str(zspec.resolve())]=sha(zspec);pins[str(zhelper.resolve())]=sha(zhelper)
    write(OUT/'inputs.json',pins);write(OUT/'invocation.json',{'source_all_Cu_API_command':command,'selected_CORE1V2_COM_fill_command':fill_command,'existing_slot':'test-only1','new_heavy_slots':0})
    write(OUT/'construction.json',{'parent_sha256':sha(parent),'candidate_sha256':sha(board),'exact0_owned_Cu_deleted':sorted(removed),'exact1_owned_Cu_added':sorted(set(new)-zone_ids),'selected_new_CORE1V2_zone_added':sorted(zone_ids),'all_unowned_entities_source_poses_zone_definitions_header_tail_unchanged':True,'all_reference_and_final_power_gates':'OPEN','adopted':False})
    env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
    with (OUT/'api.log').open('w',encoding='utf-8') as log:api_run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
    assert all(sha(p)==v for p,v in pins.items())
    if api_run.returncode:
        write(OUT/'receipt.json',{'verdict':'FAIL_CORE1V2_NATIVE_API_BEFORE_REFILL','native_exit':api_run.returncode,'candidate_sha256':sha(board),'adopted':False});return api_run.returncode
    api=json.loads((OUT/'native-parity.json').read_bytes());assert api['all_discrete_copper_exact_native_contract']['verdict']=='PASS'
    with (OUT/'native-zone.log').open('w',encoding='utf-8') as log:zone_run=subprocess.run(zcmd,env=env,stdout=log,stderr=subprocess.STDOUT)
    assert zone_run.returncode==0
    zone_native=json.loads((OUT/'native-zones.json').read_bytes());assert not zone_native['errors'] and zone_native['native_zones_checked']==1

    write(OUT/'receipt.json',{'verdict':'PASS_CORE1V2_SOURCE_POSE_68_VIA_ALL_CU_API_SCOPED_REFILL_RUNNING','candidate_sha256':sha(board),'source_API_summary':api['summary'],'all_native_discrete':api['all_discrete_copper_exact_native_contract'],'source_contact_and_original_F_In3_plus_fresh_In4_actual_flash_gate':'OPEN; independent selected fresh fill review required','adopted':False})
    print('CORE1V2_SOURCE_API_ALL_CU_PASS_START_SELECTED_CORE1V2_REFILL',flush=True)
    with (OUT/'scoped-fill.log').open('w',encoding='utf-8') as log:fill_run=subprocess.run(fill_command,env=env,stdout=log,stderr=subprocess.STDOUT)
    assert all(sha(p)==v for p,v in pins.items())
    fill=OUT/'scoped-native-fill/receipt.json'
    final={'verdict':'CORE1V2_NATIVE_SELECTED_REFILL_COMPLETE_INDEPENDENT_REFERENCE_REVIEW_OPEN' if fill_run.returncode==0 else 'FAIL_CORE1V2_SELECTED_NATIVE_REFILL','candidate_sha256':sha(board),'source_API_summary':api['summary'],'all_native_discrete':api['all_discrete_copper_exact_native_contract'],'scoped_fill_receipt_sha256':sha(fill) if fill.exists() else None,'native_fill_exit':fill_run.returncode,'whole_board_refill_DRC_retained_contacts_current_and_final_power_composition':'OPEN','selected_trial_scope':'eedf plus exact J7 .20 F track and one In4 CORE1V2 plane only; complete CORE c7 and other power proposals excluded','adopted':False}
    write(OUT/'receipt.json',final);print(json.dumps({'verdict':final['verdict'],'native_fill_exit':fill_run.returncode}),flush=True);return fill_run.returncode
if __name__=='__main__':raise SystemExit(main())
