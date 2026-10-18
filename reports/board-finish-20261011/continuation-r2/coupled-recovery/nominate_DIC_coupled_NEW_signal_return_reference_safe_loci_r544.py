"""Jointly vary only unaccepted SIG55ab/return9ef/two incident NEW tracks.

Full physical and source-reference-safe loci are bound separately for signal
and return. All original Cu/source/width/three-leg constraints remain hard.
No source cache reconstruction, new reference aperture credit or native job.
"""
from pathlib import Path
import sys,pickle,json,hashlib,time,math
H=Path(__file__).resolve().parent;P=H.parent
for d in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
out=H/'DIC-coupled-NEW-signal-return-reference-safe-loci-r544';assert not out.exists();out.mkdir();start=time.monotonic();mp=H/'Q0-only-new-FA-recess-explicit-100nm-margin-r526/model.pkl';assert sha(mp)=='97e6f5193c9102102ec86a50c7d142def2d9c498495c8acdbd7202f466f84e14';g,h,b,q,current=pickle.loads(mp.read_bytes());bf=H/'Q0-R526-full-current-contacts-source-reference-r528/actual-before-and-after-source-banks.pkl';assert sha(bf)=='9b48079a0eb2b1a592dca1fc195ffe70b350e9ff9a110f069178a9f207db0a17';banks=pickle.loads(bf.read_bytes());LG='/LOGIC_GND';root=banks['after'][LG];refs={l:unary_union([r['shape']for r in root if r['kind']=='fill'and r['layer']==l])for l in('In1.Cu','In4.Cu')};sig=next(v for v in h['vias']if v['uuid']=='55ab5777-4032-59ab-94d1-d5a4478c7a72');ret=next(v for v in h['vias']if v['uuid']=='9ef5dbc8-049b-5a46-b319-e13870c3e4c4');NET=K.L.norm(sig['net']);assert NET=='/motherboard_io_control/DIC_IOL1_CS_BUFFER'and K.L.norm(ret['net'])==LG;incident=[t for t in h['tracks']if K.L.norm(t['net'])==NET and any(math.dist(xy,[sig['x'],sig['y']])<1e-10 for xy in(t['a'],t['b']))];assert len(incident)==2;withheld={sig['uuid'],ret['uuid']}|{t['uuid']for t in incident};sp=P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(sp)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';iv=K.C.inventory(sp.read_bytes());assert withheld.isdisjoint(iv[3]);dom=h['domains_normalized'];gap=lambda a,n:.15 if dom.get(K.L.norm(a))==dom.get(K.L.norm(n))else .6;window=box(129.8,89.5,132.2,92.3);records,trees=K.F.build({**h,'zones':[]});reserve,exempt=K.A.reservations();common=[];smd=[];holes=[]
for p in h['pads']:
 if p['smd']:
  for l,rs in p['layers'].items():
   if l in('F.Cu','B.Cu'):smd.extend((p['uuid'],sh)for sh in K.L.poly(rs)if sh.distance(window)<.7)
 holes.extend((p['uuid'],sh)for sh in K.L.poly(p.get('hole')or[])if sh.distance(window)<.7)
for v in h['vias']:
 if v['uuid']in withheld or Point(v['x'],v['y']).distance(window)>1:continue
 common.append(K.Z.bounded_disk(v,max(.815,v['drill']/2+.1+.280)))
common.extend(K.Z.bounded_buffer(sh,.380)for uid,sh in smd+holes)
for r in h['rule_areas']:
 if r.get('no_vias'):common.extend(K.Z.bounded_buffer(sh,.275)for sh in K.L.poly(r['outline'])if sh.distance(window)<.7)
