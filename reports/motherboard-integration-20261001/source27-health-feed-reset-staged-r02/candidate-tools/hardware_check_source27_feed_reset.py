"""Exact parent-only receiving CLR successor; no ramp or manufacture claim."""
from pathlib import Path
import json,hashlib
from hardware_validate_motor_feed_reset import validate
ROOT=Path(__file__).resolve().parents[1]
BASELINE='reports/motherboard-integration-20261001/source27-health-parent-staged-r01/final-source27-candidate/motherboard/design.json'
BASELINE_SHA='250be5ded6c3e7f4c4413d5066d368df8e32288c7f828807c20ebeecbf3a5226'
PEER_SHA='d7be099c0703d1a61cb8557b015e650a2334609f9b117dbda15737bcc1112979'
HELPER_SHA='0e2688c721f48d73f52a82bcc73de35ab0591007b9dd888efa8dadf59b34c0e5'
PRIMARY='reports/motherboard-power-entry-20261001/feed-latch-reset-source-r01/candidate-r04'
PRIMARY_SHA='c75808eba7431a3cbb2c2c39758dbc28c92f028768f9e3c46a0f66c3089e6a0a'
ADDED=('C11089','C11090','C11091','C11092','R11082','R11083','U11035','U11036','U11037','U11038')
OVERRIDES={('U11032','6'):'/motherboard_power_entry/MOTOR_FEED_CLEAR_FAST_N_A',('U11034','6'):'/motherboard_power_entry/MOTOR_FEED_CLEAR_FAST_N_B'}
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def check_feed_reset(tree,model,mapping,actual):
 errors=[];meta=model.get('motor_feed_reset_correction');ledger=mapping.get('reviewed_motor_feed_reset_delta')
 present=bool(meta or ledger or any(r in model['components']for r in ADDED))
 if not present:return errors,{},{}
 for rel,h in((BASELINE,BASELINE_SHA),('tools/hardware_validate_motor_feed_reset.py',PEER_SHA),('tools/hardware_apply_motor_feed_reset.py',HELPER_SHA),(PRIMARY+'/freeze-receipt.json',PRIMARY_SHA)):
  if not(ROOT/rel).is_file()or sha(ROOT/rel)!=h:errors.append('Frozen receiving CLR review dependency changed '+rel)
 if errors:return errors,{},{}
 if not ledger or ledger.get('id')!='MB-MOTOR-FEED-POR-001' or ledger.get('parent_only_override')is not True or ledger.get('inherited_child_and_Source26_immutable')is not True or ledger.get('physical_qualified')is not False or ledger.get('frozen_receipt_sha256')!=PRIMARY_SHA or ledger.get('frozen_primary_review_sha256')!=sha(ROOT/PRIMARY/'primary-and-integration-review.json') or ledger.get('exact_added_references')!=list(ADDED):errors.append('Exact frozen parent receiving CLR ledger required')
 baseline=json.loads((ROOT/BASELINE).read_text());errors.extend(validate(model,baseline,actual)['errors'])
 expected_functions={'FEED_POR':{'1':'RESET_N','2':'GND','3':'MR_N','4':'CT','5':'SENSE','6':'VDD'},'FEED_SCHMITT':{'1':'NC','2':'A','3':'GND','4':'Y','5':'VCC'}}
 for name,pins in expected_functions.items():
  rows=tree.findall('.//libparts/libpart[@lib="CNC_MB_FeedReset"][@part="'+name+'"]')
  if len(rows)!=1 or {p.get('num'):p.get('name')for p in rows[0].findall('pins/pin')}!=pins:errors.append('Exact primary native reset function map required '+name)
 extra={}
 for bank,sup,buf,c1,c2,pd in(('A','U11035','U11036','C11089','C11090','R11082'),('B','U11037','U11038','C11091','C11092','R11083')):
  slow='/motherboard_power_entry/MOTOR_FEED_CLEAR_N_'+bank;fast='/motherboard_power_entry/MOTOR_FEED_CLEAR_FAST_N_'+bank;raw='/motherboard_power_entry/MOTION_5V_RAW';gnd='/LOGIC_GND'
  new={sup:{'1':slow,'2':gnd,'3':raw,'4':None,'5':raw,'6':raw},buf:{'1':None,'2':slow,'3':gnd,'4':fast,'5':raw},c1:{'1':raw,'2':gnd},c2:{'1':raw,'2':gnd},pd:{'1':fast,'2':gnd}}
  for ref,pins in new.items():
   for pin,net in pins.items():extra[ref,pin]=net
  capowners=((c1,sup,'6','2'),(c2,buf,'5','3'))
  for cap,owner,power,ret in capowners:
   if actual.get((cap,'1'))!=actual.get((owner,power))or actual.get((cap,'2'))!=actual.get((owner,ret)):errors.append('Actual RAW local reset bypass must own correct physical power/return '+cap)
  if actual.get((buf,'2'))!=actual.get((sup,'1'))or actual.get((buf,'4'))!=actual.get(('U11032'if bank=='A'else'U11034','6')):errors.append('Actual RAW reset source/buffer/receiving CLR topology required '+bank)
 return errors,OVERRIDES,extra
