"""Read completed uncapped native partitions without restarting any refill."""
import hashlib,importlib.util,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
OUT=H/'R9-completed-uncapped-native-continuity-r114'
M=H/'SAFE-exploratory-native-trial-r9/measure'
EXPECTED='3b579aa7ea4cf4c070c22e36df8dca2fbfcdefccd0e3c2a874ebf337acda3919'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def write(p,x):Path(p).write_text(json.dumps(x,indent=1)+'\n')
def main():
    assert not OUT.exists()
    backend=H/'measure_field_power_native_backend_r1.py'
    sys.path.insert(0,str(H));spec=importlib.util.spec_from_file_location('frozen_native_backend',backend);N=importlib.util.module_from_spec(spec);spec.loader.exec_module(N)
    candidate=M/'copy/board.kicad_pcb';assert sha(candidate)==EXPECTED
    after=read(M/'partitions.json');assert after['sha256']==EXPECTED and after['refilled']
    baselines={
        'dc936':(H/'field-power-native-trial-r1/field-power-native-trial.kicad_pcb',H/'field-power-native-trial-r1/measure/partitions.json'),
        '1beb':(H/'combined-reset-cm-native-r5-cache-refresh/combined-reset-cm-cache-refreshed.kicad_pcb',H/'combined-reset-cm-native-r5-cache-refresh/measure/partitions.json'),
        'r07':(Path('Z:/pcb-runs/claude-finish/integrate/revs/r07-ripup-signals-1.kicad_pcb'),Path('Z:/pcb-runs/claude-finish/integrate/measure/r07-ripup-signals-1/partitions.json')),
        'r06':(Path('Z:/pcb-runs/claude-finish/integrate/revs/r06-stitch-plane-pads-2.kicad_pcb'),Path('Z:/pcb-runs/claude-finish/integrate/measure/r06-stitch-plane-pads-2/partitions.json')),
        'c9':(H/'cap-signal-native-r1/cap-signal-host-only.kicad_pcb',H/'cap-signal-native-r1/measure/partitions.json')}
    files=[Path(__file__),backend,candidate,M/'partitions.json',M/'actual-full-refill-contract.json',H/'SAFE-exploratory-native-trial-r9/native-parity.json']
    for bp,pp in baselines.values():files.extend([bp,pp])
    pins={str(p.resolve()):sha(p) for p in files}
    sys.path.insert(0,str(B/'parity-repair'))
    from host_parity import load_parser
    parser=load_parser(B/'parity-repair/root106/tools/netlist_parity.py')
    C=N.C;current=C.inventory(candidate.read_bytes());old_board=C.inventory(baselines['c9'][0].read_bytes())
    changed=set();ledger=[]
    import collections
    for uid,ch in old_board[3].items():
        if C.pcbtext.chunk_kind(ch)!='footprint' or current[3].get(uid)==ch:continue
        roots=[parser['sexpr_parse'](s.decode()) for s in [ch,current[3][uid]]]
        props={p[1]:p[2] for p in parser['children'](roots[0],'property')};ref=props['Reference'];seen=collections.Counter();maps=[]
        for root in roots:
            mapping={}
            for pad in parser['children'](root,'pad'):
                puid=parser['atom'](pad,'uuid');net=parser['child'](pad,'net');mapping[puid]={'number':pad[1],'net':net[1] if net else ''}
            maps.append(mapping)
        assert set(maps[0])==set(maps[1])
        for pad in parser['children'](roots[0],'pad'):
            puid=parser['atom'](pad,'uuid');pin=pad[1];name=ref+'.'+pin+'#'+str(seen[pin]);seen[pin]+=1
            old,new=maps[0][puid],maps[1][puid];assert old['number']==new['number']
            if old['net']!=new['net']:
                changed.add(name);ledger.append({'physical_pad_uuid':puid,'partition_pad':name,'before_net_raw':old['net'],'after_net_raw':new['net']})
    assert len(ledger)==14
    proofs={};raw={}
    for role,(bp,pp) in baselines.items():
        before=read(pp);assert before['sha256']==sha(bp) and before['refilled']
        proofs[role]=N.old_relationships(before,after,changed);raw[role]=N.old_relationships(before,after,set())
    for p,s in pins.items():assert sha(p)==s,p
    OUT.mkdir();write(OUT/'inputs.json',pins)
    record={'verdict':'UNCAPPED_NATIVE_RELATIONSHIP_DIAGNOSTIC_FLASH_CONTRACT_REMAINS_FAILED','candidate_sha256':EXPECTED,'API_unconnected_count':after['api_unconnected_count'],'uncapped_pad_island_joins':after['pad_island_joins'],'unchanged_original_pad_relationships':proofs,'raw_original_all_pad_relationships_no_source_retag_omissions':raw,'exact14_original_source_retag_ledger':ledger,'source_retags_require_separate_new_power_qualification':True,'failed_actual_flash_contract_sha256':sha(M/'actual-full-refill-contract.json'),'native_jobs':0,'board_written':False,'adopted':False,'manufacturing_ready':False}
    write(OUT/'receipt.json',record)
    print(json.dumps({'candidate':EXPECTED,'api':after['api_unconnected_count'],'joins':after['pad_island_joins'],'unchanged_losses':{k:len(v['losses']) for k,v in proofs.items()},'raw_losses':{k:len(v['losses']) for k,v in raw.items()},'receipt_sha256':sha(OUT/'receipt.json')}),flush=True)
if __name__=='__main__':main()