physical={};physicalrows=[]
for kind,net in[('signal',NET),('return',LG)]:
 masks=list(common);ledger=[]
 for l in K.LAYERS:
  for j in trees[l].query(window.buffer(.9),predicate='intersects'):
   r=records[l][int(j)]
   if r['uuid']in withheld or K.L.norm(r['net'])==net:continue
   radius=.25+gap(net,r['net'])+.025;mask=K.Z.bounded_buffer(r['shape'],radius);masks.append(mask);ledger.append({'kind':'actual_foreign_discrete_'+r['kind'],'UUID':r['uuid'],'raw_net':r['net'],'layer':l,'radius_mm':radius,'mask_WKB_sha256':K.C.sha(mask.wkb)})
  for z in q:
   if z['layer']!=l or K.L.norm(z['net'])==net or z['shape'].distance(window)>.9:continue
   radius=.25+max(float(z['clearance_mm']),gap(net,z['net']))+.025;mask=K.Z.bounded_buffer(z['shape'],radius);masks.append(mask);ledger.append({'kind':'exact_current_owned_role','UUID':z['uuid'],'raw_net':z['net'],'layer':l,'radius_mm':radius,'mask_WKB_sha256':K.C.sha(mask.wkb)})
 for r in reserve['keepouts']:
  if net not in exempt.get(r['name'],set()):masks.extend(K.Z.bounded_buffer(sh,.275)for sh in K.L.poly(r['outline'])if sh.distance(window)<.7)
 physical[kind]=window.difference(unary_union(masks));(out/(kind+'-all6-native-current-physical-locus.wkb')).write_bytes(physical[kind].wkb);physicalrows.append({'kind':kind,'physical_area_mm2':physical[kind].area,'physical_empty':physical[kind].is_empty,'foreign_obstacles':ledger})
put(out/'all6-coupled-physical-locus-ledgers.json',physicalrows)
# Only actual BEFORE source-covered copper is an old-reference obligation.
# It is not replaced by native outlines, another domain or a generic plane.
outmap={'F.Cu':'In1.Cu','In2.Cu':'In1.Cu','B.Cu':'In4.Cu','In3.Cu':'In4.Cu'};requirements=[];refmasks={'signal':[],'return':[]};rrows=[]
for outer,inner in outmap.items():
 for j in trees[outer].query(window.buffer(1),predicate='intersects'):
  r=records[outer][int(j)]
  if r['kind']!='track'or r['uuid']in withheld or K.L.norm(r['net'])==LG or dom.get(K.L.norm(r['net']))!=dom[LG]:continue
  actual=r['shape'].intersection(refs[inner])
  if actual.is_empty:continue
  requirements.append((r,actual));rrows.append({'UUID':r['uuid'],'raw_net':r['net'],'outer':outer,'actual_source_reference_layer':inner,'native_original_UID':r['uuid']in iv[3],'actual_before_required_source_body_WKB_sha256':K.C.sha(actual.wkb)})
  refmasks['signal'].append(K.Z.bounded_buffer(actual,.525));refmasks['return'].append(K.Z.bounded_buffer(actual,.1))
safe={k:physical[k].difference(unary_union(refmasks[k]))for k in physical}
for k,s in safe.items():(out/(k+'-strict-before-source-reference-safe-locus.wkb')).write_bytes(s.wkb)
put(out/'all-retained-actual-current-source-reference-body-mask-authorities.json',rrows);oldS=Point(sig['x'],sig['y']);oldR=Point(ret['x'],ret['y']);sigCandidates=[]
for part in K.RF.parts(safe['signal'].buffer(-.002,quad_segs=128)):
 for p in[part.representative_point(),nearest_points(oldS,part)[1]]:
  at=[round(c,6)for c in p.coords[0]]
  if safe['signal'].covers(Point(at)):sigCandidates.append(at)
for dx in range(-12,13):
 for dy in range(-12,13):
  at=[round(sig['x']+dx*.025,6),round(sig['y']+dy*.025,6)]
  if safe['signal'].covers(Point(at))and at not in sigCandidates:sigCandidates.append(at)
