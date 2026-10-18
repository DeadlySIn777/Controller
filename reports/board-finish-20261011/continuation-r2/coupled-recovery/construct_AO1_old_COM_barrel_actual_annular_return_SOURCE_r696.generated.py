"""Controlled move of exactly one old COM barrel and its single own B stub.

Same-net ground uses actual solid/thermal fill profile and physical drill loss.
No SIGNAL antipad is applied to the moved COM barrel. All unrelated Cu is HARD.
"""
from pathlib import Path
import sys,json,pickle,hashlib,time,math,re
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import tri_route as T
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
COM='/motherboard_analog_output/AO1_COM';NET='/motherboard_analog_output/AO1_DAC_CS_N';UID='2e243304-8de5-44b1-bee4-d95e5ae3017b';STUB='3aa40856-2328-4f06-886c-1bac6022f851';OUT=H/'AO1-only-old-COM-barrel-own-B-stub-exact-profile-controlled-detour-actual-annular-source-return-r696'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def parts(s):
 if s.is_empty:return[]
 if s.geom_type=='Polygon':return[s]
 return[p for x in getattr(s,'geoms',[])for p in parts(x)]
def sites(s,desired,limit=12):
 rows=[]
 for face in parts(s):
  for pt in(face.representative_point(),nearest_points(face,Point(desired))[0]):
   xy=[round(pt.x,6),round(pt.y,6)]
   if s.covers(Point(xy))and xy not in rows:rows.append(xy)
 return sorted(rows,key=lambda xy:math.dist(xy,desired))[:limit]
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,s=None):
  p=Path(p);v=sha(p);assert s is None or s==v;pins[str(p.resolve())]=v;return p
 mp=pin(H/'AO1-R656-seven-GROUND-additions-joint-R20-independent-source-geometry-r658/R20-plus-only-seven-ground-tracks-prospective-source-audit-context.pkl','94ea2f68b967fac5c78a8085291b1f46de54b2f5b29a33de12253fe8119f7c23');before=pickle.loads(mp.read_bytes());gp=pin(mp.parent/'actual-before-R20-and-prospective-ground-added-COM-groups.pkl','d26f50bfa4047a6e29e572eb3daf3a7fdf72c323ee3adeabeb9567198c53c3f9');bg=pickle.loads(gp.read_bytes())['after'];root=K.root(bg,'U14619','7');refs={ly:unary_union([r['shape']for r in root if r['kind']=='fill'and r['layer']==ly])for ly in('In1.Cu','In4.Cu')};v=next(v for v in before['vias']if v['uuid']==UID);old=[v['x'],v['y']];stub=next(t for t in before['tracks']if t['uuid']==STUB);assert v['d']==.6 and v['drill']==.3 and stub['w']==.2 and stub['layer']=='B.Cu';assert list(stub['b'])==old
 sp=pin(ROOT/'field-power/FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753/FIELD-ROOT-Q0-DIC-DI6-known-failure-diagnostic.kicad_pcb','7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2');raw=K.C.inventory(sp.read_bytes())[3];peerp=pin(H/'AO1-MON3-VREF-and-only-b177-5V-native-width-endpoint-source-detour-r19/MON3-VREF-plus-exact-b177-5V-controlled-detour-NOMINEE.pkl','d35097754a50017d6d4b17d4388dbced44c63547b39fbddbcda31b8a78cf4181');retired=pickle.loads(peerp.read_bytes())['deleted_original_chunks'];base={**before,'tracks':[t for t in before['tracks']if t['uuid']!=STUB],'vias':[q for q in before['vias']if q['uuid']!=UID]};existing={q['uuid']for q in before['tracks']+before['vias']};heldtracks=[];heldvias=[]
 for uid,ch in raw.items():
  if uid in retired:assert ch==retired[uid];continue
  if uid in existing or not ch.lstrip().startswith((b'(segment',b'(via')):continue
  q=K.A.G.parse(uid,ch,{})
  if q['kind']=='segment':heldtracks.append({'uuid':uid,'net':q['net'],'layer':q['layer'],'a':q['a'],'b':q['b'],'w':q['w']})
  else:heldvias.append({'uuid':uid,'net':q['net'],'x':q['at'][0],'y':q['at'][1],'d':q['d'],'drill':q['drill'],'flashed':list(K.LAYERS)})
 planner={**base,'tracks':base['tracks']+heldtracks,'vias':base['vias']+heldvias};rec,trees=K.F.build({**planner,'zones':[]});dom=before['domains_normalized'];gap=lambda a,b:.15 if dom[K.L.norm(a)]==dom[K.L.norm(b)]else .6;win=box(371,123,382,133);clip=win.buffer(1);freeF_obs=[];SG_obs=[];COM_obs=[];RET_obs=[];stub_obs=[]
 for ly in K.LAYERS:
  for i in trees[ly].query(clip,predicate='intersects'):
   r=rec[ly][int(i)];shape=r['shape'].intersection(clip);inside=.005 if r['kind']=='pad'else 0.
   if K.L.norm(r['net'])!=NET:
    req=gap(r['net'],NET)+.025;SG_obs.append(K.Z.bounded_buffer(shape,req+.25+inside))
    if ly=='F.Cu':freeF_obs.append(K.Z.bounded_buffer(shape,req+.1+inside))
   if K.L.norm(r['net'])!=COM:
    req=gap(r['net'],COM)+.025;COM_obs.append(K.Z.bounded_buffer(shape,req+.3+inside));RET_obs.append(K.Z.bounded_buffer(shape,req+.25+inside))
    if ly=='B.Cu':stub_obs.append(K.Z.bounded_buffer(shape,req+.1+inside))
 # Exact old/current foreign fills are hard for moved GROUND; ordinary SIGNAL
 # sites defer only native same-domain fill antipads to separate AFTER auditing.
 fillrows=[]
 for z in before['zones']:
  for ly,rs in z['fills'].items():
   for sh in K.L.poly(rs):
    if sh.envelope.disjoint(clip):continue
    cl=float(z['clearance_mm']);fillrows.append((z['uuid'],z['net'],ly,sh,cl,'R20_R656_native_profile'))
 latep=pin(ROOT/'field-power/R157-actual-rooted-old-barrel-minimal-local-ground-landing-nominees-r665/only-source-rooted-existing-barrel-local-ground-landing-proposals-NOT_MODEL.pkl');late=pickle.loads(latep.read_bytes())
 for z in late:
  if z['shape'].envelope.disjoint(clip):continue
  for role in('shape','zone_outline_shape'):fillrows.append((z['uuid'],z['net'],z['layer'],z[role],float(z['clearance_mm']),'held_R665_'+role))
 for uid,n,ly,sh,cl,origin in fillrows:
  if K.L.norm(n)!=COM:
   req=max(cl,gap(n,COM))+.025;COM_obs.append(K.Z.bounded_buffer(sh.intersection(clip),req+.3));RET_obs.append(K.Z.bounded_buffer(sh.intersection(clip),req+.25))
   if ly=='B.Cu':stub_obs.append(K.Z.bounded_buffer(sh.intersection(clip),req+.1))
  if K.L.norm(n)!=NET and(origin!='R20_R656_native_profile'or uid not in raw or gap(n,NET)!=.15):
   req=max(cl,gap(n,NET))+.025;SG_obs.append(K.Z.bounded_buffer(sh.intersection(clip),req+.25))
   if ly=='F.Cu':freeF_obs.append(K.Z.bounded_buffer(sh.intersection(clip),req+.1))
 holes,ht=K.hole_context(planner)
 for sh in holes:
  if sh.envelope.disjoint(clip):continue
  COM_obs.append(K.Z.bounded_buffer(sh,.15+.275));RET_obs.append(K.Z.bounded_buffer(sh,.1+.275));SG_obs.append(K.Z.bounded_buffer(sh,.1+.275));freeF_obs.append(K.Z.bounded_buffer(sh,.1+.275));stub_obs.append(K.Z.bounded_buffer(sh,.1+.275))
 for pad in before['pads']:
  if not pad['smd']:continue
  for ly,rs in pad['layers'].items():
   if ly not in('F.Cu','B.Cu'):continue
   for sh in K.L.poly(rs):
    if sh.envelope.disjoint(clip):continue
    COM_obs.append(K.Z.bounded_buffer(sh,.15+.275+.005));RET_obs.append(K.Z.bounded_buffer(sh,.1+.275+.005));SG_obs.append(K.Z.bounded_buffer(sh,.1+.275+.005))
 for q in planner['vias']:
  if not Point(q['x'],q['y']).envelope.disjoint(clip):SG_obs.append(K.Z.bounded_disk(q,.815))
 reserve,exempt=K.A.reservations()
 for rule in before['rule_areas']:
  if set(rule['layers']).intersection(K.LAYERS):
   for sh in K.L.poly(rule['outline']):
    if rule.get('no_vias'):COM_obs.append(K.Z.bounded_buffer(sh,.325));RET_obs.append(K.Z.bounded_buffer(sh,.275));SG_obs.append(K.Z.bounded_buffer(sh,.275))
    if 'F.Cu'in rule['layers']and rule.get('no_tracks'):freeF_obs.append(K.Z.bounded_buffer(sh,.125))
    if 'B.Cu'in rule['layers']and rule.get('no_tracks'):stub_obs.append(K.Z.bounded_buffer(sh,.125))
 for rule in reserve['keepouts']:
  for net,va,fa,ly in((COM,COM_obs,stub_obs,'B.Cu'),(NET,SG_obs,freeF_obs,'F.Cu')):
   if net in exempt.get(rule['name'],set()):continue
   for sh in K.L.poly(rule['outline']):
    if set(rule['layers']).intersection(K.LAYERS):
     va.append(K.Z.bounded_buffer(sh,.325 if net==COM else .275))
     if net==COM:RET_obs.append(K.Z.bounded_buffer(sh,.275))
    if ly in rule['layers']:fa.append(K.Z.bounded_buffer(sh,.125))
 COMfree=win.difference(unary_union(COM_obs));RETfree=win.difference(unary_union(RET_obs));SGfree=win.difference(unary_union(SG_obs));Ffree=win.difference(unary_union(freeF_obs)).intersection(refs['In1.Cu'].buffer(-.105));Bfree=win.difference(unary_union(stub_obs));Bfaces=[s for s in parts(Bfree)if s.covers(Point(stub['a']))];Bconnected=unary_union(Bfaces);pad=next(p for p in before['pads']if p['uuid']=='5bd36a6a-0ece-4d8a-bb54-e362786d2249');start=[pad['x'],pad['y']];baseface=unary_union([s for s in parts(Ffree)if s.covers(Point(start))]);SGsites=SGfree.intersection(baseface);sourcecenters=COMfree.intersection(refs['In1.Cu'].buffer(.299975,quad_segs=128)).intersection(refs['In4.Cu'].buffer(.299975,quad_segs=128));print('R696_REGIONS','COM',COMfree.area,'SOURCEcenters',sourcecenters.area,'SGsites',SGsites.area,flush=True)
 RETsource=RETfree.intersection(refs['In1.Cu'].buffer(.249975,quad_segs=128)).intersection(refs['In4.Cu'].buffer(.249975,quad_segs=128));print('R696_RET_REGION',RETsource.area,'distance_to_SG',RETsource.distance(SGsites),flush=True)
 (OUT/'bounded-source-COM-SG-stub-axis-regions.pkl').write_bytes(pickle.dumps({'COMfree':COMfree,'SGfree':SGfree,'Ffree':Ffree,'Bfree':Bfree,'Bconnected':Bconnected,'SGsites':SGsites,'SOURCEcenters':sourcecenters,'RETsource':RETsource,'RETfree':RETfree},protocol=5))
 trials=[];selected=None
 offsets=sorted(((dx,dy)for dx in range(-120,121)for dy in range(-120,121)if dx or dy),key=lambda v:(v[0]*v[0]+v[1]*v[1],v))
 for dx,dy in offsets:
  at=[round(old[0]+dx*.025,6),round(old[1]+dy*.025,6)];pt=Point(at)
  if not sourcecenters.covers(pt):continue
  newstub={**stub,'b':at};line=LineString([stub['a'],at])
  if not Bconnected.covers(pt):continue
  ann=pt.buffer(.3,quad_segs=128).difference(pt.buffer(.15,quad_segs=128));contact={ly:ann.intersection(refs[ly]).area for ly in refs}
  if any(a<=.005 for a in contact.values()):continue
  f1=Ffree.difference(K.Z.bounded_buffer(pt,.3+.175+.1));faces=[s for s in parts(f1)if s.covers(Point(start))];sourceSG=SGsites.difference(pt.buffer(.815,quad_segs=128)).intersection(unary_union(faces));opts=sites(sourceSG,[376.67,127.71],6);trial={'old_COM_move_mm':at,'offset_um':[dx*25,dy*25],'actual_BEFORE_both_inner_SOURCE_annulus_contact_mm2':contact,'source_SG_options':opts};trials.append(trial)
  for pos in opts:
   ring=Point(pos).buffer(.999,quad_segs=128).difference(Point(pos).buffer(.901,quad_segs=128));returnOptions=sites(RETsource.intersection(ring).difference(pt.buffer(.815,quad_segs=128)),[pos[0]+.95,pos[1]],8)
   if not returnOptions:continue
   groundReturn=returnOptions[0]
   if not all(Point(groundReturn).buffer(.25,quad_segs=128).difference(Point(groundReturn).buffer(.1,quad_segs=128)).intersection(refs[ly]).area>.005 for ly in refs):continue
   bface=next((s for s in Bfaces if s.covers(pt)),None)
   if bface is None:continue
   bpath,bsearch=T.route(bface,tuple(stub['a']),tuple(at));bpath=[[round(x,6),round(y,6)]for x,y in bpath]
   if len(bpath)<2 or not bface.covers(LineString(bpath)):continue
   facesWithReturn=[s for s in parts(f1.difference(K.Z.bounded_buffer(Point(groundReturn),.25+.175+.1)))if s.covers(Point(start))]
   faces=facesWithReturn
   face=next((s for s in faces if s.covers(Point(pos))),None)
   if face is None:continue
   path,search=T.route(face,tuple(start),tuple(pos));path=[[round(x,6),round(y,6)]for x,y in path]
   if len(path)<2 or not face.covers(LineString(path)):continue
   selected={**trial,'source_signal_nominee_mm':pos,'source_pair_distance_mm':math.dist(groundReturn,pos),'NEW_source_return_via_mm':groundReturn,'NEW_source_return_via_d_drill_mm':[.5,.2],'entry_F_path_mm':path,'entry_route_search':search,'owned_B_stub_detour_mm':bpath,'owned_B_stub_search':bsearch};break
  if selected:break
 (OUT/'raw-local-controlled-move-attempts.json').write_text(json.dumps(trials,indent=1)+'\n');chunks={};packetdata={'selected':selected,'old_controlled_chunks':{UID:raw[UID],STUB:raw[STUB]},'original_deletes':{},'new_chunks':{},'tracks':[],'vias':[]}
 if selected:
  at=selected['old_COM_move_mm'];text=' '.join(format(x,'.6f').rstrip('0').rstrip('.')for x in at).encode();oldat=b'376.772997 127.45';assert raw[UID].count(b'(at '+oldat+b')')==1;chunks={UID:raw[UID].replace(b'(at '+oldat+b')',b'(at '+text+b')')};identity=K.A.N.SourceNets(sp.read_bytes());newtracks=[]
  for ix,(a,b1)in enumerate(zip(selected['owned_B_stub_detour_mm'],selected['owned_B_stub_detour_mm'][1:])):
   tid,ch=identity.serial_segment(COM,'B.Cu',a,b1,.2)
   if ix==0:ch=ch.replace(tid.encode(),STUB.encode());tid=STUB
   chunks[tid]=ch;newtracks.append({'uuid':tid,'net':identity.raw(COM),'layer':'B.Cu','a':a,'b':b1,'w':.2})
  identity.assert_chunks(chunks);newvia={**v,'x':at[0],'y':at[1]};packetdata.update({'original_deletes':{UID:raw[UID],STUB:raw[STUB]},'new_chunks':chunks,'tracks':newtracks,'vias':[newvia]});after={**before,'tracks':[t for t in before['tracks']if t['uuid']!=STUB]+newtracks,'vias':[newvia if q['uuid']==UID else q for q in before['vias']]};ng=K.physical(after,COM,K.hole_context(after))[1];newroot=K.root(ng,'U14619','7');oldkeys=K.keys(root);newkeys=K.keys(newroot);lost=sorted(oldkeys-newkeys);groupbad=K.contact_losses(bg,ng)[1];assert not lost and not groupbad,(lost,groupbad);packetdata['prospective_old_COM_source_keys_lost']=lost;packetdata['prospective_old_COM_groups_lost']=groupbad;packetdata['prospective_source_group_keys']=len(newkeys)
 packet=OUT/'only-old-COM-barrel-and-single-own-B-stub-native-profile-controlled-move-NOMINEE.pkl';packet.write_bytes(pickle.dumps(packetdata,protocol=5));r={'verdict':'ONE_OLD_COM_BARREL_AND_ONE_OWN_STUB_EXACT_PROFILE_ESCAPE_NOMINATED_ALL_OTHERS_HARD_INDEPENDENT_OPEN'if selected else'CONTROLLED_COM_BARREL_OWN_STUB_SOURCE_ESCAPE_BOUNDED_INCOMPLETE','input_SHA256':pins,'selected':selected,'old_new_integer_pose_ledger':None if not selected else{'old_IU':[round(x*1e6)for x in old],'new_IU':[round(x*1e6)for x in selected['old_COM_move_mm']]},'same_native_UUIDs_controlled_ONLY':[UID,STUB],'exact_via_diameter_drill_mm':[.6,.3],'via_lock_net_span_all_nonpose_fields_literal_exact':True,'same_stub_width_layer_fixed_other_endpoint_owned_detour_mm':{'width':.2,'layer':'B.Cu','fixed_at':stub['a']},'same_COM_solid_thermal_profile_no_SIGNAL_antipad':True,'physical_drill_loss_recomputed':bool(selected),'source_signal_candidate_is_entry_only_not_a_complete_route':True,'ordinary_source_return_is_distinct_NEW_via_NOT_old_moved_barrel':True,'full_native_AFTER_all_sources_refs_contacts_current_loop_SI':'OPEN','packet_file':str(packet.resolve()),'packet_SHA256':sha(packet),'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-st};(OUT/'receipt.json').write_text(json.dumps(r,indent=1)+'\n')
 for p,s in pins.items():assert sha(p)==s,p
 print('R696_COMPLETE',sha(OUT/'receipt.json'),r['verdict'],'selected',selected,flush=True)
if __name__=='__main__':main()
