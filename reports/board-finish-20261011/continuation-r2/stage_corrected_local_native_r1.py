"""Attest corrected local copper/zone serialization in an isolated native clone.

This is a source/API geometry gate only. Final CORE/IO3/protected24, fresh fill
and contact/current acceptance remain separate mandatory gates.
"""
import ast,hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;OUT=H/'corrected-local-native-contract-r1'
sys.path.insert(0,str(H));import native_pose_signal_contract as NC
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
    assert not OUT.exists()
    recipe=H/'field-power/corrected-local-native-recipe-r22/receipt.json';r=json.loads(recipe.read_bytes());assert sha(recipe)=='2c3478cf494b8944c0e1c6b2e1437655f244b4a41b813ce25455feeacc1c7f36'
    stage=H/'field-power-native-trial-r1';parent=stage/'copy/board.kicad_pcb';assert sha(parent)=='dc93656a303d8a507369617ef60ac4f3aaf5b78e6f8bb699a391ed5a8b6ccb6b'
    inv=NC.C.inventory(parent.read_bytes());add=[];ids=set()
    for row in r['discrete_rows']+r['zone_rows']:
        p=Path(row['chunk_path']);assert sha(p)==row['chunk_sha256'];chunk=p.read_bytes();uid=NC.C.pcbtext.chunk_uuid(chunk)
        assert uid==row['uuid'] and uid not in inv[3] and uid not in ids
        ids.add(uid);add.append(chunk)
    data=inv[0]+b''.join(inv[1])+b''.join(add)+inv[2];after=NC.C.inventory(data)
    assert all(after[3][uid]==chunk for uid,chunk in inv[3].items()) and after[0]==inv[0] and after[2]==inv[2]
    OUT.mkdir();copy=OUT/'copy';copy.mkdir();board=copy/'board.kicad_pcb';board.write_bytes(data)
    for ext in ('.kicad_pro','.kicad_dru'):shutil.copy2(parent.with_suffix(ext),board.with_suffix(ext))
    command=json.loads((stage/'invocation.json').read_bytes())['command'];parser=Path(command[8]);ns={'re':re};tree=ast.parse(parser.read_text(encoding='utf-8'))
    decl=[n for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='TOKEN' or isinstance(n,ast.FunctionDef) and n.name in ('sexpr_parse','child','children','atom','norm')]
    exec(compile(ast.Module(body=decl,type_ignores=[]),'frozen-root106-net-parser','exec'),ns);parse,child=ns['sexpr_parse'],ns['child'];iu=lambda v:int(round(float(v)*1000000))
    copper={}
    for uid,ch in after[4].items():
        root=parse(ch.decode());kind=root[0];net=child(root,'net');row={'kind':kind,'raw_net':net[1] if net else '','chunk_sha256':hashlib.sha256(ch).hexdigest()}
        if kind=='via':row.update(at_IU=list(map(iu,child(root,'at')[1:3])),drill_IU=iu(child(root,'drill')[1]),diameters_IU={l:iu(child(root,'size')[1]) for l in ('F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu')})
        elif kind=='segment':row.update(start_IU=list(map(iu,child(root,'start')[1:3])),end_IU=list(map(iu,child(root,'end')[1:3])),width_IU=iu(child(root,'width')[1]),layer=child(root,'layer')[1])
        else:raise ValueError('Unsupported Cu kind '+kind)
        copper[uid]=row
    expected=OUT/'all-copper-expected.json';write(expected,{'board_path':str(board.resolve()),'board_sha256':sha(board),'copper':copper})
    via=json.loads((stage/'native-via-spec.json').read_bytes());via['board_sha256']=sha(board)
    for row in r['discrete_rows']:
        if row['kind']!='via':continue
        v=row['geometry'];via['added_vias'].append({'uuid':v['uuid'],'net':v['net'].replace('{slash}','/'),'net_raw':v['net'],'at':[v['x'],v['y']],'d':v['d'],'drill':v['drill']})
    via_path=OUT/'native-via-spec.json';write(via_path,via)
    command[9]=str(via_path.resolve());command[10]=str(board.resolve());command[-1]=str((OUT/'native-parity.json').resolve());original_helper=command[4]
    command[4:5]=[str((H/'native_all_copper_contract_r1.py').resolve()),original_helper,str(expected.resolve())]
    zone_expected=[]
    for row in r['zone_rows']:
        root=parse(Path(row['chunk_path']).read_text(encoding='utf-8'));rings=[]
        for polygon in root[1:]:
            if not isinstance(polygon,list) or polygon[0]!='polygon':continue
            pts=child(polygon,'pts');rings.append([list(map(iu,q[1:3])) for q in pts[1:] if isinstance(q,list) and q[0]=='xy'])
        assert len(rings)==1+row['hole_rings']
        zone_expected.append({'uuid':row['uuid'],'raw_net':row['raw_net'],'layer':row['layer'],'rings_IU':rings})
    zone_spec=OUT/'expected-zones.json';write(zone_spec,{'candidate_sha256':sha(board),'zones':zone_expected})
    zone_original=H/'field-zone-native-contract-r2-layer-sets/native_field_zone_layer_sets_r2.py';zone_helper=OUT/'native_local_zone_contract.py';zcode=zone_original.read_text(encoding='utf-8');anchor='PASS_NATIVE_41_FIELD_ZONES_ALL_RINGS_SETTINGS_RAW_NETS';assert zcode.count(anchor)==1
    zone_helper.write_text(zcode.replace(anchor,'PASS_NATIVE_52_CORRECTED_LOCAL_ZONES_ALL_RINGS_SETTINGS_RAW_NETS'),encoding='utf-8')
    zcmd=json.loads((H/'field-zone-native-contract-r2-layer-sets/invocation.json').read_bytes())['command'];zcmd[4:]=[str(zone_helper.resolve()),str(zone_spec.resolve()),str(board.resolve()),str((OUT/'native-zones.json').resolve())]
    pins={str(p.resolve()):sha(p) for p in (Path(__file__),recipe,parent,parent.with_suffix('.kicad_pro'),parent.with_suffix('.kicad_dru'),board,board.with_suffix('.kicad_pro'),board.with_suffix('.kicad_dru'),expected,via_path,zone_spec,zone_original,zone_helper)}
    for row in r['discrete_rows']+r['zone_rows']:pins[row['chunk_path']]=row['chunk_sha256']
    for arg in command+zcmd:
        p=Path(arg)
        if p.is_file():pins[str(p.resolve())]=sha(p)
    write(OUT/'inputs.json',pins);write(OUT/'invocation.json',{'source_pose_87via_all_Cu_command':command,'52_exact_zone_command':zcmd,'existing_slot':'test-only1','new_heavy_slots':0,'no_save_refill_DRC':True})
    write(OUT/'construction.json',{'parent_sha256':sha(parent),'candidate_sha256':sha(board),'all_parent_entities_header_tail_exact':True,'added_vias':19,'added_segments':98,'added_zones':52,'project_and_DRC_rule_bytes_unchanged_from_PG_trial':True,'final_CORE_IO3_protected_B5_analog_and_mutual_contacts_current':'OPEN','existing18701851_In3_flash':'Prospective; mandatory after fresh refill','adopted':False})
    env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH'];results=[]
    for name,cmd in [('source-all-copper',command),('zones',zcmd)]:
        with (OUT/(name+'.log')).open('w',encoding='utf-8') as log:run=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
        results.append({'name':name,'exit_code':run.returncode})
        if run.returncode:break
    for p,digest in pins.items():assert sha(p)==digest,('Frozen input changed',p)
    api=json.loads((OUT/'native-parity.json').read_bytes()) if (OUT/'native-parity.json').exists() else {};zones=json.loads((OUT/'native-zones.json').read_bytes()) if (OUT/'native-zones.json').exists() else {}
    ok=len(results)==2 and all(x['exit_code']==0 for x in results) and api.get('all_discrete_copper_exact_native_contract',{}).get('verdict')=='PASS' and zones.get('native_zones_checked')==52 and not zones.get('errors')
    receipt={'verdict':'PASS_SOURCE_POSE_87_VIAS_ALL_DISCRETE_AND_52_LOCAL_ZONES_API_ONLY' if ok else 'FAIL_CORRECTED_LOCAL_NATIVE_API','candidate_sha256':sha(board),'runs':results,'source_API_summary':api.get('summary'),'all_native_discrete':api.get('all_discrete_copper_exact_native_contract'),'zone_count':zones.get('native_zones_checked'),'zone_holes':zones.get('native_holes_checked'),'source_full_mutual_current_flash_and_DRC_after_refill':'OPEN; partial geometry-only clone excludes final power feeds','adopted':False,'native_saved_or_refilled':False};write(OUT/'receipt.json',receipt)
    print(json.dumps({'verdict':receipt['verdict'],'candidate_sha256':sha(board),'zones':receipt['zone_count'],'native_Cu':receipt['all_native_discrete'],'runs':results}),flush=True)
    return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
