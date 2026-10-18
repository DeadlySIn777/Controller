"""Read-only independent final receipt/binding replay; starts no native jobs."""
import datetime,hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
STAGE=HERE.parent
sys.path.insert(0,str(STAGE))
import measure_combined_r1 as M

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    destination=HERE/'final-consistency.json'
    if destination.exists():raise ValueError('Distinct immutable receipt required')
    out=M.HERE/'measure/r07-four-fag-shared'
    proof=json.loads((out/'proof.json').read_bytes());inputs=json.loads((out/'inputs.json').read_bytes());ready=json.loads((STAGE/'ready-r1.json').read_bytes());status=json.loads((out/'status.json').read_bytes())
    errors=[]
    for name,pins in (('ready',ready['files']),('construction',inputs['construction_file_hashes']),('baseline',inputs['baseline_file_hashes']),('tools',inputs['tools']),('observed',proof['observed_file_hashes'])):
        for path,digest in pins.items():
            if sha(path)!=digest:errors.append(name+' changed:'+path)
    if sha(out/'inputs.json')!=proof['inputs_sha256']:errors.append('Exact inputs bytes differ')
    for role,identity in inputs['native_binaries'].items():
        if sha(identity['path'])!=identity['sha256'] or identity!=proof['native_binaries'][role] or identity!=ready['native_binaries'][role]:errors.append('Binary identity:'+role)
    for name,identity in inputs['imported_helpers'].items():
        if sha(identity['path'])!=identity['sha256'] or ready['files'].get(identity['path'])!=identity['sha256']:errors.append('Helper binding:'+name)
    invocation=json.loads((STAGE/'invocation-r1.json').read_bytes());options=invocation['command'][2:];args=type('Args',(),{})()
    for i in range(0,len(options),2):setattr(args,options[i][2:].replace('-','_'),Path(options[i+1]))
    if sha(args.candidate)!=proof['candidate_sha256'] or sha(args.live_board)!=inputs['before_sha256']:errors.append('Source/live board identity')
    source=json.loads((out/'source-proof.json').read_bytes())
    M.verify_source(args,inputs['source_parity_precheck'])
    if source['verdict']!='PASS' or source['candidate_sha256']!=proof['candidate_sha256']:errors.append('Source/API parity')
    for path,digest in source['observed_output_hashes'].items():
        if sha(path)!=digest:errors.append('Source output identity:'+path)
    contract=M.validate_construction(args.construction,args.candidate)
    if contract!=proof['exact_reconstructed_source_contract']:errors.append('Construction replay differs')
    after=json.loads((out/'partitions.json').read_bytes());M.check_board(after,args.candidate)
    guards={};summaries={}
    for role,board,directory,prefix in (('r07',args.before_board,args.before_measure,'baseline-'),('r06',args.r06_board,args.r06_measure,'r06-')):
        part=json.loads((out/(prefix+'partitions.json')).read_bytes());M.check_board(part,board)
        guards[role]=M.compare(part,after)
        key='connectivity_r07_live' if role=='r07' else 'connectivity_r06'
        if guards[role]!=proof[key]:errors.append('Guard differs:'+role)
        for name in ('partitions.json','summary.json','sha256.txt','drc.json'):
            if (out/(prefix+name)).read_bytes()!=(directory/name).read_bytes():errors.append('Baseline receipt:'+role+name)
        manifest=M.manifest((out/(prefix+'sha256.txt')).read_bytes())
        for name in M.PROJECT_NAMES|{'board.kicad_pcb'}:
            if sha(directory/'copy'/name)!=manifest[name]:errors.append('Baseline measured copy:'+role+name)
        summaries[role]=M.check_summary(json.loads((out/(prefix+'drc.json')).read_bytes()),part,json.loads((out/(prefix+'summary.json')).read_bytes()),sha(board))
    summaries['after']=M.check_summary(json.loads((out/'drc.json').read_bytes()),after,json.loads((out/'summary.json').read_bytes()),sha(args.candidate))
    if summaries['after']!=proof['drc']['after']:errors.append('Raw DRC summary differs')
    manifest=M.manifest((out/'sha256.txt').read_bytes())
    for name in M.PROJECT_NAMES|{'board.kicad_pcb'}:
        if sha(out/'copy'/name)!=manifest[name]:errors.append('Candidate measured copy:'+name)
    expected=M.combined_verdict(guards['r07'],guards['r06'],summaries['after']['errors'])
    if expected!=proof['verdict'] or status['phase']!='COMPLETE' or status['verdict']!=expected:errors.append('Final fatal verdict/status differs')
    if proof['adopted'] or proof['manufacturing_ready']:errors.append('Improper adoption/readiness claim')
    result={'schema':'four-fag-independent-final-receipt-replay-v1','verdict':'PASS_RECEIPT_REPLAY_CANDIDATE_FAIL' if not errors else 'FAIL_REPLAY',
            'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate_sha256':proof['candidate_sha256'],
            'candidate_native_verdict':expected,'against_actual_r07':guards['r07'],'against_r06':guards['r06'],'drc':summaries,
            'api_unconnected':after['unconnected'],'pad_joins':sum(max(0,len(groups)-1) for groups in after['nets'].values()),
            'ready_files':len(ready['files']),'construction_pins':len(inputs['construction_file_hashes']),'helpers_rehashed':len(inputs['imported_helpers']),
            'proof_observed_files_rehashed':len(proof['observed_file_hashes']),'native_binary_roles':sorted(inputs['native_binaries']),
            'proof_sha256':sha(out/'proof.json'),'inputs_sha256':sha(out/'inputs.json'),'ready_sha256':sha(STAGE/'ready-r1.json'),
            'source_proof_sha256':sha(out/'source-proof.json'),'strict_source_reference_receipt_sha256':sha(HERE/'strict-reference-r1.json'),
            'evaluator_sha256':sha(__file__),'failures':errors,'native_jobs':0,'adopted':False,'manufacturing_ready':False,
            'limits':['Same frozen strict native guard and raw-DRC evaluator independently rerun; no fresh native computation','Current identities are rehashed; original launch timing remains the original runner evidence','Four-signal stricter reference replay is separate host source evidence, not full electrical/physical qualification','Candidate is withheld because fourteen r06 pad relationships remain lost, despite r07 seven gains/zero losses and ordinary DRC zero']}
    destination.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('verdict','candidate_native_verdict','api_unconnected','pad_joins','ready_files','helpers_rehashed','failures')}))

if __name__=='__main__':main()
