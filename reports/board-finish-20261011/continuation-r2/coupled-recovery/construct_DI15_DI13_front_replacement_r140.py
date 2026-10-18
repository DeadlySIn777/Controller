"""Couple exactly two DI13 tracks to DI15's real new ground handoffs.

No power carve or extra signal layer. Current ground/reference geometry is
source-rooted after all ordinary return holes. DI15 signal operation and
complete independent/native/SI/contact gates remain separate work.
"""
import sys,json,pickle,time,math,copy,collections,uuid
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
for p in(H.parent/'field-power',H.parent/'sbc-power',H):sys.path.insert(0,str(p))
import audit_aux_exact_raw as A
import contact_layout as L
import fast_contacts as F
import complete_geometry_r2 as GE
import guarded_power_projection_r44 as Z
import construct_di6_direct_source_escape_r5 as K
import audit_c10036_r24_full_independent_r30 as Q
import audit_ao1_positive_operation_r4 as SERIAL
import tri_route as T
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
C=A.C;GND='/LOGIC_GND';NET='/motherboard_di/DI15_LOGIC';BLOCK='/motherboard_di/DI13_LOGIC';LAYERS=Q.LAYERS
def newzonelegal(h,cur,win,removed):
 rec,trees=F.build({**h,'zones':[]});domains=h['domains_normalized'];obs=[];ledger=[];owned={z['uuid'] for z in cur['zones']}
 for i in trees['In3.Cu'].query(win.buffer(1),predicate='intersects'):
  q=rec['In3.Cu'][int(i)];n=L.norm(q['net'])
  if n==GND:continue
  gap=max(.25,.15 if domains.get(n)==domains[GND] else .6)+.025;cut=Z.bounded_buffer(q['shape'],gap);obs.append(cut);ledger.append({'kind':q['kind'],'UUID':q['uuid'],'raw_net':q['net'],'mask_WKB_sha256':C.sha(cut.wkb),'guarded_mm':gap})
 for v in h['vias']:
  if L.norm(v['net'])!=GND and Point(v['x'],v['y']).distance(win)<1:obs.append(Z.bounded_disk(v,v['drill']/2+.275))
 for p in h['pads']:
  if L.norm(p['net'])!=GND:obs.extend(Z.bounded_buffer(q,.275) for q in L.poly(p.get('hole') or []) if q.distance(win)<1)
 for z in cur['zones']:
  n=L.norm(z['net'])
  if z['layer']=='In3.Cu' and n!=GND and z['shape'].distance(win)<1:
   gap=max(.25,float(z.get('clearance_mm',.15)),.15 if domains.get(n)==domains[GND] else .6)+.025;obs.append(Z.bounded_buffer(z['shape'],gap));ledger.append({'kind':'positive_power_hard','UUID':z['uuid'],'raw_net':z['net'],'guarded_mm':gap})
 for z in cur['after']['zones']:
  n=L.norm(z['net'])
  if n==GND or z['uuid'] in owned:continue
  for q in L.poly(z['fills'].get('In3.Cu',[])):
   if q.distance(win)>1:continue
   gap=max(.25,float(z.get('clearance_mm',.15)),.15 if domains.get(n)==domains[GND] else .6)+.025;obs.append(Z.bounded_buffer(q,gap));ledger.append({'kind':'original_foreign_fill_hard','UUID':z['uuid'],'raw_net':z['net'],'guarded_mm':gap})
 reserve,exempt=A.reservations()
 for q in h['rule_areas']:
  if 'In3.Cu' in q['layers'] and q.get('no_zones'):obs.extend(Z.bounded_buffer(p,.025) for p in L.poly(q['outline']) if p.distance(win)<1)
 for q in reserve['keepouts']:
  if 'In3.Cu' in q['layers'] and GND not in exempt.get(q['name'],set()):obs.extend(Z.bounded_buffer(p,.025) for p in L.poly(q['outline']) if p.distance(win)<1)
 return win.difference(unary_union(obs)),ledger
