"""Bind the unchanged 68-via contract to the exact added-zone candidate hash."""
import hashlib,json,os,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;OLD=H/'field-zone-source-api-r1';OUT=H/'field-zone-source-api-r2-bound-hash'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
    if OUT.exists():raise ValueError('Fresh exact candidate-bound attestation required')
    command=json.loads((OLD/'invocation.json').read_bytes())['command'];board=H/'field-zone-native-contract-r1/copy/board.kicad_pcb';old_spec=H/'sbc-native-contract-r1/native-via-spec.json'
    indices=[i for i,v in enumerate(command) if v==str(old_spec.resolve())]
    if len(indices)!=1:raise ValueError('Exact frozen via spec argument differs')
    original=json.loads(old_spec.read_bytes());spec=dict(original);spec['board_sha256']=sha(board)
    if original['added_vias']!=spec['added_vias']:raise ValueError('Actual via contract changed')
    OUT.mkdir();bound=OUT/'native-via-spec.json';write(bound,spec);command[indices[0]]=str(bound.resolve());command[-1]=str((OUT/'native-parity.json').resolve())
    pins=json.loads((OLD/'inputs.json').read_bytes())
    for p in (Path(__file__),old_spec,bound,OLD/'receipt.json'):pins[str(p.resolve())]=sha(p)
    write(OUT/'inputs.json',pins);write(OUT/'derivation.json',{'only_change':'Bind board_sha256 to exact field-zone candidate; every original 68-via UUID/raw net/position/dia/drill contract, all 26 poses, 23 pad masks/shapes/angles and field checks unchanged','original_board_sha256':original['board_sha256'],'candidate_sha256':sha(board),'via_rows_byte_semantics_unchanged':True,'board_changed':False})
    write(OUT/'invocation.json',{'command':command,'existing_slot':'test-only1','no_save_refill_DRC':True,'new_heavy_slots':0})
    env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
    with (OUT/'native.log').open('w',encoding='utf-8') as log:run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
    for p,h in pins.items():
        if sha(p)!=h:raise ValueError('Frozen exact candidate-bound input changed: '+p)
    report=json.loads((OUT/'native-parity.json').read_bytes()) if (OUT/'native-parity.json').exists() else {}
    passed=run.returncode==0 and report.get('native_field_pose_diagnostic',{}).get('verdict')=='PASS' and report.get('summary',{}).get('parity_defects')==0
    receipt={'verdict':'PASS_FIELD_ZONES_SOURCE_API_26_POSES_68_VIAS_23_SMD_MASKS_AND_FIELDS' if passed else 'FAIL_FIELD_ZONES_SOURCE_API','candidate_sha256':sha(board),'native_exit_code':run.returncode,'native_summary':report.get('summary'),'adopted':False,'full_native_refill_DRC_contact_current':'OPEN'}
    write(OUT/'receipt.json',receipt);print(json.dumps(receipt),flush=True)
    return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
