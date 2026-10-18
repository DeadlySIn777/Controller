"""Native DRC coupons for exact proposed CM neck scope; no board adoption."""
import hashlib,json,os,re,shutil,subprocess,sys,uuid
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import native_pose_signal_contract as H
C=H.C;OUT=HERE/'cm-terminal-native-rule-coupons-r1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def segment(tag,net,layer,a,b,w):
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-native-rule-coupon/'+tag))
    f=lambda v:format(v,'.9f').rstrip('0').rstrip('.')
    return uid,(f'\t(segment\n\t\t(start {f(a[0])} {f(a[1])})\n\t\t(end {f(b[0])} {f(b[1])})\n\t\t(width {f(w)})\n\t\t(layer "{layer}")\n\t\t(net "{net}")\n\t\t(uuid "{uid}")\n\t)\n').encode()
def main():
    if OUT.exists():raise ValueError('Fresh native constraint coupon required')
    stage=HERE/'coupled-recovery/cm-terminal-profile-r1';proposal=json.loads((stage/'proposal.json').read_bytes())
    parent=HERE/'combined-reset-cm-native-r5-cache-refresh/combined-reset-cm-cache-refreshed.kicad_pcb';inv=C.inventory(parent.read_bytes())
    if sha(parent)!='1beb9a2296ae451daed4b905383ccc5bd3ee083b3400cf5ef2e3ab2e7b7dae6b':raise ValueError('Frozen native CM parent changed')
    neck=inv[4][proposal['exact_selected_neck_uuid']]
    if digest(neck)!=proposal['exact_selected_neck_chunk_sha256']:raise ValueError('Exact CM neck source changed')
    rules=stage/'board.kicad_dru.proposed';project=stage/'board.kicad_pro.proposed';area=stage/'terminal-rule-area.chunk'
    if sha(rules)!=proposal['proposed_rules_sha256'] or sha(project)!=proposal['proposed_project_sha256'] or sha(area)!=proposal['area_chunk_sha256']:raise ValueError('Frozen rule proposal changed')
    controls={};net=proposal['native_raw_net']
    for tag,n,layer,a,b,w in [
      ('same-net-outside-area',net,'F.Cu',(129,166),(129,167),.2),
      ('same-net-wrong-layer',net,'B.Cu',(128.252,166),(128.252,167),.2),
      ('same-net-wrong-width',net,'F.Cu',(128.252,166),(128.252,167),.19),
      ('controlled-other-literal-net','/motherboard_compute/CM_CAN_SPI_MISO','F.Cu',(128.252,166),(128.252,167),.2),
      ('same-net-too-long',net,'F.Cu',(128.252,165.945),(128.252,167.18),.2)]:
        u,ch=segment(tag,n,layer,a,b,w);controls[tag]={'uuid':u,'chunk':ch,'expected_width_error':tag!='same-net-too-long','expected_length_error':tag=='same-net-too-long'}
    edges=[ch for ch in inv[1] if C.pcbtext.chunk_kind(ch).startswith('gr_') and b'(layer "Edge.Cuts")' in ch]
    prefix=inv[0]+b''.join(edges)+area.read_bytes()
    OUT.mkdir();base=OUT/'original-profile';test=OUT/'proposed-profile'
    base.mkdir();test.mkdir()
    original=HERE.parent/'controlled-geometry/future-copy-proposal/board.kicad_dru.proposed'
    for path,contents,rulepath in [(base,prefix+neck+inv[2],original),(test,prefix+neck+b''.join(r['chunk'] for r in controls.values())+inv[2],rules)]:
        (path/'board.kicad_pcb').write_bytes(contents);shutil.copy2(project,path/'board.kicad_pro');shutil.copy2(rulepath,path/'board.kicad_dru')
    pins={str(p.resolve()):sha(p) for p in [Path(__file__),parent,stage/'proposal.json',rules,project,area,original]+[p for root in [base,test] for p in root.iterdir()]}
    write(OUT/'inputs.json',pins);write(OUT/'construction.json',{'actual_CM_neck_chunk_byte_exact':True,'actual_header_and_edge_chunks_exact':True,'only_coupon_control_segments_are_synthetic':True,'coupon_UUIDs':{k:{f:v for f,v in r.items() if f!='chunk'} for k,r in controls.items()},'new_rule_area_byte_exact':True,'no_live_board_project_or_rules_modified':True,'new_heavy_slots':0,'qualification_scope':'Native parse and exact applicability/negative controls only, no board DRC/SI/fabrication qualification','official_reference':'https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html'})
    env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH'];results={}
    for role,path in [('original',base),('proposed',test)]:
        command=['C:/Program Files/Git/usr/bin/sh.exe','Z:/pcb-runs/claude-finish/tools/heavyt.sh','kicad','C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--severity-all','--all-track-errors','--output',str((path/'drc.json').resolve()),str((path/'board.kicad_pcb').resolve())]
        write(path/'invocation.json',{'command':command,'existing_slot':'test-only1','no_refill_no_schematic_parity':True})
        with (path/'native.log').open('w',encoding='utf-8') as log:run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
        if not (path/'drc.json').exists():raise ValueError('Native coupon did not complete:'+role)
        report=json.loads((path/'drc.json').read_bytes());violations=report.get('violations',[])
        by_uuid={}
        for row in violations:
            for item in row.get('items',[]):
                by_uuid.setdefault(item.get('uuid'),[]).append({'type':row['type'],'description':row['description']})
        results[role]={'native_exit_code':run.returncode,'by_uuid':by_uuid,'violation_types':sorted({r['type'] for r in violations})}
    uid=proposal['exact_selected_neck_uuid'];errors=[]
    def has(role,u,kind):return any(r['type']==kind for r in results[role]['by_uuid'].get(u,[]))
    if not has('original',uid,'track_width'):errors.append('Original controlled profile did not reject actual .20mm neck')
    if has('proposed',uid,'track_width') or has('proposed',uid,'track_segment_length'):errors.append('Proposed profile rejects its exact selected neck')
    for name,r in controls.items():
        if has('proposed',r['uuid'],'track_width')!=r['expected_width_error']:errors.append(name+': width scope mismatch')
        if has('proposed',r['uuid'],'track_segment_length')!=r['expected_length_error']:errors.append(name+': length scope mismatch')
    for p,h in pins.items():
        if sha(p)!=h:raise ValueError('Frozen coupon input changed:'+p)
    record={'verdict':'PASS_NATIVE_RULE_PARSE_EXACT_NECK_AND_FIVE_NEGATIVE_CONTROLS' if not errors else 'FAIL_NATIVE_RULE_SCOPE','errors':errors,'results':results,'subject_parent_sha256':sha(parent),'proposed_rules_sha256':sha(rules),'installed':False,'whole_board_controlled_route_reference_return_extracted_SI':'OPEN','manufacturing_ready':False}
    write(OUT/'receipt.json',record);print(json.dumps({'verdict':record['verdict'],'errors':errors,'violation_types':{k:v['violation_types'] for k,v in results.items()}}),flush=True);return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
