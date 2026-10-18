import hashlib,json,os,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;OUT=H/'native-raw-domain-contract-r1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    assert not OUT.exists()
    board=H/'corrected-local-native-contract-r1/copy/board.kicad_pcb'
    expected=H/'static-raw-domain-contract-r2/receipt.json'
    assert json.loads(expected.read_bytes())['verdict']=='PASS_STATIC_EXACT_RAW_DOMAIN_MEMBERSHIP'
    assert sha(board)=='6b2652d91e9a3e4be2552dd372e623f7d1cac1457a09da8a931a0af0e44c0675'
    wrapper=Path('Z:/pcb-runs/claude-finish/tools/heavyt.sh');runtime=Path('C:/Program Files/KiCad/10.0/bin/python.exe');helper=H/'native_raw_domains_r1.py'
    OUT.mkdir();command=['C:/Program Files/Git/usr/bin/sh.exe',str(wrapper),'kicad',str(runtime),str(helper.resolve()),str(board.resolve()),str(expected.resolve()),str((OUT/'receipt.json').resolve())]
    pins={str(p.resolve()):sha(p) for p in (Path(__file__),helper,board,board.with_suffix('.kicad_pro'),board.with_suffix('.kicad_dru'),expected,wrapper,runtime)}
    (OUT/'inputs.json').write_text(json.dumps(pins,indent=1)+'\n',encoding='utf-8')
    (OUT/'invocation.json').write_text(json.dumps({'command':command,'existing_slot':'test-only1','new_slots':0},indent=1)+'\n',encoding='utf-8')
    env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
    with (OUT/'native.log').open('w',encoding='utf-8') as log:run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
    assert all(sha(p)==h for p,h in pins.items())
    record=json.loads((OUT/'receipt.json').read_bytes())
    print(json.dumps({'native_exit':run.returncode,'verdict':record['verdict'],'raw_net_count':record['raw_net_count'],'errors':record['errors']}))
    return run.returncode
if __name__=='__main__':raise SystemExit(main())
