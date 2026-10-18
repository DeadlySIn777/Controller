"""Apply one exact capacitor pose correction and attest every field source pose."""
import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import native_pose_signal_contract as H
C=H.C
PRIOR=HERE/'combined-power-source-native-r1'
OWNED=HERE/'field-power/board-delta-r4-c92-pose'
SOURCE=HERE/'field-power/combined-power-source-r3-hierarchy'
OUT=HERE/'combined-power-source-native-r2-c92'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sha_raw(raw): return hashlib.sha256(raw).hexdigest()
def write(p,o): p.write_text(json.dumps(o,indent=1)+'\n',encoding='utf-8')
def main():
    if OUT.exists(): raise ValueError('Fresh corrected-pose candidate required')
    pins=json.loads((PRIOR/'inputs.json').read_bytes())
    for p,h in pins.items():
        if sha(p)!=h: raise ValueError('Prior construction changed: '+p)
    recipe=json.loads((OWNED/'receipt.json').read_bytes())
    ledger=json.loads((OWNED/'native-pose-ledger.json').read_bytes())
    if recipe['verdict']!='PASS_EXACT_C92_ROOT_POSE_AND_REFERENCE_ANCHOR_CORRECTION' or ledger['verdict']!='PASS_HOST_ABSOLUTE_PAD_AND_SOURCE_LEDGER': raise ValueError('Pose proposal not valid')
    r3=json.loads((SOURCE/'source-export/receipt-r2.json').read_bytes())
    if r3['verdict']!='PASS' or r3['hierarchy_zero_electrical_delta']!='PASS' or sha(SOURCE/'source-export/fresh.net')!=ledger['fresh_native_source_sha256']: raise ValueError('Pose source identity differs')
    extra_paths=[Path(__file__),OWNED/'receipt.json',OWNED/'native-pose-ledger.json',Path(recipe['corrected_chunk_path']),SOURCE/'receipt.json',SOURCE/'source-export/receipt-r2.json',SOURCE/'source-export/fresh.net',HERE/'combined-power-native-repeat-r3/receipt.json',HERE/'native_entry_diagnostic_r4.py']
    pins.update({str(p.resolve()):sha(p) for p in extra_paths})
    raw=(PRIOR/'combined-power-source-host-only.kicad_pcb').read_bytes();inv=C.inventory(raw)
    uid=recipe['footprint_uuid'];old=inv[3][uid];replacement=Path(recipe['corrected_chunk_path']).read_bytes()
    if sha_raw(old)!=recipe['before_sha256'] or sha_raw(replacement)!=recipe['corrected_chunk_sha256']: raise ValueError('Capacitor exact source chunks differ')
    wanted=old
    for field in recipe['exact_two_field_changes']:
        before=field['before'].encode();after=field['after'].encode()
        if wanted.count(before)!=1: raise ValueError('Pose correction field not unique')
        wanted=wanted.replace(before,after,1)
    if wanted!=replacement: raise ValueError('Capacitor changes more than declared root pose and reference anchor')
    result=inv[0]+b''.join(replacement if C.pcbtext.chunk_uuid(ch)==uid else ch for ch in inv[1])+inv[2]
    new=C.inventory(result)
    if new[0]!=inv[0] or new[2]!=inv[2] or set(new[3])!=set(inv[3]) or any(new[3][u]!=ch for u,ch in inv[3].items() if u!=uid): raise ValueError('Unowned candidate entity changed')
    for row in ledger['rows']:
        p=Path(row['chunk_path']);pins[str(p.resolve())]=sha(p)
        if sha(p)!=row['chunk_sha256'] or new[3][row['native_footprint_uuid']]!=p.read_bytes(): raise ValueError('Frozen full pose ledger chunk differs: '+row['ref'])
    OUT.mkdir();candidate=OUT/'combined-power-source-c92-corrected.kicad_pcb';candidate.write_bytes(result)
    copy=OUT/'copy';copy.mkdir();board=copy/'board.kicad_pcb';shutil.copy2(candidate,board)
    for ext in ['.kicad_pro','.kicad_dru']: shutil.copy2((PRIOR/'copy/board.kicad_pcb').with_suffix(ext),board.with_suffix(ext))
    spec=json.loads((PRIOR/'native-via-spec.json').read_bytes());spec['board_sha256']=sha(candidate);write(OUT/'native-via-spec.json',spec)
    original=(HERE/'native_entry_diagnostic_r4.py').read_text()
    helper=OUT/'native_entry_pose_r5.py'
    original=original.replace('import hashlib, importlib.util, json, sys','import hashlib, importlib.util, json, sys, math')
    marker='    tool_path, spec_path = Path(argv[0]), Path(argv[1])\n'
    if original.count(marker)!=1: raise ValueError('Native entry argument marker differs')
    original=original.replace(marker,"    pose_ledger_path=Path(argv.pop(0))\n"+marker)
    marker='        output.write_text(json.dumps(report,indent=1)+\'\\n\',encoding=\'utf-8\')\n'
    pose_code='''        pose=json.loads(pose_ledger_path.read_bytes())
        footprints={str(f.GetReference()):f for f in board.GetFootprints()}
        pose_rows=[]
        for row in pose['rows']:
            fp=footprints[row['ref']]
            if str(fp.m_Uuid.AsString())!=row['native_footprint_uuid'] or str(fp.GetPath().AsString())!=row['schematic_path'] or str(fp.GetLayerName())!=row['layer']:raise ValueError('Native field footprint identity/path/side differs:'+row['ref'])
            position=fp.GetPosition();at=[pcbnew.ToMM(position.x),pcbnew.ToMM(position.y)]
            angle=fp.GetOrientationDegrees();planned=row['root_pose_mm_deg']
            if at!=planned[:2] or abs((angle-planned[2]+180)%360-180)>1e-9:raise ValueError('Native field root pose differs:'+row['ref'])
            pads={str(p.m_Uuid.AsString()):p for p in fp.Pads()}
            if set(pads)!={p['pad_uuid'] for p in row['pads']}:raise ValueError('Native field pad inventory differs:'+row['ref'])
            observed=[]
            for expected_pad in row['pads']:
                pad=pads[expected_pad['pad_uuid']];at_pad=pad.GetPosition();point=[pcbnew.ToMM(at_pad.x),pcbnew.ToMM(at_pad.y)]
                delta=math.dist(point,expected_pad['absolute_center_mm'])
                if str(pad.GetNumber())!=expected_pad['pin'] or str(pad.GetNetname())!=expected_pad['raw_net'] or delta>.003000001:raise ValueError('Native field absolute pad identity/net/pose differs:'+row['ref']+'/'+expected_pad['pin'])
                flashed=[str(board.GetLayerName(layer)) for layer in layer_ids if pad.FlashLayer(layer)]
                if set(flashed)!=set(expected_pad['actual_original_clone_native_flashes']):raise ValueError('Native field actual pad annuli differ:'+row['ref']+'/'+expected_pad['pin'])
                observed.append({'uuid':expected_pad['pad_uuid'],'pin':expected_pad['pin'],'net_raw':str(pad.GetNetname()),'actual_nm':[int(at_pad.x),int(at_pad.y)],'actual_mm':point,'host_absolute_center_delta_mm':delta,'actual_flashed_layers':flashed})
            pose_rows.append({'ref':row['ref'],'actual_root_pose_mm_deg':at+[angle],'pads':observed})
        report['source_owned_native_poses']={'verdict':'PASS','rows':pose_rows,'footprints':len(pose_rows),'exact_root_pose_required':True,'absolute_pad_center_planning_model_budget_mm':.003,'actual_pad_raw_nets_UUIDs_numbers_and_flash_masks_exact':True,'no_refill_DRC_or_save':True}
'''
    if original.count(marker)!=1: raise ValueError('Native report write marker differs')
    helper.write_text(original.replace(marker,pose_code+marker),encoding='utf-8')
    prior_command=json.loads((PRIOR/'invocation.json').read_bytes())['command'];command=prior_command[:4]+[str(helper.resolve()),str((OWNED/'native-pose-ledger.json').resolve()),prior_command[5],str((OUT/'native-via-spec.json').resolve()),str(board.resolve()),'--netlist',str((SOURCE/'source-export/fresh.net').resolve()),'--no-connectivity','--examples','40',str((OUT/'native-parity.json').resolve())]
    pins.update({str(p.resolve()):sha(p) for p in [candidate,board,board.with_suffix('.kicad_pro'),board.with_suffix('.kicad_dru'),helper,OUT/'native-via-spec.json']})
    for p,h in pins.items():
        if sha(p)!=h: raise ValueError('Construction input changed: '+p)
    write(OUT/'construction.json',{'parent_sha256':sha_raw(raw),'candidate_sha256':sha(candidate),'exact_owned_changes':recipe['exact_two_field_changes'],'unowned_whole_board_entities_exact':True,'fresh_source_netlist_sha256':sha(SOURCE/'source-export/fresh.net'),'native_pose_ledger_sha256':sha(OWNED/'native-pose-ledger.json'),'all19_footprint_chunks_bound_before_native':True,'adopted':False})
    write(OUT/'inputs.json',pins);write(OUT/'invocation.json',{'command':command,'existing_slot':'test-only1','new_heavy_slots':0,'refill':False,'DRC':False,'board_save':False})
    env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
    with (OUT/'native.log').open('w',encoding='utf-8') as log:run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
    for p,h in pins.items():
        if sha(p)!=h: raise ValueError('Native input changed: '+p)
    api=json.loads((OUT/'native-parity.json').read_bytes()) if (OUT/'native-parity.json').exists() else {}
    passed=run.returncode==0 and api.get('summary',{}).get('parity_defects')==0 and api.get('source_owned_native_poses',{}).get('verdict')=='PASS' and api.get('added_via_annuli',{}).get('verdict')=='PASS'
    receipt={'verdict':'PASS_SOURCE_NATIVE_API_AND19_POSES' if passed else 'FAIL_NATIVE_POSE_OR_API_GATE','candidate_sha256':sha(candidate),'native_exit_code':run.returncode,'native_summary':api.get('summary'),'native_pose_count':api.get('source_owned_native_poses',{}).get('footprints'),'actual_added_via_count':len(api.get('added_via_annuli',{}).get('rows',[])),'full_refill_DRC_dual_connectivity':'NOT_EXECUTED','adopted':False}
    write(OUT/'receipt.json',receipt);print(json.dumps(receipt),flush=True)
    return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
