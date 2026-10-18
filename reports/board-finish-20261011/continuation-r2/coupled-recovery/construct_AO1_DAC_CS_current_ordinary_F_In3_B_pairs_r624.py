"""Fresh paired AO1 DAC-CS constructor reusing saved continuous routing methods.

Both actual native pads are bare. All retained power and old fault Cu remain fixed. Native
and current HOST J1/In1 support are both required for this nomination;
actual all-net AFTER/full source/reference/native gates remain independent.
"""
from pathlib import Path
import sys,json,pickle,hashlib,math,time
H=Path(__file__).resolve().parent;P=H.parent
for d in(P,P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import audit_ao1_positive_operation_r4 as SERIAL
import restore_field_current_mixed_precision_states_r366 as MS
import tri_route as T
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
OUT=H/'AO1-DAC-CS-current-ordinary-F-In3-B-two-pair-constructor-r624';NET='/motherboard_analog_output/AO1_DAC_CS_N';LG='/motherboard_analog_output/AO1_COM'
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def pieces(s):
 if s.is_empty:return[]
 if s.geom_type=='Polygon':return[s]
 return[p for x in getattr(s,'geoms',[])for p in pieces(x)]
def sites(s,desired,limit=40):
 rows=[]
 for p in pieces(s):
  a=p.representative_point();z=nearest_points(p,Point(desired))[0]
  for pt in(a,z,Point((a.x+z.x)/2,(a.y+z.y)/2)):
   at=[round(pt.x,6),round(pt.y,6)]
   if s.covers(Point(at))and all(math.dist(at,r)>.015 for r in rows):rows.append(at)
 return sorted(rows,key=lambda r:math.dist(r,desired))[:limit]
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,v=None):
  p=Path(p);s=sha(p);assert v is None or s==v;pins[str(p.resolve())]=s;return p
 mp=pin(H/'DI6-twelve-NEW-exact-current-normal-antipads-r578/model.pkl','cfe6fcbc3e13360edb56916f18a9a88038e84a8841e2e0f8e5faf93ea3399793');g,h,b,q,c=pickle.loads(mp.read_bytes());MS.restore_bound_field_current_precision_states(b,q);cp=pin(H/'AO1-COM-actual-full-native-current-source-and-two-residual-port-binding-r622/exact_actual_current_AO1_COM_source_and_ports_NOMINATION_ONLY.pkl','02e9ea37628b2dba138d1e57514a390f1c4419ef3ca8c66ed6f2653eecb6b72b');census=pickle.loads(cp.read_bytes());reference=census['references']['In1.Cu'];reference4=census['references']['In4.Cu'];native=census['native_refs']['In1.Cu'];root=census['current_root'];sourcefile=pin(P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb','eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a');identity=K.A.N.SourceNets(sourcefile.read_bytes());original=K.C.inventory(sourcefile.read_bytes())[3]
 sourcepad=next(p for p in h['pads']if p['uuid']=='5bd36a6a-0ece-4d8a-bb54-e362786d2249');targetpad=next(p for p in h['pads']if p['uuid']=='6cc6e8f2-29a9-482e-a9b7-c53dea062394');assert(sourcepad['ref'],str(sourcepad['num']),K.L.norm(sourcepad['net']))==('U14626','7',NET);assert(targetpad['ref'],str(targetpad['num']),K.L.norm(targetpad['net']))==('R14633','1',NET);start=[sourcepad['x'],sourcepad['y']];end=[targetpad['x'],targetpad['y']];win=box(368,121,389,154);reference=reference.intersection(win.buffer(2));reference4=reference4.intersection(win.buffer(2));peertracks=[];peervias=[]
 for peer in census['VREF_four_hard_peer_items']:
  if peer['kind']=='segment':peertracks.append({'uuid':peer['uuid'],'net':peer['net'],'layer':peer['layer'],'a':peer['a'],'b':peer['b'],'w':peer['w']})
  else:assert peer['kind']=='via';peervias.append({'uuid':peer['uuid'],'net':peer['net'],'x':peer['at'][0],'y':peer['at'][1],'d':peer['d'],'drill':peer['drill'],'flashed':list(K.LAYERS)})
 planner_h={**h,'tracks':h['tracks']+peertracks,'vias':h['vias']+peervias};rec,trees=K.F.build({**planner_h,'zones':[]});dom=h['domains_normalized'];gap=lambda a,n:.15 if dom[K.L.norm(a)]==dom[K.L.norm(n)]else .6;holes,ht=K.hole_context(planner_h);owners=[(K.L.norm(v['net']),False)for v in planner_h['vias']]+[(K.L.norm(p['net']),p['npth'])for p in h['pads']for s in K.L.poly(p.get('hole')or[])];assert len(owners)==len(holes);localholes=[(s,o)for s,o in zip(holes,owners)if not s.envelope.disjoint(win.buffer(1))];smd=[s for p in h['pads']if p['smd']for ly,rs in p['layers'].items()if ly in('F.Cu','B.Cu')for s in K.L.poly(rs)if not s.envelope.disjoint(win.buffer(1))];reservation,exempt=K.A.reservations();peerfile=pin(P/'field-power/R157-actual-rooted-old-barrel-minimal-local-ground-landing-nominees-r665/only-source-rooted-existing-barrel-local-ground-landing-proposals-NOT_MODEL.pkl');peer=pickle.loads(peerfile.read_bytes());held=[z for z in peer if not z['shape'].envelope.disjoint(win.buffer(1))];nzone=[]
 for z in c['zones']:
  for ly,rs in z['fills'].items():nzone.extend((z,ly,s)for s in K.L.poly(rs)if not s.envelope.disjoint(win.buffer(1)))
 free={};vr={}
 for net in(NET,LG):
  va=[]
  for ly in K.LAYERS:
   ta=[];vobs=[]
   for i in trees[ly].query(win.buffer(1),predicate='intersects'):
    r=rec[ly][int(i)]
    if K.L.norm(r['net'])==net:continue
    req=gap(r['net'],net)+.025;shape=r['shape'].intersection(win.buffer(1));ta.append(K.Z.bounded_buffer(shape,req+.105));vobs.append(K.Z.bounded_buffer(shape,req+.255))
   for z,layer,sh in nzone:
    if layer!=ly or K.L.norm(z['net'])==net:continue
    if z['uuid']in original and gap(z['net'],net)==.15:continue
    req=max(float(z['clearance_mm']),gap(z['net'],net))+.025;sh=sh.intersection(win.buffer(1));ta.append(K.Z.bounded_buffer(sh,req+.105));vobs.append(K.Z.bounded_buffer(sh,req+.255))
   for z in q+held:
    if z['layer']!=ly or K.L.norm(z['net'])==net:continue
    req=max(float(z['clearance_mm']),gap(z['net'],net))+.025
    for role in('shape','zone_outline_shape'):
     sh=z[role].intersection(win.buffer(1));ta.append(K.Z.bounded_buffer(sh,req+.105));vobs.append(K.Z.bounded_buffer(sh,req+.255))
   for area in h['rule_areas']:
    if ly not in area['layers']:continue
    for sh in K.L.poly(area['outline']):
     if area.get('no_tracks'):ta.append(K.Z.bounded_buffer(sh,.130))
     if area.get('no_vias'):vobs.append(K.Z.bounded_buffer(sh,.280))
   for area in reservation['keepouts']:
    if ly in area['layers']and net not in exempt.get(area['name'],set()):
     for sh in K.L.poly(area['outline']):ta.append(K.Z.bounded_buffer(sh,.130));vobs.append(K.Z.bounded_buffer(sh,.280))
   ta.extend(K.Z.bounded_buffer(sh,.385)for sh,o in localholes if o[0]!=net or o[1]);vobs.extend(K.Z.bounded_buffer(sh,.385)for sh,o in localholes);free[net,ly]=win.difference(unary_union(ta));va.extend(vobs)
  va.extend(K.Z.bounded_disk(v,.815)for v in planner_h['vias']if not Point(v['x'],v['y']).envelope.disjoint(win.buffer(1)));va.extend(K.Z.bounded_buffer(sh,.385)for sh in smd);vr[net]=win.difference(unary_union(va));print('R624_REGIONS',net,vr[net].area,flush=True)
 refsafe=reference.intersection(win.buffer(1)).buffer(-.105);ff=free[NET,'F.Cu'].intersection(refsafe);inner=free[NET,'In3.Cu'].intersection(reference4.intersection(win.buffer(1)).buffer(-.105));bb=free[NET,'B.Cu'].intersection(reference4.intersection(win.buffer(1)).buffer(-.105));fcsource=[s for s in pieces(ff)if s.covers(Point(start))];fctarget=[s for s in pieces(bb)if s.covers(Point(end))];sourceSites=vr[NET].intersection(unary_union(fcsource));targetSites=vr[NET].intersection(unary_union(fctarget));retRegion=vr[LG].intersection(reference).intersection(reference4);cache=OUT/'bounded-current-native-host-source-free-regions-NOMINATION_ONLY.pkl';cache.write_bytes(pickle.dumps({'free':free,'via':vr,'ff':ff,'inner':inner,'sourceSites':sourceSites,'targetSites':targetSites,'retRegion':retRegion,'reference':reference},protocol=5));print('R624_ENDPOINTS',len(fcsource),len(fctarget),sourceSites.area,targetSites.area,'returns',retRegion.area,flush=True)
 sourceOptions=[];targetOptions=[]
 for region,desired,choices in((sourceSites,[374.05,127.8],sourceOptions),(targetSites,[381.3,145.0],targetOptions)):
  for at in sites(region,desired,60):
   ring=Point(at).buffer(.999,quad_segs=128).difference(Point(at).buffer(.901,quad_segs=128));rr=sites(retRegion.intersection(ring),[at[0]+.925,at[1]],8)
   rr=[r for r in rr if .9<=math.dist(at,r)<=1 and all(Point(r).buffer(.225,quad_segs=128).difference(Point(r).buffer(.125,quad_segs=128)).intersection(ref).area>.005 for ref in(reference,reference4))]
   if rr:choices.append({'signal':at,'returns':rr})
 put(OUT/'source-and-target-continuous-ordinary-pair-options.json',{'source':sourceOptions,'target':targetOptions});attempts=[];selected=None
 for a in sourceOptions[:15]:
  for z in targetOptions[:15]:
   for ar in a['returns'][:3]:
    for zr in z['returns'][:3]:
     disks=unary_union([K.Z.bounded_buffer(Point(x),.630)for x in(ar,zr)]);paths=[];row={'source_signal':a['signal'],'source_return':ar,'target_signal':z['signal'],'target_return':zr,'paths':paths};attempts.append(row)
     for ly,p1,p2,free1 in(('F.Cu',start,a['signal'],ff),('In3.Cu',a['signal'],z['signal'],inner),('B.Cu',z['signal'],end,bb)):
      cs=[s for s in pieces(free1.difference(disks))if s.covers(Point(p1))and s.covers(Point(p2))]
      if not cs:break
      pts,search=T.route(cs[0],tuple(p1),tuple(p2));pts=[[round(x,6),round(y,6)]for x,y in pts]
      if len(pts)<2 or not cs[0].covers(LineString(pts)):break
      paths.append({'layer':ly,'points_mm':pts,'width_mm':.2,'search':search,'length_mm':LineString(pts).length})
     if len(paths)==3:selected=row;break
    if selected:break
   if selected:break
  if selected:break
 put(OUT/'finite-continuous-three-leg-path-attempts.json',attempts);nt=[];nv=[];chunks={}
 if selected:
  for path in selected['paths']:
   for a,z in zip(path['points_mm'],path['points_mm'][1:]):
    uid,ch=identity.serial_segment(NET,path['layer'],a,z,.2);chunks[uid]=ch;nt.append({'uuid':uid,'net':identity.raw(NET),'layer':path['layer'],'w':.2,'a':a,'b':z})
  for net,at in((NET,selected['source_signal']),(NET,selected['target_signal']),(LG,selected['source_return']),(LG,selected['target_return'])):
   uid,ch=SERIAL.serial_via(identity,net,at);chunks[uid]=ch;nv.append({'uuid':uid,'net':identity.raw(net),'x':at[0],'y':at[1],'d':.5,'drill':.2,'flashed':list(K.LAYERS)})
  identity.assert_chunks(chunks);assert set(chunks).isdisjoint(original);print('R624_POSITIVE',selected['source_signal'],selected['target_signal'],len(nt),flush=True)
 packet=OUT/'only-NEW-AO1-DAC-CS-three-leg-two-ordinary-pair-NOMINEE.pkl';packet.write_bytes(pickle.dumps({'tracks':nt,'vias':nv,'exact_new_chunks':chunks,'original_deletes':{},'selected':selected,'reference_layers':['In1.Cu','In4.Cu'],'used_leg_layers':['F.Cu','In3.Cu','B.Cu']},protocol=5));result={'verdict':'CURRENT_AO1_DAC_CS_CONTINUOUS_THREE_LEG_PAIRED_CONSTRUCTOR_POSITIVE_INDEPENDENT_GATES_OPEN'if selected else'CURRENT_AO1_DAC_CS_CONTINUOUS_SOURCE_TARGET_PAIR_OR_TRANSPORT_BOUNDED_INCOMPLETE','current_model_SHA256':sha(mp),'actual_R622_native_and_current_AO1_COM_refs_SHA256':sha(cp),'selected':selected,'source_pair_options':len(sourceOptions),'target_pair_options':len(targetOptions),'exact_sparse_packet_file':str(packet.resolve()),'exact_sparse_packet_SHA256':sha(packet),'all_original_current_power_fault_and_peer_Cu_fixed':True,'native_job_board_or_source_changes':0,'max_signal_layer_legs':3,'ordinary_signal_return_window_mm':[.9,1.0],'source_reference_root_selector':['U14619','7'],'reference_clipped_to_local_window_plus_2mm_all_used_bodies_inside':True,'VREF_four_prospective_items_HARD_only_not_reference_credit':True,'real_source_connected_both_In1_In4_returns_no_generic_plane_waiver':True,'all_native_and_current_new_physical_holes_root_oldcontacts_zero_oldref_newbodies_SI_current_qualification':'OPEN','input_SHA256':pins,'adopted':False,'elapsed_seconds':time.monotonic()-st};put(OUT/'receipt.json',result);print('R624_COMPLETE',sha(OUT/'receipt.json'),result['verdict'],flush=True)
if __name__=='__main__':main()
