"""Independent actual CORE R109 immutable-native-fill scope, all PDN signals included, no native job."""
import sys,json,pickle,copy,time,math,collections
from pathlib import Path
H=Path(__file__).resolve().parent;sys.dont_write_bytecode=True
for p in(H.parent/'field-power',H.parent/'sbc-power',H):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import audit_aux_exact_raw as A
import contact_layout as L
import fast_contacts as F
import restore_SAFE_generated_precision_states_r168 as PS
import guarded_power_projection_r44 as Z
import physical_reference_losses_r3_zero_r208 as RF
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
C=A.C;LAYERS=K.LAYERS;O=H/'CORE-R109-vs-actual-R214-independent-r232'
ROOTS=K.ROOTS+[('/mc_local_power/CORE_5V','R11022','2'),('/motherboard_motors/AUX_5V_B','U11014','6')]
PROFILE=('net','layer','clearance_mm','min_thickness_mm','pad_connect_mode','priority','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm')
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();A.read(__file__)
 for module in(K,A,L,F,PS,Z,RF):A.read(module.__file__)
 base=H.parent/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214';br=A.read(base/'model.pkl');assert C.sha(br)=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e';g,h0,b0,q0,before=pickle.loads(br);oldprecision=PS.restore_bound_generated_precision_states(b0,q0)
 candidate=H.parent/'CORE-narrow-immutable-R214-materialized-source-proposal-r109';r=json.loads(A.read(candidate/'receipt.json'));assert C.sha(A.read(candidate/'receipt.json'))=='ee3ac6173b2ee41e48ad330686c46054994b299c34835b68ba971b0929d9d7c5';raw=A.read(candidate/'model.pkl');assert C.sha(raw)==r['model_sha256']=='fcd5182a7f2d415195508bda0297b9da9eed8cf118b0d78d1d52f942c844a773';ng,h,b,q,after=pickle.loads(raw);newprecision=PS.restore_bound_generated_precision_states(b,q);assert ng==g
 d=pickle.loads(A.read(candidate/'proposed-discrete.pkl'));assert not d['tracks']and len(d['vias'])==2;nv=d['vias'];nids={v['uuid']for v in nv};assert nids=={'8e2d3546-318d-571e-a2af-6f143fbdb5ba','0c3c4802-aa2d-55ad-a84b-6e2acf573601'};assert h['vias']==h0['vias']+nv
 for key in h0:
  if key!='vias':assert h[key]==h0[key],key
 assert all(v['net']=='/CORE_1V2'and(v['d'],v['drill'])==(.5,.2)and set(v['flashed'])==set(LAYERS)for v in nv);source=A.read(H.parent/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb');assert C.sha(source)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';identity=A.N.SourceNets(source);assert identity.raw('/CORE_1V2')=='/CORE_1V2'
 parent=H.parent/'joint-positive-head-signal-reference-mask-proposal-r83';rp=json.loads(A.read(parent/'receipt.json'));assert C.sha(A.read(parent/'receipt.json'))=='ec4a2744f502fc250ecf5f5e0e04c6e043dd7b5b1fe916419231163e4aafaf33';praw=A.read(parent/'model.pkl');assert C.sha(praw)==r['parent_R83_model_sha256']=='e9d67e30fd34bf5e42db2faa23b8c4c32ea11e8be9b8e414b8f8e5419fd2bd2c';pg,ph,pb,pq,pa=pickle.loads(praw);assert pg==g and ph==h0;PS.restore_bound_generated_precision_states(pb,pq);by0={z['uuid']:z for z in q0};byp={z['uuid']:z for z in pq};by={z['uuid']:z for z in q};assert set(by)==set(by0)|{'b0453302-df03-561f-9bc4-0560bc66658a'};core=by['b0453302-df03-561f-9bc4-0560bc66658a'];assert core['net']=='/CORE_1V2'and core['layer']=='In2.Cu';reb= json.loads(A.read(parent/'remove-only-geometry-rebase-ledger.json'));assert C.sha(A.read(parent/'remove-only-geometry-rebase-ledger.json'))==rp['remove_only_delta_ledger_sha256'];roles=json.loads(A.read(candidate/'owned-remove-only-role-cuts.json'));rolemap={(r['UUID'],r['role']):r for r in roles};replay=[];changed=[]
 for row in reb:
  uid,role=row['UUID'],row['role'];assert C.sha(by0[uid][role].wkb)==row['joint_prior_WKB_sha256']and C.sha(byp[uid][role].wkb)==row['joint_result_WKB_sha256'];assert byp[uid][role].difference(by0[uid][role]).is_empty;replay.append({'UUID':uid,'role':role,'exact_R214_before_sha256':row['joint_prior_WKB_sha256'],'exact_R83_after_sha256':row['joint_result_WKB_sha256'],'frozen_mask_sha256':row['exact_frozen_mask_WKB_sha256'],'remove_only':True})
 for uid,z in by.items():
  assert all(k in z for k in('net','layer','clearance_mm'))
  if uid not in by0:continue
  assert all(z.get(k)==by0[uid].get(k)for k in PROFILE);assert {k:v for k,v in z.items()if k not in('shape','zone_outline_shape')}=={k:v for k,v in by0[uid].items()if k not in('shape','zone_outline_shape')}
  for role in('shape','zone_outline_shape'):
   if(uid,role)in rolemap:
    rr=rolemap[uid,role];assert C.sha(byp[uid][role].wkb)==rr['before_WKB_sha256']and C.sha(z[role].wkb)==rr['after_WKB_sha256'];assert z[role].difference(byp[uid][role]).is_empty
   else:assert z[role].wkb==byp[uid][role].wkb
   if z[role].wkb!=by0[uid][role].wkb:changed.append({'UUID':uid,'net':z['net'],'layer':z['layer'],'role':role,'before_WKB_sha256':C.sha(by0[uid][role].wkb),'after_WKB_sha256':C.sha(z[role].wkb),'removed_mm2':by0[uid][role].difference(z[role]).area,'newly_added_mm2':z[role].difference(by0[uid][role]).area})
 for via in nv:assert core['zone_outline_shape'].covers(Point(via['x'],via['y'])),'Own intended CORE In2 outline must include exact barrel centre'
 exact100=H.parent/'CORE-In2-owned-notch-materialized-source-proposal-r100';raw100=A.read(exact100/'model.pkl');assert C.sha(raw100)=='db01ba8f89c614c72b19688ec6479c96e8524259f1968eaa2dd3f2caeef49635';g100,h100,b100,q100,after100=pickle.loads(raw100);assert g100==g and h100==h;assert b100['CORE_R100_only_added_ordinary_native_actual_fill_projection']==b['CORE_R109_only_added_ordinary_native_actual_fill_projection'];assert {k:v for k,v in b100.items()if k!='CORE_R100_only_added_ordinary_native_actual_fill_projection'}=={k:v for k,v in b.items()if k!='CORE_R109_only_added_ordinary_native_actual_fill_projection'};put(O/'exact-provenance-row-key-difference-only.json',{'old_key':'CORE_R100_only_added_ordinary_native_actual_fill_projection','new_key':'CORE_R109_only_added_ordinary_native_actual_fill_projection','exact_same_row_values':b['CORE_R109_only_added_ordinary_native_actual_fill_projection'],'every_other_metadata_value_exact':True});qm100={z['uuid']:z for z in q100};assert set(qm100)==set(by);same_roles=[]
 for uid,z in by.items():
  old=qm100[uid];assert {k:v for k,v in z.items()if k not in('shape','zone_outline_shape')}=={k:v for k,v in old.items()if k not in('shape','zone_outline_shape')}
  for role in('shape','zone_outline_shape'):
   assert z[role].wkb==old[role].wkb,(uid,role)
   same_roles.append({'UUID':uid,'role':role,'R100_R109_identical_WKB_sha256':C.sha(z[role].wkb)})
 assert r['actual_native_fill_immutable_R214_baseline_sha256']==C.sha(br) and r['only_owned_remove_only_masks_are_applied_NO_reclaimed_old_fill_credit'] is True
 put(O/'exact-R100-R109-native-discrete-generated-role-identity.json',same_roles)
 del raw100,g100,h100,b100,q100,after100,qm100
 put(O/'exact-R83-R109-owned-role-authority-replay.json',replay);put(O/'complete-owned-role-delta-vs-R214.json',changed);put(O/'bound-generated-role-precision-old-new.json',{'old':oldprecision,'new':newprecision});del praw,pg,ph,pb,pq,pa,byp
 # Every native design/old Cu item is unchanged; derived fill gains/losses and
 # generated-role changes are explicit BEFORE/AFTER facts, never blanket masks.
 zold={z['uuid']:z for z in before['zones']};znew={z['uuid']:z for z in after['zones']};filldelta=[];affected={'/CORE_1V2'}
 for uid,z in znew.items():
  if uid not in zold:affected.add(L.norm(z['net']));continue
  for layer in set(z['fills'])|set(zold[uid]['fills']):
   a=unary_union(L.poly(zold[uid]['fills'].get(layer,[])));n=unary_union(L.poly(z['fills'].get(layer,[])))
   if a.wkb==n.wkb:continue
   lost=a.difference(n);gain=n.difference(a)
   if lost.is_empty and gain.is_empty:continue
   affected.add(L.norm(z['net']));filldelta.append({'zone_UUID':uid,'raw_net':z['net'],'layer':layer,'before_WKB_sha256':C.sha(a.wkb),'after_WKB_sha256':C.sha(n.wkb),'lost_actual_Cu_mm2':lost.area,'new_actual_projection_credit_mm2':gain.area,'split_before_piece_count':len(RF.parts(a)),'split_after_piece_count':len(RF.parts(n)),'native_final_refill_and_any_reclaimed_reference':'OPEN'})
 put(O/'native-derived-fill-gain-claim-ledger.json',[row for row in filldelta if row['new_actual_projection_credit_mm2']>0]); put(O/'all-derived-native-and-owned-fill-deltas-vs-R214.json',filldelta);print('R232_EXACT_METADATA_ROLES_AND_FILL_DELTAS_BOUND',len(changed),len(filldelta),sorted(affected),flush=True)
 # TRUE circular via/round cap/native pad/hole clearance on all six layers.
 rec,trees=F.build({**h,'zones':[]});dom=h['domains_normalized'];gap=lambda a,b:.15 if dom.get(L.norm(a))==dom.get(L.norm(b))else .6;checks=[];errors=[];smd=[(p['uuid'],p['ref'],p['num'],sh)for p in h['pads']if p['smd']for layer,rs in p['layers'].items()if layer in('F.Cu','B.Cu')for sh in L.poly(rs)];st=STRtree([x[3]for x in smd]);holeitems=[(v['uuid'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],s)for p in h['pads']for s in L.poly(p.get('hole')or[])];aperture=[]
 def check(kind,uid,other,layer,distance,required):
  row={'kind':kind,'owned_UUID':uid,'other_UUID':other,'layer':layer,'true_gap_mm':distance,'required_mm':required};checks.append(row)
  if distance<required:errors.append(row)
 for v in nv:
  p=Point(v['x'],v['y'])
  for layer in LAYERS:
   for j in trees[layer].query(p.buffer(1.5),predicate='intersects'):
    old=rec[layer][int(j)]
    if L.norm(old['net'])=='/CORE_1V2':continue
    if old['kind']=='via':t=old['source'];distance=p.distance(Point(t['x'],t['y']))-(v['d']+t['d'])/2
    elif old['kind']=='track'and not old['source'].get('m'):t=old['source'];distance=p.distance(LineString([t['a'],t['b']]))-v['d']/2-t['w']/2
    else:distance=p.distance(old['shape'])-v['d']/2
    check('all6_true_ordinary_barrel_to_'+old['kind'],v['uuid'],old['uuid'],layer,distance,gap(v['net'],old['net'])+.025)
   for z in after['zones']:
    if L.norm(z['net'])=='/CORE_1V2':continue
    for sh in L.poly(z['fills'].get(layer,[])):
     if sh.distance(p)>1.5:continue
     check('all6_true_ordinary_barrel_to_actual_projected_fill',v['uuid'],z['uuid'],layer,p.distance(sh)-v['d']/2,max(float(z['clearance_mm']),gap(v['net'],z['net']))+.025)
  near=smd[int(st.nearest(p))];sm=p.distance(near[3])-v['drill']/2-.005;dr=min((p.distance(sh)-v['drill']/2-.005,uid)for uid,sh in holeitems if uid!=v['uuid']);pitch=min((p.distance(Point(t['x'],t['y'])),t['uuid'])for t in h['vias']if t['uuid']!=v['uuid']);row={'UUID':v['uuid'],'actual_at_mm':[v['x'],v['y']],'guarded_nearest_SMD_mm':sm,'nearest_SMD':[near[0],near[1],near[2]],'guarded_nearest_every_hole':dr,'nearest_ordinary_pitch':pitch};aperture.append(row)
  if sm<.275 or dr[0]<.275 or pitch[0]<.815:errors.append({'kind':'ordinary_hole_SMD_pitch',**row})
 for j in trees['In2.Cu'].query(core['shape'].buffer(.8),predicate='intersects'):
  old=rec['In2.Cu'][int(j)]
  if L.norm(old['net'])=='/CORE_1V2':continue
  if old['kind']=='via':v=old['source'];distance=core['shape'].distance(Point(v['x'],v['y']))-v['d']/2
  elif old['kind']=='track'and not old['source'].get('m'):t=old['source'];distance=core['shape'].distance(LineString([t['a'],t['b']]))-t['w']/2
  else:distance=core['shape'].distance(old['shape'])
  check('new_CORE_zone_true_cap_pad_barrel_currentpeer',core['uuid'],old['uuid'],'In2.Cu',distance,max(float(core['clearance_mm']),gap(core['net'],old['net']))+.025)
 for z in after['zones']:
  if L.norm(z['net'])=='/CORE_1V2':continue
  for sh in L.poly(z['fills'].get('In2.Cu',[])):
   if sh.distance(core['shape'])>1.5:continue
   check('new_CORE_zone_actual_fill_and_owned_currentpeer',core['uuid'],z['uuid'],'In2.Cu',core['shape'].distance(sh),max(float(core['clearance_mm']),float(z['clearance_mm']),gap(core['net'],z['net']))+.025)
 outline=unary_union(L.poly(h['outline'])).buffer(-.525);res,exempt=A.reservations()
 for item,shape,layers,via in[(v,Z.bounded_disk(v,v['d']/2),LAYERS,True)for v in nv]+[(core,core['zone_outline_shape'],['In2.Cu'],False)]:
  if not outline.covers(shape):errors.append({'kind':'native_board_edge','UUID':item['uuid']})
  for rule in h['rule_areas']:
   if set(layers)&set(rule['layers'])and rule.get('no_vias'if via else'no_zones')and any(shape.distance(s)<.025 for s in L.poly(rule['outline'])):errors.append({'kind':'native_keepout','UUID':item['uuid'],'rule_UUID':rule['uuid']})
  if via:
   for rule in res['keepouts']:
    if L.norm(item['net'])not in exempt.get(rule['name'],set())and set(layers)&set(rule['layers'])and any(shape.distance(s)<.025 for s in L.poly(rule['outline'])):errors.append({'kind':'frozen_via_reservation','UUID':item['uuid'],'rule':rule['name']})
 put(O/'true-all6-caps-pads-holes-currentpeer-checks.json',checks);put(O/'true-all6-caps-pads-holes-currentpeer-errors.json',errors);put(O/'ordinary-aperture.json',aperture);print('R232_TRUE_CURRENT_PEER_GEOMETRY',len(checks),len(errors),flush=True)
 oldctx=K.hole_context(before);newctx=K.hole_context(after);oldgroups={};newgroups={};contacts=[];badcontacts=[];direct=[];directbad=[];nets=sorted({L.norm(z['net'])for z in before['zones']}|{'/motherboard_motors/AUX_5V_B'});assert len(nets)==77;newholes=[Z.bounded_disk(v,v['drill']/2)for v in nv];changedfill={(r['zone_UUID'],r['layer'])for r in filldelta}
 for net in nets:
  _,old=K.physical(before,net,oldctx);oldgroups[net]=old
  if net in affected:_,new=K.physical(after,net,newctx)
  else:
   assert all(not sh.intersects(r['shape'])for xs in old for r in xs for sh in newholes);new=old
  newgroups[net]=new;rows,bad=K.contact_losses(old,new);contacts.append({'net':net,'all_surviving_actual_layer_key_groups':rows,'actual_drilled_split_contact_losses':bad,'exact_unchanged_net_and_new_holes_disjoint_reused':net not in affected});badcontacts.extend({'net':net,**r}for r in bad)
  if net in affected:
   final=collections.defaultdict(list)
   for xs in new:
    for r in xs:
     if r['kind']=='fill':final[r['uuid'],r['layer']].append(r['shape'])
   for layer in LAYERS:
    metal=[r for xs in old for r in xs if r['layer']==layer and r['kind']!='fill'];tree=STRtree([r['shape']for r in metal])
    for fill in(r for xs in old for r in xs if r['kind']=='fill'and r['layer']==layer and(r['uuid'],layer)in changedfill):
     for j in tree.query(fill['shape'].buffer(.000002),predicate='intersects'):
      r=metal[int(j)]
      if r['shape'].distance(fill['shape'])>.000002:continue
      hit=any(s.distance(r['shape'])<=.000002 for s in final[fill['uuid'],layer]);row={'net':net,'zone_UUID':fill['uuid'],'layer':layer,'old_drilled_fill_piece_WKB_sha256':C.sha(fill['shape'].wkb),'old_contact_layer_key':[r['kind'],r['uuid'],layer],'same_zone_direct_contact_retained':hit};direct.append(row)
      if not hit:directbad.append(row)
  put(O/'all77-contact-checkpoint.json',contacts);print('R232_ALL77_ACTUAL_DRILLED',net,len(bad),flush=True)
 sources=[];refs=[]
 for net,ref,pin in ROOTS:
  old=K.root(oldgroups[net],ref,pin);new=K.root(newgroups[net],ref,pin);lost=sorted(K.keys(old)-K.keys(new));sources.append({'net':net,'actual_source':ref+'.'+pin,'actual_old_named_source_pads':len({r['uuid']for r in old if r['kind']=='pad'and r['pin']}),'actual_new_named_source_pads':len({r['uuid']for r in new if r['kind']=='pad'and r['pin']}),'prior_actual_source_layer_keys_lost':[list(k)for k in lost]})
  if ref in('J11001','J11003','J11005'):
   bad,proof=RF.audit(before,K.source_refs(old),K.source_refs(new),net);refs.append({'ground':net,'all_actual_retained_signal_AND_PDN_power_body_reference_losses':bad,'strict_zero_proof':proof,'excluded104_power_nets':[],'excluded130_mandatory_nets':[]})
 lg=K.root(newgroups['/LOGIC_GND'],'J11001','2');actual_in1=K.source_refs(lg)['In2.Cu'];physical_reference=core['shape'].difference(actual_in1);(O/'new_CORE_In2_fullbody_J1_In1_gap.wkb').write_bytes(physical_reference.wkb);bodyref={'CORE_new_zone_UUID':core['uuid'],'full_actual_drilled_zone_body_WKB_sha256':C.sha(core['shape'].wkb),'actual_J1_In1_full_reference_gap_mm2':physical_reference.area,'actual_J1_In1_gap_empty':physical_reference.is_empty,'whole_current_dc_PDN_loop_SI_and_any_own_hole_support':'OPEN; no generic own disk credit used'}
 # Finite actual physical source landing on both used power layers; new
 # native flashes and .8A barrels remain independent qualification gates.
 cr=K.root(newgroups['/CORE_1V2'],'L2001','2');ck=K.keys(cr);landing=[]
 for via in nv:
  ann=Point(via['x'],via['y']).buffer(.25,quad_segs=128).difference(Point(via['x'],via['y']).buffer(.1,quad_segs=128));areas={layer:ann.intersection(unary_union([r['shape']for r in cr if r['kind']=='fill'and r['layer']==layer])).area for layer in('In2.Cu','In3.Cu')};landing.append({'via_UUID':via['uuid'],'actual_CORE_L2001_2_source_layer_keys':[layer for layer in LAYERS if('via',via['uuid'],layer)in ck],'finite_actual_CORE_plane_annular_overlap_mm2':areas,'native_all6_actual_flash_source_0_8A_and_shared_decoupling':'OPEN'})
 (O/'actual-drilled-groups.pkl').write_bytes(pickle.dumps(newgroups,protocol=5));put(O/'all77-actual-layer-contacts.json',contacts);put(O/'all-old-direct-layer-fill-contacts.json',direct);put(O/'all-old-direct-layer-fill-contact-losses.json',directbad);put(O/'nine-actual-source-banks.json',sources);put(O/'three-bank-ZERO-signal-and-all104PDN-reference.json',refs);put(O/'new_CORE-fullbody-source-reference.json',bodyref);put(O/'new_CORE-actual-source-plane-landings.json',landing);ok=not(errors or badcontacts or directbad or any(r['prior_actual_source_layer_keys_lost']for r in sources)or any(r['all_actual_retained_signal_AND_PDN_power_body_reference_losses']for r in refs))and physical_reference.is_empty and all(all(a>0 for a in r['finite_actual_CORE_plane_annular_overlap_mm2'].values())for r in landing)
 result={'verdict':'CORE_R109_VS_R214_INDEPENDENT_TRUE_ALL6_ACTUAL_DRILLED_CONTACT_SOURCE_ZERO_REFERENCE_PASS_CURRENT_NATIVE_OPEN'if ok else'CORE_R109_VS_R214_INDEPENDENT_TRUE_GEOMETRY_CONTACT_SOURCE_OR_ZERO_REFERENCE_FAIL','original_R214_model_sha256':C.sha(br),'R109_constructor_receipt_sha256':C.sha(A.read(candidate/'receipt.json')),'R109_model_sha256':C.sha(raw),'all_original_Cu_FP_pad_source_native_design_zone_and_rule_metadata_exact_vs_R214':True,'all104_PDN_power_nets_and130_mandatory_signals_NOT_EXCLUDED':True,'all77_actual_drilled_contact_losses':badcontacts,'direct_actual_original_layer_fill_contact_losses':directbad,'nine_prior_source_bank_layer_key_loss_count':sum(len(r['prior_actual_source_layer_keys_lost'])for r in sources),'three_bank_strict_ZERO_retained_reference_loss_count':sum(len(r['all_actual_retained_signal_AND_PDN_power_body_reference_losses'])for r in refs),'true_all6_geometry_errors':errors,'new_CORE_fullbody_actual_J1_reference':bodyref,'source_plane_landing':landing,'full_CORE_0_8A_IO3_2A_FAG_4_58442937244A_four_RTN_protected_peer_mesh_cap_loop_fault_transient_current_drop_thermal_SI':'OPEN; field/SBC independent current review remains mandatory','original104_PDN_proposal_and_original_ROOT42_raw_fullboard_reference_FAIL_preserved':True,'no_inherited_production_or_adoption_flags_flipped':True,'DIC_C1022_not_yet_composed_and_final_exact_sparse_rebase':'OPEN','native_actual_all6_source_parity_full_refill_DRC_original198b_dc936_r06_r07':'OPEN','read_files_sha256':A.READS,'output_files_sha256':{str(p):C.sha(p.read_bytes())for p in O.iterdir()if p.is_file()and p.name!='receipt.json'},'native_jobs':0,'board_written':False,'source_or_project_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-started};put(O/'receipt.json',result);print(json.dumps({'receipt_sha256':C.sha((O/'receipt.json').read_bytes()),'verdict':result['verdict'],'geometry_errors':len(errors),'all77_layer_contact_losses':len(badcontacts),'direct_fill_contact_losses':len(directbad),'source_losses':result['nine_prior_source_bank_layer_key_loss_count'],'ZERO_reference_losses':result['three_bank_strict_ZERO_retained_reference_loss_count'],'new_CORE_body_reference_gap_mm2':physical_reference.area}),flush=True)
if __name__=='__main__':main()
