"""Native exact PG fine-neck rule scope coupons; no production board changes."""
import hashlib,json,os,re,shutil,subprocess,sys,uuid
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
import native_pose_signal_contract as N
C=N.C;OUT=H/'pg-native-rule-scope-r1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
    if OUT.exists():raise ValueError('Fresh PG native scope check required')
    root=H/'sbc-power/PG-native-rule-proposal-r7';receipt=root/'receipt.json';r=json.loads(receipt.read_bytes())
    parent=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';inv=C.inventory(parent.read_bytes())
    if sha(parent)!=r['exact_native_discrete_board_sha256'] or sha(receipt)!='468c0f1ccff701dce7954aa8fc17bd0db884cd3b02b9dbac1d200ce7832fe15c':raise ValueError('Frozen exact PG source differs')
    area=Path(r['area_chunk_file']);rule=Path(r['rule_file'])
    if sha(area)!=r['area_chunk_sha256'] or sha(rule)!=r['rule_sha256']:raise ValueError('Frozen exact PG rule/area differs')
    fine={u:inv[4][u] for u in r['fine_track_uuids']}
    if len(fine)!=3 or r['cumulative_fine_length_mm']>r['cumulative_owned_limit_mm']:raise ValueError('PG owned cumulative fine limit failed')
    base=H/'sbc-native-contract-r1/copy/board.kicad_pcb';project=base.with_suffix('.kicad_pro');original=base.with_suffix('.kicad_dru')
    config=[ch for ch in inv[1] if C.pcbtext.chunk_uuid(ch) is None];edges=[ch for ch in inv[1] if C.pcbtext.chunk_kind(ch).startswith('gr_') and b'(layer "Edge.Cuts")' in ch]
    prefix=inv[0]+b''.join(config)+b''.join(edges)+area.read_bytes();seed=next(iter(fine.values()));controls={}
    for tag in ['outside-area','wrong-layer','wrong-literal-net','wrong-width']:
        uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-pg-native-scope/'+tag));ch=re.sub(rb'\(uuid "[^"]+"\)',lambda _:b'(uuid "'+uid.encode()+b'")',seed)
        if tag=='outside-area':
            ch=re.sub(rb'\((start|end)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\)',lambda m:b'('+m[1]+b' '+format(float(m[2])+5,'.9f').encode()+b' '+m[3]+b')',ch)
        elif tag=='wrong-layer':ch=ch.replace(b'(layer "F.Cu")',b'(layer "B.Cu")')
        elif tag=='wrong-literal-net':ch=ch.replace(r['exact_raw_native_net'].encode(),b'/motherboard_compute/CM_HOST_SPI_SCLK')
        elif tag=='wrong-width':ch=ch.replace(b'(width 0.125)',b'(width 0.13)')
        controls[tag]={'uuid':uid,'chunk':ch}
    OUT.mkdir();cases={};pins={str(p.resolve()):sha(p) for p in [Path(__file__),parent,receipt,area,rule,project,original]}
    for name,chunks,proposed in [('original-exact',list(fine.values()),False),('proposed-exact',list(fine.values()),True)]+[(name,[row['chunk']],True) for name,row in controls.items()]:
        case=OUT/name;case.mkdir();board=case/'board.kicad_pcb';board.write_bytes(prefix+b''.join(chunks)+inv[2]);shutil.copy2(project,board.with_suffix('.kicad_pro'))
        board.with_suffix('.kicad_dru').write_bytes(original.read_bytes()+(b'\n'+rule.read_bytes() if proposed else b''))
        cases[name]=case
        for p in [board,board.with_suffix('.kicad_pro'),board.with_suffix('.kicad_dru')]:pins[str(p.resolve())]=sha(p)
    write(OUT/'inputs.json',pins);write(OUT/'construction.json',{'parent_sha256':sha(parent),'all3_actual_PG_fine_chunks_byte_exact':True,'all_other_controls_are_isolated_synthetic_coupons':True,'all_original_rules_bytes_exact_prefix':True,'area_byte_exact':True,'cumulative_owned_fine_length_mm':r['cumulative_fine_length_mm'],'cumulative_owned_limit_mm':r['cumulative_owned_limit_mm'],'all_original_design_board_project_rules_unchanged':True,'no_production_refill_DRC_or_adoption':True,'new_heavy_slots':0,'control_UUIDs':{name:row['uuid'] for name,row in controls.items()}})
    env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH'];results={}
    for name,case in cases.items():
        command=['C:/Program Files/Git/usr/bin/sh.exe','Z:/pcb-runs/claude-finish/tools/heavyt.sh','kicad','C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--severity-all','--all-track-errors','--output',str((case/'drc.json').resolve()),str((case/'board.kicad_pcb').resolve())]
        write(case/'invocation.json',{'command':command,'existing_slot':'test-only1','no_schematic_parity_or_refill':True})
        with (case/'native.log').open('w',encoding='utf-8') as log:run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
        if not (case/'drc.json').exists():raise ValueError('Native PG coupon failed to complete:'+name)
        report=json.loads((case/'drc.json').read_bytes());by_uuid={}
        for row in report.get('violations',[]):
            for item in row.get('items',[]):by_uuid.setdefault(item.get('uuid'),[]).append({'type':row['type'],'description':row['description']})
        results[name]={'native_exit_code':run.returncode,'by_uuid':by_uuid}
    errors=[]
    def has(case,u,kind):return any(row['type']==kind for row in results[case]['by_uuid'].get(u,[]))
    for u in fine:
        if not has('original-exact',u,'track_width'):errors.append(u+': original profile did not reject fine width')
        if has('proposed-exact',u,'track_width') or has('proposed-exact',u,'track_segment_length'):errors.append(u+': exact intended fine piece rejected')
    for name,row in controls.items():
        if not has(name,row['uuid'],'track_width'):errors.append(name+': unexpected fine-width exemption')
    for p,h in pins.items():
        if sha(p)!=h:raise ValueError('Frozen PG native scope input changed:'+p)
    record={'verdict':'PASS_NATIVE_PG_RULE_EXACT3_FINE_TRACKS_AND4_NEGATIVE_CONTROLS' if not errors else 'FAIL_PG_NATIVE_RULE_SCOPE','errors':errors,'parent_sha256':sha(parent),'source_recipe_sha256':sha(receipt),'exact_fine_track_UUIDs':list(fine),'results':results,'cumulative_length_enforced_by_exact_host_owned_recipe_not_native_segment_rule':True,'installed':False,'whole_board_fill_DRC_and_power_contact_current_gates':'OPEN','manufacturing_ready':False}
    write(OUT/'receipt.json',record);print(json.dumps({'verdict':record['verdict'],'errors':errors}),flush=True);return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
