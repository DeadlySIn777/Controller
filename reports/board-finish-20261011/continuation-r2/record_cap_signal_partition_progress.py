"""Record complete native connectivity while separate full DRC is pending."""
import hashlib,json,sys,datetime
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
import measure_cap_signal_r1 as M
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    out=HERE/'cap-signal-native-r1/measure';target=out/'native-partition-progress-r1.json'
    if target.exists():raise ValueError('Fresh progress receipt required')
    inputs=json.loads((out/'inputs.json').read_bytes());construction=HERE/'cap-signal-native-r1/construction.json'
    M.verify_inputs(out,inputs,sha(out/'inputs.json'),M.ReadSet())
    for field in ('construction_file_hashes','baseline_file_hashes','tools'):
        for p,h in inputs[field].items():
            if sha(p)!=h:raise ValueError('Frozen run input changed '+p)
    for role,row in inputs['imported_helpers'].items():
        if sha(row['path'])!=row['sha256']:raise ValueError('Frozen helper changed '+role)
    candidate=Path(inputs['after_board']);proof=M.validate_construction(construction,candidate)
    if sha(candidate)!=inputs['after_sha256'] or sha(inputs['live_board'])!=inputs['before_sha256']:raise ValueError('Candidate/live changed')
    paths={k:out/n for k,n in [('candidate','partitions.json'),('r07','baseline-partitions.json'),('r06','r06-partitions.json')]};rows={k:json.loads(p.read_bytes()) for k,p in paths.items()}
    M.check_board(rows['candidate'],candidate);M.check_board(rows['r07'],inputs['before_board'])
    r06board=HERE.parent.parent/'routing-resume-20261011'
    source=json.loads(construction.read_bytes());r06=Path('Z:/pcb-runs/claude-finish/integrate/revs/r06-stitch-plane-pads-2.kicad_pcb');M.check_board(rows['r06'],r06)
    live=M.compare(rows['r07'],rows['candidate']);old=M.compare(rows['r06'],rows['candidate'])
    progress={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'evidence_class':'fresh native KiCad in-memory refill plus full uncapped pad connectivity; DRC separately pending','candidate_sha256':inputs['after_sha256'],'missing_pad_joins':rows['candidate']['pad_island_joins'],'unconnected_api_uncapped':rows['candidate']['api_unconnected_count'],'connectivity_r07_live':live,'connectivity_r06':old,'exact_native_owned_construction':proof,'full_DRC':'RUNNING','final_measurement_verdict':'OPEN; r06 still contains losses','source_parity':'PASS; separate frozen source-proof.json','observed_partition_hashes':{k:{'path':str(p),'sha256':sha(p)} for k,p in paths.items()},'adopted':False,'manufacturing_ready':False}
    target.write_text(json.dumps(progress,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({k:progress[k] for k in ['candidate_sha256','missing_pad_joins','unconnected_api_uncapped','connectivity_r07_live','connectivity_r06','full_DRC']}),flush=True)
if __name__=='__main__':main()
