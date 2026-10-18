"""Stage bounded validator and future builder hooks; no live tool writes."""
from pathlib import Path
import sys,shutil,json,hashlib
ROOT=Path.cwd();STAGE=ROOT/'reports/motherboard-integration-20261001/source27-health-feed-reset-staged-r02'
OLD=ROOT/'reports/motherboard-integration-20261001/source27-health-parent-staged-r01'
T=STAGE/'candidate-tools';shutil.copytree(OLD/'candidate-tools',T)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
baseline=OLD/'final-source27-candidate/motherboard/design.json'
peer=ROOT/'tools/hardware_validate_motor_feed_reset.py';helper=ROOT/'tools/hardware_apply_motor_feed_reset.py'
checker='''"""Exact parent-only receiving CLR successor; no ramp or manufacture claim."""
from pathlib import Path
import json,hashlib
from hardware_validate_motor_feed_reset import validate
ROOT=Path(__file__).resolve().parents[1]
BASELINE='''+repr(baseline.relative_to(ROOT).as_posix())+'''
BASELINE_SHA='''+repr(sha(baseline))+'''
PEER_SHA='''+repr(sha(peer))+'''
HELPER_SHA='''+repr(sha(helper))+'''
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
'''
(T/'hardware_check_source27_feed_reset.py').write_text(checker)
validator=T/'hardware_validate_motherboard.py';text=validator.read_text()
needle="    errors=[];actual=nodes(tree);parts=model['components'];expected={}\n"
replacement=needle+"    from hardware_check_source27_feed_reset import check_feed_reset\n    feed_errors,feed_overrides,feed_extra=check_feed_reset(tree,model,mapping,actual)\n    errors.extend(feed_errors)\n"
assert text.count(needle)==1;text=text.replace(needle,replacement)
needle='        overrides.update(unused)\n';assert text.count(needle)==1
text=text.replace(needle,needle+"        if name=='motherboard_power_entry':overrides.update(feed_overrides)\n")
needle="    extra={key for key in actual if key[0] in parts}-set(expected)\n";assert text.count(needle)==1
text=text.replace(needle,"    for key,wanted in feed_extra.items():\n        expected[key]=wanted\n        if wanted is None:\n            if not actual.get(key,'').startswith('unconnected-'):errors.append('Exact new reset NC endpoint required '+repr(key))\n        elif actual.get(key)!=wanted:errors.append('Exact receiving CLR native endpoint required '+repr(key))\n"+needle)
validator.write_text(text)
overlay='''"""Fresh parent-only successor after the exact health overlay executes once."""
from pathlib import Path
import copy,json,csv,hashlib
from hardware_build_assembly import parse,dump,child,children,value,q
from hardware_apply_motor_feed_reset import apply_feed_reset,footprint_text
LEDGER='''+repr(json.loads((STAGE/'candidate/motherboard/assembly-map.json').read_text())['reviewed_motor_feed_reset_delta'])+'''
def apply_generated_parent_feed_reset(folder,root):
 folder=Path(folder);root=Path(root).resolve();model=json.loads((folder/'design.json').read_text());mapping=json.loads((folder/'assembly-map.json').read_text())
 trees={name:parse((folder/(name+'.kicad_sch')).read_text())for name in('mc_local_power','motherboard_power_entry')}
 trees,new,receipt=apply_feed_reset(trees,model)
 for name,tree in trees.items():(folder/(name+'.kicad_sch')).write_text(dump(tree)+'\\n')
 libdefs=[]
 for d in children(child(trees['motherboard_power_entry'],'lib_symbols'),'symbol'):
  if value(d[1]).startswith('CNC_MB_FeedReset:'):
   d=copy.deepcopy(d);d[1]=q(value(d[1]).split(':')[1]);libdefs.append(d)
 (folder/'CNC_MB_FeedReset.kicad_sym').write_text(dump(['kicad_symbol_lib',['version','20241209'],['generator',q('motherboard_feed_reset')]]+libdefs)+'\\n')
 pretty=folder/'CNC_MB_FeedReset.pretty';pretty.mkdir(exist_ok=False)
 for n in(5,6):(pretty/('TI_DBV'+str(n)+'.kicad_mod')).write_text(footprint_text(n))
 for filename,table,uri,kind in(('fp-lib-table','fp_lib_table','CNC_MB_FeedReset.pretty','KiCad'),('sym-lib-table','sym_lib_table','CNC_MB_FeedReset.kicad_sym','KiCad')):
  tree=parse((folder/filename).read_text());tree.append(parse('(lib(name "CNC_MB_FeedReset")(type "'+kind+'")(uri "${KIPRJMOD}/'+uri+'")(options "")(descr "Exact manufacturer receiving CLR source"))'));(folder/filename).write_text(dump(tree)+'\\n')
 mapping['physical_parts']=2698;mapping['reviewed_motor_feed_reset_delta']=copy.deepcopy(LEDGER)
 deps=(root/'tools/hardware_apply_motor_feed_reset.py',Path(__file__).resolve())
 for dep in deps:
  key=dep.relative_to(root).as_posix()if dep.is_relative_to(root)else str(dep);h=hashlib.sha256(dep.read_bytes()).hexdigest()
  for m in(new['source_sha256'],mapping['input_sha256']):m[key]=h
 (folder/'design.json').write_text(json.dumps(new,indent=2)+'\\n');(folder/'assembly-map.json').write_text(json.dumps(mapping,indent=2)+'\\n')
 with(folder/'bom.csv').open(newline='',encoding='utf8')as f:r=csv.DictReader(f);fields=r.fieldnames;rows=list(r)
 byref={row['Reference']:row for row in rows}
 for ref in('R11074','R11078'):
  part=new['components'][ref];byref[ref].update(MPN=part['mpn'],Value=part['value'])
 for ref in receipt['exact_added_references']:
  part=new['components'][ref];row={key:''for key in fields};row.update(Reference=ref,MPN=part['mpn'],Value=part['value'],Footprint=part['footprint'],DNP='false',Scope='actual_on_motherboard_component_candidate',Status=part['status']);rows.append(row)
 with(folder/'bom.csv').open('w',newline='',encoding='utf8')as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 return receipt
'''
(T/'hardware_apply_parent_feed_reset_overlay.py').write_text(overlay)
builder=T/'hardware_build_motherboard.py';text=builder.read_text();needle='    apply_generated_parent_health(OUT, prior_qualification, ROOT)\n';assert text.count(needle)==1
text=text.replace(needle,needle+'    from hardware_apply_parent_feed_reset_overlay import apply_generated_parent_feed_reset\n    apply_generated_parent_feed_reset(OUT, ROOT)\n');builder.write_text(text)
print(json.dumps(dict(staged_tools=T.as_posix(),live_tools_unchanged=True)))
