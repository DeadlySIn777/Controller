"""Freeze complete serialized discrete copper geometry, then check it through the test-only native slot."""
import ast,hashlib,json,os,re,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;OUT=H/'all-copper-native-contract-r1'
sys.path.insert(0,str(H));import native_pose_signal_contract as NC

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,value):Path(p).write_text(json.dumps(value,indent=1)+'\n',encoding='utf-8')
def main():
    if OUT.exists():raise ValueError('Fresh complete copper check required')
    stage=H/'field-power-native-trial-r1';board=stage/'copy/board.kicad_pcb';receipt=json.loads((stage/'receipt.json').read_bytes())
    if sha(board)!=receipt['candidate_sha256'] or receipt['verdict']!='PASS_SOURCE_NATIVE_API_26_POSES_68_VIAS_AND_FIELD_ZONES_WITH_PG_AREA':raise ValueError('Frozen candidate gate rejected')
    invocation=stage/'invocation.json';command=json.loads(invocation.read_bytes())['command'];parser=Path(command[9])
    tree=ast.parse(parser.read_text(encoding='utf-8'));ns={'re':re}
    decl=[n for n in tree.body if (isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='TOKEN') or (isinstance(n,ast.FunctionDef) and n.name in ('sexpr_parse','child','children','atom','norm'))]
    exec(compile(ast.Module(body=decl,type_ignores=[]),'frozen-net-parser','exec'),ns)
    parse,child=ns['sexpr_parse'],ns['child'];iu=lambda value:int(round(float(value)*1000000));copper={}
    for uid,ch in NC.C.inventory(board.read_bytes())[4].items():
        root=parse(ch.decode());kind=root[0];net=child(root,'net')
        row={'kind':kind,'raw_net':net[1] if net else '','chunk_sha256':hashlib.sha256(ch).hexdigest()}
        if kind=='via':row.update(at_IU=list(map(iu,child(root,'at')[1:3])),drill_IU=iu(child(root,'drill')[1]),diameters_IU={l:iu(child(root,'size')[1]) for l in ('F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu')})
        elif kind=='segment':row.update(start_IU=list(map(iu,child(root,'start')[1:3])),end_IU=list(map(iu,child(root,'end')[1:3])),width_IU=iu(child(root,'width')[1]),layer=child(root,'layer')[1])
        else:raise ValueError('Unsupported serialized copper kind '+kind)
        copper[uid]=row
    OUT.mkdir();expected=OUT/'expected.json';write(expected,{'board_path':str(board.resolve()),'board_sha256':sha(board),'copper':copper})
    original_helper=command[4];command[4:5]=[str((H/'native_all_copper_contract_r1.py').resolve()),original_helper,str(expected.resolve())];command[-1]=str((OUT/'native-parity.json').resolve())
    pins={str(p.resolve()):sha(p) for p in (Path(__file__),H/'native_all_copper_contract_r1.py',board,board.with_suffix('.kicad_pro'),board.with_suffix('.kicad_dru'),stage/'receipt.json',invocation,expected,parser)}
    for arg in command:
        p=Path(arg)
        if p.is_file():pins[str(p.resolve())]=sha(p)
    write(OUT/'inputs.json',pins);write(OUT/'invocation.json',{'command':command,'existing_slot':'test-only1','new_heavy_slots':0})
    env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
    with (OUT/'native.log').open('w',encoding='utf-8') as log:run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
    for p,h in pins.items():
        if sha(p)!=h:raise ValueError('Frozen complete native input changed: '+p)
    native=json.loads((OUT/'native-parity.json').read_bytes()) if (OUT/'native-parity.json').exists() else {}
    gate=native.get('all_discrete_copper_exact_native_contract',{});passed=run.returncode==0 and gate.get('verdict')=='PASS'
    report={'verdict':'PASS_ALL_NATIVE_DISCRETE_COPPER_AND_SOURCE_POSE_CONTRACT' if passed else 'FAIL_ALL_NATIVE_DISCRETE_COPPER','candidate_sha256':sha(board),'native_exit_code':run.returncode,'copper_contract':gate,'source_API_summary':native.get('summary'),'adopted':False,'full_refill_connectivity_DRC_current_and_final_composition':'OPEN'}
    write(OUT/'receipt.json',report);print(json.dumps(report),flush=True)
    return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
