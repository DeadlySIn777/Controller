"""Exact sparse native packet with exact inner own guards; no adoption or refill."""
import json,pickle,hashlib,sys,re,copy,uuid,time,traceback
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import audit_aux_exact_raw as A
import guarded_power_projection_r44 as Z
import audit_ao1_positive_operation_r4 as SERIAL
D=H/'sbc-power/CM79-R369-one-positive-LG-nine-settings-exact-native-outline-profile-r371'
R=H/'sbc-power/CM79-R366-no-hole-IO3-plus-positive-J1-In4-support-fresh-current-independent-r369'
N=H/'sbc-power/CM79-R371-new-ordinary-pair-F-In3-actual-JD12-B3-source-reconnect-r397'
P=H/'sbc-power/CM79-R371-R7035-small-genuine-rigid-translation-old-terminal-stubs-new-ordinary-return-nomination-r385'
O=H/'sbc-power/CM79-R397-exact-five-tracks-three-ordinary-vias-R7035-real-pose-r398'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();assert sha(N/'receipt.json')=='58a2eee9785542ee284eb5e3fa35ba8b17c3452c9af528982cb5c9dd70139152';n=pickle.loads((N/'only-new-ordinary-pair-two-leg-R7035-ENC-source-reconnect.pkl').read_bytes());g,h,b,q,c=pickle.loads((D/'model.pkl').read_bytes());pose=n['R7035_pose_and_source_scope'];mm=pose['R7035'];scope=pose['scope'];pair=n['new_ordinary_SIG_LG_pair'];returns=json.loads((P/'only-return-sites-blocked-by-movable-R7035-own-pad-or-courtyard.json').read_text());ret=next(r for r in returns if r['new_LG_xy']==[83.675,23.877276]);gp=Point(*ret['new_LG_xy']);assert mm['court'].distance(gp)>=.275 and all(gp.distance(p['shape'])-.25>=.175 and gp.distance(p['shape'])-.1>=.28 for p in mm['pads']);source=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';raw=source.read_bytes();iv=A.C.inventory(raw);ident=A.N.SourceNets(raw);nt=[];path=pose['IO3_path']['path']
 for i,(a,bb)in enumerate(zip(path,path[1:])):nt.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'R398-R7035-IO3-source-stub:'+str(i))),'net':'/IO_3V3','layer':'F.Cu','w':.2,'a':list(a),'b':list(bb)})
 nt+=n['new_F_tracks']+n['new_lower_tracks'];assert len(nt)==5;adds={};nv=[]
 for net,xy in[(scope['source_pin_nets']['2'],pair['new_SIG_xy']),('/LOGIC_GND',pair['new_LG_xy']),('/LOGIC_GND',ret['new_LG_xy'])]:
  uid,ch=SERIAL.serial_via(ident,L.norm(net),xy);assert uid not in adds and uid not in iv[3];adds[uid]=ch;nv.append({'uuid':uid,'net':ident.raw(net),'x':xy[0],'y':xy[1],'d':.5,'drill':.2,'span':list(K.LAYERS),'flashed':list(K.LAYERS),'prospective_not_native':True,'mask_provenance':'NEW_ORDINARY_DEFAULT_REQUIRE_FRESH_NATIVE_ALL6_AFTERFILL'})
 fmt=lambda x:format(x,'.9f').rstrip('0').rstrip('.')
 for t in nt:
  t['net']=ident.raw(t['net']);ch=('\t(segment\n\t\t(start '+fmt(t['a'][0])+' '+fmt(t['a'][1])+')\n\t\t(end '+fmt(t['b'][0])+' '+fmt(t['b'][1])+')\n\t\t(width '+fmt(t['w'])+')\n\t\t(layer "'+t['layer']+'")\n\t\t(net "'+t['net']+'")\n\t\t(uuid "'+t['uuid']+'")\n\t)\n').encode();parsed=A.G.parse(t['uuid'],ch,{});assert(parsed['net'],parsed['layer'],parsed['a'],parsed['b'],parsed['w'])==(L.norm(t['net']),t['layer'],t['a'],t['b'],t['w']);assert t['uuid']not in adds and t['uuid']not in iv[3];adds[t['uuid']]=ch
 ident.assert_chunks(adds);originalFP=[(u,ch)for u,ch in iv[3].items()if A.C.pcbtext.chunk_kind(ch)=='footprint'and re.search(rb'\(property\s+"Reference"\s+"R7035"',ch)];assert len(originalFP)==1;fpuid,before=originalFP[0];ast=K.Q.parse(before.decode());oldAt=K.Q.child(ast,'at');oldpose=[float(x)for x in oldAt[1:]];oldpose+=[0]if len(oldpose)==2 else[];assert oldpose==[84.547,24.7,0];target=[81.147,27.7,180.0];match=re.search(rb'\(at\s+[^()]+\)',before);assert K.Q.parse(match.group().decode())==oldAt;after=before[:match.start()]+('(at '+' '.join(fmt(x)for x in target)+')').encode()+before[match.end():];newast=K.Q.parse(after.decode());revert=copy.deepcopy(newast);K.Q.child(revert,'at')[:]=oldAt;assert revert==ast
 groups=pickle.loads((R/'fresh-actual-drilled-changed-source-groups.pkl').read_bytes());lg=K.root(groups['/LOGIC_GND'],'J11001','2');refs={ly:unary_union([rr['shape']for rr in lg if rr['kind']=='fill'and rr['layer']==ly])for ly in('In1.Cu','In4.Cu')};sig=Point(*pair['new_SIG_xy']);groundHoles=unary_union([Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)for v in nv]);postRefs={ly:refs[ly].difference(sig.buffer(.5,quad_segs=128)).difference(groundHoles)for ly in refs};oldP=next(p for p in h['pads']if p['uuid']==n['exact_original_JD12_B3_pad_UUID']);ptGuard=unary_union(L.poly(oldP['layers']['In3.Cu'])).buffer(.275,quad_segs=128);sigGuard=sig.buffer(.525,quad_segs=128);ioGuard=Point(80.65,24.5).buffer(.575,quad_segs=128);oldHoles=unary_union([Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)for v in h['vias']]+[sh for p in h['pads']for sh in L.poly(p.get('hole')or[])]);bodyproof=[]
 for t in nt:
  actual=Z.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2).difference(unary_union([oldHoles,groundHoles]));guard=ioGuard if L.norm(t['net'])=='/IO_3V3'else unary_union([sigGuard,ptGuard])if t['layer']=='In3.Cu'else sigGuard;rlayer='In1.Cu'if t['layer']=='F.Cu'else'In4.Cu';gap=actual.difference(guard).difference(postRefs[rlayer]);fn=O/(t['uuid']+'-exact-inner-own-guards-body-reference-gap.wkb');fn.write_bytes(gap.wkb);bodyproof.append({'UUID':t['uuid'],'layer':t['layer'],'net':t['net'],'exact_inner_own_guards_reference_gap_EMPTY':gap.is_empty,'raw_gap_mm2':gap.area,'raw_gap_type':gap.geom_type,'raw_gap_sha256':sha(fn)})
 put(O/'all-five-body-reference-exact-inner-own-guard-proof.json',bodyproof);assert all(r['exact_inner_own_guards_reference_gap_EMPTY']for r in bodyproof)
 for mp in mm['pads']:assert mp['shape'].difference(postRefs['In1.Cu']).is_empty
 operations=[]
 for u,ch in adds.items():
  p=O/(u+'.native-chunk');p.write_bytes(ch);operations.append({'action':'add','uuid':u,'kind':A.C.pcbtext.chunk_kind(ch),'file':str(p.resolve()),'sha256':sha(p)})
 fbp=O/'R7035.exact-before-footprint-chunk';fap=O/'R7035.exact-rigid-after-footprint-chunk';fbp.write_bytes(before);fap.write_bytes(after);put(O/'exact-new-Cu-operation-ledger.json',operations);packet={'tracks':nt,'vias':nv,'original_native_Cu_deletes':[],'FP_UUID':fpuid,'ref':'R7035','original_root_mm_deg':oldpose,'target_root_mm_deg':target,'model_rigid_pose_degrees_dx_dy':[180,-3.4,3.0],'exact_FP_before_file':str(fbp.resolve()),'exact_FP_before_sha256':sha(fbp),'exact_FP_after_file':str(fap.resolve()),'exact_FP_after_sha256':sha(fap),'R7036_original_untouched':True,'R7035_source_scope':scope,'exact_JD12_B3_UUID':n['exact_original_JD12_B3_pad_UUID'],'new_SIG_source_own_cap_mm':.525,'existing_IO3_6007_own_cap_mm':.575,'existing_JD12_own_guard':'EXACT_ORIGINAL_RAW_PAD_SHAPE_BUFFER_275_INNER_FINITE_NO_Z_OUTWARD','ordinary_SIG_LG_pair':pair,'existing_IO33945_new_LG_return':ret,'source_refs_fresh_all_original_source_keys_oldrelationships_ref_losses_native_pose_all6_via_masks_afterfill_current_thermal':'OPEN'};(O/'exact-five-tracks-three-vias-R7035-pose-only-packet.pkl').write_bytes(pickle.dumps(packet,protocol=5));put(O/'receipt.json',{'verdict':'EXACT_SPARSE_NATIVE_PACKET_AND_INNER_OWN_GUARD_BODY_REFERENCE_PASS_FULLSOURCE_NATIVE_OPEN','R371_model_sha256':sha(D/'model.pkl'),'R397_receipt_sha256':sha(N/'receipt.json'),'packet_sha256':sha(O/'exact-five-tracks-three-vias-R7035-pose-only-packet.pkl'),'operation_ledger_sha256':sha(O/'exact-new-Cu-operation-ledger.json'),'new_tracks':5,'new_ordinary_vias':3,'original_track_or_via_deletes':0,'genuine_FP_root_pose_replacements':1,'all_local_FP_AST_value_nets_pad_UUIDs_geometry_source_contracts_exact':True,'R7036_original_pose_and_all_Cu_preserved':True,'all_five_exact_inner_terminal_guard_new_body_refs_PASS':True,'native_clone_pose_masks_source_refill_DRC_current_capacity_thermal':'OPEN','adopted':False,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R398',sha(O/'receipt.json'),sha(O/'exact-five-tracks-three-vias-R7035-pose-only-packet.pkl'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
