"""Invalidate derived zone-fill caches only, retaining every design primitive."""
import hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import native_pose_signal_contract as H
C=H.C
PRIOR=HERE/'combined-reset-cm-native-r4';OUT=HERE/'combined-reset-cm-native-r5-cache-refresh'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def strip_cache(ch):
    spans=[]
    for match in re.finditer(rb'(?m)^\t\t\((filled_polygon|fill_segments)\b',ch):
        start=match.start();i=ch.find(b'(',start);depth=0;quoted=False;escape=False
        for j in range(i,len(ch)):
            value=ch[j]
            if quoted:
                if escape:escape=False
                elif value==92:escape=True
                elif value==34:quoted=False
                continue
            if value==34:quoted=True
            elif value==40:depth+=1
            elif value==41:
                depth-=1
                if depth==0:
                    end=j+1
                    while end<len(ch) and ch[end] in (13,10):end+=1
                    spans.append((start,end,match.group(1).decode()));break
        else:raise ValueError('Unterminated derived zone cache')
    result=ch
    for a,b,token in reversed(spans):result=result[:a]+result[b:]
    return result,spans
def main():
    if OUT.exists():raise ValueError('Fresh cache refresh required')
    pins=json.loads((PRIOR/'inputs.json').read_bytes())
    for p,h in pins.items():
        if sha(p)!=h:raise ValueError('Frozen combined input changed: '+p)
    board=PRIOR/'combined-reset-cm-host-only.kicad_pcb';raw=board.read_bytes();iv=C.inventory(raw)
    rebuilt=[];ledger=[]
    for ch in iv[1]:
        if C.pcbtext.chunk_kind(ch)=='zone':
            replacement,spans=strip_cache(ch)
            if spans:ledger.append({'zone_uuid':C.pcbtext.chunk_uuid(ch),'before_sha256':digest(ch),'after_sha256':digest(replacement),'only_removed_derived_children':[{'token':token,'bytes':b-a,'sha256':digest(ch[a:b])} for a,b,token in spans],'all_remaining_zone_bytes_exact':True})
            rebuilt.append(replacement)
        else:rebuilt.append(ch)
    if not ledger:raise ValueError('Expected old fill caches')
    result=iv[0]+b''.join(rebuilt)+iv[2];ni=C.inventory(result)
    if ni[0]!=iv[0] or ni[2]!=iv[2] or set(ni[3])!=set(iv[3]):raise ValueError('Whole board design identity changed')
    changed={r['zone_uuid'] for r in ledger}
    for uid,ch in iv[3].items():
        if uid not in changed and ni[3][uid]!=ch:raise ValueError('Unowned design primitive changed')
        if uid in changed and strip_cache(ch)[0]!=ni[3][uid]:raise ValueError('Zone contains a non-cache change')
    if ni[4]!=iv[4]:raise ValueError('Copper primitive changed during cache refresh')
    OUT.mkdir();candidate=OUT/'combined-reset-cm-cache-refreshed.kicad_pcb';candidate.write_bytes(result)
    copy=OUT/'copy';copy.mkdir();nativeboard=copy/'board.kicad_pcb';shutil.copy2(candidate,nativeboard)
    for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2((PRIOR/'copy/board.kicad_pcb').with_suffix(ext),nativeboard.with_suffix(ext))
    spec=json.loads((PRIOR/'native-via-spec.json').read_bytes());spec['board_sha256']=sha(candidate);write(OUT/'native-via-spec.json',spec)
    command=json.loads((PRIOR/'invocation.json').read_bytes())['command'];command[7]=str((OUT/'native-via-spec.json').resolve());command[8]=str(nativeboard.resolve());command[-1]=str((OUT/'native-parity.json').resolve())
    for p in [Path(__file__),board,PRIOR/'receipt.json',PRIOR/'net-diagnostic-r1/native.json',PRIOR/'construction.json',PRIOR/'native-via-spec.json',candidate,nativeboard,nativeboard.with_suffix('.kicad_pro'),nativeboard.with_suffix('.kicad_dru'),OUT/'native-via-spec.json']:
        pins[str(p.resolve())]=sha(p)
    write(OUT/'construction.json',{'parent_sha256':sha(board),'candidate_sha256':sha(candidate),'removed_cache_zone_count':len(ledger),'removed_cache_children':sum(len(r['only_removed_derived_children']) for r in ledger),'cache_ledger':ledger,'every_non_zone_primitive_and_zone_outline_configuration_net_priority_UUID_exact':True,'all_original_FP_and_discrete_Cu_chunks_byte_exact':True,'native_cause':'Reader assigns some free GND vias to IO3 on original cached fill during LoadBoard; cache refresh is a test of that cause, not a net override','adopted':False})
    write(OUT/'inputs.json',pins);write(OUT/'invocation.json',{'command':command,'existing_slot':'test-only1','new_heavy_slots':0,'board_save':False,'refill':False,'DRC':False})
    env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
    with (OUT/'native.log').open('w',encoding='utf-8') as log:run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
    for p,h in pins.items():
        if sha(p)!=h:raise ValueError('Frozen cache-refresh input changed: '+p)
    api=json.loads((OUT/'native-parity.json').read_bytes()) if (OUT/'native-parity.json').exists() else {}
    passed=run.returncode==0 and api.get('summary',{}).get('parity_defects')==0 and api.get('source_owned_native_poses',{}).get('verdict')=='PASS' and api.get('added_via_annuli',{}).get('verdict')=='PASS'
    receipt={'verdict':'PASS_SOURCE_NATIVE_API_19_POSES_19_VIAS' if passed else 'FAIL_CACHE_REFRESH_NATIVE_GATE','candidate_sha256':sha(candidate),'native_exit_code':run.returncode,'native_summary':api.get('summary'),'cache_refresh_design_primitive_identity':'PASS','all19_added_restored_vias_exact_native_net_position_size_drill_and6flashes':passed,'native_full_refill_DRC_allnet_relationships':'OPEN','adopted':False}
    write(OUT/'receipt.json',receipt);print(json.dumps(receipt),flush=True)
    return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
