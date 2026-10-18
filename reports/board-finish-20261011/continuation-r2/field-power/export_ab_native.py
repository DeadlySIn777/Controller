"""One authorized shared-slot AB schematic export; no ERC, board load or save."""
import datetime,json,os,subprocess,sys,time
from pathlib import Path
from inventory import HERE,BASE,NET,PARSER,BOARD,sha
from source_precheck import precheck

sys.path.insert(0,str(BASE/'parity-repair'))
from host_parity import load_parser,source_identity

DIR=HERE/'ab-prereg-split-source'
OUT=DIR/'source-export'
WRAPPER=Path('Z:/pcb-runs/claude-finish/tools/heavy.sh')
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
def write(p,r):p.write_text(json.dumps(r,indent=1)+'\n',encoding='utf-8')
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def canonical_component(c):return {k:c[k] for k in ['value','footprint','sheet_names','sheet_tstamps','tstamps','properties','dnp','exclude_from_board','exclude_from_bom','pins']}
def compare(before,after,receipt):
 defects={}
 for nl in [before,after]:
  for k in ['duplicate_refs','node_conflicts','name_collisions']:
   if nl[k]:raise ValueError('Malformed native netlist '+k)
 oldrefs=set(before['components']);newrefs=set(receipt['new_components'])
 defects['unexpected_component_refs']=sorted(set(after['components'])-(oldrefs|newrefs))
 defects['missing_component_refs']=sorted((oldrefs|newrefs)-set(after['components']))
 defects['changed_existing_components']=[r for r in sorted(oldrefs&set(after['components'])) if canonical_component(before['components'][r])!=canonical_component(after['components'][r])]
 changes={(r['ref'],r['pin']):r for r in receipt['pin_net_changes']}
 nodes=dict(before['node_net']);delta=[]
 for key,row in changes.items():
  if nodes.get(key)!=row['from'].replace('{slash}','/'):raise ValueError('Incorrect frozen old pin mapping '+str(key))
  nodes[key]=row['to'].replace('{slash}','/')
  delta.append({'ref':key[0],'pin':key[1],'from':before['node_net'][key],'to':after['node_net'].get(key)})
 defects['existing_node_assignment_changes_outside_ledger']=[{'ref':k[0],'pin':k[1],'expected':v,'actual':after['node_net'].get(k)} for k,v in nodes.items() if after['node_net'].get(k)!=v]
 defects['missing_existing_nodes']=[list(k) for k in nodes if k not in after['node_net']]
 defects['unexpected_new_nodes']=[list(k) for k in after['node_net'] if k not in nodes and k[0] not in newrefs]
 defects['new_component_node_contract']=[]
 newnodes={}
 for ref,part in receipt['new_components'].items():
  actualpins={p:n for (r,p),n in after['node_net'].items() if r==ref}
  if set(actualpins)!=set(part['pins']):defects['new_component_node_contract'].append({'ref':ref,'pin_set':actualpins})
  for pin,wanted in part['pins'].items():
   got=actualpins.get(pin);newnodes[(ref,pin)]=got
   valid=(got==wanted.replace('{slash}','/')) if wanted is not None else bool(got and got.startswith('unconnected-') and 'U11038-' in got and ('Pad'+pin+')') in got)
   if not valid:defects['new_component_node_contract'].append({'ref':ref,'pin':pin,'expected':wanted,'actual':got})
  if ref in after['components']:
   c=after['components'][ref];clone=before['components'][part['clone']]
   allowed={'tstamps'}
   differences=[k for k in canonical_component(clone) if k not in allowed and c[k]!=clone[k]]
   if differences:defects.setdefault('new_component_clone_attributes',[]).append({'ref':ref,'fields':differences})
 def node_roles(nl):return {(n['ref'],n['pin']):(n['pinfunction'],n['pintype']) for net in nl['nets'].values() for n in net['nodes']}
 oldroles,newroles=node_roles(before),node_roles(after)
 defects['changed_existing_pin_roles']=[list(k) for k,v in oldroles.items() if newroles.get(k)!=v]
 # Derive expected full net membership from old assignments plus the exact ledger.
 expected=dict(nodes);expected.update(newnodes)
 defects['full_node_set_mismatch']=sorted([list(k) for k in set(expected)^set(after['node_net'])])
 defects['full_net_name_set_mismatch']=sorted(set(expected.values())^set(after['nets']))
 return {'verdict':'PASS' if not any(defects.values()) else 'FAIL','defects':defects,'counts':{k:len(v) for k,v in defects.items()},'existing_pin_net_moves':delta,'new_node_assignments':[{'ref':r,'pin':p,'net':n} for (r,p),n in sorted(newnodes.items())],'existing_components':len(oldrefs),'new_components':len(newrefs),'before_nodes':len(before['node_net']),'after_nodes':len(after['node_net']),'before_nets':len(before['nets']),'after_nets':len(after['nets']),'all_existing_component_attributes_preserved':not defects['changed_existing_components'],'old_unconnected_names_preserved':not defects['existing_node_assignment_changes_outside_ledger']}
