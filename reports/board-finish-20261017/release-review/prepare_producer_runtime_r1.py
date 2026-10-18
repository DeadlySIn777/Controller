"""Prepare a guarded full suite; never run before root differential PASS."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;OUT=H/'producer-fifo-independent-supplement-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    supplement=json.loads((OUT/'receipt.json').read_bytes());assert supplement['status']=='PRODUCER_FIFO_FOCUSED_SUPPLEMENT_PASS'
    source=H/'transport-cmd-alignment-r1/run_full_runtime_with_transport.py';text=source.read_text()
    before='release-review/event-capture-select-r2/cnc3_runtime_events.v';assert text.count(before)==1
    text=text.replace(before,'event-producer-fifo-r1/cnc3_runtime_events.v')
    guard=''' parent_gate=ROOT/'reports/board-finish-20261017/event-producer-fifo-r1/behavior-receipt.json'
 supplement_gate=ROOT/'reports/board-finish-20261017/release-review/producer-fifo-independent-supplement-r1/receipt.json'
 producer_source=ROOT/'reports/board-finish-20261017/event-producer-fifo-r1/cnc3_runtime_events.v'
 producer_diff=ROOT/'reports/board-finish-20261017/event-producer-fifo-r1/candidate_diff.v'
 assert parent_gate.exists(),'WAIT_ROOT_DIFFERENTIAL_PASS'
 assert json.loads(parent_gate.read_bytes())['status']=='PRODUCER_FIFO_DIFFERENTIAL_PASS'
 assert json.loads(supplement_gate.read_bytes())['status']=='PRODUCER_FIFO_FOCUSED_SUPPLEMENT_PASS'
 assert sha(producer_source)=='4d21b8af4ca2decc10d872361fb033fcaecb939b14ff4d62d959609cdc2f30d6'
 assert producer_diff.read_text().replace('module cnc3_runtime_events_candidate(', 'module cnc3_runtime_events(')==producer_source.read_text()
'''
    marker='def main():\n';assert text.count(marker)==1;text=text.replace(marker,marker+guard)
    marker=' def execute(name,argv):\n';assert text.count(marker)==1
    binding=" receipt['producer_qualification_gate']={'root_differential_receipt_SHA256':sha(parent_gate),'independent_supplement_receipt_SHA256':sha(supplement_gate),'exact_selected_producer_source_SHA256':sha(producer_source),'candidate_diff_normalization_equals_selected_source':True}\n"
    text=text.replace(marker,binding+marker)
    target=OUT/'run_full_runtime_qualified.py';assert not target.exists();target.write_text(text)
    record={'status':'FULL_SUITE_RUNNER_PREPARED_ROOT_DIFFERENTIAL_PASS_REQUIRED','source_runner_SHA256':sha(source),'derived_runner_SHA256':sha(target),'fixed_bank_SHA256':'6f034f17c2f70c7161ad13dc605e7ab484844bd71688f6af04bc4bbe46a43841','selected_events_SHA256':'4d21b8af4ca2decc10d872361fb033fcaecb939b14ff4d62d959609cdc2f30d6','verified_transport_SHA256':'c909378cb28cf87c7113b1b92c6cdd82f71e166c64eb87548a8880ba85c9d4cc','runner_delta':'producer event overlay replaces capture-only event overlay; exact root PASS, supplement PASS and source/diff-normalization guard before creating outputs; frozen tests and taskset16,17 unchanged','launched':False,'adopted':False}
    (OUT/'full-suite-runner-preparation.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
if __name__=='__main__':main()
