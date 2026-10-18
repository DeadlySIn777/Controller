"""Independent read-only current phase/source/input consistency observation."""
import datetime,hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
STAGE=HERE.parent
sys.path.insert(0,str(STAGE))
import measure_combined_r1 as M

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    out=M.HERE/'measure/r07-four-fag-shared'
    inputs_path=out/'inputs.json';inputs=json.loads(inputs_path.read_bytes())
    ready_path=STAGE/'ready-r1.json';ready=json.loads(ready_path.read_bytes())
    failures=[]
    for paths in (ready['files'],inputs['tools'],inputs['construction_file_hashes'],inputs['baseline_file_hashes']):
        for path,expected in paths.items():
            if sha(path)!=expected:failures.append('Bound file changed:'+path)
    for role,binary in inputs['native_binaries'].items():
        if sha(binary['path'])!=binary['sha256'] or binary!=ready['native_binaries'][role]:failures.append('Native binary binding:'+role)
    for name,identity in inputs['imported_helpers'].items():
        if sha(identity['path'])!=identity['sha256']:failures.append('Loaded helper changed:'+name)
        if ready['files'].get(identity['path'])!=identity['sha256']:failures.append('At-run helper not in ready source closure:'+name)
    if not (set(inputs['construction_file_hashes'])>=set(json.loads((M.V.FAG/'staged/construction.json').read_bytes())['source_files_sha256'])):failures.append('Constructor source closure omitted')
    M.verify_source(type('Args',(),{'out':out})(),inputs['source_parity_precheck'])
    source=json.loads((out/'source-proof.json').read_bytes())
    if source['verdict']!='PASS' or source['candidate_sha256']!=M.V.EXPECTED['candidate']:failures.append('Current source/API verdict')
    for path,expected in source['observed_output_hashes'].items():
        if sha(path)!=expected:failures.append('Native source output changed:'+path)
    annuli=source['native_api']['added_via_annuli']['rows']
    actual={(row['net'],row['d'],row['drill']) for row in annuli}
    if len(annuli)!=7 or sum(row['net']=='/motherboard_motors/FIELD_GND' for row in annuli)!=5:failures.append('Added via ownership inventory')
    if any(row['actual_via_type']!=4 or row['actual_flashed_layers']!=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'] for row in annuli):failures.append('Native added via type/annuli')
    assertion_count=(out/'native-parity.log').read_text(encoding='utf-8').count('assert "false" failed in GetWidth()')
    result={'schema':'four-fag-independent-phase-observation-v1','verdict':'PASS_CURRENT_BINDINGS' if not failures else 'FAIL',
            'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':json.loads((out/'status.json').read_bytes()),
            'inputs_sha256_observed_now':sha(inputs_path),'ready_sha256':sha(ready_path),'source_proof_sha256':sha(out/'source-proof.json'),
            'ready_files':len(ready['files']),'construction_pins':len(inputs['construction_file_hashes']),'loaded_nonstdlib_helpers':len(inputs['imported_helpers']),
            'binary_roles':sorted(inputs['native_binaries']),'source_export_counts':{key:source['fresh_export'][key] for key in ('components','nets','nodes')},
            'actual_added_via_annuli':annuli,'native_GetWidth_warning_count':assertion_count,'failures':failures,
            'native_jobs':0,'adopted':False,'manufacturing_ready':False,
            'limits':['This observes current bindings, not an independent assertion of original launcher time','Seven diameter-query warnings recorded; parity and FlashLayer checks completed, uniform native source widths exact','Original C11061 remains16V, corrected hierarchy/library branch separate','Main refill/DRC and dual connectivity verdicts still pending']}
    destination=HERE/'phase-source-consistency.json'
    if destination.exists():raise ValueError('Distinct observation required')
    destination.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('verdict','ready_files','construction_pins','loaded_nonstdlib_helpers','native_GetWidth_warning_count','failures')}))
if __name__=='__main__':main()