def main():
 if OUT.exists():raise ValueError('Refuse existing native export output')
 receipt=json.loads((DIR/'receipt-r2.json').read_text(encoding='utf-8'))
 host=precheck(DIR)
 paths=[DIR/name for name in receipt['files']]+[NET,PARSER,BOARD,WRAPPER,CLI,Path(__file__),HERE/'source-pin-graph-r1.json',HERE/'source-semantic-precheck-r1.json',DIR/'receipt-r2.json']
 frozen={str(p.resolve()):sha(p) for p in paths}
 OUT.mkdir();write(OUT/'status.json',{'phase':'QUEUED_ON_EXISTING_SHARED_SLOT','started_utc':stamp(),'host_precheck':host,'input_hashes':frozen})
 command=['C:/Program Files/Git/usr/bin/sh.exe',WRAPPER.as_posix(),'kicad',CLI.as_posix(),'sch','export','netlist','--format','kicadsexpr','--output',(OUT/'fresh.net').resolve().as_posix(),(DIR/'source/motherboard.kicad_sch').resolve().as_posix()]
 write(OUT/'invocation.json',{'command':command,'slot':'existing shared KiCad heavy.sh; no new slot','UTF8':True,'threads':2,'board_load':False,'ERC':False,'DRC':False,'native_source_export_only':True})
 env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH'];env.update(PYTHONUTF8='1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
 start=time.time()
 with (OUT/'export.log').open('w',encoding='utf-8') as log:run=subprocess.run(command,env=env,cwd=DIR/'source',stdout=log,stderr=subprocess.STDOUT)
 result={'verdict':'FAIL','native_exit_code':run.returncode,'elapsed_seconds':round(time.time()-start,3),'board_saved':False,'ERC':False,'DRC':False,'adopted':False,'manufacturing_ready':False}
 try:
  if run.returncode:raise ValueError('Native source export failed')
  if frozen!={p:sha(p) for p in frozen}:raise ValueError('Pinned inputs changed')
  parser=load_parser(PARSER);old=parser['read_netlist'](NET);new=parser['read_netlist'](OUT/'fresh.net')
  semantic=compare(old,new,receipt);identity=source_identity(DIR/'source',new,parser)
  write(OUT/'semantic-delta.json',semantic);write(OUT/'source-identity.json',identity)
  result.update(verdict='PASS' if semantic['verdict']=='PASS' and identity['verdict']=='PASS' else 'FAIL',semantic_delta=semantic,source_identity_verdict=identity['verdict'],fresh_export_sha256=sha(OUT/'fresh.net'),inputs_before=frozen,inputs_after={p:sha(p) for p in frozen},evidence_class='Native KiCad schematic netlist export + full canonical original/new component and node semantic comparison')
 except Exception as exc:result['reason']=str(exc)
 write(OUT/'receipt.json',result);write(OUT/'status.json',{'phase':'COMPLETE','verdict':result['verdict'],'finished_utc':stamp()})
 print(json.dumps(result));return 0 if result['verdict']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