def trackfree(h,cur,win,ground,newvias):
 # Exact existing DI13 source/target groups already have F copper. No new
 # DI13 vias or invented endpoint disk; every new F body needs actual In1.
 layer='F.Cu';rec,trees=F.build({**h,'zones':[]});domains=h['domains_normalized'];obs=[]
 for i in trees[layer].query(win.buffer(1),predicate='intersects'):
  q=rec[layer][int(i)];n=L.norm(q['net'])
  if n!=BLOCK:obs.append(Z.bounded_buffer(q['shape'],(.15 if domains.get(n)==domains[BLOCK] else .6)+.030))
 for z in cur['zones']:
  n=L.norm(z['net'])
  if z['layer']==layer and n!=BLOCK and z['shape'].distance(win)<1:obs.append(Z.bounded_buffer(z['shape'],max(float(z.get('clearance_mm',.15)),.15 if domains.get(n)==domains[BLOCK] else .6)+.030))
 for z in cur['after']['zones']:
  n=L.norm(z['net'])
  if n==BLOCK or domains.get(n)==domains[BLOCK]:continue
  obs.extend(Z.bounded_buffer(p,max(float(z.get('clearance_mm',.15)),.6)+.030) for p in L.poly(z['fills'].get(layer,[])) if p.distance(win)<1)
 for v in h['vias']:
  if L.norm(v['net'])!=BLOCK and Point(v['x'],v['y']).distance(win)<1:obs.append(Z.bounded_disk(v,v['drill']/2+.280))
 for p in h['pads']:
  if L.norm(p['net'])!=BLOCK:obs.extend(Z.bounded_buffer(q,.280) for q in L.poly(p.get('hole') or []) if q.distance(win)<1)
 reserve,exempt=A.reservations()
 for q in h['rule_areas']:
  if layer in q['layers'] and q.get('no_tracks'):obs.extend(Z.bounded_buffer(p,.025) for p in L.poly(q['outline']) if p.distance(win)<1)
 for q in reserve['keepouts']:
  if layer in q['layers'] and BLOCK not in exempt.get(q['name'],set()):obs.extend(Z.bounded_buffer(p,.025) for p in L.poly(q['outline']) if p.distance(win)<1)
 reference=cur['source_planes']['In1.Cu'].intersection(win.buffer(1)).difference(unary_union([Z.bounded_disk(v,.1) for v in newvias]));physical=win.difference(unary_union(obs)).buffer(-.105,quad_segs=128)
 return physical.intersection(reference.buffer(-.105,quad_segs=128)),[],physical.covers(Point(123.95,102.15)),physical.covers(Point(130.549999,109.65)),reference.covers(Point(123.95,102.15)),reference.covers(Point(130.549999,109.65))
def projection(cur,h,nt,nv,z):
 fills=[];ledger=[]
 for oldz in cur['after']['zones']:
  nz={**oldz,'fills':{}};net=L.norm(nz['net']);local=float(nz.get('clearance_mm',.15))
  for layer,records in oldz['fills'].items():
   original=unary_union(L.poly(records));cuts=[];details=[]
   for t in nt:
    n=L.norm(t['net'])
    if layer!=t['layer'] or n==net:continue
    rad=t['w']/2+max(local,.15 if h['domains_normalized'].get(n)==h['domains_normalized'].get(net) else .6)+.025;cut=Z.bounded_buffer(LineString([t['a'],t['b']]),rad)
    if cut.intersects(original):cuts.append(cut);details.append({'kind':'new_track','UUID':t['uuid'],'outward_radius_mm':rad})
   for v in nv:
    n=L.norm(v['net']);rad=v['drill']/2 if n==net else max(v['drill']/2+.275,v['d']/2+max(local,.15 if h['domains_normalized'].get(n)==h['domains_normalized'].get(net) else .6)+.025);cut=Z.bounded_disk(v,rad)
    if cut.intersects(original):cuts.append(cut);details.append({'kind':'new_via','UUID':v['uuid'],'outward_radius_mm':rad})
   if layer=='In3.Cu' and net!=GND:
    req=max(local,.25,.15 if h['domains_normalized'].get(net)==h['domains_normalized'][GND] else .6)+.025;cut=Z.bounded_buffer(z['shape'],req)
    if cut.intersects(original):cuts.append(cut);details.append({'kind':'new_reference_zone','UUID':z['uuid'],'outward_mm':req})
   rem=original.difference(unary_union(cuts));nz['fills'][layer]=GE.records(rem)
   if cuts:ledger.append({'zone_UUID':oldz['uuid'],'layer':layer,'net':oldz['net'],'before_WKB_sha256':C.sha(original.wkb),'after_WKB_sha256':C.sha(rem.wkb),'removed_mm2':original.difference(rem).area,'new_physical_piece_count':len(GE.records(rem)),'cuts':details})
  fills.append(nz)
 fills.append({'uuid':z['uuid'],'net':GND,'clearance_mm':.25,'priority':124,'fills':{'In3.Cu':GE.records(z['shape'])}});return {**cur['after'],'tracks':h['tracks'],'vias':h['vias'],'zones':fills},ledger
