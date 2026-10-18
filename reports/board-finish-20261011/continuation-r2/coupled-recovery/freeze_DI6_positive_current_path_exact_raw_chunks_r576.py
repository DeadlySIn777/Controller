"""Close R574 saved positive constructor without rerunning search.

Correct only the serializer API call. All earlier raw failures and the
prospective target own-aperture scope remain separate and unqualified.
"""
from pathlib import Path
import sys,json,pickle,hashlib,math,time
H=Path(__file__).resolve().parent;P=H.parent
for d in(P,P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import audit_ao1_positive_operation_r4 as SERIAL
from shapely.geometry import Point,LineString
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
OUT=H/'DI6-positive-current-path-exact-raw-owned-chunks-r576'
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,s=None):
  p=Path(p);v=sha(p);assert s is None or s==v;pins[str(p.resolve())]=v;return p
 src=pin(H/'construct_DI6_actual_retained_target_NEW_only_r574.py','f843c99273265d4f0b70cf0960d3a5d0a1c7aac98831c2a75f352e8f45e96d6d');R=H/'DI6-actual-retained-target-NEW-only-policy-constructor-r574';cf=pin(R/'bounded-reference-native-owned-regions-NOMINATION_ONLY.pkl');af=pin(R/'finite-continuous-candidate-path-attempts.json');cache=pickle.loads(cf.read_bytes());attempts=json.loads(af.read_bytes());selected=next(z for z in attempts if len(z['paths'])==2);assert selected['signal_at_mm']==[117.966083,102.840819]and selected['return_at_mm']==[117.065348,102.819051]and .9<=selected['distance_mm']<=1.0
 mp=pin(H/'DIC-retired-cutter-policy-coupled-current-r556/model.pkl','95d1636e90b8d11530cbc6ba461c60f7e68272e08d1e7cd4b5863bf0a43b46d5');sp=pin(P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb','eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a');source=sp.read_bytes();native=K.C.inventory(source)[3];identity=K.A.N.SourceNets(source);g,h,b,q,c=pickle.loads(mp.read_bytes());existing={v['uuid']for v in h['tracks']+h['vias']};NET='/motherboard_di/DI6_LOGIC';LG='/LOGIC_GND';tracks=[];vias=[];chunks={};newrows=[]
 retob=K.Z.bounded_buffer(Point(selected['return_at_mm']),.630)
 for path in selected['paths']:
  assert path['layer']in('F.Cu','In3.Cu')and path['width_mm']==.2;free=cache['ff'if path['layer']=='F.Cu'else'ii'].difference(retob);assert free.covers(LineString(path['points_mm']))
  for a,bb in zip(path['points_mm'],path['points_mm'][1:]):
   uid,ch=identity.serial_segment(NET,path['layer'],a,bb,.2);p=K.A.G.parse(uid,ch,{});assert(p['kind'],p['net'],p['layer'],p['w'],p['a'],p['b'])==('segment',NET,path['layer'],.2,a,bb);chunks[uid]=ch;tracks.append({'uuid':uid,'net':identity.raw(NET),'layer':path['layer'],'w':.2,'a':a,'b':bb})
 for net,at,uid in((NET,selected['signal_at_mm'],'65920d23-af51-5551-a4a2-bc8273927a44'),(LG,selected['return_at_mm'],'eea4f681-f21b-5b3a-a1af-7c6ba82e51a1')):
  assert cache['viaregions'][net].covers(Point(at));old,ch=SERIAL.serial_via(identity,net,at);assert ch.count(old.encode())==1;ch=ch.replace(old.encode(),uid.encode());p=K.A.G.parse(uid,ch,{});assert(p['kind'],p['net'],p['at'],p['d'],p['drill'])==('via',net,at,.5,.2);assert not any(t in ch for t in(b'remove_unused_layers',b'keep_end_layers',b'zone_connection'));chunks[uid]=ch;vias.append({'uuid':uid,'net':identity.raw(net),'x':at[0],'y':at[1],'d':.5,'drill':.2,'flashed':list(K.LAYERS)})
 identity.assert_chunks(chunks);assert set(chunks).isdisjoint(native)and set(chunks).isdisjoint(existing);assert len(tracks)==10 and len(vias)==2
 for uid,ch in sorted(chunks.items()):
  f=OUT/(uid+'.chunk');f.write_bytes(ch);p=K.A.G.parse(uid,ch,{});newrows.append({'UUID':uid,'kind':p['kind'],'raw_native_net_token':identity.raw(p['net']),'file':str(f.resolve()),'SHA256':sha(f)})
 targetscope=pin(R/'exact-existing-native-target-own-aperture-nomination-scope.json');put(OUT/'R574-preserved-serializer-reader-failure.json',{'source_file':str(src.resolve()),'source_SHA256':sha(src),'failure':'AttributeError SERIAL.serial_track; actual established API is SourceNets.serial_segment. Error was after saving positive exact regions and paths, before any model/board/chunk emission.','search_not_rerun':True,'original_R574_files_unchanged':True})
 packet=OUT/'only-twelve-NEW-DI6-discrete-items-NOMINEE.pkl';packet.write_bytes(pickle.dumps({'tracks':tracks,'vias':vias,'exact_new_chunks':chunks,'exact_original_deletes':{},'source_current_parent_SHA256':sha(mp),'source_own_target_scope_file':str(targetscope.resolve()),'selected':selected,'required_all6_native_NEW_annuli':True,'no_original583bf_drill_restore':True},protocol=5));pin(Path(__file__));pin(Path(SERIAL.__file__))
 for p in R.iterdir():
  if p.is_file():pin(p)
 receipt={'verdict':'CONCRETE_NEW_ONLY_DI6_CURRENT_PORT_POLICY_PAIR_ROUTE_CONSTRUCTOR_COMPLETE_FULL_INDEPENDENT_GATES_OPEN','exact_current_parent_model_SHA256':sha(mp),'source_eedf_SHA256':sha(sp),'positive_R574_path_checkpoint_SHA256':sha(af),'bounded_geometry_checkpoint_SHA256':sha(cf),'sparse_packet_file':str(packet.resolve()),'sparse_packet_SHA256':sha(packet),'exact_new_chunk_rows':newrows,'only_NEW_tracks':10,'only_NEW_ordinary_vias':2,'ordinary_source_pair':{'signal_at_mm':selected['signal_at_mm'],'return_at_mm':selected['return_at_mm'],'distance_mm':math.dist(selected['signal_at_mm'],selected['return_at_mm']),'saved_hard_window_mm':[.9,1.0]},'layer_legs':2,'source_attachment':{'native_U13001_pin12_UUID':'8cb51ce7-ffcc-432a-90f1-6f2c2e13b06f','first_point_mm':[119.176252,97.39558],'actual_current_drilled_contact':'OPEN'},'retained_target':{'native_signal_UUID':'0ff4e506-7bc1-48ad-91fd-aeb598e74c7a','actual_native_In3_track_UUID':'3a0b46f2-c120-45e5-b93f-8d687e955639','at_mm':[113.95,119.35],'retained_native_return_UUID':'cb1390c8-49e9-4971-9ee8-740c03e5b93f','native_own_disk_radius_mm':.575,'used_In4_actual_source_and_exact_native_own_void_fullbody_support':'OPEN; separate current qualification mandatory','In1_target_credit':False},'R665_landing_proposals_as_hard_only_geometry_count':len(cache['heldpeer']),'all_original_native_current_Cu_masks_flags_power_zone_roles_FP_source_rules_untouched':True,'R14_bad.836_pair_R27_remoteMOTION210nm_and_current_inherited_failures_preserved':True,'fresh_all83_relationships_direct_all_drill_tenroots_strict_oldref_newbody_truecaps_holes_SMD_native_minfeature_SI_current':'OPEN','native_jobs':0,'board_source_project_written':False,'adopted':False,'input_SHA256':pins,'elapsed_seconds':time.monotonic()-st};put(OUT/'receipt.json',receipt);print('R576_COMPLETE',sha(OUT/'receipt.json'),sha(packet),flush=True)
if __name__=='__main__':main()
