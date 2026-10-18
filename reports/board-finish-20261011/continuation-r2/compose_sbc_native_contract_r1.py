"""Apply only frozen owned SBC parts/copper for a separate native contract check."""
import hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import native_pose_signal_contract as H
C=H.C
OUT=HERE/'sbc-native-contract-r1';STAGE=HERE/'combined-reset-cm-native-r5-cache-refresh'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
    if OUT.exists():raise ValueError('Fresh SBC native contract required')
    recipe_path=HERE/'sbc-power/owned-native-parts-r4/receipt.json'
    mask_path=recipe_path.parent/'pad-mask-and-text-ledger.json'
    recipe=json.loads(recipe_path.read_bytes());mask=json.loads(mask_path.read_bytes())
    parent=STAGE/'combined-reset-cm-cache-refreshed.kicad_pcb';raw=parent.read_bytes();inv=C.inventory(raw)
    if sha(recipe_path)!='5e44a6779ad8c19051784945deaaa40cd6cbf922d6020677000dd07aa3bd04f6' or sha(mask_path)!='06e746713daa74fcb5c11908d4944cb654d82582789b31963b998118da7d0d94':raise ValueError('Frozen SBC recipe changed')
    if sha(parent)!=recipe['parent_board_sha256'] or mask['source_parent_sha256']!=sha(parent):raise ValueError('Recipe parent changed')
    pins={str(p.resolve()):sha(p) for p in [Path(__file__),HERE/'native_sbc_contract_r1.py',recipe_path,mask_path,parent,STAGE/'receipt.json']}; replacements={};deletes=set();adds={}
    for row in recipe['footprint_replacements']:
        u=row['uuid'];p=Path(row['new_chunk_path']);chunk=p.read_bytes()
        if digest(inv[3][u])!=row['original_parent_chunk_sha256'] or digest(chunk)!=row['new_chunk_sha256'] or C.pcbtext.chunk_uuid(chunk)!=u:raise ValueError('Frozen footprint chunk differs')
        replacements[u]=chunk;pins[str(p.resolve())]=sha(p)
    for row in recipe['old_Cu_removals']:
        if digest(inv[4][row['uuid']])!=row['sha256']:raise ValueError('Owned copper deletion differs')
        deletes.add(row['uuid'])
    for row in recipe['new_Cu_items']:
        p=Path(row['new_chunk_path']);chunk=p.read_bytes();u=row['uuid']
        if digest(chunk)!=row['new_chunk_sha256'] or C.pcbtext.chunk_uuid(chunk)!=u or u in inv[3] or u in adds:raise ValueError('New copper identity differs')
        adds[u]=chunk;pins[str(p.resolve())]=sha(p)
    if len(replacements)!=7 or len(deletes)!=27 or len(adds)!=132:raise ValueError('Owned recipe inventory differs')
    result=inv[0]+b''.join(replacements.get(C.pcbtext.chunk_uuid(ch),ch) for ch in inv[1] if C.pcbtext.chunk_uuid(ch) not in deletes)+b''.join(adds.values())+inv[2]
    after=C.inventory(result)
    if after[0]!=inv[0] or after[2]!=inv[2] or set(after[3])!=(set(inv[3])-deletes)|set(adds):raise ValueError('Design inventory changed outside recipe')
    if any(after[3].get(u)!=ch for u,ch in inv[3].items() if u not in deletes|set(replacements)):raise ValueError('Unowned design primitive changed')
    identity=H.N.SourceNets(result).assert_no_collisions(result)
    OUT.mkdir();candidate=OUT/'sbc-owned-native-contract.kicad_pcb';candidate.write_bytes(result)
    copy=OUT/'copy';copy.mkdir();board=copy/'board.kicad_pcb';shutil.copy2(candidate,board)
    for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2((STAGE/'copy/board.kicad_pcb').with_suffix(ext),board.with_suffix(ext))
    pose=json.loads((HERE/'field-power/board-delta-r4-c92-pose/native-pose-ledger.json').read_bytes())
    if {r['ref'] for r in pose['rows']}&{r['ref'] for r in mask['footprints']}:raise ValueError('Overlapping owned pose ledgers')
    for row in mask['footprints']:
        chunk=replacements[row['footprint_UUID']];path=re.search(rb'\(path\s+"([^"]+)"\)',chunk)
        if not path:raise ValueError('Owned footprint has no schematic path')
        pose['rows'].append({'ref':row['ref'],'native_footprint_uuid':row['footprint_UUID'],'schematic_path':path[1].decode(),'layer':row['target_native_layer'],'root_pose_mm_deg':row['target_pose_mm_deg'],'pads':[{'pad_uuid':p['physical_pad_UUID'],'pin':p['pin'],'raw_net':p['expected_raw_net'],'absolute_center_mm':p['absolute_position_mm'],'actual_original_clone_native_flashes':p['expected_copper_layer_names']} for p in row['pads']]})
    write(OUT/'native-pose-ledger.json',pose)
    vias=json.loads((STAGE/'native-via-spec.json').read_bytes());vias['board_sha256']=sha(candidate)
    if {r['uuid'] for r in vias['added_vias']}&deletes:raise ValueError('Recipe deletes previously attested owned via')
    for row in recipe['new_Cu_items']:
        if row['kind']!='via':continue
        v=row['native_model'];vias['added_vias'].append({'uuid':row['uuid'],'net':v['net'].replace('{slash}','/'),'at':[v['x'],v['y']],'d':v['d'],'drill':v['drill']})
    for row in vias['added_vias']:
        rawnet=re.search(rb'\(net\s+"([^"]+)"\)',after[4][row['uuid']])
        if not rawnet:raise ValueError('Owned via has no literal raw net')
        row['net_raw']=rawnet[1].decode()
    if len(vias['added_vias'])!=68 or len(pose['rows'])!=26:raise ValueError('Combined native witness inventory differs')
    write(OUT/'native-via-spec.json',vias)
    command=json.loads((STAGE/'invocation.json').read_bytes())['command']
    # Outer attestation adds exact SMD masks/angles/text positions to frozen helper.
    command=command[:4]+[str((HERE/'native_sbc_contract_r1.py').resolve()),command[4],str(mask_path.resolve()),str((OUT/'native-pose-ledger.json').resolve()),command[6],str((OUT/'native-via-spec.json').resolve()),str(board.resolve())]+command[9:]
    command[-1]=str((OUT/'native-parity.json').resolve())
    for p in [candidate,board,board.with_suffix('.kicad_pro'),board.with_suffix('.kicad_dru'),OUT/'native-pose-ledger.json',OUT/'native-via-spec.json',Path(command[5]),Path(command[8]),Path(command[12])]:pins[str(p.resolve())]=sha(p)
    write(OUT/'construction.json',{'parent_sha256':sha(parent),'candidate_sha256':sha(candidate),'footprint_replacements':list(replacements),'old_Cu_removals':sorted(deletes),'new_Cu_UUIDs':sorted(adds),'every_unowned_primitive_header_trailer_and_zone_exact':True,'raw_net_identity':identity,'power_zones_not_yet_composed':True,'all_old_contact_continuity_current_reference_native_refill_DRC':'OPEN','adopted':False})
    write(OUT/'inputs.json',pins);write(OUT/'invocation.json',{'command':command,'existing_slot':'test-only1','new_heavy_slots':0,'no_fill_DRC_save_or_adoption':True})
    env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
    with (OUT/'native.log').open('w',encoding='utf-8') as log:run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
    for p,h in pins.items():
        if sha(p)!=h:raise ValueError('Frozen native contract input changed:'+p)
    report=json.loads((OUT/'native-parity.json').read_bytes()) if (OUT/'native-parity.json').exists() else {}
    passed=run.returncode==0 and report.get('summary',{}).get('parity_defects')==0 and report.get('SBC_exact_native_pad_masks_shapes_angles_and_field_poses',{}).get('verdict')=='PASS' and report.get('all_declared_vias_exact_raw_net_identity',{}).get('verdict')=='PASS'
    receipt={'verdict':'PASS_SOURCE_API_26_POSES_68_VIAS_AND_23_SMD_PAD_MASKS' if passed else 'FAIL_NATIVE_PARTIAL_CONTRACT','candidate_sha256':sha(candidate),'native_exit_code':run.returncode,'native_summary':report.get('summary'),'power_planes_contact_current_reference_and_full_refill_DRC':'OPEN','adopted':False}
    write(OUT/'receipt.json',receipt);print(json.dumps(receipt),flush=True);return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
