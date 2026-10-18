from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;D=H/'arithmetic-sharing-peer-addendum-r01'
if D.exists():raise RuntimeError('fresh addendum required')
D.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
handoff=H/'arithmetic-sharing-handoff-r01/receipt.json';peer=H/'peer-prefix-optimization-review-r01/receipt.json'
assert json.loads(peer.read_text())['status']=='PASS'
report=H/'prefix-record-full-r01/report.json';r=json.loads(report.read_text());assert r['coarse_T20_capacity_screen']['status']=='PASS'
receipt={'status':'PASS','immutable_handoff':{'path':str(handoff),'sha256':sha(handoff)},'independent_read_only_review':{'path':str(peer),'sha256':sha(peer),'new_HDL_run_claimed':False},'report_metadata_qualification':{'artifact':str(report),'sha256':sha(report),'inherited_stale_open_dependency':r['open_dependencies'][0],'correct_current_interpretation':'The optimized lower-bound screen passes at19,477/19,728. Complete-product capacity and actual vendor fit/timing remain open; CAP3/fullprovider/output logic not included. Historical failed screens stay historical. The inherited replay template sentence is not a current overflow result.','frozen_report_or_runner_modified':False},'public_source_CAD_runtime_adopted':False}
(D/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',newline='\n');print(D/'receipt.json',sha(D/'receipt.json'))
