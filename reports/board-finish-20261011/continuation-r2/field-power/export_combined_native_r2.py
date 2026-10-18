"""Authorized existing test-slot fresh combined source export and exact contract."""
import copy,json,re,os,subprocess,time,sys
from pathlib import Path
from inventory import HERE,NET,PARSER,BOARD,sha
from export_ab_native import compare,canonical_component,write,stamp,load_parser,source_identity,CLI
from compose_source import sym
from source_precheck import precheck
from verify_source import verify_variant
DIR=HERE/'combined-power-source-r2';OUT=DIR/'source-export'
WRAPPER=Path('Z:/pcb-runs/claude-finish/tools/heavyt.sh')
def host_contract(r):
 p=DIR/'source/motherboard_power_entry.kicad_sch';s=p.read_text(encoding='utf-8')
 for row in r['allowed_existing_component_property_changes']:
  _,(a,b,t,n)=sym(s,row['ref'])
  for prop,v in row['exact_property_changes'].items():
   t,c=re.subn(r'\(property "'+prop+r'" "'+re.escape(v['to'])+r'"','(property "'+prop+'" "'+v['from']+'"',t);assert c==1
  s=s[:a]+t+s[b:]
 a=precheck(DIR,{'motherboard_power_entry.kicad_sch':s});b=verify_variant(DIR);assert a['verdict']==b['verdict']=='PASS';return {'object_gate':a,'independent_pin_graph':b,'allowed_old_properties':r['allowed_existing_component_property_changes']}
def semantic_contract(old,new,r):
 expected_old=copy.deepcopy(old);changes=[]
 for row in r['allowed_existing_component_property_changes']:
  ref=row['ref'];exp=expected_old['components'][ref];act=new['components'][ref];delta={}
  for key,v in row['exact_property_changes'].items():
   if key=='Value':
    assert exp['value']==v['from'] and act['value']==v['to'];exp['value']=v['to']
   elif key=='MPN':
    assert exp['properties']['MPN']==v['from'] and act['properties']['MPN']==v['to'];exp['properties']['MPN']=v['to']
   else:raise ValueError('Unapproved old property name')
   delta[key]=v
  changes.append({'ref':ref,'exact_properties':delta})
 # New C95 is explicitly a geometry/role clone with changed Value and MPN.
 # Verify the actual BOM, then undo only that exception in memory so the base
 # full canonical clone comparison still checks every other attribute.
 adjusted_new=copy.deepcopy(new);exceptions=[]
 for ref,props in r.get('new_component_clone_property_exceptions',{}).items():
  assert ref=='C11095' and set(props)=={'Value','MPN'};part=r['new_components'][ref];c=adjusted_new['components'][ref];clone=old['components'][part['clone']]
  for key,v in props.items():
   if key=='Value':assert c['value']==v['actual']==part['value'] and clone['value']==v['clone'];c['value']=v['clone']
   else:assert c['properties']['MPN']==v['actual']==part['mpn'] and clone['properties']['MPN']==v['clone'];c['properties']['MPN']=v['clone']
  exceptions.append({'ref':ref,'actual_Value_MPN':props,'all_other_clone_attributes_checked':True})
 result=compare(expected_old,adjusted_new,r)
 result['allowed_existing_component_property_changes']=changes;result['new_part_BOM_exceptions']=exceptions
 result.pop('all_existing_component_attributes_preserved',None)
 result['all_existing_attributes_preserved_except_exact_2_Value_MPN_pairs']=not result['defects']['changed_existing_components']
 assert len(changes)==2 and len(result['existing_pin_net_moves'])==14 and result['new_components']==6
 return result
def main():
 if OUT.exists():raise ValueError('Refuse an existing export receipt')
 r=json.loads((DIR/'receipt.json').read_text(encoding='utf-8'));host=host_contract(r)
 paths=[DIR/name for name in r['files']]+[DIR/'receipt.json',DIR/'host-precheck.json',NET,PARSER,BOARD,WRAPPER,CLI,Path(__file__),HERE/'compose_source_r2.py',HERE/'compose_source.py',HERE/'stage_cap_bom_r2.py',HERE/'cap-primary/C1608X7R1H105K080AB-DC-bias.csv',HERE/'new-local-bypass-r2.json'];frozen={str(p.resolve()):sha(p) for p in paths}
 OUT.mkdir();write(OUT/'status.json',{'phase':'QUEUED_EXISTING_TEST_KICAD_SLOT','started_utc':stamp(),'host_contract':host,'input_hashes':frozen})
 cmd=['C:/Program Files/Git/usr/bin/sh.exe',WRAPPER.as_posix(),'kicad',CLI.as_posix(),'sch','export','netlist','--format','kicadsexpr','--output',(OUT/'fresh.net').resolve().as_posix(),(DIR/'source/motherboard.kicad_sch').resolve().as_posix()]
 write(OUT/'invocation.json',{'command':cmd,'existing_slot':'heavyt.sh test-kicad one-slot; parent explicitly authorized','threads':2,'UTF8':True,'native_board_load':False,'ERC':False,'DRC':False})
 env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH'];env.update(PYTHONUTF8='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2');start=time.monotonic()
 with (OUT/'export.log').open('w',encoding='utf-8') as f:run=subprocess.run(cmd,cwd=DIR/'source',env=env,stdout=f,stderr=subprocess.STDOUT)
 result={'verdict':'FAIL','native_exit_code':run.returncode,'elapsed_seconds':time.monotonic()-start,'board_saved':False,'ERC':False,'DRC':False,'adopted':False,'manufacturing_ready':False}
 try:
  assert run.returncode==0;assert frozen=={p:sha(p) for p in frozen}
  parser=load_parser(PARSER);old=parser['read_netlist'](NET);new=parser['read_netlist'](OUT/'fresh.net');semantic=semantic_contract(old,new,r);identity=source_identity(DIR/'source',new,parser)
  assert len(new['components'])==2723 and len(new['node_net'])==9609 and len(new['nets'])==2388
  write(OUT/'semantic-delta.json',semantic);write(OUT/'source-identity.json',identity)
  result.update(verdict='PASS' if semantic['verdict']==identity['verdict']=='PASS' else 'FAIL',counts={'components':len(new['components']),'nodes':len(new['node_net']),'nets':len(new['nets'])},semantic_verdict=semantic['verdict'],semantic_defect_counts=semantic['counts'],source_identity_verdict=identity['verdict'],fresh_export_sha256=sha(OUT/'fresh.net'),source_receipt_sha256=sha(DIR/'receipt.json'),inputs_before=frozen,inputs_after={p:sha(p) for p in frozen},evidence_class='Fresh native KiCad combined source export + exact14 old net moves/6 new parts/2 old Value+MPN pairs/all other attributes and assignments preserved')
 except Exception as exc:result['reason']=str(exc)
 write(OUT/'receipt.json',result);write(OUT/'status.json',{'phase':'COMPLETE','verdict':result['verdict'],'finished_utc':stamp()});print(json.dumps({k:v for k,v in result.items() if k not in ['inputs_before','inputs_after']}));return 0 if result['verdict']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
