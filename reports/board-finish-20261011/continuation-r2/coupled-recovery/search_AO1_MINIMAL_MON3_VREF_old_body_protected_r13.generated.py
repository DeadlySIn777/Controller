"""Joint finite port search: three locked MON segments and only-new VREF."""
from pathlib import Path
import sys,json,pickle,hashlib,time,math
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in(H,ROOT/'field-power',ROOT/'sbc-power'):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import audit_ao1_positive_operation_r4 as SERIAL
import tri_route as T
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
OUT=H/'AO1-joint-MON3-VREF-port-all-retained-old-source-bodies-protected-r13'
MON='/motherboard_analog_output/AO1_MON_12V';VREF='/motherboard_analog_output/AO1_VREF';COM='/motherboard_analog_output/AO1_COM'
DELS={'6b5d7465-3e16-4492-82be-cd9ae2fb2ad5','e0c09d60-50a7-411e-9a56-ce39e23f1bff','16ac4bda-32bd-47a3-8cc4-404758a78d41'}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,o):(OUT/n).write_text(json.dumps(o,indent=1,allow_nan=False)+'\n')
def parts(s):
 if s.is_empty:return[]
 if s.geom_type=='Polygon':return[s]
 return[p for g in s.geoms for p in parts(g)]if hasattr(s,'geoms')else[]
