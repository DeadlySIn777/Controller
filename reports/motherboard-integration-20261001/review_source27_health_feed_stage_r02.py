"""Independent staged native/default/primary-function adversarial controls."""
from pathlib import Path
import sys,json,copy,hashlib,importlib.util,xml.etree.ElementTree as ET,subprocess
ROOT=Path.cwd();P=ROOT/'reports/motherboard-integration-20261001/source27-health-feed-reset-staged-r02';T=P/'candidate-tools';D=P/'candidate/motherboard'
sys.path[:0]=[str(T),str(ROOT/'tools')]
import hardware_check_source27_feed_reset as reset
reset.ROOT=ROOT
import hardware_validate_motherboard as v
v.ROOT=ROOT;v.OUT=D
model=json.loads((D/'design.json').read_text());mapping=json.loads((D/'assembly-map.json').read_text());tree=ET.parse(D/'netlist.xml');actual=v.nodes(tree)
errors=v.validate(tree,model,mapping,True)
assert not errors,errors
mutations=[]
for ref,pin,wrong in(('U11035','1','MOTOR_FEED_CLEAR_N_B'),('U11037','1','MOTOR_FEED_CLEAR_N_A'),('U11035','3','MOTOR_FEED_CLEAR_N_A'),('U11035','4','LOGIC_GND'),('U11036','5','IO_3V3'),('U11036','4','MOTOR_FEED_CLEAR_FAST_N_B'),('R11082','2','FIELD_GND'),('U11032','6','MOTOR_FEED_CLEAR_N_A'),('U11024','3','MOTOR_FEED_ON_A'),('C11089','1','MOTOR5A')):
 bad=copy.deepcopy(model);bad['components'][ref]['pins'][pin]=wrong
 e=v.validate(tree,bad,mapping,False);assert e,(ref,pin)
 mutations.append(dict(reference=ref,pin=pin,wrong=wrong,rejected=True,errors=e))
for ref,field,wrong in(('R11074','mpn','CRCW06031K00FKEA'),('U11035','mpn','TPS3808G01DBVR'),('U11037','footprint','Package_TO_SOT_SMD:SOT-23-5'),('R11082','resistance_ohm',10000)):
 bad=copy.deepcopy(model);bad['components'][ref][field]=wrong;e=v.validate(tree,bad,mapping,False);assert e
 mutations.append(dict(reference=ref,field=field,rejected=True,errors=e))
for ref in('R11082','C11090'):
 bad=copy.deepcopy(model);del bad['components'][ref];e=v.validate(tree,bad,mapping,False);assert e
 mutations.append(dict(deleted_reference=ref,rejected=True,errors=e))
bad=copy.deepcopy(mapping);del bad['reviewed_motor_feed_reset_delta'];assert v.validate(tree,model,bad,False);mutations.append(dict(missing_primary_ledger_rejected=True))
for ref,pin,wrong in(('U11032','6','/motherboard_power_entry/MOTOR_FEED_CLEAR_N_A'),('U11035','5','/IO_3V3'),('U11036','4','/motherboard_power_entry/MOTOR_FEED_CLEAR_FAST_N_B'),('R11082','2','/motherboard_motors/FIELD_GND')):
 t=copy.deepcopy(tree);node=next(n for net in t.findall('.//nets/net')for n in net.findall('node')if(n.get('ref'),n.get('pin'))==(ref,pin));net=next(net for net in t.findall('.//nets/net')if node in net.findall('node'));net.remove(node);target=next(net for net in t.findall('.//nets/net')if net.get('name')==wrong);target.append(node)
 e=v.validate(t,model,mapping,False);assert e
 mutations.append(dict(native_reference=ref,pin=pin,wrong=wrong,rejected=True,errors=e))
t=copy.deepcopy(tree);t.find('.//libparts/libpart[@lib="CNC_MB_FeedReset"][@part="FEED_POR"]/pins/pin[@num="5"]').set('name','VDD');assert v.validate(t,model,mapping,False);mutations.append(dict(primary_SENSE_VDD_swapped_rejected=True))
baseline=ET.parse(ROOT/'hardware/motherboard/netlist.xml');bn=v.nodes(baseline);delta={k:(n,actual.get(k))for k,n in bn.items()if n!=actual.get(k)}
assert set(delta)=={('U11032','6'),('U11034','6')}
erp=json.loads((P/'erc.json').read_text());vs=[r for sh in erp['sheets']for r in sh['violations']];assert len(vs)==70 and not any(r['severity']=='error'for r in vs)and not erp['ignored_checks']
r=dict(passed=True,adopted=False,actual_source_validation_errors=errors,source_parts=2698,original_327_retained_pin_maps_unchanged=True,exact_two_old_native_pin_changes=[dict(reference=k[0],pin=k[1],old=n[0],new=n[1])for k,n in delta.items()],native_ERC_errors=0,native_ERC_warnings=70,all_unsuppressed=True,meaningful_model_native_and_primary_mutation_controls=mutations,mutation_count=len(mutations),physical_qualification=False,manufacturing_ready=False)
(P/'independent-parent-validation-r02.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,mutations=len(mutations),source=2698)))