sigCandidates.sort(key=lambda xy:Point(xy).distance(oldS));pairs=[]
for sxy in sigCandidates:
 ss={'x':sxy[0],'y':sxy[1]};p=Point(sxy);ring=K.Z.bounded_disk(ss,1.0).difference(p.buffer(.90,quad_segs=256));rf=safe['return'].intersection(ring)
 for part in K.RF.parts(rf.buffer(-.002,quad_segs=128)):
  candidates=[part.representative_point(),nearest_points(oldR,part)[1]]
  theta=math.atan2(ret['y']-sxy[1],ret['x']-sxy[0])
  for radius in(.925,.95,.975):
   for i in range(-96,97):candidates.append(Point(sxy[0]+radius*math.cos(theta+i*math.pi/96),sxy[1]+radius*math.sin(theta+i*math.pi/96)))
  for z in candidates:
   rxy=[round(c,6)for c in z.coords[0]];rr=Point(rxy);dist=p.distance(rr)
   if not rf.covers(rr)or not .90<=dist<=1:continue
   ann=rr.buffer(.25,quad_segs=128).difference(rr.buffer(.1,quad_segs=128));aa={l:ann.buffer(-.025,quad_segs=128).intersection(sh).area for l,sh in refs.items()}
   if any(a<.005 for a in aa.values()):continue
   if any(x['signal_xy_mm']==sxy and x['return_xy_mm']==rxy for x in pairs):continue
   # Verify literal reference intersections against the exact used layers;
   # the inflated continuous masks are conservative nomination, not authority.
   nativebad=[]
   for r,required in requirements:
    radius=.525 if r['layer']in outmap else.525;loss=required.intersection(unary_union([K.Z.bounded_disk(ss,radius),K.Z.bounded_disk({'x':rxy[0],'y':rxy[1]},.1)]))
    if not loss.is_empty:nativebad.append({'UUID':r['uuid'],'layer':r['layer'],'raw_net':r['net'],'raw_loss_mm2':loss.area})
   pairs.append({'signal_UUID':sig['uuid'],'signal_xy_mm':sxy,'return_UUID':ret['uuid'],'return_xy_mm':rxy,'spacing_mm':dist,'signal_move_mm':p.distance(oldS),'return_move_mm':rr.distance(oldR),'total_move_mm':p.distance(oldS)+rr.distance(oldR),'actual_before_J1_return_annular_interior_mm2':aa,'strict_literal_all_retained_current_reference_losses':nativebad,'literal_reference_nomination_pass':not nativebad,'two_track_endpoint_full_geometry_source_current_fill_graph_source_own_and_NATIVE':'OPEN'})
  if len(pairs)>200:break
 if len(pairs)>200:break
pairs.sort(key=lambda r:(not r['literal_reference_nomination_pass'],r['total_move_mm']));put(out/'coupled-minimal-new-signal-return-pair-nominations.json',pairs[:200]);result={'verdict':'CONCRETE_MINIMAL_COUPLED_NEW_SIGNAL_RETURN_SOURCE_REFERENCE_SAFE_NOMINATION_ALL_INDEPENDENT_GATES_OPEN'if any(r['literal_reference_nomination_pass']for r in pairs)else'COUPLED_NEW_SIGNAL_RETURN_CONSERVATIVE_SOURCE_REFERENCE_LOCI_INCOMPLETE','input_current_model_sha256':sha(mp),'actual_J1_source_array_sha256':sha(bf),'native_original_source_sha256':sha(sp),'only_withdrawable_NEW_UUIDs':sorted(withheld),'exact_signal_net':sig['net'],'physical_signal_locus_area_mm2':physical['signal'].area,'physical_return_locus_area_mm2':physical['return'].area,'reference_safe_signal_locus_area_mm2':safe['signal'].area,'reference_safe_return_locus_area_mm2':safe['return'].area,'sampled_serialized_signal_candidate_count':len(sigCandidates),'coupled_pair_nomination_count':len(pairs),'first_nomination':pairs[0]if pairs else None,'ordinary_saved_return_window_mm':[.90,1.0],'all_original_and_other_current_Cu_holes_pose_native_roles_source_constraints_retained':True,'no_generic_own_aperture_or_source_cache_reclaim_credit':True,'all_full_reference_pair_source_contact_geometry_current_NATIVE_SI':'OPEN','all_raw_failures_preserved':True,'native_jobs':0,'board_or_model_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-start};put(out/'receipt.json',result);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),**result}),flush=True)
