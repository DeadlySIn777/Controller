"""Native ERC for the exact corrected hierarchy with all original dependencies."""
import collections, datetime, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE/'combined-source-erc-r2-prepared'
VARIANT=HERE/'field-power/combined-power-source-r3-hierarchy'
OUT=HERE/'combined-source-erc-r3'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(pins):
    for p,h in pins.items():
        if sha(p)!=h: raise ValueError('Frozen ERC input changed: '+p)
def write(p,o): p.write_text(json.dumps(o,indent=1)+'\n',encoding='utf-8')
def main():
    if OUT.exists(): raise ValueError('Fresh corrected ERC output required')
    prep=json.loads((BASE/'receipt.json').read_bytes())
    check(prep['input_hashes']);check(prep['clone_hashes'])
    native=json.loads((VARIANT/'source-export/receipt-r2.json').read_bytes())
    variant=json.loads((VARIANT/'receipt.json').read_bytes())
    if native['verdict']!='PASS' or native['hierarchy_zero_electrical_delta']!='PASS': raise ValueError('Corrected source native export not passed')
    for rel,h in variant['files'].items():
        if sha(VARIANT/rel)!=h: raise ValueError('Corrected source changed: '+rel)
    if sha(VARIANT/'source-export/fresh.net')!=native['fresh_export_sha256'] or sha(VARIANT/'receipt.json')!=native['source_receipt_sha256']: raise ValueError('Corrected source export binding differs')
    pins={**prep['input_hashes'],**prep['clone_hashes'],**{str((VARIANT/rel).resolve()):h for rel,h in variant['files'].items()}}
    for p in [Path(__file__),BASE/'receipt.json',VARIANT/'receipt.json',VARIANT/'host-precheck.json',VARIANT/'source-export/fresh.net',VARIANT/'source-export/receipt.json',VARIANT/'source-export/receipt-r2.json',VARIANT/'source-export/hierarchy-zero-electrical-delta-r2.json',VARIANT/'source-export/semantic-delta-r2.json',VARIANT/'source-export/source-identity-r2.json']:
        pins[str(p.resolve())]=sha(p)
    OUT.mkdir();source=OUT/'source';shutil.copytree(BASE/'source',source)
    ledger=variant['hierarchy_correction'];name=ledger['sheet']
    before=(source/name).read_bytes()
    old=ledger['before_chunk'].encode();new=ledger['after_chunk'].encode()
    if before.count(old)!=1: raise ValueError('Expected one exact old child label')
    wanted=before.replace(old,new,1)
    if (VARIANT/'source'/name).read_bytes()!=wanted: raise ValueError('Corrected source exceeds exact owned label change')
    (source/name).write_bytes(wanted)
    for rel,h in variant['files'].items():
        if sha(OUT/rel)!=h: raise ValueError('Complete library clone source differs: '+rel)
    clone={str(p.resolve()):sha(p) for p in sorted(source.rglob('*')) if p.is_file()}
    sys.path.insert(0,str(HERE.parent/'parity-repair'))
    from host_parity import load_parser
    from fresh_export import canonical
    parser_path=HERE.parent/'parity-repair/root106/tools/netlist_parity.py'
    for module in list(sys.modules.values()):
        p=getattr(module,'__file__',None)
        if p and 'board-finish-20261011' in str(p) and str(p).endswith('.py'):
            pins[str(Path(p).resolve())]=sha(p)
    pins[str(parser_path.resolve())]=sha(parser_path)
    parser=load_parser(parser_path)
    prefix=['C:/Program Files/Git/usr/bin/sh.exe','Z:/pcb-runs/claude-finish/tools/heavy.sh','kicad','C:/Program Files/KiCad/10.0/bin/kicad-cli.exe']
    for p in [Path(prefix[1]),Path(prefix[3])]: pins[str(p.resolve())]=sha(p)
    export=prefix+['sch','export','netlist','--format','kicadsexpr','--output',str(OUT/'fresh.net'),str(source/'motherboard.kicad_sch')]
    erc=prefix+['sch','erc',str(source/'motherboard.kicad_sch'),'--output',str(OUT/'erc.json'),'--format','json','--severity-all','--exit-code-violations']
    write(OUT/'inputs.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pins':pins,'clone':clone,'commands':[export,erc],'new_heavy_slots':0,'exact_owned_hierarchy_change':ledger})
    env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
    start=time.monotonic()
    with (OUT/'export.log').open('w',encoding='utf-8') as log:
        exp=subprocess.run(export,env=env,cwd=source,stdout=log,stderr=subprocess.STDOUT)
    check({**pins,**clone})
    if exp.returncode!=0: raise ValueError('Complete-library native export failed')
    expected=canonical(parser['read_netlist'](VARIANT/'source-export/fresh.net'))
    actual=canonical(parser['read_netlist'](OUT/'fresh.net'))
    if expected!=actual: raise ValueError('Complete-library semantics differ from fresh corrected source')
    write(OUT/'export-receipt.json',{'verdict':'PASS','fresh_export_sha256':sha(OUT/'fresh.net'),'components':len(actual['components']),'nets':len(actual['nets']),'nodes':len(actual['node_assignments']),'all_restored_library_semantics_exact':True})
    print('Corrected complete-library export passed; native ERC running',flush=True)
    with (OUT/'erc.log').open('w',encoding='utf-8') as log:
        run=subprocess.run(erc,env=env,cwd=source,stdout=log,stderr=subprocess.STDOUT)
    check({**pins,**clone})
    report=json.loads((OUT/'erc.json').read_bytes())
    violations=[v for sheet in report.get('sheets',[]) for v in sheet.get('violations',[])]
    counts=collections.Counter((v['type'],v['severity']) for v in violations)
    errors=sum(v['severity']=='error' for v in violations)
    warnings=sum(v['severity']=='warning' for v in violations)
    result={'verdict':'PASS_NATIVE_ERC' if not violations and run.returncode==0 else 'NATIVE_ERC_VIOLATIONS','native_exit_code':run.returncode,'errors':errors,'warnings':warnings,'violations':len(violations),'by_category':{str(k):v for k,v in sorted(counts.items())},'ignored_checks':report.get('ignored_checks'),'exact_raw_net_component_semantics':'PASS','hierarchy_correction_zero_electrical_delta':'PASS','source_dependency_input_hashes_unchanged':True,'elapsed_seconds':time.monotonic()-start,'source_only':True,'full_board_refill_DRC':'NOT_EXECUTED','adopted':False,'manufacturing_ready':False}
    write(OUT/'receipt.json',result);print(json.dumps(result),flush=True)
    return 0 if result['verdict']=='PASS_NATIVE_ERC' else 1
if __name__=='__main__': raise SystemExit(main())
