"""Bind completed direct-tool differential run and explicit-X/Z subprocess run."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;OUT=H/'event-dispatch-r1'
ROOT=H.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    prep=json.loads((OUT/'preparation-receipt.json').read_bytes())
    xz=json.loads((OUT/'explicit-xz-receipt.json').read_bytes())
    assert xz['status']=='EXPLICIT_XZ_OLD_NEW_DISPATCH_PASS'
    assert sha(Path(prep['canonical_source']))==prep['canonical_SHA256']
    assert sha(OUT/'cnc3_runtime_events.v')==prep['candidate_SHA256']
    assert sha(H/'event_dispatch_diff_tb.sv')=='53181c39f6cd29e5f62b31fd4f9edd540ceb1332c831d303e1351d772922b457'
    assert 'EVENT_DISPATCH_DIFF_PASS boundary_cases=55296 cycles=363328' in (OUT/'differential-execute.log').read_text()
    paths=[Path(__file__),H/'prepare_event_dispatch_r1.py',H/'event_dispatch_diff_tb.sv',OUT/'cnc3_runtime_events.v',OUT/'original_diff.v',OUT/'candidate_diff.v',OUT/'differential.vvp',OUT/'differential-execute.log',OUT/'explicit-xz-receipt.json',H.parent/'efinity-memory-inference-r1/registered-bypass/cnc3_event_bank.v']
    record={'status':'ISOLATED_DISPATCH_BOUNDARY_AND_EXTERNAL_STRESS_OLD_NEW_DIFFERENTIAL_PASS','canonical_unchanged':True,
      'candidate_SHA256':prep['candidate_SHA256'],'canonical_SHA256':prep['canonical_SHA256'],
      'differential_engine':'installed WSL GarciaMechBuilder Icarus Verilog, taskset CPUs16,17; four-state case-inequality checks',
      'direct_tool_compile_exit':0,'direct_tool_execute_exit':0,'direct_tool_exec_session':74189,
      'console_provenance':'differential-execute.log is verbatim stdout copied from the completed direct exec result; transcript retains compile warning and full command',
      'compile_warning':'shared test stimulus literal exceeds288bits and is truncated equally for both DUTs; no RTL compile warning; retained in tool transcript',
      'boundary_cases':55296,'cycles':363328,'producer_masks':128,'write_bank_alignments':8,'free_slots':list(range(9)),'next_sequence_starts':[254,255,1],'same_cycle_delivered_ACK':[False,True],
      'all_seven_accepting_cases':96,'ACK_cases':27648,'exact_full_cases':6144,'multi_event_sequence_wrap_cases':64,
      'seeded_boundary_scope':'Each boundary case starts after reset from an explicitly initialized legal ring state and all256known memory words, then runs actual clocked prefetch, producer/ACK dispatch and commits. This enumerates transition boundaries; it does not prove every seeded state reachable by external stimulus.',
      'external_only_scope':['260 fault enqueue attempts reach256capacity+sticky overflow','256snapshot/complete/exact ACK handshakes drain queue','clear and asynchronous reset with pending writes','30000deterministic stress cycles with requests, provider loss, captures, debounce/polarity changes, malformed ACKs, clear/reset, unknown inputs'],
      'compared_after_every_clock':['event_head/status/probe_status/index_armed/overflow','rd/wr/count/next_sequence/snapshot_sequence/delivered_sequence/prefetched_rd','write_enable/write_address/full1280bitwrite_data'],
      'explicit_XZ_scope':{'receipt_SHA256':sha(OUT/'explicit-xz-receipt.json'),'simultaneous_producers':7,'literal_Z_X_payload_preserved_in_write_bus_and_observable_head':True,'delivered_ack_pops_once':True,'unknown_if_controls':True},
      'logical_equivalence_argument':'Existing task admission/temp_count/temp_wr/temp_sequence updates and call ordering are retained. Accepted consecutive addresses number at most7, so modulo8bank destinations are distinct. Each fixed producer payload and slot is recorded once; exact one-hot case writes the same full payload/address at the same clock. Default bus zeroing and clear/reset assignments are unchanged. No forced synthesis assertion/parallel-case attribute is used.',
      'capacity_depth_width_producer_limits_changed':False,'canonical_source_adoption':False,'formal_equivalence':'NOT_RUN','native_mapping':'SEPARATE_RECEIPT','full_existing_runtime_regression_with_dispatch':'OPEN','physical_wrapper_place_route_timing':'OPEN','manufacturing_ready':False,
      'input_output_SHA256':{str(p):sha(p) for p in paths}}
    (OUT/'behavior-receipt.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:record[k] for k in ['status','boundary_cases','cycles','candidate_SHA256','canonical_unchanged']}))
if __name__=='__main__':main()
