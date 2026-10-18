"""Read-only exact Q0 blocker and existing DIC return-window diagnosis."""
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'construct_Q0_four_wall_two_port_route_r350.py'
prefix=base.read_text(encoding='utf-8').split('def req(a,bb):')[0].replace('Q0-four-wall-two-port-route-constructor-r350','Q0-B-port-and-DIC-existing-return-diagnosis-r354')
exec(compile(prefix,str(base),'exec'))
def req(a,bb):return .15 if dom.get(K.L.norm(a))==dom.get(K.L.norm(bb))else .6
ports=[]
for name,net,at in sites:
 p=Point(at);rows=[]
 for r in discrete['B.Cu']:
  if r['uuid']in delete or r['uuid']in padids or K.L.norm(r['net'])==net:continue
  d=p.distance(r['shape'])-.1
  if d<req(net,r['net'])+.030:rows.append({'kind':r['kind'],'uuid':r['uuid'],'net':r['net'],'distance_minus_new_track_halfwidth_mm':d,'required_mm':req(net,r['net'])+.030})
 for z in q:
  if z['layer']!='B.Cu'or K.L.norm(z['net'])in(net,GND):continue
  d=p.distance(z['shape'])-.1
  if d<max(req(net,z['net']),float(z['clearance_mm']))+.030:rows.append({'kind':'owned_plane_hard','uuid':z['uuid'],'net':z['net'],'distance_minus_new_track_halfwidth_mm':d})
 for z in current['zones']:
  if z.get('prospective_not_native')or K.L.norm(z['net'])==net or dom.get(K.L.norm(z['net']))==dom.get(net):continue
  for s in K.L.poly(z['fills'].get('B.Cu',[])):
   d=p.distance(s)-.1
   if d<max(req(net,z['net']),float(z['clearance_mm']))+.030:rows.append({'kind':'actual_native_foreign_domain_B_fill','uuid':z['uuid'],'net':z['net'],'actual_native_local_mm':z['clearance_mm'],'distance_minus_new_track_halfwidth_mm':d})
 for u,n,s in holes:
  if n!=net and p.distance(s)-.1<.280:rows.append({'kind':'old_hole','uuid':u,'distance_minus_track_halfwidth_mm':p.distance(s)-.1})
 for r in h['rule_areas']:
  if 'B.Cu'in r['layers']and r.get('no_tracks')and any(s.buffer(.130,quad_segs=128).covers(p)for s in K.L.poly(r['outline'])):rows.append({'kind':'native_rule_no_tracks','uuid':r['uuid']})
 for r in reserve['keepouts']:
  if 'B.Cu'in r['layers']and net not in exempt.get(r['name'],set())and any(s.buffer(.130,quad_segs=128).covers(p)for s in K.L.poly(r['outline'])):rows.append({'kind':'frozen_operator_reserved','name':r['name']})
 ports.append({'site':name,'at':at,'actual_B_new_track_blockers':rows})
put(out/'Q0-B-port-exact-blockers.json',ports)
# Existing SENSE old prefix can be preserved; nominate actual rooted reference
# attachment positions on the original straight chain, without generic disks.
senseanchors=[]
for x in [229.7,230,230.2,230.5,231,231.5,232,233,234,235,236]:
 p=Point(x,156.3691);body=K.Z.bounded_disk({'x':x,'y':156.3691},.105);gap=body.difference(refs['In4.Cu']);senseanchors.append({'xy':[x,156.3691],'actual_after_source_reference_full_cap_gap_mm2':gap.area,'actual_after_source_reference_full_cap_gap_empty':gap.is_empty})
