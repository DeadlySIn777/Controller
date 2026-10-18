"""Independent actual current contact/source/geometry/reference audit.

Replays exact sparse native chunks and per-record cuts, retains every raw
kernel/reference/scope failure, and never converts diagnostic scope into
native/manufacturing/current qualification.
"""
from pathlib import Path
import sys,pickle,json,hashlib,time,math,copy,collections
H=Path(__file__).resolve().parent;P=H.parent
for d in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as ROOT
import physical_reference_losses_r3_zero_r208 as RF
import immutable_local_fill_subtraction_r254 as IM
import restore_field_current_mixed_precision_states_r366 as MS
from shapely import from_wkb,set_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def info(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':K.C.sha(s.wkb)}
def records(s):return [[list(p.exterior.coords),[list(r.coords)for r in p.interiors]]for p in RF.parts(s)]

def main():
 st=time.monotonic();out=H/'DIC-policy-coupled-actual-current-independent-r560';assert not out.exists();out.mkdir()
 rp=H/'DIC-retired-cutter-policy-coupled-current-r556/receipt.json';assert sha(rp)=='cc71df8c96290d7a689af22213dc72b248df85f0f139c0833e314ab8b1b9204b';receipt=json.loads(rp.read_bytes());mp=Path(receipt['model_file']);assert sha(mp)=='95d1636e90b8d11530cbc6ba461c60f7e68272e08d1e7cd4b5863bf0a43b46d5';dp=Path(receipt['sparse_discrete_and_current_fill_delta_file']);assert sha(dp)=='7743366078b088048050f4c04c036961d5d0a2ac7b9225ee3f09fc67d5cef8a0';op=pickle.loads(dp.read_bytes());g,h,b,q,after=pickle.loads(mp.read_bytes());MS.restore_bound_field_current_precision_states(b,q)
 base=H/'Q0-only-new-FA-recess-explicit-100nm-margin-r526/model.pkl';assert sha(base)=='97e6f5193c9102102ec86a50c7d142def2d9c498495c8acdbd7202f466f84e14';g0,h0,b0,q0,before=pickle.loads(base.read_bytes());MS.restore_bound_field_current_precision_states(b0,q0);retire=H/'DIC-only-NEW55ab-retired-cutter-exact-source-restoration-r552/exact-retired-NEW55ab-only-cache-restoration-INTERMEDIATE_NOT_ADOPTED.pkl';assert sha(retire)=='fe1e8dfb04083ffb2084f37da0702280a654011cc090f3bd7b4bc9de93e7af85';rg,rh,rb,rq,restored=pickle.loads(retire.read_bytes());assert g==g0==rg and b==b0==rb;assert len(q)==len(q0)==len(rq)
 for a,z,zz in zip(q,q0,rq):
  assert a['uuid']==z['uuid']==zz['uuid']
  for key in a:assert a[key].wkb==z[key].wkb==zz[key].wkb if hasattr(a[key],'wkb')else a[key]==z[key]==zz[key]
 sourcefile=P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(sourcefile)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';source=sourcefile.read_bytes();iv=K.C.inventory(source);identity=K.A.N.SourceNets(source);nt=[];nv=[];deleted=op['native_deleted_chunks'];retired=set(op['retired_current_NEW_track_UUIDs']);removed=set(deleted)|retired
 assert set(deleted)=={'2baae30c-8553-42e8-95d4-0fb985c24070','3eb0b0e1-5064-4fc4-9191-b1b9d35840f4'};assert retired.isdisjoint(iv[3]);identity.assert_chunks(op['exact_new_chunks'])
 for uid,ch in deleted.items():assert iv[3][uid]==ch and source.count(ch)==1 and b'(locked yes)'in ch
 for uid,ch in op['exact_new_chunks'].items():
  p=K.A.G.parse(uid,ch,{})
  if p['kind']=='segment':
   t={'uuid':uid,'net':identity.raw(p['net']),'layer':p['layer'],'w':p['w'],'a':p['a'],'b':p['b']}
   if p['net']=='/motherboard_io_control/DI_SENSOR_G0_FAULT':assert b'(locked yes)'in ch;t['locked']=True
   nt.append(t)
  else:
   assert p['kind']=='via'and(p['d'],p['drill'])==(.5,.2);assert not any(x in ch for x in(b'remove_unused_layers',b'keep_end_layers',b'zone_connection'));nv.append({'uuid':uid,'net':identity.raw(p['net']),'x':p['at'][0],'y':p['at'][1],'d':.5,'drill':.2,'flashed':list(K.LAYERS)})
 assert len(nt)==10 and len(nv)==3;hcheck=copy.deepcopy(rh);hcheck['tracks']=[t for t in hcheck['tracks']if t['uuid']not in removed]+nt;hcheck['vias']=[v for v in hcheck['vias']if v['uuid']not in{v['uuid']for v in nv}]+nv;assert hcheck==h
 ledger=op['actual_fill_cut_ledger'];bycut={(r['zone_UUID'],r['layer']):r for r in ledger};zones=[];scopebad=[];replay=[]
 for zold in restored['zones']:
  z={**zold,'fills':{}}
  for ly,rs in zold['fills'].items():
   authority=bycut.get((z['uuid'],ly))
   if authority is None:z['fills'][ly]=rs;continue
   cuts=[]
   for row in authority['cutters']:
    cp=Path(row['exact_cutter_file']);assert sha(cp)==row['exact_cutter_SHA256'];item=next(x for x in nt+nv if x['uuid']==row['new_UUID']);same=K.L.norm(item['net'])==K.L.norm(z['net']);via='d'in item;local=float(z['clearance_mm']);req=max(local,.15 if h['domains_normalized'][K.L.norm(item['net'])]==h['domains_normalized'][K.L.norm(z['net'])]else .6)+.025;radius=item['drill']/2 if via and same else max(item['drill']/2+.275,item['d']/2+req)if via else item['w']/2+req;mask=K.Z.bounded_disk(item,radius)if via else K.Z.bounded_buffer(LineString([item['a'],item['b']]),radius);assert K.C.sha(mask.wkb)==row['exact_cutter_SHA256']and radius==row['analytic_radius_mm'];cuts.append(mask)
   allcut=unary_union(cuts);outrecords=[];steps=authority['immutable_per_record_proof']['per_original_record_operations'];parts=K.L.poly(rs);assert len(steps)==len(parts)==len(rs)
   for i,(rec,part,step)in enumerate(zip(rs,parts,steps)):
    assert i==step['record']and K.C.sha(part.wkb)==step['before_WKB_sha256'];assert set_precision(part,0).wkb==part.wkb
    if not allcut.intersects(part):assert step['untouched_record_arrays_exact'];outrecords.append(rec);continue
    sh=part.difference(allcut);res=[]
    for r in step['reserves']:
     actual=unary_union(K.L.poly(records(sh)));gain=actual.difference(part);assert K.C.sha(gain.wkb)==r['raw_gain_sha256']==sha(r['raw_gain_file']);reserve=K.Z.bounded_buffer(gain,.0001);assert K.C.sha(reserve.wkb)==r['reserve_sha256']==sha(r['reserve_file']);res.append(reserve);sh=actual.difference(reserve).intersection(part)
    actual=unary_union(K.L.poly(records(sh)));assert actual.difference(part).is_empty;assert K.C.sha(actual.wkb)==step['after_WKB_sha256']==sha(step['actual_final_record_file']);extra=part.difference(actual).difference(allcut);assert K.C.sha(extra.wkb)==step['explicit_additional_negative_sha256'];outside=extra.difference(unary_union(res))
    if not outside.is_empty:
     f=out/(z['uuid']+'-'+ly+'-'+str(i)+'-raw-extra-negative-outside-declared-local-reserves.wkb');f.write_bytes(outside.wkb);scopebad.append({'zone_UUID':z['uuid'],'layer':ly,'record':i,'raw_extra_negative_not_in_any_new_primitive_or_local_gain_reserve':info(outside),'file':str(f.resolve()),'no_area_line_or_threshold_waiver':True})
    if part.difference(actual).is_empty:outrecords.append(rec)
    else:outrecords.extend(records(sh))
   z['fills'][ly]=outrecords;replay.append({'zone_UUID':z['uuid'],'layer':ly,'every_frozen_array_operation_independently_replayed':True})
  zones.append(z)
 rebuilt={**h,'zones':zones};assert rebuilt==after;put(out/'exact-independent-per-record-cut-replay.json',replay);put(out/'raw-additional-negative-outside-scoped-cuts-or-local-reserves.json',scopebad);print('R560_EXACT_SPARSE_AND_FILL_REPLAY',len(replay),'raw scope',len(scopebad),flush=True)
 # Analytic true circle caps against real flashed annuli, native polygons,
 # all old/new physical holes, SMD apertures and current native fills/roles.
 rec,trees=K.F.build({**h,'zones':[]});dom=h['domains_normalized'];gap=lambda a,n:.15 if dom[K.L.norm(a)]==dom[K.L.norm(n)]else .6;newids={x['uuid']for x in nt+nv};checks=[];errors=[];smd=[(p,s)for p in h['pads']if p['smd']for ly,rs in p['layers'].items()if ly in('F.Cu','B.Cu')for s in K.L.poly(rs)];smdtree=STRtree([s for p,s in smd]);holes=[(v['uuid'],K.L.norm(v['net']),Point(v['x'],v['y']),v['drill']/2)for v in h['vias']];holepoints=STRtree([p for u,n,p,r in holes]);reserve,exempt=K.A.reservations();fill={ly:[]for ly in K.LAYERS}
 for z in after['zones']:
  for ly,rs in z['fills'].items():fill[ly].extend({'UUID':z['uuid'],'net':z['net'],'local':float(z['clearance_mm']),'shape':s}for s in K.L.poly(rs))
 ft={ly:STRtree([r['shape']for r in rows])for ly,rows in fill.items()}
 def check(kind,x,other,ly,d,required):
  r={'kind':kind,'new_UUID':x['uuid'],'other_UUID':other,'layer':ly,'true_gap_mm':d,'required_mm':required};checks.append(r)
  if d<required:errors.append(r)
 for x in nt+nv:
  via='d'in x;axis=Point(x['x'],x['y'])if via else LineString([x['a'],x['b']]);rad=x['d']/2 if via else x['w']/2;net=K.L.norm(x['net']);body=axis.buffer(rad,quad_segs=128);layers=K.LAYERS if via else[x['layer']]
  for ly in layers:
   for j in trees[ly].query(body.buffer(.9),predicate='intersects'):
    r=rec[ly][int(j)]
    if r['uuid']==x['uuid']or K.L.norm(r['net'])==net:continue
    s=r.get('source')
    if r['kind']=='track'and not s.get('m'):d=axis.distance(LineString([s['a'],s['b']]))-rad-s['w']/2
    elif r['kind']=='via':d=axis.distance(Point(s['x'],s['y']))-rad-(s['d']if ly in s['flashed']else s['drill'])/2
    else:d=axis.distance(r['shape'])-rad
    check('TRUE_FOREIGN_'+r['kind'],x,r['uuid'],ly,d,gap(net,r['net'])+.025)
   for j in ft[ly].query(body.buffer(.9),predicate='intersects'):
    r=fill[ly][int(j)]
    if K.L.norm(r['net'])==net:continue
    check('CURRENT_ACTUAL_NATIVE_OR_OWNED_FOREIGN_FILL',x,r['UUID'],ly,axis.distance(r['shape'])-rad,max(r['local'],gap(net,r['net']))+.025)
   for z in q:
    if z['layer']==ly and K.L.norm(z['net'])!=net and z['shape'].distance(body)<.9:check('CURRENT_OWNED_PHYSICAL_ROLE',x,z['uuid'],ly,axis.distance(z['shape'])-rad,max(float(z['clearance_mm']),gap(net,z['net']))+.025)
   for r in h['rule_areas']:
    if ly in r['layers']and r.get('no_vias'if via else'no_tracks')and any(body.intersects(s)for s in K.L.poly(r['outline'])):errors.append({'kind':'NATIVE_KEEPOUT','new_UUID':x['uuid'],'rule_UUID':r['uuid'],'layer':ly})
   for r in reserve['keepouts']:
    if ly in r['layers']and net not in exempt.get(r['name'],set())and any(body.distance(s)<.025 for s in K.L.poly(r['outline'])):errors.append({'kind':'FROZEN_RESERVE','new_UUID':x['uuid'],'name':r['name'],'layer':ly})
  for j in holepoints.query(axis.buffer(rad+.7),predicate='intersects'):
   u,n,p,r=holes[int(j)]
   if u==x['uuid']:continue
   if via:check('ORDINARY_VIA_PITCH',x,u,'ALL',axis.distance(p),.815)
   if n!=net:check('EVERY_FOREIGN_DRILL_EDGE',x,u,'ALL',axis.distance(p)-rad-r,.275)
  for p in h['pads']:
   for sh in K.L.poly(p.get('hole')or[]):
    if sh.distance(axis)<rad+.6:check('EVERY_PAD_DRILL_EDGE',x,p['uuid'],'ALL',axis.distance(sh)-rad,.275)
  if via:
   for j in smdtree.query(axis.buffer(.5),predicate='intersects'):
    p,s=smd[int(j)];check('ORDINARY_EVERY_SMD_APERTURE',x,p['uuid'],'ALL',axis.distance(s)-x['drill']/2,.275+.005)
 put(out/'all-true-native-effective-Cu-all6-hole-SMD-cap-checks.json',checks);put(out/'true-native-effective-geometry-errors.json',errors);print('R560_GEOMETRY',len(checks),len(errors),flush=True)
 cf=H/'Q0-R526-full-current-contacts-source-reference-r528/actual-new-groups.pkl';assert sha(cf)=='4bd9642ce43bc8eac41afa9098c0737e82b5861656beaa785f8c8a6feb06cf4e';oldgroups=pickle.loads(cf.read_bytes());nets=set(oldgroups)|set(receipt['changed_net_list_for_full_contact_audit']);ctx=K.hole_context(after);beforectx=K.hole_context(before);newgroups={};contacts=[];bad=[];reuse=[];direct=[];directbad=[]
 for net in sorted(nets):
  oldg=oldgroups.get(net)
  if oldg is None:oldg=K.physical(before,net,beforectx)[1];oldgroups[net]=oldg
  # Reuse only literal matching actual arrays/discrete and no changed hole
  # touching any old physical piece; every affected graph is rebuilt.
  oldz=[z for z in before['zones']if K.L.norm(z['net'])==net];newz=[z for z in after['zones']if K.L.norm(z['net'])==net];sametrack=[t for t in h0['tracks']if K.L.norm(t['net'])==net]==[t for t in h['tracks']if K.L.norm(t['net'])==net];samevia=[v for v in h0['vias']if K.L.norm(v['net'])==net]==[v for v in h['vias']if K.L.norm(v['net'])==net];newholes=[Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)for v in nv];canreuse=oldz==newz and sametrack and samevia and not any(sh.intersects(r['shape'])for sh in newholes for gr in oldg for r in gr)
  if canreuse:newg=oldg;reuse.append(net)
  else:newg=K.physical(after,net,ctx)[1]
  newgroups[net]=newg;rows,loss=K.contact_losses(oldg,newg,removed);contacts.append({'net':net,'reused_only_actual_exact_arrays_discrete_and_no_new_hole_intersection':canreuse,'old_relationships':rows,'losses':loss});bad.extend({'net':net,**r}for r in loss)
  if not canreuse:
   nby=collections.defaultdict(list);fillby=collections.defaultdict(list)
   for gr in newg:
    for r in gr:
     if r['kind']=='fill':fillby[r['layer']].append(r)
     else:nby[r['kind'],r['uuid'],r['layer']].append(r['shape'])
   for gr in oldg:
    for r in gr:
     if r['kind']=='fill'or r['uuid']in removed:continue
     oldtouch=[f for f in gr if f['kind']=='fill'and f['layer']==r['layer']and r['shape'].distance(f['shape'])<=.000002]
     if not oldtouch:continue
     nb=unary_union(nby[r['kind'],r['uuid'],r['layer']]);touch=[f for f in fillby[r['layer']]if nb.distance(f['shape'])<=.000002];row={'net':net,'actual_discrete_layer_key':[r['kind'],r['uuid'],r['layer']],'same_original_zone_direct_contacts':[f['uuid']for f in oldtouch],'after_same_zone_finite_contacts':[f['uuid']for f in touch if f['uuid']in{z['uuid']for z in oldtouch}],'inherited_physical_graph_contact_criterion_mm':.000002,'contact_criterion_unit':'2 nm, not reference/area tolerance'};direct.append(row)
     if not row['after_same_zone_finite_contacts']:directbad.append(row)
  print('R560_CONTACT',net,'reuse',canreuse,'loss',len(loss),flush=True)
 gp=out/'actual-new-all-drilled-groups.pkl';gp.write_bytes(pickle.dumps(newgroups,protocol=5));sources=[];banks={};banks0={}
 for net,ref,pin in ROOT.ROOTS+[('/motherboard_do/DOA_FIELD_3V3','U11017','1')]:
  br=K.root(oldgroups[net],ref,pin);ar=K.root(newgroups[net],ref,pin);lost=sorted(K.keys(br)-K.keys(ar));sources.append({'net':net,'actual_source':ref+'.'+pin,'prior_source_layer_keys_lost':[list(k)for k in lost],'before_named_pad_count':len({r['uuid']for r in br if r['kind']=='pad'and str(r['pin'])}),'after_named_pad_count':len({r['uuid']for r in ar if r['kind']=='pad'and str(r['pin'])})});banks[net]=ar;banks0[net]=br
 refs=[];refbad=[]
 for net,ref,pin in ROOT.ROOTS[:3]:
  rr,proof=RF.audit(before,K.source_refs(banks0[net]),K.source_refs(banks[net]),net,removed=removed);refs.append({'net':net,'strict_literal_old_reference_losses':rr,'proof':proof});refbad.extend({'ground':net,**r}for r in rr)
 put(out/'all-current-old-contact-obligations.json',contacts);put(out/'all-old-direct-layer-fill-contact-obligations.json',direct);put(out/'actual-ten-prior-source-key-obligations.json',sources);put(out/'all-three-strict-literal-old-reference-results.json',refs);print('R560_STRICT_OLD_REF',len(refbad),flush=True)
 hv={v['uuid']:v for v in h['vias']};pairs=[];LG=banks['/LOGIC_GND'];lgkeys=K.keys(LG);lgrefs=K.source_refs(LG);preGP=H/'CORE-R250-vs-actual-R214-independent-r252/actual-drilled-groups.pkl';assert sha(preGP)=='d79902573902eb14a85e42f97bcdae4928a1f9df4cd8c0ef9f35005c03d16f7e';preRoot=K.root(pickle.loads(preGP.read_bytes())['/LOGIC_GND'],'J11001','2');retireGP=H/'DIC-only-NEW55ab-retired-cutter-exact-source-restoration-r552/actual-J1-source-groups-after-only-owned-retirement-replay.pkl';targetRoot=K.root(pickle.loads(retireGP.read_bytes()),'J11001','2');ownparts=[];ownrows=[]
 for su,ru,rad in[('7a5d26bb-831f-5d1a-9459-60db126ea224','99cc6bf8-836e-5f19-983a-c3724b1062a5',.525),('55ab5777-4032-59ab-94d1-d5a4478c7a72','9ef5dbc8-049b-5a46-b319-e13870c3e4c4',.525),('1f815e33-e973-46e2-833e-96fee8d37fcf','0330815c-1d94-5c79-9932-3d491fb10d15',.575)]:
  sig,ret=hv[su],hv[ru];p=Point(ret['x'],ret['y']);ann=p.buffer(ret['d']/2,quad_segs=128).difference(p.buffer(ret['drill']/2,quad_segs=128));aa={pl:ann.buffer(-.025,quad_segs=128).intersection(lgrefs[ly]).area for ly,pl in[('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};rooted=all(('via',ru,ly)in lgkeys for ly in('In1.Cu','In4.Cu'));d=math.dist([sig['x'],sig['y']],[ret['x'],ret['y']]);ok=.90<=d<=1 and rooted and all(a>.005 for a in aa.values());pairs.append({'signal_UUID':su,'return_UUID':ru,'distance_mm':d,'hard_saved_window_mm':[.90,1.0],'actual_rooted_return_on_both_planes':rooted,'actual_annular_interior_after_every_hole_mm2':aa,'policy_and_host_source_pair_pass':ok,'native_actual_all6_flash_fill_SI':'OPEN'})
  if su=='1f815e33-e973-46e2-833e-96fee8d37fcf':continue
  beforeRoot=preRoot if su=='7a5d26bb-831f-5d1a-9459-60db126ea224'else targetRoot;disk=K.Z.bounded_disk(sig,rad);oldref=unary_union([r['shape']for r in beforeRoot if r['kind']=='fill'and r['layer']=='In1.Cu']);support=disk.intersection(oldref);ownparts.append(support if ok else Point());ownrows.append({'signal_UUID':su,'radius_mm':rad,'exact_before_source_clipped_own_credit':info(support),'pre_existing_non_source_void_denied':info(disk.difference(support)),'source_authority':'R250 actual BEFORE source, fixed source port'if beforeRoot is preRoot else'R552 exact retired-cutter primitive replay actual BEFORE J1 source','paired_return_gate_required':ok,'no_generic_disk_or_same_plane_window_waiver':True})
 own=unary_union(ownparts);newbody=[];newbodybad=[]
 for t in nt:
  body=K.A.shape({'kind':'segment',**t});support=lgrefs[t['layer']].union(own)if K.L.norm(t['net'])=='/motherboard_io_control/DIC_IOL1_CS_BUFFER'else lgrefs[t['layer']];missing=body.difference(support);row={'UUID':t['uuid'],'raw_net':t['net'],'layer':t['layer'],'actual_fullbody_source_reference_gap':info(missing),'native_locked':t.get('locked',False),'only_before_source_supported_used_SIG_own_apertures':K.L.norm(t['net'])=='/motherboard_io_control/DIC_IOL1_CS_BUFFER'};newbody.append(row)
  if not missing.is_empty:f=out/(t['uuid']+'-raw-new-body-reference-gap.wkb');f.write_bytes(missing.wkb);row['exact_raw_gap_file']=str(f.resolve());newbodybad.append(row)
 wanted={'c9bab2fa-e6cb-45f7-b879-a934865b0e12','73d7d605-feb4-47ae-b36a-40896fba4ee9'};joined=any(wanted<={r['uuid']for r in gr if r['kind']=='pad'}for gr in newgroups['/motherboard_io_control/DIC_IOL1_CS_BUFFER']);put(out/'all-three-policy-compliant-actual-source-paired-returns.json',pairs);put(out/'exact-before-source-clipped-new-own-apertures.json',ownrows);put(out/'all-ten-new-body-source-reference-results.json',newbody)
 failing=bool(errors or bad or directbad or any(r['prior_source_layer_keys_lost']for r in sources)or refbad or newbodybad or scopebad or not all(r['policy_and_host_source_pair_pass']for r in pairs)or not joined)
 rec={'verdict':'DIC_POLICY_COUPLED_INCREMENTAL_ACTUAL_CONTACT_SOURCE_GEOMETRY_REFERENCE_PASS_FULL_NATIVE_CURRENT_OPEN'if not failing else'DIC_POLICY_COUPLED_INDEPENDENT_RAW_GATES_REPAIR_REQUIRED','model_SHA256':sha(mp),'sparse_operation_SHA256':sha(dp),'original_current_R526_SHA256':sha(base),'exact_retired_source_cache_parent_R552_SHA256':sha(retire),'independent_exact_sparse_chunk_and_actual_cut_replay':True,'full_old_relationship_net_count':len(nets),'actual_old_relationship_losses':bad,'actual_old_direct_same_zone_contact_losses':directbad,'prior_ten_source_layer_key_loss_count':sum(len(r['prior_source_layer_keys_lost'])for r in sources),'true_all6_geometry_errors':errors,'strict_raw_old_reference_losses':refbad,'new_body_reference_errors':newbodybad,'raw_extra_negative_outside_scoped_cuts_or_declared_local_reserves':scopebad,'all_three_hard_policy_pairs':pairs,'actual_r06_DIC_pad_relationship_joined':joined,'all_original_native_CMD_via_definition_masks_flags_and_FP_rules_headers_exact':True,'all_NEW_fault_replacements_preserve_locked_yes':True,'signal_layer_legs':3,'max_saved_layer_legs':3,'all_q49_roles98_WKB_native_profiles_precision_source_exact':True,'raw_R554_global_reference_failures_preserved_not_waived':receipt['constructor_raw_old_reference_expression_failures_preserved'],'original_inherited_CORE93_R36828_R7_ROOT42_current_native_failures_OPEN_OR_FAIL':True,'native_api_fill_old_masks_full_all_baseline_partitions_DRC_CURRENT_SI_minfeature':'OPEN; no native launch/adoption','actual_groups_file':str(gp.resolve()),'actual_groups_SHA256':sha(gp),'native_jobs':0,'adopted':False,'board_source_project_written':False,'input_SHA256':{str(f.resolve()):sha(f)for f in(Path(__file__),rp,mp,dp,base,retire,cf,preGP,retireGP,sourcefile,Path(MS.__file__),Path(RF.__file__))},'output_SHA256':{str(f.resolve()):sha(f)for f in out.iterdir()if f.is_file()},'elapsed_seconds':time.monotonic()-st};put(out/'receipt.json',rec);print('R560_COMPLETE',sha(out/'receipt.json'),rec['verdict'],'geom',len(errors),'contacts',len(bad),'source',rec['prior_ten_source_layer_key_loss_count'],'refs',len(refbad),'newbody',len(newbodybad),'scope',len(scopebad),'joined',joined,flush=True)
if __name__=='__main__':main()
