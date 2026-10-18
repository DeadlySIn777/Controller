"""Finish exact source-bearing part edits and check the whole native pad graph.

Source agreement is deliberately separate from power copper completion.
"""
import datetime,hashlib,json,os,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
import native_pose_signal_contract as H
import measure_cap_signal_r1 as M
C=H.C;OUT=HERE/'combined-power-source-native-r1';PINS={}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(p,h=None):
    p=Path(p).resolve();raw=p.read_bytes();actual=sha(raw)
    if h and actual!=h:raise ValueError('Frozen combined source input changed '+str(p))
    PINS[str(p)]=actual;return raw
def write(name,data):(OUT/name).write_text(json.dumps(data,indent=1)+'\n',encoding='utf-8')
def main():
    if OUT.exists():raise ValueError('Fresh combined native directory required')
    read(Path(__file__));parent=HERE/'combined-owned-host-r2';receipt=json.loads(read(parent/'construction.json'))
    for p,h in receipt['input_hashes'].items():read(p,h)
    raw=read(parent/'field-source-local-partial.kicad_pcb',receipt['partial_candidate_sha256']);iv=C.inventory(raw)
    sourceparts=json.loads(read(HERE/'sbc-power/source-native-frozen-r2/receipt.json'));field=json.loads(read(HERE/'field-power/candidate-recipe-r1/receipt.json'))
    export=field['authoritative_six_part_combined_source'];fresh=Path(export['fresh_netlist']['path']);read(fresh,export['fresh_netlist']['sha256']);native_source=json.loads(read(export['native_receipt']['path'],export['native_receipt']['sha256']))
    if native_source['verdict']!='PASS' or sourceparts['source_native_netlist_sha256']!=export['fresh_netlist']['sha256']:raise ValueError('Parts and authoritative source disagree')
    changed={};operations=[]
    for row in sourceparts['two_BOM_property_chunk_edits']:
        u=row['uuid'];before=iv[3][u]
        if sha(before)!=row['original_native_chunk_sha256']:raise ValueError('Old BOM-only footprint changed')
        ch=read(row['new_chunk_path'],row['new_chunk_sha256']);expected=before
        for prop in row['property_updates']:
            old=('(property "'+prop['property']+'" "'+prop['old']+'"').encode();new=('(property "'+prop['property']+'" "'+prop['new']+'"').encode()
            if expected.count(old)!=1:raise ValueError('BOM property not unique')
            expected=expected.replace(old,new)
        if ch!=expected or C.pcbtext.chunk_uuid(ch)!=u:raise ValueError('BOM correction changes unapproved geometry/attributes')
        changed[u]=ch;operations.append({'uuid':u,'ref':row['ref'],'allowed_properties':row['property_updates'],'pose_nets_pads_unchanged':True})
    core=sourceparts['new_C11094'];u=core['new_footprint_uuid'];cap=read(core['new_native_chunk_path'],core['new_native_chunk_sha256'])
    if u in iv[3] or C.pcbtext.chunk_uuid(cap)!=u or C.pcbtext.chunk_kind(cap)!='footprint':raise ValueError('New CORE bulk footprint collision/type')
    wanted=iv[0]+b''.join(changed.get(C.pcbtext.chunk_uuid(ch),ch) for ch in iv[1])+cap+iv[2];ni=C.inventory(wanted)
    if ni[0]!=iv[0] or ni[2]!=iv[2] or any(ni[3].get(uid)!=ch for uid,ch in iv[3].items() if uid not in changed):raise ValueError('Unowned native item changed')
    names=H.N.SourceNets(wanted);names.assert_chunks(ni[4]);netproof=names.assert_no_collisions(wanted)
    footprints=sum(C.pcbtext.chunk_kind(ch)=='footprint' for ch in ni[3].values())
    if footprints!=2723 or netproof['raw_net_count']!=2388:raise ValueError('Complete combined source/board scope differs')
    OUT.mkdir();copy=OUT/'copy';copy.mkdir();candidate=OUT/'combined-power-source-host-only.kicad_pcb';candidate.write_bytes(wanted);read(candidate);(copy/'board.kicad_pcb').write_bytes(wanted)
    project=read(field['project_proposal']['path'],field['project_proposal']['sha256']);(copy/'board.kicad_pro').write_bytes(project)
    (copy/'board.kicad_dru').write_bytes(read(HERE/'cap-reset-native-r4/copy/board.kicad_dru'))
    specs=json.loads(read(HERE/'cap-reset-native-r4/native-via-spec.json'));specs['board_sha256']=sha(wanted);write('native-via-spec.json',specs)
    construction={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verdict':'HOST_EXACT_COMBINED_SOURCE_SCOPE_READY_NATIVE_PARITY_OPEN','candidate_sha256':sha(wanted),'parent_field_partial_sha256':sha(raw),'source_netlist_sha256':export['fresh_netlist']['sha256'],'components':footprints,'raw_net_identity':netproof,'new_parts':6,'old_pad_net_moves':14,'old_Value_MPN_only_pairs':operations,'new_core_cap':core,'all_unowned_native_entities_exact':True,'power_layout_and_refill_DRC_connectivity':'OPEN; source-bearing parts andlocalfieldCu only','adopted':False,'manufacturing_ready':False};write('construction.json',construction)
    entry=HERE/'native_entry_width_r3.py';parser=M.PARSER;wrapper=Path('Z:/pcb-runs/claude-finish/tools/heavyt.sh')
    for p in [entry,parser,wrapper,copy/'board.kicad_pcb',copy/'board.kicad_pro',copy/'board.kicad_dru',OUT/'native-via-spec.json',OUT/'construction.json']:read(p)
    for p,h in PINS.items():
        if sha(Path(p).read_bytes())!=h:raise ValueError('Frozen combined job input changed '+p)
    write('inputs.json',PINS)
    cmd=['C:/Program Files/Git/usr/bin/sh.exe',str(wrapper),'kicad',str(M.NATIVE_BINARIES['native_python']),str(entry.resolve()),str(parser.resolve()),str((OUT/'native-via-spec.json').resolve()),str((copy/'board.kicad_pcb').resolve()),'--netlist',str(fresh.resolve()),'--no-connectivity','--examples','40',str((OUT/'native-parity.json').resolve())];write('invocation.json',{'command':cmd,'existing_slot':'test-only1','new_heavy_slots':0,'board_save':False,'refill':False,'DRC':False})
    env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH'];env.update(PYTHONUTF8='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    with (OUT/'native.log').open('w',encoding='utf-8') as log:run=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
    if {p:sha(Path(p).read_bytes()) for p in PINS}!=PINS:raise ValueError('Frozen combined native inputs changed')
    api=json.loads((OUT/'native-parity.json').read_bytes()) if (OUT/'native-parity.json').exists() else {};summary=api.get('summary',{});ok=run.returncode==0 and summary.get('parity_defects')==0 and summary.get('normalisation_collisions')==0 and api.get('added_via_annuli',{}).get('verdict')=='PASS'
    write('receipt.json',{'verdict':'PASS_COMPLETE_SOURCE_NATIVE_API_ONLY' if ok else 'FAIL','native_exit_code':run.returncode,'candidate_sha256':sha(wanted),'source_netlist_sha256':export['fresh_netlist']['sha256'],'summary':summary,'all13_added_vias_actual_six_annuli':ok,'refill_DRC_allnet_connectivity':'NOT_EXECUTED','power_electrical_and_layout_completion':'OPEN','input_hashes':PINS,'adopted':False,'manufacturing_ready':False})
    print(json.dumps({'verdict':'PASS_COMPLETE_SOURCE_NATIVE_API_ONLY' if ok else 'FAIL','summary':summary,'candidate_sha256':sha(wanted)}),flush=True)
    return 0 if ok else 1
if __name__=='__main__':raise SystemExit(main())
