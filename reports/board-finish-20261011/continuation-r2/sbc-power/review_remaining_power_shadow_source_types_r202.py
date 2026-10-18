"""Review all84 literal supply-shadow rows with source roles and quiet stems.

No row is exempted. Potential contact envelopes nominate quiet branches to
keep hard; the graph is classification evidence, never native connectivity.
"""
import copy,hashlib,json,pickle,sys
from pathlib import Path
from collections import defaultdict,deque
from shapely import STRtree
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
for d in ('sbc-power','field-power','coupled-recovery'):sys.path.insert(0,str(H/d))
from verify_source import parse,child,children,atom
import contact_layout as C
import guarded_declared_settings_projection_r58 as GP
O=H/'sbc-power/remaining84-power-shadow-source-and-quiet-branch-review-r202'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.wkb).hexdigest()
def main():
 assert not O.exists();O.mkdir()
 prior=H/'sbc-power/CORE1V2-own-rail-shadow-classification-proposal-r191/receipt.json';review=json.loads(prior.read_bytes());target=review['other_power_losses_kept_unresolved'];assert len(target)==84
 mp=H/'sbc-power/IO3-exact-unchanged-primitive-composition-r183/model.pkl';g,h,b,z,c=pickle.loads(mp.read_bytes());assert sha(mp)=='6e96338816a234e62afc309467c804c82d91785cfe0737b7b4a465f2b24b9fa5'
 nf=H/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net';assert sha(nf)=='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2'
 src=parse(nf.read_text());nets={atom(q,'name'):q for q in children(child(src,'nets'),'net')};parts={atom(q,'ref'):q for q in children(child(src,'components'),'comp')};pins=defaultdict(list)
 for raw,n in nets.items():
  for q in children(n,'node'):pins[atom(q,'ref')].append({k:atom(q,k) for k in ('ref','pin','pinfunction','pintype')}|{'net_raw':raw})
 rails=sorted({r['raw_net'] for r in target});source_roles=[];quiet=[];physical_missing=[]
 for raw in rails:
  actual=nets[raw]
  for n in children(actual,'node'):
   row={k:atom(n,k) for k in ('ref','pin','pinfunction','pintype')}|{'rail_raw':raw};ref=row['ref'];pf=row['pinfunction'].upper();others=[r for r in pins[ref] if r['pin']!=row['pin']];othernets=[r['net_raw'] for r in others];role='POWER_RAIL_ENDPOINT_UNRESOLVED_REQUIRES_PART_REVIEW'
   if ref.startswith('C') and any(C.norm(r['net_raw'])=='/LOGIC_GND' for r in others):role='PDN_RAIL_TO_LOGIC_GND_DECOUPLING_CAPACITOR'
   elif ref.startswith('L') and any('SW' in r['net_raw'] for r in others):role='BUCK_INDUCTOR_OUTPUT_DISTRIBUTION_SOURCE'
   elif row['pintype']=='power_in':role='IC_POWER_SUPPLY_PIN'
   elif 'VOS' in pf or pf.startswith(('FB_','IN+','IN-','REF_')):role='QUIET_DIRECT_VOLTAGE_OR_CURRENT_SENSE_PIN'
   elif ref.startswith('R') and any('SENSE' in x for x in othernets):role='QUIET_VOLTAGE_DIVIDER_SUPPLY_TAP'
   elif ref.startswith('R') and any('ISNS' in x for x in othernets):role='METERED_SOURCE_SHUNT_TERMINAL_KEEP_KELVIN_REVIEW'
   elif ref.startswith('R'):role='RESISTOR_POWER_RAIL_TAP_REQUIRES_OTHER_NODE_NOISE_REVIEW'
   elif ref.startswith('J'):role='CONNECTOR_POWER_DISTRIBUTION_ENDPOINT_CONTACT_AND_RETURN_REVIEW'
   comp=parts[ref];row.update({'role':role,'component_value':atom(comp,'value'),'component_footprint':atom(comp,'footprint'),'component_fields':{atom(f,'name'):f[2] if len(f)>2 else '' for f in children(child(comp,'fields') or [],'field')},'other_source_pin_rows':others})
   ps=[p for p in h['pads'] if(p['ref'],p['num'])==(ref,row['pin'])]
   assert all(p['net']==raw for p in ps),('physical_source_raw_net_mismatch',ref,row['pin'],raw)
   row['physical_pad_rows']=[{'UUID':p['uuid'],'x':p['x'],'y':p['y'],'native_layer_names':sorted(p['layers'])} for p in ps]
   if not ps:physical_missing.append({'ref':ref,'pin':row['pin'],'raw_net':raw})
   source_roles.append(row)
   if role.startswith(('QUIET_','METERED_','RESISTOR_')):quiet.append(row)
 # Potential contact graph of exact current discrete objects only. Enclosing
 # circles/caps prevent hidden tangency from losing a quiet nomination; no
 # source credit or exemption may follow from this classification graph.
 records=defaultdict(list);meta={}
 for t in h['tracks']:
  if t['net'] not in rails:continue
  key=('track',t['uuid']);meta[key]={'kind':'track','source':t}
  if t.get('m') is not None:sh=GP.bounded_buffer(C.body(t),.000002)
  else:sh=GP.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2)
  records[t['net'],t['layer']].append((key,sh))
 for v in h['vias']:
  if v['net'] not in rails:continue
  key=('via',v['uuid']);meta[key]={'kind':'via','source':v};sh=GP.bounded_disk(v,v['d']/2)
  for layer in v['flashed']:records[v['net'],layer].append((key,sh))
 for p in h['pads']:
  if p['net'] not in rails:continue
  key=('pad',p['uuid']);meta[key]={'kind':'pad','source':p}
  for layer,rs in p['layers'].items():
   for sh in C.poly(rs):records[p['net'],layer].append((key,GP.bounded_buffer(sh,.000002)))
 graph=defaultdict(set)
 for (raw,layer),rs in records.items():
  tree=STRtree([s for k,s in rs])
  for i,(k,s) in enumerate(rs):
   for j in tree.query(s,predicate='intersects'):
    l=rs[int(j)][0]
    if l!=k:graph[k].add(l);graph[l].add(k)
 quiet_traces=defaultdict(list);branches=[]
 for role in quiet:
  seed=[('pad',p['UUID']) for p in role['physical_pad_rows']];todo=deque((k,None) for k in seed);seen=set();walk=[];stops=[]
  while todo:
   k,parent=todo.popleft()
   if k in seen:continue
   seen.add(k);neighbors=graph[k]-({parent} if parent else set())
   if k not in seed and (len(graph[k])>=3 or(k[0]=='pad' and k not in seed)):
    stops.append({'node_kind':k[0],'UUID':k[1],'potential_neighbor_count':len(graph[k]),'stop_at_possible_distribution_junction':True});continue
   if k[0]=='track':walk.append(k[1]);quiet_traces[k[1]].append({'ref':role['ref'],'pin':role['pin'],'role':role['role']})
   for other in neighbors:todo.append((other,k))
  branches.append({'quiet_ref':role['ref'],'quiet_pin':role['pin'],'rail_raw':role['rail_raw'],'role':role['role'],'physical_pad_UUIDs':[x[1] for x in seed],'potential_exclusive_stem_track_UUIDs':sorted(walk),'stop_rows':stops,'method_not_native_connectivity_or_exemption':True})
 tm={t['uuid']:t for t in h['tracks']};rows=[];mask=[]
 for r in target:
  t=tm[r['exact_track_UUID']];assert t['net']==r['raw_net'] and t['layer']==r['layer']
  risks=quiet_traces.get(t['uuid'],[]);rows.append({**r,'actual_current_native_track':t,'exact_native_track_json_sha256':hashlib.sha256(json.dumps(t,sort_keys=True).encode()).hexdigest(),'quiet_stem_nominations':risks,'classification':'QUIET_LOCAL_TAP_REVIEW_KEEP_REFERENCE_HARD' if risks else 'LITERAL_SOURCE_BACKED_DC_SUPPLY_DISTRIBUTION_CANDIDATE_REQUIRES_PDN_QUALIFICATION','row_exempted':False})
  if risks and t['layer'] in ('F.Cu','B.Cu','In3.Cu'):
   shape=GP.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2) if t.get('m') is None else GP.bounded_buffer(C.body(t),.000002)
   mask.append({'track_UUID':t['uuid'],'reference_layer':'In1.Cu' if t['layer']=='F.Cu' else 'In4.Cu','shape':shape,'potential_quiet_stem_only':True})
 mf=O/'potential-quiet-stem-reference-reservations.pkl';mf.write_bytes(pickle.dumps(mask,protocol=5))
 receipt={'verdict':'EXACT84_POWER_DISTRIBUTION_VS_POTENTIAL_QUIET_SOURCE_BRANCH_REVIEW_PROPOSAL_ONLY','parent_review_file':str(prior.resolve()),'parent_review_sha256':sha(prior),'source_sha256':sha(nf),'physical_discrete_model_sha256':sha(mp),'literal84_rows':rows,'all_actual_source_power_endpoint_roles':source_roles,'potential_quiet_branch_rows':branches,'source_roles_missing_physical_pad_rows':physical_missing,'potential_quiet_stem_reservations_file':str(mf.resolve()),'potential_quiet_stem_reservations_sha256':sha(mf),'candidate_count':sum(not r['quiet_stem_nominations'] for r in rows),'keep_hard_quiet_nomination_count':sum(bool(r['quiet_stem_nominations']) for r in rows),'signal130_preservation_still_mandatory':True,'same_rail20_and_other84_raw_legacy_losses_retained':True,'mandatory_PDN_obligations':review['mandatory_replacement_PDN_obligations']+['Every literal CORE5 distribution candidate retains full7.882034293398381A rail budget; classify only its actual branch allocation, never reduce whole fitted supply/load or call every branch7.882A.','Retain all input and output decoupling power-ground loop geometry, regulator quietVOS/FB and supervisor divider tap quality, current-sense Kelvin pickup and all analog supply filtering/ground strategy; topology classification alone qualifies none.'],'no_blanket_net_or_width_exemption':True,'no_original_checker_modification':True,'no_source_load_contact_rule_or_geometry_change':True,'no_host_failure_or_readiness_flag_flipped':True,'physical_PDN_qualified':False,'board_written':False,'native_jobs':0,'script_sha256':sha(__file__)}
 (O/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n')
 print('R202_COMPLETE',sha(O/'receipt.json'),'literal84',len(rows),'potential_quiet',receipt['keep_hard_quiet_nomination_count'],'candidates',receipt['candidate_count'],'missingphysical',len(physical_missing),flush=True)
if __name__=='__main__':main()
