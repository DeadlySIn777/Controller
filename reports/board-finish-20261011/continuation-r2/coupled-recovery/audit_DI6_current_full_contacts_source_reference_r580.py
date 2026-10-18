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
 st=time.monotonic();out=H/'DI6-current-independent-all-contacts-source-reference-r580';assert not out.exists();out.mkdir()
 rp=H/'DI6-twelve-NEW-exact-current-normal-antipads-r578/receipt.json';assert sha(rp)=='a4e9c25f6f63bf24077a6deb13f3021f17137da2ae733fe560174ba08f083dfd';receipt=json.loads(rp.read_bytes());mp=Path(receipt['model_file']);assert sha(mp)=='cfe6fcbc3e13360edb56916f18a9a88038e84a8841e2e0f8e5faf93ea3399793';dp=Path(receipt['sparse_operation_file']);assert sha(dp)==receipt['sparse_operation_SHA256'];op=pickle.loads(dp.read_bytes());g,h,b,q,after=pickle.loads(mp.read_bytes());MS.restore_bound_field_current_precision_states(b,q)
 base=H/'DIC-retired-cutter-policy-coupled-current-r556/model.pkl';assert sha(base)=='95d1636e90b8d11530cbc6ba461c60f7e68272e08d1e7cd4b5863bf0a43b46d5';g0,h0,b0,q0,before=pickle.loads(base.read_bytes());MS.restore_bound_field_current_precision_states(b0,q0);assert g==g0 and b==b0 and len(q)==len(q0)
 for a,z in zip(q,q0):
  assert a['uuid']==z['uuid']
  for key in a:assert a[key].wkb==z[key].wkb if hasattr(a[key],'wkb')else a[key]==z[key]
 sourcefile=P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(sourcefile)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';source=sourcefile.read_bytes();iv=K.C.inventory(source);identity=K.A.N.SourceNets(source);nt=[];nv=[];removed=set();identity.assert_chunks(op['exact_new_chunks']);assert not op['original_deletes']and not op['same_own_drill_role_ledger']
 for uid,ch in op['exact_new_chunks'].items():
  assert uid not in iv[3];p=K.A.G.parse(uid,ch,{})
  if p['kind']=='segment':nt.append({'uuid':uid,'net':identity.raw(p['net']),'layer':p['layer'],'w':p['w'],'a':p['a'],'b':p['b']})
  else:
   assert p['kind']=='via'and(p['d'],p['drill'])==(.5,.2);assert not any(x in ch for x in(b'remove_unused_layers',b'keep_end_layers',b'zone_connection'));nv.append({'uuid':uid,'net':identity.raw(p['net']),'x':p['at'][0],'y':p['at'][1],'d':.5,'drill':.2,'flashed':list(K.LAYERS)})
 assert len(nt)==10 and len(nv)==2;hcheck=copy.deepcopy(h0);hcheck['tracks']+=nt;hcheck['vias']+=nv
 assert {t['uuid']:t for t in hcheck['tracks']}=={t['uuid']:t for t in h['tracks']}and {v['uuid']:v for v in hcheck['vias']}=={v['uuid']:v for v in h['vias']}
 for k in h0:
  if k not in('tracks','vias'):assert h[k]==h0[k]
 ledger=op['actual_fill_ledger'];bycut={(r['zone_UUID'],r['layer']):r for r in ledger};zones=[];scopebad=[];replay=[];receipt['changed_net_list_for_full_contact_audit']=sorted({K.L.norm(x['net'])for x in nt+nv})
 for zold in before['zones']:
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
 rebuilt={**h,'zones':zones};assert rebuilt==after;put(out/'exact-independent-per-record-cut-replay.json',replay);put(out/'raw-additional-negative-outside-scoped-cuts-or-local-reserves.json',scopebad);print('R580_EXACT_SPARSE_AND_FILL_REPLAY',len(replay),'raw scope',len(scopebad),flush=True)
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
 put(out/'all-true-native-effective-Cu-all6-hole-SMD-cap-checks.json',checks);put(out/'true-native-effective-geometry-errors.json',errors);print('R580_GEOMETRY',len(checks),len(errors),flush=True)
 cf=H/'DIC-policy-coupled-actual-current-independent-r562/actual-new-all-drilled-groups.pkl';assert sha(cf)=='2c1e577fdad9358b88578a6338f934924e6ced9186ca8dc06a37e652bba9ec8c';oldgroups=pickle.loads(cf.read_bytes());nets=set(oldgroups)|set(receipt['changed_net_list_for_full_contact_audit']);ctx=K.hole_context(after);beforectx=K.hole_context(before);newgroups={};contacts=[];bad=[];reuse=[];direct=[];directbad=[]
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
   newft={ly:STRtree([f['shape']for f in fs])for ly,fs in fillby.items()}
   for gr in oldg:
    oldfb=collections.defaultdict(list)
    for f in gr:
     if f['kind']=='fill':oldfb[f['layer']].append(f)
    oldft={ly:STRtree([f['shape']for f in fs])for ly,fs in oldfb.items()}
    for r in gr:
     if r['kind']=='fill'or r['uuid']in removed or r['layer']not in oldft:continue
     oldtouch=[oldfb[r['layer']][int(i)]for i in oldft[r['layer']].query(r['shape'],predicate='dwithin',distance=.000002)if r['shape'].distance(oldfb[r['layer']][int(i)]['shape'])<=.000002]
     if not oldtouch:continue
     nb=unary_union(nby[r['kind'],r['uuid'],r['layer']]);touch=[fillby[r['layer']][int(i)]for i in newft[r['layer']].query(nb,predicate='dwithin',distance=.000002)if nb.distance(fillby[r['layer']][int(i)]['shape'])<=.000002]if r['layer']in newft else[];row={'net':net,'actual_discrete_layer_key':[r['kind'],r['uuid'],r['layer']],'same_original_zone_direct_contacts':[f['uuid']for f in oldtouch],'after_same_zone_finite_contacts':[f['uuid']for f in touch if f['uuid']in{z['uuid']for z in oldtouch}],'inherited_physical_graph_contact_criterion_mm':.000002,'contact_criterion_unit':'2 nm, not reference/area tolerance'};direct.append(row)
     if not row['after_same_zone_finite_contacts']:directbad.append(row)
  print('R580_CONTACT',net,'reuse',canreuse,'loss',len(loss),flush=True)
 gp=out/'actual-new-all-drilled-groups.pkl';gp.write_bytes(pickle.dumps(newgroups,protocol=5));sources=[];banks={};banks0={}
 for net,ref,pin in ROOT.ROOTS+[('/motherboard_do/DOA_FIELD_3V3','U11017','1')]:
  br=K.root(oldgroups[net],ref,pin);ar=K.root(newgroups[net],ref,pin);lost=sorted(K.keys(br)-K.keys(ar));sources.append({'net':net,'actual_source':ref+'.'+pin,'prior_source_layer_keys_lost':[list(k)for k in lost],'before_named_pad_count':len({r['uuid']for r in br if r['kind']=='pad'and str(r['pin'])}),'after_named_pad_count':len({r['uuid']for r in ar if r['kind']=='pad'and str(r['pin'])})});banks[net]=ar;banks0[net]=br
 refs=[];refbad=[]
 for net,ref,pin in ROOT.ROOTS[:3]:
  oldref=K.source_refs(banks0[net]);newref=K.source_refs(banks[net]);rr,proof=RF.audit(before,oldref,newref,net,removed=removed)
  def all_dimension_parts(sh):
   if sh.is_empty:return[]
   if sh.geom_type in('Polygon','LineString','Point'):return[sh]
   return[p for x in getattr(sh,'geoms',[])for p in all_dimension_parts(x)]
  deltas={ly:oldref[ly].difference(newref[ly])for ly in newref};ps={ly:all_dimension_parts(sh)for ly,sh in deltas.items()};dtrees={ly:STRtree(xs)for ly,xs in ps.items()};complete=[]
  for t in before['tracks']:
   ly=t['layer'];tn=K.L.norm(t['net'])
   if t['uuid']in removed or ly not in dtrees or tn==net or before['domains_normalized'].get(tn)!=before['domains_normalized'][net]or not ps[ly]:continue
   body=K.A.shape({'kind':'segment',**t})if t.get('m')is None else K.L.body(t);idx=dtrees[ly].query(body,predicate='intersects')
   if not len(idx):continue
   raw=body.intersection(unary_union([ps[ly][int(i)]for i in idx]))
   if raw.is_empty:continue
   f=out/(net.rsplit('/',1)[-1]+'-'+t['uuid']+'-'+ly+'-complete-dimension-raw-old-reference-loss.wkb');f.write_bytes(raw.wkb);complete.append({'uuid':t['uuid'],'net':t['net'],'layer':ly,'prior_source_reference_lost_mm2':raw.area,'exact_raw_loss':info(raw),'file':str(f.resolve()),'all_dimension_zero_area_line_and_point_witnesses_NOT_waived':True})
  refs.append({'net':net,'preserved_polygon_delta_helper_raw_rows':rr,'proof':proof,'strict_complete_dimension_old_reference_losses':complete});refbad.extend({'ground':net,**r}for r in complete)
 put(out/'all-current-old-contact-obligations.json',contacts);put(out/'all-old-direct-layer-fill-contact-obligations.json',direct);put(out/'actual-ten-prior-source-key-obligations.json',sources);put(out/'all-three-strict-literal-old-reference-results.json',refs);bankfile=out/'actual-before-and-after-ten-source-bank-primitives.pkl';bankfile.write_bytes(pickle.dumps({'before':banks0,'after':banks},protocol=5));print('R580_STRICT_OLD_REF',len(refbad),flush=True)
 hv={v['uuid']:v for v in h['vias']};LG=banks['/LOGIC_GND'];lgkeys=K.keys(LG);lgrefs=K.source_refs(LG);beforeRoot=banks0['/LOGIC_GND'];oldlgrefs=K.source_refs(beforeRoot);sig=hv['65920d23-af51-5551-a4a2-bc8273927a44'];ret=hv['eea4f681-f21b-5b3a-a1af-7c6ba82e51a1'];d=math.dist([sig['x'],sig['y']],[ret['x'],ret['y']]);ann=K.Z.bounded_disk(ret,.25).difference(K.Z.bounded_disk(ret,.1));contact={ly:ann.buffer(-.025,quad_segs=128).intersection(lgrefs[ly])for ly in('In1.Cu','In4.Cu')};pair=.90<=d<=1.0 and all(('via',ret['uuid'],ly)in lgkeys and not contact[ly].is_empty and contact[ly].area>.005 for ly in contact)
 sourceown={ly:K.Z.bounded_disk(sig,.525).intersection(oldlgrefs[ly])if pair else Point()for ly in('In1.Cu','In4.Cu')};target=hv['0ff4e506-7bc1-48ad-91fd-aeb598e74c7a'];targetret=hv['cb1390c8-49e9-4971-9ee8-740c03e5b93f'];td=math.dist([target['x'],target['y']],[targetret['x'],targetret['y']]);ta=K.Z.bounded_disk(targetret,targetret['d']/2).difference(K.Z.bounded_disk(targetret,targetret['drill']/2));targetcontact=ta.buffer(-.025,quad_segs=128).intersection(lgrefs['In4.Cu']);targetpass=.90<=td<=1.0 and('via',targetret['uuid'],'In4.Cu')in lgkeys and not targetcontact.is_empty and targetcontact.area>.005
 maskfile=P/'R155-known-reference-native-diagnostic-r157/measure/actual-full-refill-via-flashes.json';masks=json.loads(maskfile.read_bytes())['vias'];targetpass=targetpass and 'In3.Cu'in masks[target['uuid']]and'In4.Cu'in masks[targetret['uuid']];targetscope=K.Z.bounded_disk(target,.575)if targetpass else Point();qual=H/'di6-native-existing-target-return-r22.json';assert sha(qual)=='6bb5403004b11d997e867092c4362c78e7033230485d4e9d48409a770fc38ad1';newbody=[];newbodybad=[];rawtarget=[]
 for t in nt:
  ly='In1.Cu'if t['layer']=='F.Cu'else'In4.Cu';body=LineString([t['a'],t['b']]).buffer(t['w']/2,quad_segs=128);raw=body.difference(lgrefs[ly]);gap=raw.difference(sourceown[ly]);targetpart=gap.intersection(targetscope)if ly=='In4.Cu'else Point();final=gap.difference(targetscope)if ly=='In4.Cu'else gap
  row={'UUID':t['uuid'],'layer':t['layer'],'reference_layer':ly,'raw_full_body_source_gap':info(raw),'only_before_source_clipped_NEW_signal_aperture':info(sourceown[ly]),'remaining_outside_NEW_supported_aperture':info(gap),'existing_native_target_only_fixed575_qualified_return_scope_overlap':info(targetpart),'remaining_after_separately_bound_existing_target_scope':info(final),'actual_existing_target_current_void_neighbor_support_full_native':'OPEN; target subset is HOST scoped proposal, never generic radius or native qualification'};newbody.append(row)
  if not final.is_empty:
   f=out/(t['uuid']+'-raw-new-body-gap.wkb');f.write_bytes(final.wkb);newbodybad.append({**row,'file':str(f.resolve())})
  if not targetpart.is_empty:rawtarget.append(row)
 di6groups=newgroups['/motherboard_di/DI6_LOGIC'];wanted={p['uuid']for p in h['pads']if K.L.norm(p['net'])=='/motherboard_di/DI6_LOGIC'};joined=any(wanted<={r['uuid']for r in gr if r['kind']=='pad'}for gr in di6groups);put(out/'all-NEW-DI6-body-current-source-reference-results.json',newbody);put(out/'separate-existing-target575-host-supported-own-scope-proposal.json',{'signal_UUID':target['uuid'],'return_UUID':targetret['uuid'],'distance_mm':td,'actual_CURRENT_HOST_used_In4_source_annulus':info(targetcontact),'actual_R157_signal_masks':masks[target['uuid']],'actual_R157_return_masks':masks[targetret['uuid']],'historical_R22_receipt_SHA256':sha(qual),'fixed_exact_radius_mm':.575,'used_In1_credit':False,'current_host_return_pass':targetpass,'affected_new_bodies':rawtarget,'full_current_native_own_void_neighbor_reference_SI':'OPEN'})
 failing=bool(errors or bad or directbad or refbad or newbodybad or scopebad or not pair or not targetpass or not joined)
 rec={'verdict':'DI6_INCREMENTAL_HOST_CONTACT_SOURCE_GEOMETRY_REFERENCE_PASS_EXISTING_TARGET_NATIVE_SCOPE_OPEN'if not failing else'DI6_CURRENT_INDEPENDENT_REPAIR_REQUIRED','model_SHA256':sha(mp),'sparse_operation_SHA256':sha(dp),'actual_old_relationship_net_count':len(nets),'actual_old_relationship_losses':bad,'actual_old_direct_same_zone_contact_losses':directbad,'prior_ten_source_layer_key_loss_count':sum(len(r['prior_source_layer_keys_lost'])for r in sources),'true_all6_geometry_errors':errors,'strict_raw_old_reference_losses':refbad,'new_body_reference_errors':newbodybad,'raw_extra_negative_outside_scoped_cuts_or_declared_local_reserves':scopebad,'policy_source_pair_pass':pair,'source_pair_distance_mm':d,'source_return_CURRENT_HOST_annuli':{ly:info(sh)for ly,sh in contact.items()},'actual_r06_DI6_original_pad_joined':joined,'no_original_restoration_DELETE_FP_net_rule_mask_flags_changes':True,'all_q49_roles98_source_profiles_precision_WKB_exact':True,'native_existing_target_including_void_neighbor_support_current_native':'OPEN; R22 unchanged radius only host proposal and current original masks observed','all_historical_R14_bad_pair_and_R27_remoteMOTION210nm_failures_preserved':True,'native_API_all_NEW_all6_source_all_old_masks_uncapped_all_baselines_fullDRC_SI_current_minfeature':'OPEN','inherited_CORE93_R36828_R7_ROOT42_native_planner_current_failures_not_changed':True,'actual_groups_file':str(gp.resolve()),'actual_groups_SHA256':sha(gp),'input_SHA256':{str(f.resolve()):sha(f)for f in(Path(__file__),rp,mp,dp,base,cf,sourcefile,maskfile,qual,Path(MS.__file__),Path(RF.__file__))},'output_SHA256':{str(f.resolve()):sha(f)for f in out.iterdir()if f.is_file()},'native_jobs':0,'board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-st};put(out/'receipt.json',rec);print('R580_COMPLETE',sha(out/'receipt.json'),rec['verdict'],'geom',len(errors),'contacts',len(bad),'source',rec['prior_ten_source_layer_key_loss_count'],'refs',len(refbad),'newbody',len(newbodybad),'scope',len(scopebad),'joined',joined,flush=True)
if __name__=='__main__':main()
