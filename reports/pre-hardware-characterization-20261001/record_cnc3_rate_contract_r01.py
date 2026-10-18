"""Record the frozen CNC3 rate contract separately from component experiments."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'gateware/v3/frozen/spec/protocol.json'
norm=Path('C:/Users/Gluis/claude-worktrees/controller-interface-spec/docs/interface-spec/01-protocol-and-schedule.md')
out=ROOT/'reports/pre-hardware-characterization-20261001/CNC3-frozen-rate-contract-r01'
out.mkdir(exist_ok=False)
spec=json.loads(source.read_text())
layout=spec['frames']['cap3_page0']
fields=layout['fields'] if isinstance(layout,dict) else layout
wanted={r['name']:r['rule'] for r in fields if r['name']in('core_hz','max_rate','timing_min','timing_max')}
assert wanted=={'core_hz':'50,000,000','max_rate':'0x01000000','timing_min':'100','timing_max':'1023'},wanted
rate=50_000_000*int(wanted['max_rate'],16)/2**32
assert rate==195312.5
text=norm.read_text(encoding='utf8')
line=next(x for x in text.splitlines() if x.startswith('| D01-12 |'))
assert '195,312.5' in line and '2,000,000' in line
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
v={'status':'SOURCE_CONTRACT_CONFIRMED_ENFORCEMENT_AND_HIGHER_TARGET_OPEN',
   'evidence_type':'SOURCE_INSPECTION_AND_EXACT_ARITHMETIC',
   'input_sha256':{str(p):sha(p) for p in (source,norm,Path(__file__))},
   'spec_revision':spec['spec_revision'],'literal_CAP3_fields':wanted,
   'actual_CNC3_protocol_contract_steps_per_second':rate,
   'assumed_core_hz':50_000_000,'max_unsigned_magnitude_rate':16777216,
   'configured_timing_min_core_ticks':100,'configured_timing_max_core_ticks':1023,
   'normative_decision':line,
   'historical_CNC1_same_value_is_separate_evidence':True,
   'current_stateful_candidate_rate_enforcement':'Root identified missing incoming MAX_RATE/channel timing checks; actual corrective implementation and adversarial acceptance tests required before accepting stateful candidate',
   'user_2MHz_target':'Retained as unfinished target. Actual protocol/rate/timing evolution, drive limits, routed electrical qualification, vendor timing and complete runtime tests required; no hidden cap or specification change made.',
   'isolated_9_and_12_tick_component_sweeps_are_not_current_protocol_configuration':True,
   'hardware_qualified':False,'manufacturing_ready':False}
(out/'receipt.json').write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
print(json.dumps({'rate_contract':rate,'hardware_qualified':False}))
