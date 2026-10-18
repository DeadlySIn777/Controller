"""Exact current pad-UUID census of all saved native r06 relationship losses.

Retain Claude's exact relationship authority; host current topology is
separate from native continuity/ref/reference/SI acceptance.
"""
import sys,json,pickle,time,collections
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import audit_c10036_r24_full_independent_r30 as Q
C=A.C
def main():
 started=time.monotonic();out=HERE/'original14-current-safe-r22-DI6-census-r68.json';assert not out.exists();A.read(__file__);rp=HERE/'di15-safe-root-r22-DI6-bind-r62.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='a8234fa46de66b43eeefcf2bfbdb3d8563bf862a2ce60c46212b17e77ea314be';raw=A.read(r['model_path']);assert C.sha(raw)==r['model_sha256'];cur=pickle.loads(raw);g=cur['after'];graphp=HERE/'conflict-graph.json';graph=json.loads(A.read(graphp));assert graph['native_loss_count']==14;losses=graph['lost_route_rows'];assert len(losses)==14
 nativekeys=[p for p in graph['source_files_sha256'] if 'remaining-r06-losses.json' in p];assert len(nativekeys)==1;nrp=Path(nativekeys[0]);nraw=A.read(nrp);assert C.sha(nraw)==graph['source_files_sha256'][str(nrp)];native=json.loads(nraw);assert native['against_r06']['lost']==14 and native['candidate_sha256']==graph['candidate_sha256'];pads=collections.defaultdict(list)
 for p in g['pads']:pads[(p['ref'],str(p['num']))].append(p)
 rows=[]
 for lostrow in losses:
  net=lostrow['net'];uf,groups=Q.physical(g,net);locations={};actual_labels=[]
  for i,group in enumerate(groups):
   labels=[]
   for q in group:
    if q['kind']=='pad':locations.setdefault(q['uuid'],set()).add(i);labels.append(q['ref']+'.'+str(q['pin']))
   if labels:actual_labels.append(sorted(set(labels)))
  checks=[]
  for rel in lostrow['native_lost_relationships']:
   assert rel in next(p for p in native['rows'] if L.norm(p['net'])==net)['relationships'];labels=rel['r06_pad_relationship'];endpoints=[];splitgroups=[];errors=[]
   for label in labels:
    prefix,index=label.rsplit('#',1);ref,pin=prefix.rsplit('.',1);poss=pads[ref,pin]
    if index!='0' or len(poss)!=1:errors.append({'label':label,'current_matching_physical_pad_UUIDs':[p['uuid'] for p in poss],'reason':'native pad ordinal or physical pad identity ambiguous'});continue
    p=poss[0];ids=sorted(locations.get(p['uuid'],set()));endpoints.append({'native_r06_pad_label':label,'exact_current_UUID':p['uuid'],'raw_net':p['net'],'actual_layers':list(p['layers']),'physical_group_indices':ids});splitgroups.append(set(ids))
    if L.norm(p['net'])!=net:errors.append({'label':label,'reason':'raw source net now differs','current_raw_net':p['net']})
   common=set.intersection(*splitgroups) if splitgroups else set();joined=not errors and len(endpoints)==len(labels) and bool(common);checks.append({'original_r06_native_relationship':labels,'exact_current_pad_endpoints':endpoints,'joined_current_physical_HOST_only':joined,'common_group_indices':sorted(common),'identity_or_net_errors':errors,'historical198b_native_split':rel['current_split_native_groups']})
  rows.append({'net':net,'domain':lostrow['domain'],'controlled_class':lostrow['policy'].get('class') if lostrow.get('policy') else None,'all_original_lost_relationships_joined_current_HOST_only':all(q['joined_current_physical_HOST_only'] for q in checks),'relationships':checks,'current_actual_pad_groups':actual_labels,'original_r06_missing_item_count_in_198b':len(lostrow['missing_original_items']),'saved_original_conflict_edges_diagnostic_only':lostrow['conflict_edges'],'saved_original_blocker_nets_diagnostic_only':sorted(lostrow['blocking_nets'])});print('ORIGINAL14_CURRENT_HOST',net,rows[-1]['all_original_lost_relationships_joined_current_HOST_only'],[[p['native_r06_pad_label'] for p in q['exact_current_pad_endpoints']] for q in checks],flush=True)
 evidence=[]
 for name in('di6-native-owned-ledger-r14/receipt.json','di6-matched-actual-native-independent-r27.json','ao1-reference-coupled-r19.json','ao1-native-com-reference-independent-r4.json','ao1-reference-coupled-r19-independent-native-bound-r19.json','cm-complete-independent-audit-r4-r2.json','xf-coupled-transition-r1.json','xf-continuous-landings-r6.json','xf-component-diagnostic-r1.json'):
  p=HERE/name
  if not p.exists():continue
  e=json.loads(A.read(p));evidence.append({'file':str(p),'sha256':C.sha(A.read(p)),'verdict':e.get('verdict'),'in_current_model':None,'scope':'separate frozen evidence; no automatic integration/native-current-reference acceptance'})
 report={'verdict':'ALL14_ORIGINAL_NATIVE_LOSS_RELATIONSHIPS_ACCOUNTED_CURRENT_HOST_ONLY','model_sha256':r['model_sha256'],'model_receipt_sha256':C.sha(A.read(rp)),'original_relationship_graph_sha256':C.sha(A.read(graphp)),'original14_native_authority_file':str(nrp),'original14_native_authority_sha256':C.sha(nraw),'rows':rows,'relationship_nets_joined_HOST':sum(q['all_original_lost_relationships_joined_current_HOST_only'] for q in rows),'relationship_nets_still_split_HOST':sum(not q['all_original_lost_relationships_joined_current_HOST_only'] for q in rows),'saved_recovery_evidence':evidence,'AO19_exact_delta_not_automatically_composed_into_ROOT_safe_R22':True,'no_native_acceptance_from_this_census':True,'DI6_three_matched_native_remote_reference_losses':'OPEN','native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'joined':report['relationship_nets_joined_HOST'],'split':report['relationship_nets_still_split_HOST']}),flush=True)
if __name__=='__main__':main()
