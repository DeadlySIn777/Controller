"""Independent current combined repair audit. No native or current acceptance."""
import hashlib,json,pickle,sys,math,collections,time,textwrap
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import guarded_power_projection_r44 as Z
A,L,F,GE,Q,RF,OS,C=(getattr(K,n)for n in('A','L','F','GE','Q','RF','OS','C'))
LAYERS=K.LAYERS;STRtree=K.STRtree
OUT=H/'U10003-HOST-joint-independent-actual-source-contacts-oldrefs-r255'
BP=H/'coupled-recovery/DIC-C1022-exact-R250-original-guard-construction-r262/model.pkl'
MP=H/'U10003-HOST-field-joint-current-exact-raw-precision-bound-r253/model.pkl'
OP=H/'U10003-HOST-shared-field-fresh-R262-sparse-current-diagnostic-r252/full-sparse-operation.pkl'
FG='/motherboard_motors/FIELD_GND';LG='/LOGIC_GND';FB='/motherboard_do/FIELD_B_0V'
FLT='/motherboard_do/DOA_FLT_N_FIELD';CLK='/motherboard_do/DOA_SCLK_FIELD';HOST='/motherboard_do/DOA_SDI_HOST'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
def ds(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def main():
 assert not OUT.exists();OUT.mkdir();started=time.monotonic()
 assert sha(BP)=='64a1f6e1597c9d757b187c3b6db85d79685ee376399bdd4738f915b87b1a0144'
 assert sha(MP)=='765ce30b24ed3109b7c938f964775690a99f08504c464313bcf712b078421440'
 g,h0,b0,q0,before=pickle.loads(BP.read_bytes());ng,h,b,q,after=pickle.loads(MP.read_bytes());assert g==ng
 d=pickle.loads(OP.read_bytes());removed={t['uuid']for t in d['removed_original_tracks']};nt=d['new_tracks'];nv=d['new_vias'];assert (len(removed),len(nt),len(nv))==(6,13,4)
 oldt={t['uuid']:t for t in h0['tracks']};oldtids=set(oldt);newt={t['uuid']:t for t in h['tracks']};oldv={v['uuid']:v for v in h0['vias']};newv={v['uuid']:v for v in h['vias']}
 assert set(newt)==oldtids-removed|{t['uuid']for t in nt};assert all(newt[u]==t for u,t in oldt.items()if u not in removed)
 assert set(newv)==set(oldv)|{v['uuid']for v in nv};assert all(newv[u]==v for u,v in oldv.items())
 for kind,key in [('pads','uuid'),('footprints','ref')]:
  aa={x[key]:x for x in h0[kind]};bb={x[key]:x for x in h[kind]};assert aa.keys()==bb.keys();assert all(bb[u]==v for u,v in aa.items()if v['ref']!='R10007')
 assert all(h[k]==v for k,v in h0.items()if k not in('tracks','vias','pads','footprints'))
 affected={L.norm(t['net'])for t in nt+nv}|{L.norm(p['net'])for p in h['pads']if p['ref']=='R10007'}
 z0={z['uuid']:z for z in before['zones']};changed=[]
 for z in after['zones']:
  old=z0.get(z['uuid'])
  if old is None or z['fills']!=old['fills']:affected.add(L.norm(z['net']));changed.append({'UUID':z['uuid'],'net':L.norm(z['net']),'layers':list(z['fills'])})
  if old is not None:assert {k:v for k,v in z.items()if k!='fills'}=={k:v for k,v in old.items()if k!='fills'}
 assert set(z0)<={z['uuid']for z in after['zones']}
 put(OUT/'affected-nets-and-fill-scopes.json',{'nets':sorted(affected),'changed_fills':changed});print('R255_EXACT_CURRENT_BOUND',sorted(affected),flush=True)
 dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom[L.norm(a)]==dom[L.norm(bb)]else.6
 code=Path(K.__file__).read_text();start=code.index(' # True circular caps/annuli are measured');end=code.index(' # Separate any native-cache guard deficit',start)
 ns={**globals(),**locals(),'O':OUT,'nt':nt+[oldt['06f5b2a7-dc39-4a5d-9309-5badd13a2347']]};exec(compile(textwrap.dedent(code[start:end]),'fresh_combined_true_geometry','exec'),ns,ns);geometry_errors=ns['errors'];checks=ns['checks']
 contexts=[K.hole_context(x)for x in(before,after)];groups={};contacts=[];direct=[];sources=[]
 cachemodel=H/'U10003-HOST-field-joint-current-exact-raw-precision-bound-r247/model.pkl';assert sha(cachemodel)=='9b5ce5fcc6fcf741f73ba48cd15ab396a022115ba7110ee3d4c7fc27459cbf86';cached=pickle.loads(cachemodel.read_bytes())[4]
 cachefile=H/'U10003-HOST-joint-independent-actual-source-contacts-oldrefs-r248/fresh-actual-drilled-affected-groups.pkl';assert sha(cachefile)=='642a32fe670eb21b4675a3d898a1ee56e6afb73e6921b16a43804f5a4f5edfc1';cache=pickle.loads(cachefile.read_bytes());reuse={FG,FLT}
 assert after['vias']==cached['vias'] and after['pads']==cached['pads']
 for net in reuse:
  for kind in('tracks','vias','pads','zones'):assert [x for x in after[kind]if L.norm(x['net'])==net]==[x for x in cached[kind]if L.norm(x['net'])==net],(net,kind)
 put(OUT/'exact-unchanged-field-graph-cache-binding.json',{'exact_R248_source_model_SHA256':sha(cachemodel),'exact_fresh_R248_groups_SHA256':sha(cachefile),'new_current_SHA256':sha(MP),'reused_nets':sorted(reuse),'all_net_physical_records_and_ALL_drills_exact':True,'other_three_nets_rebuilt_fresh':True})

 for net in sorted(affected):
  put(OUT/'status.json',{'phase':'FRESH_BEFORE_AFTER_DRILLED_GROUPS','net':net,'finished':list(groups),'all_further_gates':'OPEN'})
  
  if net in reuse:old,new=cache[net]
  else:
   _,old=K.physical(before,net,contexts[0]);_,new=K.physical(after,net,contexts[1])
  groups[net]=(old,new);print('R255_GROUPS',net,len(old),len(new),flush=True)
  (OUT/('groups-'+hashlib.sha256(net.encode()).hexdigest()[:12]+'.pkl')).write_bytes(pickle.dumps({'net':net,'before':old,'after':new},protocol=5))
  rows,bad=K.contact_losses(old,new,removed);contacts.append({'net':net,'old_groups':len(old),'after_groups':len(new),'old_relationships':rows,'losses':bad})
  for ly in LAYERS:
   oldfill=unary_union([x['shape']for xs in old for x in xs if x['kind']=='fill'and x['layer']==ly]);newfill=unary_union([x['shape']for xs in new for x in xs if x['kind']=='fill'and x['layer']==ly]);oldmetal={};newmetal=collections.defaultdict(list)
   if oldfill.is_empty:continue
   for xs in old:
    for x in xs:
     if x['kind']!='fill'and x['layer']==ly and x['uuid']not in removed and not(x['kind']=='pad'and x.get('ref')=='R10007'):oldmetal.setdefault((x['kind'],x['uuid'],ly),[]).append(x['shape'])
   for xs in new:
    for x in xs:
     if x['kind']!='fill'and x['layer']==ly:newmetal[x['kind'],x['uuid'],ly].append(x['shape'])
   for key,shapes in oldmetal.items():
    body=unary_union(shapes)
    if body.distance(oldfill)>.000002:continue
    now=unary_union(newmetal.get(key,[]));dist=None if now.is_empty or newfill.is_empty else now.distance(newfill)
    direct.append({'net':net,'physical_key':list(key),'retained_old_direct_fill_touch':dist is not None and dist<=.000002,'after_gap_mm':dist,'host_contact_operator_mm':.000002})
 for net,ref,pin in K.ROOTS:
  if net not in groups:continue
  oldroot=K.root(groups[net][0],ref,pin);newroot=K.root(groups[net][1],ref,pin);lost=K.keys(oldroot)-K.keys(newroot)-{('track',u,l)for u in removed for l in LAYERS}
  sources.append({'net':net,'root':[ref,pin],'prior_keys_lost':[list(k)for k in sorted(lost)]})
 put(OUT/'all-affected-old-relationships.json',contacts);put(OUT/'all-affected-old-direct-fill-contacts.json',direct);put(OUT/'actual-source-bank-deltas.json',sources)
 allgroups=OUT/'fresh-actual-drilled-affected-groups.pkl';allgroups.write_bytes(pickle.dumps(groups,protocol=5))
 oldrefrows=[];oldrefbad=[];roots={}
 for net,ref in ((FG,'J11003'),(LG,'J11001'),(FB,'J11005')):
  if net not in groups:continue
  oldroot=K.root(groups[net][0],ref,'2');newroot=K.root(groups[net][1],ref,'2');roots[net]=newroot;orr=K.source_refs(oldroot);nrr=K.source_refs(newroot)
  rows,stats=RF.audit(h0,orr,nrr,net,removed)
  for row in rows:
   t=oldt[row['uuid']];body=K.A.shape({'kind':'segment',**t})if not t.get('m')else L.body(t);loss=body.intersection(orr[t['layer']]).difference(nrr[t['layer']]);row.update({'reference_net':net,'literal_direct_formula_loss':ds(loss)})
   if not loss.is_empty:oldrefbad.append(row);(OUT/(net.rsplit('/',1)[-1]+'-'+t['uuid']+'-old-ref-loss.wkb')).write_bytes(loss.wkb)
  oldrefrows.extend(rows);print('R255_STRICT_OLD_REFS',net,len(rows),sum(not x['literal_direct_formula_loss']['empty']for x in rows),flush=True)
 put(OUT/'strict-original-routed-references.json',oldrefrows);put(OUT/'strict-original-routed-reference-failures.json',oldrefbad)
 # Each net owns only its exact named terminal caps. Ground metal credit is
 # confined to actual same-net source-rooted annuli on the reference layer.
 capspec={FLT:[('7f2431b3-4dcd-5b17-88ce-8aae4c3d66d4',.525),('2938cbdd-1d38-4238-9455-504b30f06e5e',.575)],CLK:[('1f45e002-4f40-4087-bbed-3be260272d8f',.375)]}
 hostpack=pickle.loads((H/'R10007-HOST-exact-native-six-track-one-via-rigid-pose-r235/exact-discrete-and-rigid-pose-packet.pkl').read_bytes())
 capspec[HOST]=[(hostpack['vias'][0]['uuid'],hostpack['new_signal_exact_own_cap_mm']),(hostpack['source_terminal_UUID'],hostpack['source_terminal_exact_own_cap_mm'])]
 refrows=[]
 restored=oldt['06f5b2a7-dc39-4a5d-9309-5badd13a2347']
 for t in nt+[restored]:
  net=L.norm(t['net']);ground=LG if net in(LG,HOST)else FG;root=roots[ground];rr=K.source_refs(root);inner=K.MAP[t['layer']]
  body=K.A.shape({'kind':'segment',**t});holes,ht=contexts[1];actual=body.difference(unary_union([holes[int(j)]for j in ht.query(body,predicate='intersects')]))
  caps=unary_union([Z.bounded_disk(newv[u],rad)for u,rad in capspec.get(net,[])])
  gm=unary_union([x['shape']for x in root if x['kind']=='via'and x['layer']==inner])if net==ground else unary_union([])
  raw=actual.difference(rr[t['layer']]);remaining=actual.difference(rr[t['layer']].union(caps).union(gm));row={'UUID':t['uuid'],'net':net,'layer':t['layer'],'reference_layer':inner,'actual_body':ds(actual),'raw_gap':ds(raw),'strict_gap_outside_exact_own_caps_or_actual_source_ground_annuli':ds(remaining),'cap_specification':capspec.get(net,[])};refrows.append(row)
  if not remaining.is_empty:(OUT/(t['uuid']+'-new-body-reference-gap.wkb')).write_bytes(remaining.wkb)
 put(OUT/'all-new-and-restored-clock-body-references.json',refrows)
 # Both FPGA-independent ordinary field returns must touch actual J3 fill;
 # the HOST return must touch actual J1 fill on both reference planes.
 pairs=[('1f45e002-4f40-4087-bbed-3be260272d8f','ef759308-9779-5e0d-96f6-ccebe745b9c0',FG),('7f2431b3-4dcd-5b17-88ce-8aae4c3d66d4','ef759308-9779-5e0d-96f6-ccebe745b9c0',FG),('2938cbdd-1d38-4238-9455-504b30f06e5e','73811c12-9f84-5491-bfee-0c5ee985a7a8',FG),(hostpack['vias'][0]['uuid'],hostpack['existing_ground_return_UUID'],LG)]
 returns=[]
 # Resolve the full shared UUID from the exact sparse packet, avoiding labels.
 shared=next(v for v in nv if L.norm(v['net'])==FG and v['uuid']!='73811c12-9f84-5491-bfee-0c5ee985a7a8')
 pairs=[(s,shared['uuid']if r.startswith('ef759308')else r,n)for s,r,n in pairs]
 for su,ru,net in pairs:
  sv=newv[su];rv=newv[ru];root=roots[net];kk=K.keys(root);distance=math.hypot(sv['x']-rv['x'],sv['y']-rv['y']);ar=[]
  for ly in('In1.Cu','In4.Cu'):
   ann=unary_union([x['shape']for x in root if x['kind']=='via'and x['uuid']==ru and x['layer']==ly]);fill=unary_union([x['shape']for x in root if x['kind']=='fill'and x['layer']==ly]);ar.append({'layer':ly,'actual_source_key':('via',ru,ly)in kk,'annulus_overlap':ds(ann.intersection(fill))})
  returns.append({'signal_UUID':su,'ground_UUID':ru,'source_net':net,'distance_mm':distance,'ordinary_window_pass':.9<=distance<=1,'both_source_annuli':ar,'both_annuli_pass':all(x['actual_source_key']and not x['annulus_overlap']['empty']for x in ar)})
 put(OUT/'ordinary-source-rooted-return-pairs.json',returns)
 badgroups=sum(len(x['losses'])for x in contacts);baddirect=[x for x in direct if not x['retained_old_direct_fill_touch']];badsource=sum(len(x['prior_keys_lost'])for x in sources);badnew=[x for x in refrows if not x['strict_gap_outside_exact_own_caps_or_actual_source_ground_annuli']['empty']]
 result={'status':'SCOPED_JOINT_CHECK_REPAIR_REQUIRED'if geometry_errors or badgroups or baddirect or badsource or oldrefbad or badnew or not all(x['ordinary_window_pass']and x['both_annuli_pass']for x in returns)else'SCOPED_JOINT_ACTUAL_CONTACT_SOURCE_REFERENCE_PASS_OTHER_GATES_OPEN','before_SHA256':sha(BP),'after_SHA256':sha(MP),'sparse_operation_SHA256':sha(OP),'affected_nets':sorted(affected),'geometry_checks':len(checks),'geometry_errors':len(geometry_errors),'old_relationship_losses':badgroups,'old_direct_contacts':len(direct),'old_direct_contact_losses':len(baddirect),'prior_source_keys_lost':badsource,'strict_old_routed_reference_failures':len(oldrefbad),'new_body_reference_failures':len(badnew),'returns':returns,'fresh_groups_SHA256':sha(allgroups),'raw_boolean_precision_and_native_integer_edge_conversion':'OPEN; no global regrid','native_fill_DRC_current_SI_thermal':'OPEN','original_six_triangle_R217_supplement':'NOT automatically credited; exact witness rebinding required if repeated','all_inherited_DIC_core_power_raw_failures':'RETAINED','native_jobs':0,'adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-started};put(OUT/'receipt.json',result);put(OUT/'status.json',{'phase':'COMPLETE','status':result['status']});print('R255_COMPLETE',sha(OUT/'receipt.json'),result['status'],flush=True)
if __name__=='__main__':main()