put(out/'SENSE-retained-old-prefix-source-reference-anchors.json',senseanchors)
lgroot=K.root(groups['/LOGIC_GND'],'J11001','2');lgrefs={l:unary_union([r['shape']for r in lgroot if r['kind']=='fill'and r['layer']==l])for l in('In1.Cu','In4.Cu')}
maskfile=P/'R155-known-reference-native-diagnostic-r157/measure/original-parent-retained-via-actual-flash-masks.json';m=json.loads(maskfile.read_text());assert m['parent_sha256']==sha(source);mask=m['retained_original_via_masks'];newnative=P/'R155-known-reference-native-diagnostic-r157/native-parity.json.actual-vias.json';nm=json.loads(newnative.read_text());assert nm['board_sha256']==m['candidate_sha256'];mask.update({r['expected']['uuid']:r['actual_flashed_layers']for r in nm['rows']})
dic=[]
for sid in ['7a5d26bb-9547-501d-b8ea-5e0a63327e64','55ab5777-04fa-5fa2-8822-10fd7828e947','1f815e33-e973-46e2-833e-96fee8d37fcf']:
 candidates=[v for v in h['vias']if v['uuid'].startswith(sid[:8])];assert len(candidates)==1;signal=candidates[0];rows=[]
 for v in h['vias']:
  if K.L.norm(v['net'])!='/LOGIC_GND':continue
  d=math.dist([signal['x'],signal['y']],[v['x'],v['y']])
  if not .90<=d<=1.:continue
  actual=[r for r in lgroot if r['kind']=='via'and r['uuid']==v['uuid']];layers={l:unary_union([r['shape']for r in actual if r['layer']==l])for l in lgrefs};ann=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=128).difference(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128));witness={l:{'actual_native_flashed':l in mask.get(v['uuid'],[]),'actual_current_drilled_source_via_layer_present':not layers[l].is_empty,'actual_source_fill_annular_contact_mm2':ann.intersection(lgrefs[l]).area,'actual_finite_interior_contact_mm2':ann.buffer(-.025,quad_segs=128).intersection(lgrefs[l]).area}for l in lgrefs};rows.append({'return_UUID':v['uuid'],'return_xy_mm':[v['x'],v['y']],'distance_mm':d,'actual_native_mask':mask.get(v['uuid']),'layer_witnesses':witness,'existing_return_geometry_window_and_actual_host_source_nomination_pass':all(z['actual_native_flashed']and z['actual_current_drilled_source_via_layer_present']and z['actual_finite_interior_contact_mm2']>.002 for z in witness.values())})
 dic.append({'signal_UUID':signal['uuid'],'signal_xy_mm':[signal['x'],signal['y']],'all_existing_same_raw_LOGIC_GND_vias_in_saved_window':rows,'scope':'R155 actual host-drilled source + exact staged native flash masks, final fresh native Fill/source/reference remains OPEN'})
put(out/'DIC-existing-real-return-window-ledger.json',dic)
# Peer read-only nomination wall check uses only their detached new packet.
cmfolder=P/'sbc-power/CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289';cmfile=cmfolder/'only-new-CM-ordinary-discrete-no-deletes.pkl';cm=pickle.loads(cmfile.read_bytes());put(out/'CM49-sparse-packet-structure.json',{'type':str(type(cm)),'keys':list(cm)if isinstance(cm,dict)else None});axis=LineString([(116,202.715),(120,202.715)]);cmrows=[]
items=cm.get('tracks',[])+cm.get('vias',[])if isinstance(cm,dict)else cm
for t in items:
 via='d'in t
 if not via and t['layer']!='B.Cu':continue
 gap=axis.distance(Point(t['x'],t['y'])if via else LineString([t['a'],t['b']]))-.625-(t['d']/2 if via else t['w']/2)
 if gap>=.175:continue
 cmrows.append({'uuid':t['uuid'],'kind':'via'if via else'track','exact_proposed_geometry':t,'full_width_1p25_B_test_axis_mm':[[116,202.715],[120,202.715]],'true_analytic_gap_mm':gap,'same_domain_native_required_mm':.15,'planning_required_mm':.175,'authority':'unadopted exact detached R289 CM49 sparse packet; original native sources untouched'})
put(out/'CM49-own-new-blockers-of-B-power-test-segment.json',cmrows)
result={'verdict':'READ_ONLY_Q0_LOCAL_BLOCKER_DIC_EXISTING_RETURN_AND_CM_PEER_NOMINATION_DIAGNOSIS','model_file':str(model),'model_sha256':sha(model),'R368_actual_groups_file':str(groupsfile),'R368_actual_groups_sha256':sha(groupsfile),'operator_file':str(operator),'operator_sha256':sha(operator),'native_original_mask_file':str(maskfile),'native_original_mask_sha256':sha(maskfile),'native_new_via_file':str(newnative),'native_new_via_sha256':sha(newnative),'Q0_B_ports':ports,'DIC_existing_saved_window_counts':[len(r['all_existing_same_raw_LOGIC_GND_vias_in_saved_window'])for r in dic],'DIC_existing_qualified_nominee_counts':[sum(z['existing_return_geometry_window_and_actual_host_source_nomination_pass']for z in r['all_existing_same_raw_LOGIC_GND_vias_in_saved_window'])for r in dic],'CM49_packet_file':str(cmfile),'CM49_packet_sha256':sha(cmfile),'CM49_local_owned_nominee_blocker_count':len(cmrows),'all_native_final_source_reference_SI_current':'OPEN','board_written':False,'model_changed':False,'native_jobs':0,'elapsed_seconds':time.monotonic()-start};put(out/'receipt.json',result);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'Q0_ports':ports,'DIC_counts':result['DIC_existing_saved_window_counts'],'DIC_source_nominee_counts':result['DIC_existing_qualified_nominee_counts'],'CM49_blockers':len(cmrows)}),flush=True)