def main():
 started=time.monotonic();out=H/'DI15-DI13-coupled-reference-constructor-r140.json';assert not out.exists();A.read(__file__);rp=H/'di15-safe-root-r42-DI6-bind-r118.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='bb171905c94a5795d7ae3e3ded2a367c4d02a4b463bf9c82b4c6c962126c69c6';raw=A.read(r['model_path']);assert C.sha(raw)==r['model_sha256'];cur=pickle.loads(raw);h0=cur['h'];source=A.read(cur['binding']['exact_native_discrete_board_file']);identity=A.N.SourceNets(source);inventory=C.inventory(source);policy={L.norm(n):q for n,q in json.loads(A.read(A.S.CONTROLLED))['nets'].items()};assert policy.get(BLOCK) is None and policy.get(NET) is None
 r124p=H/'DI15-entry-return-coupled-track-diagnostic-r124.json';r124=json.loads(A.read(r124p));assert C.sha(A.read(r124p))=='3367d6d3c79f50b164d57ff533033fbdefa2943f386cb422ffb2d2d929dcb57e';assert r124['current_source_model_sha256']==r['model_sha256'];removed={'3bb187ed-1000-4c6e-b4c1-f2c754e5711a','c9ee35c6-c3b0-4e94-a7e8-1ef501789956'};ts={t['uuid']:t for t in h0['tracks']};deletes={u:inventory[3][u] for u in sorted(removed)}
 for u,ch in deletes.items():
  p=A.G.parse(u,ch,{});t=ts[u];assert source.count(ch)==1 and(p['net'],p['a'],p['b'],p['w'],p['layer'])==(BLOCK,t['a'],t['b'],t['w'],t['layer']);assert L.norm(t['net'])==BLOCK and t['layer']=='In3.Cu' and t['w']==.2 and t.get('m') is None
 r94p=H/'di15-zero-power-carve-reference-pieces-r94/receipt.json';r94=json.loads(A.read(r94p));assert C.sha(A.read(r94p))=='271c9f168df53b0fa35150cc40575aceea3ce528b1adce40bca9ec2b3e7c6e3f';rb=A.read(r94['source_only_model_file']);assert C.sha(rb)==r94['source_only_model_sha256'];saved=pickle.loads(rb);chosen=next(z for z in saved['new_zones'] if z['uuid']=='dfa413d0-8afc-5c3a-a113-b1ec1487b3b8');island=chosen['shape'];body=saved['body'];line=LineString(saved['points']);exit_at=[128.695,109.614094];exit_signal=[129.043609356,109.208265565];hbase=copy.deepcopy(h0);hbase['tracks']=[t for t in h0['tracks'] if t['uuid'] not in removed];win=box(110,85,145,125);legal,maskledger=newzonelegal(hbase,cur,win,removed);original_new_island=island;island=set_precision(island.intersection(legal).buffer(-.000010,quad_segs=64),Z.GRID);new_only_outward_trim={'original_R94_WKB_sha256':C.sha(original_new_island.wkb),'outward_trimmed_WKB_sha256':C.sha(island.wkb),'removed_new_only_mm2':original_new_island.difference(island).area,'original_native_or_power_Cu_trimmed':0,'explicit_new_only_inward_margin_mm':.000010,'native_serialization_grid_mm':Z.GRID,'new_only_quantization_added_mm2':island.difference(original_new_island).area,'final_new_shape_area_mm2':island.area,'actual_remaining_outside_legal_mm2':island.difference(legal).area,'strict_legal_covers_new_shape':legal.covers(island)};assert not island.is_empty and legal.covers(island);_,oldgroups=Q.physical(cur['after'],BLOCK);_,prunedgroups=Q.physical({**cur['after'],'tracks':hbase['tracks']},BLOCK);start_components=[xs for xs in prunedgroups if any(q['kind']!='fill' and q['layer']=='In3.Cu' and q['shape'].intersects(Point(123.95,102.15).buffer(.11,quad_segs=128)) for q in xs)];end_components=[xs for xs in prunedgroups if any(q['kind']!='fill' and q['layer']=='In3.Cu' and q['shape'].intersects(Point(130.549999,109.65).buffer(.30,quad_segs=128)) for q in xs)];assert len(start_components)==len(end_components)==1;startmetal=unary_union([q['shape'] for q in start_components[0] if q['kind']!='fill' and q['layer']=='F.Cu']);endmetal=unary_union([q['shape'] for q in end_components[0] if q['kind']!='fill' and q['layer']=='F.Cu']);actual_surviving_contact_component_authority={'source_discrete_keys':[list(k) for k in sorted(Q.discrete_keys(start_components[0]))],'target_discrete_keys':[list(k) for k in sorted(Q.discrete_keys(end_components[0]))],'source_metal_WKB_sha256':C.sha(startmetal.wkb),'target_metal_WKB_sha256':C.sha(endmetal.wkb),'every_remaining_existing_Cu_item_preserved':True};attempts=[];nominee=None
 for nom in r124['best_nominations'][:12]:
  if {q['uuid'] for q in nom['track_deltas_to_construct']}!=removed:continue
  at=nom['return_at_mm'];pts=[at,exit_at];nv=[];chunks={};branches=[];pairs=[]
  for pos,sig in zip(pts,[nom['signal_via_at_mm'],exit_signal]):
   p=Point(pos);attach=nearest_points(island.buffer(-.12,quad_segs=128),p)[0];branch=Z.bounded_buffer(LineString([list(attach.coords)[0],pos]),.15)
   if not legal.covers(branch) or branch.intersection(island).area<.004:break
   u,ch=SERIAL.serial_via(identity,GND,pos);assert u not in inventory[3] and u not in {v['uuid'] for v in h0['vias']};nv.append({'uuid':u,'net':identity.raw(GND),'x':pos[0],'y':pos[1],'d':.5,'drill':.2,'flashed':list(LAYERS)});chunks[u]=ch;branches.append(branch);pairs.append({'signal_handoff_at_mm':sig,'return_at_mm':pos,'distance_mm':math.dist(pos,sig),'new_ground_UUID':u,'branch_points_mm':[list(attach.coords)[0],pos],'branch_width_mm':.30,'branch_WKB_sha256':C.sha(branch.wkb)})
  row={'entry_at_mm':at,'new_branch_count':len(branches)};attempts.append(row)
  if len(branches)!=2:continue
  shape=island.union(unary_union(branches));u=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/DI15/DI13-coupled-reference-r140/'+C.sha(shape.wkb)));z={**chosen,'uuid':u,'shape':shape,'name':'DI15 ordinary In2 paired source reference with DI13 local rework R140'};h=copy.deepcopy(hbase);h['vias']+=nv;free,oldviawitness,startphys,endphys,startref,endref=trackfree(h,cur,win,z,nv);row.update({'exact_retained_DI13_transition_witnesses':oldviawitness,'start_physical_center_covered':startphys,'end_physical_center_covered':endphys,'start_adjacent_source_center_covered':startref,'end_adjacent_source_center_covered':endref});start=[123.95,102.15];end=[130.549999,109.65];sourceattach=startmetal.buffer(-.04,quad_segs=128).intersection(free).intersection(Point(start).buffer(15,quad_segs=128));targetattach=endmetal.buffer(-.04,quad_segs=128).intersection(free).intersection(Point(end).buffer(15,quad_segs=128));parts=[p for p in K.pieces(free) if p.intersects(sourceattach) and p.intersects(targetattach)];row['DI13_continuous_full_body_source_reference_components']=len(parts);row['actual_referenced_surviving_source_attachment_mm2']=sourceattach.area;row['actual_referenced_surviving_target_attachment_mm2']=targetattach.area;row['actual_surviving_contact_component_authority']=actual_surviving_contact_component_authority;row['new_signal_layer']='F.Cu';row['new_DI13_signal_vias']=0;print(json.dumps({'phase':'actual_F_groups','entry':at,'source_attachment_mm2':sourceattach.area,'target_attachment_mm2':targetattach.area,'common_components':len(parts)}),flush=True)
  if parts:
   start_options=K.sites(sourceattach.intersection(parts[0]),start,6);end_options=K.sites(targetattach.intersection(parts[0]),end,6)
   if not start_options or not end_options:parts=[]
   else:start=start_options[0]['at_mm'];end=end_options[0]['at_mm'];row['actual_new_attachment_centres_mm']=[start,end];row['actual_start_existing_metal_overlap_mm2']=Point(start).buffer(.1,quad_segs=128).intersection(startmetal).area;row['actual_end_existing_metal_overlap_mm2']=Point(end).buffer(.1,quad_segs=128).intersection(endmetal).area
  if not parts:continue
  print(json.dumps({'phase':'F_route','chosen_endpoints':[start,end],'component_area_mm2':parts[0].area}),flush=True);route,search=T.route(parts[0],tuple(start),tuple(end));route=[[round(x,6),round(y,6)] for x,y in route];nt=[]
  for a,b in zip(route,route[1:]):
   uid,ch=identity.serial_segment(BLOCK,'F.Cu',a,b,.2);assert uid not in inventory[3] and uid not in set(chunks) and uid not in {q['uuid'] for q in h0['tracks']};chunks[uid]=ch;nt.append({'uuid':uid,'net':identity.raw(BLOCK),'layer':'F.Cu','a':a,'b':b,'w':.2})
  h['tracks']+=nt;identity.assert_chunks(chunks);after,ledger=projection(cur,h,nt,nv,z);_,groups=Q.physical(after,GND);root=next(xs for xs in groups if any(q['kind']=='pad' and(q['ref'],str(q['pin']))==('J11001','2') for q in xs));refs={l:unary_union([q['shape'] for q in root if q['kind']=='fill' and q['layer']==l]) for l in('In1.Cu','In3.Cu','In4.Cu')};lost=sorted(Q.discrete_keys(cur['root'])-Q.discrete_keys(root));gap=body.difference(refs['In1.Cu'].union(refs['In3.Cu']));pairproof=[]
  for q,v in zip(pairs,nv):
   p=Point(q['return_at_mm']);ann=p.buffer(.25,quad_segs=128).difference(p.buffer(.1,quad_segs=128));sig=Point(q['signal_handoff_at_mm']);pairproof.append({**q,'finite_actual_J1_source_annular_contacts_mm2':{l:ann.intersection(ref).area for l,ref in refs.items()},'full_guarded_handoff_signal_disk_source_coverage':{l:ref.covers(sig.buffer(.105,quad_segs=128)) for l,ref in refs.items() if l in('In1.Cu','In3.Cu')}})
  ub,bg=Q.physical(after,BLOCK);mapping=collections.defaultdict(set)
  for i,xs in enumerate(bg):
   for key in Q.discrete_keys(xs):mapping[key].add(i)
  obligations=[];contactloss=[]
  for i,xs in enumerate(oldgroups):
   keys=Q.discrete_keys(xs)-{('track',uid) for uid in removed};indices=set().union(*(mapping.get(k,{'MISSING'}) for k in keys)) if keys else set();q={'old_group':i,'surviving_discrete_keys':[list(k) for k in sorted(keys)],'candidate_groups':sorted(str(x) for x in indices)};obligations.append(q)
   if len(indices)>1 or 'MISSING' in indices:contactloss.append(q)
  final_old_disks=[];final_old_witness=[]
  for witness in oldviawitness:
   retained=[]
   for pair in witness['legitimate_actual_existing_paired_returns']:
    p=Point(pair['at_mm']);diameter,drill=pair['diameter_drill_mm'];ann=p.buffer(diameter/2,quad_segs=128).difference(p.buffer(drill/2,quad_segs=128));areas={l:ann.intersection(refs[l]).area for l in('In1.Cu','In4.Cu')}
    if all(x>.004 for x in areas.values()):retained.append({**pair,'finite_final_J1_source_annular_contacts_mm2':areas})
   final_old_witness.append({**witness,'final_legitimate_paired_returns':retained})
   if retained:final_old_disks.append(Point(witness['at_mm']).buffer(witness['unchanged_own_transition_radius_mm'],quad_segs=128))
  oldscope=unary_union(final_old_disks);trackrefs=[{'uuid':t['uuid'],'actual_adjacent_In1_J1_source_full_body_gap_before_own_scope_mm2':A.shape({'kind':'segment',**t}).difference(refs['In1.Cu']).area,'actual_adjacent_In1_J1_source_full_body_gap_mm2':A.shape({'kind':'segment',**t}).difference(refs['In1.Cu']).area,'legitimate_retained_same_net_own_scopes':final_old_witness} for t in nt];row.update({'DI13_route_points_mm':route,'DI13_route_length_mm':LineString(route).length,'DI13_search':search,'actual_In2_body_source_union_gap_mm2_nomination_only':gap.area,'prior_LG_source_keys_lost':lost,'DI13_surviving_contact_losses':contactloss,'DI13_new_track_reference':trackrefs,'actual_handoff_pair_proof':pairproof})
  if not lost and gap.is_empty and not contactloss and all(q['actual_adjacent_In1_J1_source_full_body_gap_mm2']==0 for q in trackrefs) and all(all(x>.004 for x in q['finite_actual_J1_source_annular_contacts_mm2'].values()) and all(q['full_guarded_handoff_signal_disk_source_coverage'].values()) for q in pairproof):
   model=H/'DI15-DI13-coupled-reference-r140-model.pkl';assert not model.exists();model.write_bytes(pickle.dumps({'current':cur,'h':h,'after':after,'new_zones':[z],'zones':cur['zones']+[z],'new_vias':nv,'new_tracks':nt,'removed_UUIDs':sorted(removed),'exact_deleted_chunks':deletes,'exact_new_chunks':chunks,'refs':refs,'root':root,'groups':groups,'body':body,'points':saved['points'],'handoff_returns':pairproof},protocol=5));nominee={**row,'source_model_file':str(model),'source_model_sha256':C.sha(model.read_bytes()),'exact_deleted_chunks':{u:ch.decode() for u,ch in deletes.items()},'exact_new_chunks':{u:ch.decode() for u,ch in chunks.items()},'new_ground_zone_UUID':z['uuid'],'new_zone_WKB_sha256':C.sha(shape.wkb),'new_native_zone_profile':{k:z[k] for k in('net','layer','clearance_mm','priority','minimum_thickness_mm','island_removal_mode','island_area_min_mm2','thermal_gap_mm','thermal_bridge_width_mm')},'surviving_DI13_contact_obligations':obligations,'projection_ledger':ledger};break
 report={'verdict':'DI15_DI13_EXACT_TWO_TRACK_REWORK_ACTUAL_SOURCE_HANDOFF_POSITIVE_CONSTRUCTION_INDEPENDENT_OPEN' if nominee else'DI15_DI13_EXACT_COUPLED_REFERENCE_CONSTRUCTION_INCOMPLETE','source_parent_sha256':C.sha(source),'source_board_file':cur['binding']['exact_native_discrete_board_file'],'R118_receipt_sha256':C.sha(A.read(rp)),'current_model_sha256':r['model_sha256'],'R124_exact_entry_track_nominations_sha256':C.sha(A.read(r124p)),'R94_exact_central_new_only_piece_sha256':C.sha(original_new_island.wkb),'new_only_outward_margin_correction':new_only_outward_trim,'removed_source_UUIDs':sorted(removed),'held_original_and_positive_power_ground_mask_ledger':maskledger,'attempts':attempts,'selected':nominee,'old_original_or_positive_power_Cu_carves':0,'source_FP_project_rules_native_zone_outlines_changed':0,'max_signal_layer_segments':3,'DI15_complete_F_In2_F_signal_constructor_and_pairing':'OPEN','complete_unchanged_all_net_contacts_r06_r07_outer_reference_native_current_SI':'OPEN','native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':report['verdict'],'selected':nominee,'attempt_count':len(attempts)}),flush=True)
if __name__=='__main__':main()
