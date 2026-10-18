"""Bind exact transport source, actual SPI differential and full frozen suite."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;OUT=H/'transport-cmd-alignment-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    prep=json.loads((OUT/'preparation-receipt.json').read_bytes())
    diff=json.loads((OUT/'behavior-receipt.json').read_bytes())
    runtime=json.loads((OUT/'full-runtime/receipt.json').read_bytes())
    assert diff['status']=='ACTUAL_SPI_OLD_NEW_TRANSPORT_ALIGNMENT_DIFFERENTIAL_PASS'
    assert runtime['status']=='PASS' and runtime['sources_unchanged']
    source=Path(prep['source']);candidate=OUT/'cnc3_spi_transport_stateful.v'
    assert sha(source)==prep['canonical_SHA256']
    assert sha(candidate)==prep['candidate_SHA256']==diff['candidate_SHA256']==runtime['copied_input_sha256']['cnc3_spi_transport_stateful.v']
    assert runtime['copied_input_sha256']['cnc3_event_bank.v']=='6f034f17c2f70c7161ad13dc605e7ab484844bd71688f6af04bc4bbe46a43841'
    assert runtime['copied_input_sha256']['cnc3_runtime_events.v']=='4a42ebe2f669d1854da0d19477a375279201da171b9fa82ebea43b15e0fb1da9'
    assert 'TRANSPORT_ALIGNMENT_DIFF_PASS cycles=1098329 transactions=80' in (OUT/'execute.log').read_text()
    assert 'SIM2_RUNTIME_PASS checks=1190' in (OUT/'full-runtime/execute.log').read_text()
    paths=[Path(__file__),source,candidate,OUT/'candidate.patch',OUT/'preparation-receipt.json',OUT/'behavior-receipt.json',OUT/'full-runtime/receipt.json',OUT/'runtime-runner-derivation.json',H/'transport_alignment_diff_tb.sv',H/'event-capture-select-r2/reviewable-two-file-overlay-packet.json']
    record={'status':'ISOLATED_CMD_ALIGNMENT_ACTUAL_SPI_DIFFERENTIAL_AND_FULL_SIM2_REGRESSION_PASS_NATIVE_RESOURCE_UNEXECUTED',
      'canonical_source':str(source),'canonical_SHA256':sha(source),'candidate':str(candidate),'candidate_SHA256':sha(candidate),
      'canonical_sources_and_tests_unchanged':True,'adopted':False,
      'exact_scope':'Only CMD RX bit placement, CMD received-CRC/rate-word taps and completed-frame assignment; full1408RX/full1408completed-frame/full1392TXsnapshot/48header buffers retained',
      'inductive_source_argument':['After reset both RX buffers are zero.','During FB the RX shift update is identical.','During CMD candidate RX equals {original_RX[767:0],640zero} before and after every sample. This normalization is preserved through pauses, timing/CRC errors, overrun, CS overlap, transaction end and reset.','CMD CRC16 trailer655:640 and rate-prefix670:640 equal original15:0 and30:0 respectively. FB CRC32C/header taps are unchanged.','Every completion guard therefore sees the same values, and direct candidate frame commit equals the original conditional alignment. All completed frame/snapshot/valid/rejection/rate/MISO behavior follows without changing protocol state or buffer depth.'],
      'actual_SPI_differential':{'cycles':1098329,'transactions':80,'valid_CMD':16,'valid_FB':16,'rejected_headers':40,'streamed_rate_words':417,'binary_fuzz_cycles':180000,'four_state_wire_fuzz_cycles':3000,'comparison':'all public outputs and held fields, full protocol/CRC/timing/TX snapshot state; explicit normalized RX; checks before/after clock and asynchronous reset pulses'},
      'full_frozen_SIM2_suite':{'runtime_SPI_checks':1190,'events_checks':9,'event_storage_checks':11,'provider_checks':7,'default_deny_cycles':10000,'overlays':['registered RAM bypass','literal counter capture selectors','CMD transport alignment']},
      'formal_equivalence':'NOT_RUN','native_resource_mapping':'NOT_RUN_FOR_TRANSPORT_CANDIDATE','physical_wrapper_I4_fit_place_route_timing':'OPEN','bitstream_or_hardware_programming':False,'manufacturing_ready':False,
      'input_SHA256':{str(p):sha(p) for p in paths}}
    (OUT/'reviewable-transport-overlay-packet.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:record[k] for k in ['status','candidate_SHA256','canonical_sources_and_tests_unchanged']}))
if __name__=='__main__':main()