def sites(s,desired,limit=144):
 rows=[]
 for p in parts(s):
  a=p.representative_point();b=nearest_points(p,Point(desired))[0]
  for q in(a,b,Point((a.x+b.x)/2,(a.y+b.y)/2)):
   at=[round(q.x,6),round(q.y,6)]
   if p.covers(Point(at))and all(math.dist(at,z)>.015 for z in rows):rows.append(at)
 return sorted(rows,key=lambda p:math.dist(p,desired))[:limit]
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,s=None):
  p=Path(p);v=sha(p);assert s is None or v==s;pins[str(p.resolve())]=v;return p
 rr=pin(H/'AO1-MON-three-locked-segment-counterfactual-VREF-port-r9/receipt.json');r=json.loads(rr.read_bytes());cf=pin(rr.parent/'exact-current-Cu-continuous-source-only-regions.pkl',r['region_cache_SHA256']);data=pickle.loads(cf.read_bytes());refs=data['source_refs'];sourcefree=data['sourcefree'];sgregion=data['signalregion'];retregion=data['returnregion'];cp=pin(H/'AO1-saved-four-add-exact-current-native-screen-r1/pinned-current-local-Cu-native-before-source-only-screen.pkl','0349ddad81a9dc6dd0ef106c3a65ce03e0ff44ae3d04244e882bbe0475590a2e');ctx=pickle.loads(cp.read_bytes());c=ctx['full_before'];win=ctx['win'];local=ctx['current'];local={**local,'tracks':[t for t in local['tracks']if t['uuid']not in DELS]};records,trees=K.F.build(local);dom=c['domains_normalized'];req=lambda a,b:.15 if dom[K.L.norm(a)]==dom[K.L.norm(b)]else .6;obs=[]
 for row in records['F.Cu']:
  if K.L.norm(row['net'])!=MON:obs.append(K.Z.bounded_buffer(row['shape'],req(MON,row['net'])+.125010))
 for z in c['zones']:
  if K.L.norm(z['net'])==MON or req(MON,z['net'])==.15:continue
  for s in K.L.poly(z['fills'].get('F.Cu',[])):
   if not s.envelope.disjoint(win.buffer(1)):obs.append(K.Z.bounded_buffer(s.intersection(win.buffer(1)),max(z['clearance_mm'],req(MON,z['net']))+.125010))
 reserve,exempt=K.A.reservations()
 for rule in c['rule_areas']:
  if 'F.Cu'in rule['layers']and rule.get('no_tracks'):obs.extend(K.Z.bounded_buffer(s,.130)for s in K.L.poly(rule['outline'])if not s.envelope.disjoint(win.buffer(1)))
 for rule in reserve['keepouts']:
  if 'F.Cu'in rule['layers']and MON not in exempt.get(rule['name'],set()):obs.extend(K.Z.bounded_buffer(s,.130)for s in K.L.poly(rule['outline'])if not s.envelope.disjoint(win.buffer(1)))
 obs.extend(K.Z.bounded_disk(v,v['drill']/2+.375005)for v in local['vias']if K.L.norm(v['net'])!=MON);obs.extend(K.Z.bounded_buffer(s,.375005)for p in local['pads']for s in K.L.poly(p.get('hole')or[])if K.L.norm(p['net'])!=MON or p['npth']);monfree=win.difference(unary_union(obs)).intersection(refs['In1.Cu'].buffer(-.100005));start=[369.35,125.15];end=[374.55,130.049999];ep=[375.498,129.0];ats=[]
 oldrefprotected=[];protected=[]
 radius=max(float(z['clearance_mm']) for z in c['zones']if K.L.norm(z['net'])==COM)+.25+.000005
 for t in c['tracks']:
  ly=t['layer'];net=K.L.norm(t['net'])
  if t['uuid']in DELS or net==COM or c['domains_normalized'].get(net)!=c['domains_normalized'][COM]or ly not in K.MAP:continue
  body=K.L.body(t)
  if body.envelope.disjoint(win.buffer(1)):continue
  covered=body.intersection(refs[K.MAP[ly]])
  if covered.is_empty:continue
  obstacle=K.Z.bounded_buffer(covered,radius);protected.append(obstacle);oldrefprotected.append({'old_UUID':t['uuid'],'raw_net':t['net'],'body_layer':ly,'SOURCE_reference_layer':K.MAP[ly],'native_normal_new_SG_cut_radius_with_guard_mm':radius,'covered_body_WKB_SHA256':hashlib.sha256(covered.wkb).hexdigest(),'protected_obstacle_WKB_SHA256':hashlib.sha256(obstacle.wkb).hexdigest()})
 beforeports=sgregion;sgregion=sgregion.difference(unary_union(protected));put('all-current-retained-old-SOURCE-body-new-SG-antipad-port-protection.json',oldrefprotected)
 put('old-source-body-protected-port-summary.json',{'protected_body_count':len(oldrefprotected),'before_area_mm2':beforeports.area,'after_area_mm2':sgregion.area,'original_5V_b17752d1_raw_R12_loss_held_mm2':.011436208194387076,'old_SOURCE_contact_or_area_threshold_waivers':0})

 for desired in([372.8,130.5],[373.7,131.3],[376.6,129]):
  for at in sites(sgregion,desired):
   if all(math.dist(at,q)>.015 for q in ats):ats.append(at)
 print('AO1_R13_JOINT_SIGNAL_SITES',len(ats),flush=True);attempts=[];chosen=None
 for at in ats:
  ring=Point(at).buffer(.999,quad_segs=128).difference(Point(at).buffer(.901,quad_segs=128));rr=retregion.intersection(ring);rts=[]
  for desired in([at[0]-.95,at[1]],[at[0],at[1]+.95],[at[0]+.95,at[1]]):
   for rt in sites(rr,desired,18):
    if all(math.dist(rt,q)>.015 for q in rts):rts.append(rt)
  for rt in rts:
   if not .90<=math.dist(at,rt)<=1:continue
   returnob=K.Z.bounded_buffer(Point(rt),.625010);paths=[];trial={'signal_at_mm':at,'return_at_mm':rt,'distance_mm':math.dist(at,rt),'paths':paths};attempts.append(trial)
   for ly in('F.Cu','B.Cu'):
    ff=sourcefree[ly].difference(returnob);cc=[p for p in parts(ff)if p.covers(Point(ep))and p.covers(Point(at))]
    if not cc:break
    pts,search=T.route(cc[0],ep,at);pts=[[round(x,6),round(y,6)]for x,y in pts]
    if len(pts)<2 or not cc[0].covers(LineString(pts)):break
    paths.append({'layer':ly,'points_mm':pts,'width_mm':.2,'search':search,'length_mm':LineString(pts).length})
   if len(paths)!=2:continue
   cutters=[K.Z.bounded_buffer(LineString(paths[0]['points_mm']),.375010),K.Z.bounded_buffer(Point(at),.625010),K.Z.bounded_buffer(Point(rt),.525010)];mf=monfree.difference(unary_union(cutters));mc=[p for p in parts(mf)if p.covers(Point(start))and p.covers(Point(end))]
   trial['MON_common_components']=len(mc)
   if not mc:continue
   pts,search=T.route(mc[0],start,end);pts=[[round(x,6),round(y,6)]for x,y in pts]
   if len(pts)<2 or not mc[0].covers(LineString(pts)):continue
   trial['MON_detour']={'layer':'F.Cu','points_mm':pts,'width_mm':.2,'locked_yes':True,'length_mm':LineString(pts).length,'search':search};chosen=trial;break
  if chosen:break
  put('progress.json',{'checked_signal_sites':ats.index(at)+1,'signal_sites':len(ats),'attempts':len(attempts),'elapsed_seconds':time.monotonic()-st})
 put('joint-current-port-and-monitor-attempts.json',attempts);sp=pin(ROOT/'field-power/FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753/FIELD-ROOT-Q0-DIC-DI6-known-failure-diagnostic.kicad_pcb','7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2');ident=K.A.N.SourceNets(sp.read_bytes());native=K.C.inventory(sp.read_bytes())[3];nt=[];nv=[];chunks={};deleted={}
 if chosen:
  for path in chosen['paths']+[chosen['MON_detour']]:
   net=MON if path.get('locked_yes')else VREF
   for a,b in zip(path['points_mm'],path['points_mm'][1:]):
    uid,ch=ident.serial_segment(net,path['layer'],a,b,.2)
    if net==MON:ch=ch.replace(b'\t\t(layer ',b'\t\t(locked yes)\n\t\t(layer ');assert b'(locked yes)'in ch
    chunks[uid]=ch;nt.append({'uuid':uid,'net':ident.raw(net),'layer':path['layer'],'a':a,'b':b,'w':.2,'locked_yes':net==MON})
  for net,at in((VREF,chosen['signal_at_mm']),(COM,chosen['return_at_mm'])):
   uid,ch=SERIAL.serial_via(ident,net,at);chunks[uid]=ch;nv.append({'uuid':uid,'net':ident.raw(net),'x':at[0],'y':at[1],'d':.5,'drill':.2,'flashed':list(K.LAYERS)})
  deleted={u:native[u]for u in sorted(DELS)}
  for uid,ch in deleted.items():
   p=K.A.G.parse(uid,ch,{});assert p['net']==MON and p['layer']=='F.Cu'and p['w']==.2 and b'(locked yes)'in ch
  ident.assert_chunks(chunks);assert set(chunks).isdisjoint(native)
 packet=OUT/'ONLY_NEW_VREF-and-MON3-exact-locked-endpoint-detour-NOMINEE.pkl';packet.write_bytes(pickle.dumps({'tracks':nt,'vias':nv,'exact_new_chunks':chunks,'deleted_original_chunks':deleted,'selected':chosen},protocol=5));cache=OUT/'exact-current-coupled-prospective-reference-inputs.pkl';cache.write_bytes(pickle.dumps({'actual_full_before':c,'current_local_minus_MON3':local,'source_refs':refs,'MON_baseline_free':monfree,'VREF_guard_regions':data},protocol=5));result={'verdict':'CONSTRUCTIVE_MINIMAL_OWNED_MON3_AND_ONLY_NEW_VREF_CURRENT_COUPLED_NOMINEE'if chosen else'BOUNDED_JOINT_MON3_VREF_ALL_PORT_ATTEMPTS_NO_COUPLED_PATH','selected':chosen,'signal_site_count':len(ats),'attempts':len(attempts),'new_tracks':len(nt),'new_vias':len(nv),'original_owned_Mon3_replaced':sorted(deleted),'all_original_SDI_5V_and_other_Cu_preserved':True,'packet_file':str(packet.resolve()),'packet_SHA256':sha(packet),'context_cache_SHA256':sha(cache),'all_source_old_contacts_refs_true_caps_native_current_analog_SI_gates':'OPEN','every_retained_old_source_body_now_protected_from_new_SG_native_antipad':True,'raw_R12_real_5V_loss_preserved':True,'native_jobs':0,'adopted':False,'input_SHA256':pins,'elapsed_seconds':time.monotonic()-st};put('receipt.json',result);print(json.dumps({k:result[k]for k in('verdict','signal_site_count','attempts','new_tracks','new_vias','selected','elapsed_seconds')}),flush=True)
if __name__=='__main__':main()
