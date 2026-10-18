"""Coupled Q0 pulldown pose nomination on exact R155, all protected power hard."""
import sys,json,pickle,hashlib,math,csv,io,re,time
from pathlib import Path
H=Path(__file__).resolve().parent;P=H.parent;sys.dont_write_bytecode=True
for p in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import tri_route as T
from shapely import affinity
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely import from_wkb
from shapely.strtree import STRtree
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def parts(g):return K.RF.parts(g)
def transform(sh,angle,dx,dy,anchor):return affinity.translate(affinity.rotate(sh,angle,origin=anchor),xoff=dx,yoff=dy)
start=time.monotonic();model=P/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl';assert sha(model)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';g,h,b,q,current=pickle.loads(model.read_bytes());NET='/motherboard_do/DOA_Q0_READY_N';GND='/motherboard_motors/FIELD_GND';domain=h['domains_normalized'];out=H/'Q0-R10016-source-pose-coupled-nomination-r334';assert not out.exists();out.mkdir()
source=P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(source)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';identity=K.A.N.SourceNets(source.read_bytes());iv=K.C.inventory(source.read_bytes());fps=[(u,ch)for u,ch in iv[3].items()if K.C.pcbtext.chunk_kind(ch)=='footprint'and re.search(rb'\(property\s+"Reference"\s+"R10016"',ch)];assert len(fps)==1;fuid,fchunk=fps[0];(out/'R10016.original-native-footprint-chunk').write_bytes(fchunk)
fp=next(f for f in h['footprints']if f['ref']=='R10016');pads={p['num']:p for p in h['pads']if p['ref']=='R10016'};assert K.L.norm(pads['1']['net'])==NET and K.L.norm(pads['2']['net'])==GND;anchor=(pads['2']['x'],pads['2']['y']);oldsh={i:unary_union(K.L.poly(p['layers']['F.Cu']))for i,p in pads.items()};court=unary_union(K.L.poly(fp['courtyard']['F']));padids={p['uuid']for p in pads.values()};window=box(219,148,241,176)
ref=from_wkb((H/'Q0-current-R155-source-reference-blockers-r316/actual-J11003-In1-rooted-reference-local.wkb').read_bytes());groupfile=P/'field-power/REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r368/actual-drilled-current-groups.pkl';root=K.root(pickle.loads(groupfile.read_bytes())[GND],'J11003','2');retained=[r for r in root if r['uuid']not in padids];sourceUF=K.A.S.UF()
for r in retained:sourceUF.find(r['key'])
for layer in K.LAYERS:
 layerrows=[r for r in retained if r['layer']==layer];tree=STRtree([r['shape']for r in layerrows])
 for i,r in enumerate(layerrows):
  for j in tree.query(r['shape'].buffer(.000002),predicate='intersects'):
   j=int(j)
   if i<j and r['shape'].distance(layerrows[j]['shape'])<=.000002:sourceUF.join(r['key'],layerrows[j]['key'])
rootkey=next(r['key']for r in retained if r['kind']=='pad'and(r['ref'],str(r['pin']))==('J11003','2'));trueRoot=[r for r in retained if sourceUF.find(r['key'])==sourceUF.find(rootkey)]
withdrawal_missing=K.keys(retained)-K.keys(trueRoot);assert not withdrawal_missing,('Old ground pad withdrawal disconnects prior source objects',withdrawal_missing)
groundF=unary_union([r['shape']for r in trueRoot if r['layer']=='F.Cu']);sourcepad=next(p for p in h['pads']if(p['ref'],str(p['num']))==('U10004','1'));signalF=unary_union(K.L.poly(sourcepad['layers']['F.Cu']))
discrete,trees=K.F.build({**h,'zones':[]},layers={'F.Cu'});holes=[(v['uuid'],v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],p['net'],s)for p in h['pads']for s in K.L.poly(p.get('hole')or[])];hole_tree=STRtree([r[2]for r in holes]);courts=[(f['ref'],s)for f in h['footprints']if f['ref']!='R10016'for s in K.L.poly(f['courtyard'].get('F',[]))];court_tree=STRtree([r[1]for r in courts]);reserve,exempt=K.A.reservations();qF=[z for z in q if z['layer']=='F.Cu'];nativeF=[(z,s)for z in current['zones']if not z.get('prospective_not_native')for s in K.L.poly(z['fills'].get('F.Cu',[]))];rows=[];selected=None
def req(a,b):return .15 if domain.get(K.L.norm(a))==domain.get(K.L.norm(b))else .6
def obstacles(net,newsh,peer_tracks=()):
 obs=[]
 for t in peer_tracks:
  if K.L.norm(t['net'])!=net:obs.append(K.A.shape({'kind':'segment',**t}).buffer(req(net,t['net'])+.030,quad_segs=128))
 for j in trees['F.Cu'].query(window.buffer(1),predicate='intersects'):
  r=discrete['F.Cu'][int(j)]
  if r['uuid']in padids or K.L.norm(r['net'])==net:continue
  obs.append(r['shape'].buffer(req(net,r['net'])+.030,quad_segs=128))
 for num,shape in newsh.items():
  if K.L.norm(pads[num]['net'])!=net:obs.append(shape.buffer(req(net,pads[num]['net'])+.030,quad_segs=128))
 for z in qF:
  if K.L.norm(z['net'])!=net and z['shape'].distance(window)<1:obs.append(z['shape'].buffer(max(req(net,z['net']),float(z['clearance_mm']))+.030,quad_segs=128))
 for z,shape in nativeF:
  if K.L.norm(z['net'])!=net and domain.get(K.L.norm(z['net']))!=domain.get(net)and shape.distance(window)<1:obs.append(shape.buffer(max(req(net,z['net']),float(z['clearance_mm']))+.030,quad_segs=128))
 for uid,n,shape in holes:
  if K.L.norm(n)!=net and shape.distance(window)<1:obs.append(shape.buffer(.280,quad_segs=128))
 for r in h['rule_areas']:
  if'F.Cu'in r['layers']and r.get('no_tracks'):obs.extend(s.buffer(.025,quad_segs=128)for s in K.L.poly(r['outline']))
 for r in reserve['keepouts']:
  if'F.Cu'in r['layers']and net not in exempt.get(r['name'],set()):obs.extend(s.buffer(.025,quad_segs=128)for s in K.L.poly(r['outline']))
 return window.difference(unary_union(obs)).buffer(-.105,quad_segs=128).intersection(ref.buffer(-.105,quad_segs=128))
