"""Fresh existing-slot export; prove one hierarchy correction changes zero nodes."""
import json,os,subprocess,time
from inventory import HERE,NET,PARSER,BOARD,sha
from export_ab_native import canonical_component,write,stamp,load_parser,source_identity,CLI
from export_combined_native_r2 import semantic_contract
from stage_hierarchy_r3 import OUT as DIR,BASE,locate,inherited_contract,UID
from verify_source import verify_variant,parse,children,atom
OUT=DIR/'source-export';WRAPPER=__import__('pathlib').Path('Z:/pcb-runs/claude-finish/tools/heavyt.sh')
def raw_net_names(path):
 root=parse(path.read_text(encoding='utf-8'));nets=children(root,'nets');assert len(nets)==1
 return {atom(n,'name') for n in children(nets[0],'net')}
def main():
 assert not OUT.exists();r=json.loads((DIR/'receipt.json').read_text(encoding='utf-8'));h=r['hierarchy_correction']
 s=(DIR/'source/motherboard_do.kicad_sch').read_text(encoding='utf-8');a,b,n,c=locate(s,UID);assert c==h['after_chunk'];undo=s[:a]+h['before_chunk']+s[b:]
 host=inherited_contract(DIR,r,undo);v=verify_variant(DIR,r);assert host['verdict']==v['verdict']=='PASS'
 paths=[DIR/name for name in r['files']]+[DIR/'receipt.json',DIR/'host-precheck.json',NET,PARSER,BOARD,WRAPPER,CLI,BASE/'source-export/fresh.net',BASE/'source-export/receipt.json',__import__('pathlib').Path(__file__),HERE/'stage_hierarchy_r3.py',HERE/'export_combined_native_r2.py'];frozen={str(p.resolve()):sha(p) for p in paths}
 OUT.mkdir();write(OUT/'status.json',{'phase':'QUEUED_EXISTING_TEST_KICAD_SLOT','started_utc':stamp(),'input_hashes':frozen})
 cmd=['C:/Program Files/Git/usr/bin/sh.exe',WRAPPER.as_posix(),'kicad',CLI.as_posix(),'sch','export','netlist','--format','kicadsexpr','--output',(OUT/'fresh.net').resolve().as_posix(),(DIR/'source/motherboard.kicad_sch').resolve().as_posix()]
 write(OUT/'invocation.json',{'command':cmd,'existing_slot':'heavyt.sh test-kicad one-slot; root explicitly requested fresh hierarchy export','threads':2,'UTF8':True,'native_board_load':False,'ERC':False,'DRC':False})
 env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH'];env.update(PYTHONUTF8='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2');start=time.monotonic()
 with (OUT/'export.log').open('w',encoding='utf-8') as f:run=subprocess.run(cmd,cwd=DIR/'source',env=env,stdout=f,stderr=subprocess.STDOUT)
 result={'verdict':'FAIL','native_exit_code':run.returncode,'elapsed_seconds':time.monotonic()-start,'board_saved':False,'ERC':False,'DRC':False,'adopted':False,'manufacturing_ready':False}
 try:
  assert run.returncode==0;assert frozen=={p:sha(p) for p in frozen}
  p=load_parser(PARSER);old=p['read_netlist'](NET);prior=p['read_netlist'](BASE/'source-export/fresh.net');new=p['read_netlist'](OUT/'fresh.net')
  zero={'same_component_refs':set(prior['components'])==set(new['components']),'canonical_component_differences':[ref for ref in prior['components'] if canonical_component(prior['components'][ref])!=canonical_component(new['components'][ref])],'same_full_pin_net_assignments':prior['node_net']==new['node_net'],'same_full_net_memberships':prior['nets']==new['nets'],'same_exact_raw_native_net_tokens':raw_net_names(BASE/'source-export/fresh.net')==raw_net_names(OUT/'fresh.net'),'expected_single_host_hierarchy_object':h}
  assert zero['same_component_refs'] and not zero['canonical_component_differences'] and zero['same_full_pin_net_assignments'] and zero['same_full_net_memberships'] and zero['same_exact_raw_native_net_tokens'],zero
  zero['verdict']='PASS';sem=semantic_contract(old,new,r);identity=source_identity(DIR/'source',new,p)
  assert sem['verdict']==identity['verdict']=='PASS';assert len(new['components'])==2723 and len(new['node_net'])==9609 and len(new['nets'])==2388
  write(OUT/'hierarchy-zero-electrical-delta.json',zero);write(OUT/'semantic-delta.json',sem);write(OUT/'source-identity.json',identity)
  result.update(verdict='PASS',counts={'components':2723,'nodes':9609,'nets':2388},semantic_verdict=sem['verdict'],semantic_defect_counts=sem['counts'],source_identity_verdict=identity['verdict'],hierarchy_zero_electrical_delta='PASS',fresh_export_sha256=sha(OUT/'fresh.net'),source_receipt_sha256=sha(DIR/'receipt.json'),inputs_before=frozen,inputs_after={p:sha(p) for p in frozen},evidence_class='Fresh native combined source export; exact14 moves+6 parts+2 Value/MPN pairs; one retained child-port repair with zero additional electrical delta')
 except Exception as exc:result['reason']=str(exc)
 write(OUT/'receipt.json',result);write(OUT/'status.json',{'phase':'COMPLETE','verdict':result['verdict'],'finished_utc':stamp()});print(json.dumps({k:v for k,v in result.items() if k not in ['inputs_before','inputs_after']}));return 0 if result['verdict']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
