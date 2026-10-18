"""Re-run full source/pose/pad/via attestation after adding exact field zones."""
import hashlib,json,os,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;OUT=H/'field-zone-source-api-r1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
    if OUT.exists():raise ValueError('Fresh zone source/API attestation required')
    native=H/'field-zone-native-contract-r2-layer-sets/receipt.json';r=json.loads(native.read_bytes());board=H/'field-zone-native-contract-r1/copy/board.kicad_pcb'
    if r['verdict']!='PASS_NATIVE_41_FIELD_ZONES_ALL_RINGS_SETTINGS_RAW_NETS' or sha(board)!=r['candidate_sha256']:raise ValueError('Native field zone attestation rejected')
    prior=H/'sbc-native-contract-r3-layer-ids';invocation=prior/'invocation.json';command=json.loads(invocation.read_bytes())['command']
    parent=H/'sbc-native-contract-r1/copy/board.kicad_pcb';matches=[i for i,v in enumerate(command) if v==str(parent.resolve())]
    if len(matches)!=1:raise ValueError('Exact parent argument differs')
    command[matches[0]]=str(board.resolve())
    OUT.mkdir();command[-1]=str((OUT/'native-parity.json').resolve())
    pins=json.loads((prior/'inputs.json').read_bytes())
    for p in (Path(__file__),invocation,native,board,board.with_suffix('.kicad_pro'),board.with_suffix('.kicad_dru')):pins[str(p.resolve())]=sha(p)
    write(OUT/'inputs.json',pins);write(OUT/'invocation.json',{'command':command,'existing_slot':'test-only1','all26_poses_68_vias_23_SMD_masks_and_field_pose_gate_unchanged':True,'no_save_refill_DRC':True,'new_heavy_slots':0})
    env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
    with (OUT/'native.log').open('w',encoding='utf-8') as log:run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
    for p,h in pins.items():
        if sha(p)!=h:raise ValueError('Frozen source/API native input changed: '+p)
    report=json.loads((OUT/'native-parity.json').read_bytes()) if (OUT/'native-parity.json').exists() else {}
    passed=run.returncode==0 and report.get('native_field_pose_diagnostic',{}).get('verdict')=='PASS' and report.get('summary',{}).get('parity_defects')==0
    receipt={'verdict':'PASS_FIELD_ZONES_SOURCE_API_26_POSES_68_VIAS_23_SMD_MASKS_AND_FIELDS' if passed else 'FAIL_FIELD_ZONES_SOURCE_API','candidate_sha256':sha(board),'native_exit_code':run.returncode,'native_summary':report.get('summary'),'adopted':False,'full_native_refill_DRC_contact_current':'OPEN'}
    write(OUT/'receipt.json',receipt);print(json.dumps(receipt),flush=True)
    return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