poses=sorted([(angle,dx,dy)for angle in(0,180,90,-90)for dx in(0,-.5,.5,-1,1,-1.5,1.5)for dy in(0,-.5,.5,-1,1,-1.3,1.3,-1.6,1.6,-2,2)if angle or dx or dy],key=lambda p:(math.hypot(p[1],p[2])+(0 if p[0]==180 else .2 if p[0]else .1),abs(p[0]),p[1],p[2]))
for angle,dx,dy in poses:
 newsh={i:transform(s,angle,dx,dy,anchor)for i,s in oldsh.items()};newcourt=transform(court,angle,dx,dy,anchor);bad=[];contact=[];newholes=[]
 for j in court_tree.query(newcourt.buffer(.025),predicate='intersects'):
  name,other=courts[int(j)]
  if newcourt.distance(other)<.025:bad.append({'kind':'courtyard','other_ref':name,'distance_mm':newcourt.distance(other)})
 for num,shape in newsh.items():
  net=K.L.norm(pads[num]['net'])
  for j in trees['F.Cu'].query(shape.buffer(.8),predicate='intersects'):
   r=discrete['F.Cu'][int(j)]
   if r['uuid']in padids or K.L.norm(r['net'])==net:continue
   if r['kind']=='track'and not r['source'].get('m'):d=LineString([r['source']['a'],r['source']['b']]).distance(shape)-r['source']['w']/2
   elif r['kind']=='via':d=Point(r['source']['x'],r['source']['y']).distance(shape)-r['source']['d']/2
   else:d=shape.distance(r['shape'])
   if d<req(net,r['net'])+.025:bad.append({'kind':'new_pad_to_actual_foreign_'+r['kind'],'pad':num,'other_UUID':r['uuid'],'actual_mm':d,'required_mm':req(net,r['net'])+.025})
  for j in hole_tree.query(shape.buffer(.280),predicate='intersects'):
   uid,n,hole=holes[int(j)];d=shape.distance(hole);old=oldsh[num].distance(hole)
   if d<.280:
    same=shape.equals(oldsh[num]);bad.append({'kind':'new_SMD_every_hole_aperture','pad':num,'hole_UUID':uid,'actual_mm':d,'old_mm':old,'old_exact_pad_geometry_preserved':same,'no_new_VIPPO_waiver':True})
  for z in qF:
   if K.L.norm(z['net'])!=net and shape.distance(z['shape'])<max(req(net,z['net']),float(z['clearance_mm']))+.025:bad.append({'kind':'current_owned_F_plane_hard','pad':num,'other_UUID':z['uuid']})
  gap=shape.difference(ref);contact.append({'pad':num,'new_F_pad_actual_J11003_In1_full_body_gap_mm2':gap.area,'new_F_pad_actual_source_reference_gap_empty':gap.is_empty,'new_F_ground_pad_actual_rooted_F_Cu_overlap_mm2':shape.intersection(groundF).area if num=='2'else None})
 row={'geometric_rotation_degrees':angle,'translation_mm':[dx,dy],'checks':bad,'source_reference_rows':contact};rows.append(row)
 if bad:continue
 groundtracks=[];groundchunks={};ground_body=unary_union([]);ground_witness={'direct_existing_root_overlap_mm2':newsh['2'].intersection(groundF).area,'exact_old_R10016_pad_absent_from_source_graph':True}
 if ground_witness['direct_existing_root_overlap_mm2']<=.004:
  groundfree=obstacles(GND,newsh);ga=[newsh['2'].buffer(-.04,quad_segs=128).intersection(groundfree),groundF.buffer(-.02,quad_segs=128).intersection(groundfree)];row['ground_attachment_areas_mm2']=[x.area for x in ga]
  for part in parts(groundfree):
   aa=[x.intersection(part)for x in ga]
   if any(x.is_empty for x in aa):continue
   p0,p1=nearest_points(*aa);ends=[[round(p.x,6),round(p.y,6)]for p in(p0,p1)]
   if not all(part.covers(Point(p))for p in ends):continue
   path0,search0=T.route(part,tuple(ends[0]),tuple(ends[1]));path0=[[round(x,6),round(y,6)]for x,y in path0]
   if len(path0)<2:continue
   gb=unary_union([K.A.shape({'kind':'segment','a':a,'b':bb,'w':.2})for a,bb in zip(path0,path0[1:])])
   if not gb.difference(ref).is_empty or min(gb.intersection(newsh['2']).area,gb.intersection(groundF).area)<=.004:continue
   for a,bb in zip(path0,path0[1:]):
    uid,ch=identity.serial_segment(GND,'F.Cu',a,bb,.2);assert uid not in iv[3];groundchunks[uid]=ch;groundtracks.append({'uuid':uid,'net':identity.raw(GND),'a':a,'b':bb,'w':.2,'layer':'F.Cu'})
   ground_body=gb;ground_witness.update(new_F_ground_path_mm=path0,strict_ground_route_actual_In1_source_gap_empty=True,ground_new_pad_and_real_retained_root_overlaps_mm2=[gb.intersection(newsh['2']).area,gb.intersection(groundF).area],search=search0);break
  if not groundtracks:continue
 free=obstacles(NET,newsh,groundtracks);attach=[signalF.buffer(-.04,quad_segs=128).intersection(free),newsh['1'].buffer(-.04,quad_segs=128).intersection(free)];row['signal_attachment_areas_mm2']=[s.area for s in attach]
 for ci,part in enumerate(parts(free)):
  aa=[s.intersection(part)for s in attach]
  if any(s.is_empty for s in aa):continue
  a,bb=nearest_points(*aa);endpoints=[[round(v.x,6),round(v.y,6)]for v in(a,bb)]
  if not all(part.covers(Point(p))for p in endpoints):continue
  path,search=T.route(part,tuple(endpoints[0]),tuple(endpoints[1]));path=[[round(x,6),round(y,6)]for x,y in path]
  if len(path)<2:continue
  body=unary_union([K.A.shape({'kind':'segment','a':a,'b':bb,'w':.2})for a,bb in zip(path,path[1:])]);gap=body.difference(ref)
  if not gap.is_empty or min(body.intersection(signalF).area,body.intersection(newsh['1']).area)<=.004:continue
  chunks={};tracks=[]
  for a,bb in zip(path,path[1:]):
   uid,ch=identity.serial_segment(NET,'F.Cu',a,bb,.2);assert uid not in iv[3];chunks[uid]=ch;tracks.append({'uuid':uid,'net':identity.raw(NET),'a':a,'b':bb,'w':.2,'layer':'F.Cu'})
  identity.assert_chunks(chunks);newroot=transform(Point(fp['x'],fp['y']),angle,dx,dy,anchor);selected={**row,'new_native_root_xy_mm':[round(newroot.x,6),round(newroot.y,6)],'native_angle_delta_degrees':(-angle)%360,'ground_pin2_new_centre_mm':[round(anchor[0]+dx,6),round(anchor[1]+dy,6)],'new_tracks':groundtracks+tracks,'exact_add_chunks':{u:c.decode()for u,c in {**groundchunks,**chunks}.items()},'actual_withdrawn_old_pad_source_ground_witness':ground_witness,'new_pad_whole_body_reference_rows_preserved_OPEN_not_waived':contact,'path_mm':path,'length_mm':LineString(path).length,'strict_signal_full_body_source_reference_gap_empty':True,'signal_source_and_target_finite_overlap_mm2':[body.intersection(signalF).area,body.intersection(newsh['1']).area],'actual_ground_pin_root_contact_mm2':newsh['2'].intersection(groundF.union(ground_body)).area,'source_original_FP_UUID':fuid,'source_original_FP_chunk_SHA256':sha(out/'R10016.original-native-footprint-chunk'),'all_existing_native_tracks_vias_zones_otherFPs_unchanged':True,'no_new_signal_holes_or_transitions':True,'native_pose_attestation_source_parity_actual_full_no_loss_DRC_reference_current_SI':'OPEN','search':search}
  for num,s in newsh.items():(out/('R10016-new-pad'+num+'.wkb')).write_bytes(s.wkb)
  (out/'R10016-new-courtyard.wkb').write_bytes(newcourt.wkb)
  for uid,ch in {**groundchunks,**chunks}.items():(out/(uid+'.segment-chunk')).write_bytes(ch)
  break
 if selected:break
 print('Q0_POSE_LEGAL_SOURCE_ONLY_NO_COMMON_F_COMPONENT',angle,dx,dy,row.get('signal_attachment_areas_mm2'),flush=True)
