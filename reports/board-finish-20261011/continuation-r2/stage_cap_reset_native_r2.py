"""Add audited reset/return copper to the exact measured cap/signal candidate."""
import datetime,hashlib,json,os,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
import native_pose_signal_contract as H
import measure_cap_signal_r1 as M
from shapely.ops import unary_union
C=H.C
OUT=HERE/'cap-reset-native-r2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,o):p.write_text(json.dumps(o,indent=1)+'\n',encoding='utf-8')
def main():
    if OUT.exists():raise ValueError('Fresh staged native directory required')
    parent=HERE/'cap-signal-native-r1';parentboard=parent/'cap-signal-host-only.kicad_pcb';construction=parent/'construction.json'
    parentproof=H.validate_construction(construction,parentboard);native=json.loads((parent/'measure/proof.json').read_bytes())
    if parentproof['verdict']!='PASS' or native['connectivity']['lost'] or native['connectivity_r06']['lost']!=13:raise ValueError('Unexpected measured parent')
    auditpath=HERE/'ground-escape-audit-r6/audit.json';audit=json.loads(auditpath.read_bytes())
    if audit['verdict']!='HOST_READY_NATIVE_ELECTRICAL_OPEN' or audit['errors'] or audit['existing_plane_contacts_removed']:raise ValueError('Independent reset audit rejected')
    for p,h in audit['inputs'].items():
        if sha(p)!=h:raise ValueError('Frozen reset audit input changed '+p)
    raw=parentboard.read_bytes();iv=C.inventory(raw);new={r['uuid']:r['raw_chunk'].encode() for r in audit['new_items']}
    if len(new)!=16 or set(new)&set(iv[3]):raise ValueError('Unexpected reset additions/collision')
    parentrecipe=json.loads(construction.read_bytes());cap=json.loads(Path(parentrecipe['cap_audit']['path']).read_bytes());original=C.inventory(Path(parentrecipe['source']['path']).read_bytes());capchunks=[r['exact_serialized_chunk'].encode() for r in cap['added_items']]+[original[4][r['uuid']] for r in cap['deleted_items']]
    separation=unary_union([H.body(ch) for ch in capchunks]).distance(unary_union([H.body(ch) for ch in new.values()]))
    if separation<2:raise ValueError('Cap modification intersects audited reset region')
    wanted=iv[0]+b''.join(iv[1])+b''.join(new.values())+iv[2];ni=C.inventory(wanted);nets=H.N.SourceNets(raw)
    if ni[0]!=iv[0] or ni[2]!=iv[2] or ni[5]!=iv[5] or any(ni[3].get(u)!=ch for u,ch in iv[3].items()):raise ValueError('Unowned native geometry changed')
    nets.assert_chunks(ni[4]);nets.assert_no_collisions(wanted)
    OUT.mkdir();copy=OUT/'copy';copy.mkdir();candidate=OUT/'cap-reset-host-only.kicad_pcb';candidate.write_bytes(wanted);(copy/'board.kicad_pcb').write_bytes(wanted)
    inherited=[]
    for name in ['board.kicad_pro','board.kicad_dru']:
        p=parent/'measure/copy'/name;(copy/name).write_bytes(p.read_bytes());inherited.append(p)
    r07=C.inventory(Path('Z:/pcb-runs/claude-finish/integrate/revs/r07-ripup-signals-1.kicad_pcb').read_bytes())
    added=[]
    for u,ch in ni[4].items():
        if u in r07[4] or C.pcbtext.chunk_kind(ch)!='via':continue
        added.append({'uuid':u,'net':M.net(ch),'at':M.xy(ch,'at'),'d':M.scalar(ch,'size'),'drill':M.scalar(ch,'drill')})
    if len(added)!=13:raise ValueError('Expected13 new-from-r07 ordinary vias')
    spec=OUT/'native-via-spec.json';write(spec,{'board_sha256':sha(candidate),'added_vias':added})
    parser=BASE/'parity-repair/root106/tools/netlist_parity.py';entry=HERE/'native_entry_width_r3.py';wrapper=Path('Z:/pcb-runs/claude-finish/tools/heavyt.sh');fresh=parent/'measure/fresh.net'
    pinned=[Path(__file__),parentboard,construction,parent/'measure/proof.json',parent/'measure/source-proof.json',parent/'measure/inputs.json',auditpath,candidate,copy/'board.kicad_pcb',copy/'board.kicad_pro',copy/'board.kicad_dru',spec,parser,entry,wrapper,fresh,*inherited]
    pins={str(p.resolve()):sha(p) for p in pinned}
    receipt={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'parent_sha256':sha(parentboard),'candidate_sha256':sha(candidate),'added_reset_items':16,'cap_region_separation_mm':separation,'exact_unowned_items_preserved':True,'raw_net_identity':'2384 distinct raw tokens;0 collisions','independent_reset_geometry':'PASS;paired source-connected returns,all old contacts retained','current_reset_edge_length_timing_review':'OPEN;42.693mm added ordinary route','native_refill_DRC_allnet_connectivity':'NOT_EXECUTED;next combined run','new_vias_from_r07':13,'input_hashes':pins,'adopted':False,'manufacturing_ready':False}
    write(OUT/'construction.json',receipt)
    cmd=['C:/Program Files/Git/usr/bin/sh.exe',str(wrapper),'kicad','C:/Program Files/KiCad/10.0/bin/python.exe',str(entry.resolve()),str(parser.resolve()),str(spec.resolve()),str((copy/'board.kicad_pcb').resolve()),'--netlist',str(fresh.resolve()),'--no-connectivity','--examples','40',str((OUT/'native-parity.json').resolve())]
    write(OUT/'invocation.json',{'command':cmd,'existing_slot':'test-only1','new_heavy_slots':0,'board_save':False,'refill':False,'DRC':False})
    env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH'];env.update(PYTHONUTF8='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    with (OUT/'native.log').open('w',encoding='utf-8') as log:run=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
    if {p:sha(p) for p in pins}!=pins:raise ValueError('Frozen fast native inputs changed')
    proof=json.loads((OUT/'native-parity.json').read_bytes()) if (OUT/'native-parity.json').exists() else {}
    okay=run.returncode==0 and proof.get('summary',{}).get('parity_defects')==0 and proof.get('summary',{}).get('normalisation_collisions')==0 and proof.get('added_via_annuli',{}).get('verdict')=='PASS'
    write(OUT/'receipt.json',{'verdict':'PASS_SOURCE_NATIVE_API_ONLY' if okay else 'FAIL','native_exit_code':run.returncode,'candidate_sha256':sha(candidate),'summary':proof.get('summary'),'all13_added_vias_actual_six_annuli':okay,'outputs':{str((OUT/n).resolve()):sha(OUT/n) for n in ['construction.json','native-parity.json','native.log'] if (OUT/n).exists()},'refill_DRC_allnet_connectivity':'OPEN','adopted':False})
    print(json.dumps({'verdict':'PASS_SOURCE_NATIVE_API_ONLY' if okay else 'FAIL','summary':proof.get('summary'),'candidate_sha256':sha(candidate),'13actual_vias':okay}),flush=True)
    return 0 if okay else 1
if __name__=='__main__':raise SystemExit(main())
