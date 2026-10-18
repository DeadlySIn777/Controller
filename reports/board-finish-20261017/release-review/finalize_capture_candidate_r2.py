"""Review packet for the smallest behavior-qualified RAM/capture overlay."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;OUT=H/'event-capture-select-r2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    prep=json.loads((OUT/'preparation-receipt.json').read_bytes())
    behavior=json.loads((OUT/'behavior-receipt.json').read_bytes())
    unique=json.loads((OUT/'unique-selector-receipt.json').read_bytes())
    runtime=json.loads((OUT/'full-runtime/receipt.json').read_bytes())
    mapping=json.loads((OUT/'native-full-map/receipt.json').read_bytes())
    assert behavior['status']=='CAPTURE_ONLY_SELECTOR_EXHAUSTION_AND_STRICT_BOUNDARY_DIFFERENTIAL_PASS'
    assert unique['status']=='ALL_65536_FOUR_STATE_SELECTORS_THREE_DISTINCT_CHANNEL_PAYLOAD_PROFILES_PASS'
    assert runtime['status']=='PASS' and runtime['sources_unchanged'] and mapping['execution']['exit']==0
    assert mapping['canonical_sources_unchanged'] and mapping['project_semantics_unchanged']
    events=OUT/'cnc3_runtime_events.v';bank=H.parent/'efinity-memory-inference-r1/registered-bypass/cnc3_event_bank.v'
    assert sha(events)==prep['candidate_SHA256']==runtime['copied_input_sha256']['cnc3_runtime_events.v']
    assert sha(bank)==runtime['copied_input_sha256']['cnc3_event_bank.v']=='6f034f17c2f70c7161ad13dc605e7ab484844bd71688f6af04bc4bbe46a43841'
    source=Path(prep['source']);assert sha(source)==prep['canonical_SHA256']
    resources=mapping['resources'];screen=resources['EFX_LUT4']+resources['EFX_ADD']
    paths=[Path(__file__),source,events,bank,OUT/'candidate.patch',OUT/'preparation-receipt.json',OUT/'behavior-receipt.json',OUT/'unique-selector-receipt.json',OUT/'full-runtime/receipt.json',OUT/'native-full-map/receipt.json',H.parent/'efinity-bram-behavior-r1/receipt.json']
    record={'status':'TWO_FILE_RAM_AND_LITERAL_CAPTURE_OVERLAY_BEHAVIOR_QUALIFIED_NATIVE_MAP_PASS_OVER_CAPACITY',
      'selected_for_review_only':True,'canonical_source_adoption':False,
      'exact_overlays':[{'destination':'gateware/v3/runtime/cnc3_event_bank.v','candidate':str(bank),'candidate_SHA256':sha(bank),'canonical_SHA256':'65fa79532ac564c58d878b7e2b804de11e5af7e85b1157638d7823645aa92659','change':'unconditional registered RAM read plus registered write-first bypass; no array reset or latency change'},
       {'destination':'gateware/v3/runtime/cnc3_runtime_events.v','candidate':str(events),'candidate_SHA256':sha(events),'canonical_SHA256':prep['canonical_SHA256'],'change':'only capture function: sixteen literal selector cases replace guarded arithmetic variable part-selects'}],
      'features_unchanged':['256records','160bits/record','eightbanks','sevenproducers/clock','producer ordering','capture cycle','sequence255to1wrap','same-cycle ACK admission','head masking/prefetch','overflow','clear/reset','invalid and unknown selectors return0','selected X/Z payload bits'],
      'strict_boundary_cases':55296,'strict_differential_cycles':363328,'strict_bus_scope':'all1280write_data bits plus addresses/enables equal, public outputs and queue state equal',
      'independent_selector_tests':{'full_four_state_patterns':65536,'distinct_channel_payload_profiles':3,'function_checks':196608,'unknown_selector_checks':195840},
      'full_unchanged_regression':{'runtime_SPI_checks':1190,'events_checks':9,'event_storage_checks':11,'provider_checks':7,'default_deny_cycles':10000,'physical_authority':False},
      'native_mapping_scope':'disconnected functional SIM2 top, TrionT20F256/I4 map only, insert-ios0; not physical controller wrapper',
      'native_speed_resources':resources,'coarse_LUT4_plus_ADD':screen,'T20_equivalent_LE_screen':19728,'over_screen':screen-19728,'RAM5K_used_available':[resources['EFX_RAM_5K'],204],
      'other_experiments_not_included':['r1fixedproducerdispatcher','r3helddisabledbuses','r4prefixadmission'],
      'remaining':['resource fit','complete physical wrapper and135port integration','I4place/route/static timing and external delays','drive/slew/load and unused I/O defaults','CDC/reset release','full production provider/qualification','bitstream/hardware measurements'],
      'formal_equivalence':'NOT_RUN','manufacturing_ready':False,'input_SHA256':{str(p):sha(p) for p in paths}}
    (OUT/'reviewable-two-file-overlay-packet.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:record[k] for k in ['status','native_speed_resources','coarse_LUT4_plus_ADD','over_screen']}))
if __name__=='__main__':main()