report={'verdict':'Q0_R10016_COUPLED_POSE_SIGNAL_POSITIVE_NOMINATION_FULL_INDEPENDENT_NATIVE_OPEN'if selected else'Q0_R10016_FINITE_SOURCE_POSE_SCREEN_INCOMPLETE','model_file':str(model),'model_sha256':sha(model),'source_native_parent_file':str(source),'source_native_parent_sha256':sha(source),'actual_R368_source_group_file':str(groupfile),'actual_R368_source_group_sha256':sha(groupfile),'old_reference_diagnosis_file':str(H/'Q0-current-R155-source-reference-blockers-r316/receipt.json'),'old_reference_diagnosis_sha256':sha(H/'Q0-current-R155-source-reference-blockers-r316/receipt.json'),'original_R10016_FP_UUID':fuid,'original_R10016_10k_pulldown_ground_not_supply':True,'selected':selected,'all_finite_pose_rows':rows,'pose_count':len(rows),'every_current_protected_power_role_hard':True,'actual_old_ground_pad_removed_before_source_witness':True,'all_prior_ground_source_keys_retained_after_old_pad_withdrawal':True,'source_union_excludes_own_phantom_old_pad_geometry':True,'new_SMD_whole_pad_reference_DC_loop_and_SI_qualification':'OPEN; raw exact gaps preserved; every new routed full body strictly reference covered','unchanged_inherited_R155_R368_28_R7_CORE_ROOT42_current_native_failures':True,'actual_F_native_same_domain_fill_retreat_contact_and_source_gates':'MANDATORY_OPEN','no_new_VIPPO_process_waiver':True,'native_jobs':0,'board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-start};put(out/'receipt.json',report);print(json.dumps({'receipt_file':str(out/'receipt.json'),'receipt_sha256':sha(out/'receipt.json'),'selected':selected,'poses':len(rows)}),flush=True)
