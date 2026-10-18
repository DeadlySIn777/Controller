"""Exact full-width CORE5 detour and a no-hole T4→T1 ground join.

Every original shared contact is ledgered. Geometry nomination alone never
sets source/reference/current/native gates true. R7 remains separate.
"""
import hashlib,json,pickle,sys,uuid,traceback,copy
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
for d in('sbc-power','field-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as GP
import restore_SAFE_generated_precision_states_r168 as PS
O=H/'sbc-power/T4-duplicate-CORE5-fullwidth-detour-nominee-r255'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.wkb).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1)+'\n')
def main():
 assert not O.exists();O.mkdir();mp=H/'coupled-recovery/CORE-R112-per-polygon-immutable-owned-construction-r246/model.pkl';assert sha(mp)=='32b60c225aa42347e3739c41d297c0f6047ee87978b42270958678fc6b51e685';g,h,b,z,c=pickle.loads(mp.read_bytes());replay=PS.restore_bound_generated_precision_states(b,z);removed={'abcf41c9-701e-4b18-87b4-146cd5fd51b4','d825eb25-c4d4-4ac0-ae26-ea3a0c1eeeb0'};old=[t for t in h['tracks']if t['uuid']in removed];assert len(old)==2;assert all((t['net'],t['layer'],t['w'],t['a'],t['b'])==('/mc_local_power{slash}CORE_5V','F.Cu',1.25,[154.65,96.65],[167.75,96.65])for t in old)
 corepoints=[[154.65,96.65],[154.65,98.05],[167.75,98.05],[167.75,96.65]];groundpoints=[[157.69,95.677],[157.69,96.2],[155.75,96.2],[155.29,95.677]];adds=[]
 for role,net,w,points in [('CORE5-fullwidth',old[0]['net'],1.25,corepoints),('T4-to-real-T1','/LOGIC_GND',.2,groundpoints)]:
  for i,(a,bb)in enumerate(zip(points,points[1:])):adds.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'T4-R255:'+role+':'+str(i))),'net':net,'layer':'F.Cu','w':w,'a':a,'b':bb})
 oldbody=GP.bounded_buffer(LineString([old[0]['a'],old[0]['b']]),.625);corebody=unary_union([GP.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2)for t in adds if t['net']==old[0]['net']]);groundbody=unary_union([GP.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2)for t in adds if t['net']=='/LOGIC_GND']);current_h=copy.deepcopy(h);current_h['tracks']=[t for t in h['tracks']if t['uuid']not in removed]+adds;rec,trees=F.build({**current_h,'zones':[]});before,_=F.build(c,nets={C.norm(old[0]['net'])});checks=[];errors=[];contactrows=[]
 for r in before['F.Cu']:
  if r['uuid']in removed or not r['shape'].intersects(oldbody):continue
  touch=r['shape'].intersection(oldbody);aftertouch=r['shape'].intersection(corebody);contactrows.append({'kind':r['kind'],'UUID':r['uuid'],'raw_net':r['net'],'old_contact_mm2':touch.area,'new_contact_mm2':aftertouch.area,'whole_old_same_layer_piece_required_to_reconnect':True,'physical_piece_WKB_sha256':digest(r['shape'])})
 for t in adds:
  axis=LineString([t['a'],t['b']]);body=GP.bounded_buffer(axis,t['w']/2);novel=body.difference(oldbody)if t['net']==old[0]['net']else body
  for j in trees['F.Cu'].query(body.buffer(.8),predicate='intersects'):
   r=rec['F.Cu'][int(j)]
   if C.norm(r['net'])==C.norm(t['net']):continue
   if r['kind']=='track':tt=r['source'];gap=axis.distance(LineString([tt['a'],tt['b']]))-(t['w']+tt['w'])/2;target=GP.bounded_buffer(LineString([tt['a'],tt['b']]),tt['w']/2)
   elif r['kind']=='via':v=r['source'];gap=axis.distance(Point(v['x'],v['y']))-t['w']/2-v['d']/2;target=GP.bounded_disk(v,v['d']/2)
   else:gap=axis.distance(r['shape'])-t['w']/2;target=r['shape']
   req=GP.G.gap(h,t['net'],r['net'])+.025;novgap=novel.distance(target)if not novel.is_empty else float('inf');row={'kind':'new_true_F_Cu','UUID':t['uuid'],'raw_net':t['net'],'other_UUID':r['uuid'],'other_raw_net':r['net'],'full_body_gap_mm':gap,'required_mm':req,'added_only_geometry_gap_mm':novgap,'inherited_unchanged_original_CORE5_anchor_body_only':gap<req and novgap>=req};checks.append(row)
   if gap<req and novgap<req:errors.append(row)
  for q in z:
   if q['layer']!='F.Cu'or C.norm(q['net'])==C.norm(t['net']):continue
   req=max(q['clearance_mm'],GP.G.gap(h,t['net'],q['net']))+.025;gap=axis.distance(q['shape'])-t['w']/2;novgap=novel.distance(q['shape'])if not novel.is_empty else float('inf')
   if gap<req and novgap<req:errors.append({'kind':'owned_NEW_plane_conflict','UUID':t['uuid'],'other_UUID':q['uuid'],'other_net':q['net'],'gap_mm':gap,'added_only_gap_mm':novgap,'required_mm':req,'no_plane_carve_authorized_by_nomination':True})
  for v in h['vias']:
   if C.norm(v['net'])==C.norm(t['net']):continue
   p=Point(v['x'],v['y'])
   if p.distance(axis)>t['w']/2+v['drill']/2+.4:continue
   hole=GP.bounded_disk(v,v['drill']/2+.00000002);gap=body.distance(hole)-.005;novgap=novel.distance(hole)-.005
   if gap<.275 and novgap<.275:errors.append({'kind':'new_ordinary_foreign_drill_guard','UUID':t['uuid'],'other_UUID':v['uuid'],'gap_mm':gap,'added_only_gap_mm':novgap,'required_mm':.275})
 # Ground endpoints are literal pads; T1 is already connected through its
 # native ordinary barrel. The helper cannot grant a made-up return disk.
 p4=next(p for p in h['pads']if(p['ref'],p['num'])==('U1001','T4'));p1=next(p for p in h['pads']if(p['ref'],p['num'])==('U1001','T1'));assert p4['net']==p1['net']=='/LOGIC_GND';endpoint={'T4_pad':p4,'T1_pad':p1,'ground_tracks_actual_pad_touch_mm2':{p['num']:groundbody.intersection(unary_union(C.poly(p['layers']['F.Cu']))).area for p in(p4,p1)},'actual_T1_before_J1_membership_and_after_T4_source_full_graph_required':True}
 for sh in (oldbody,corebody,groundbody):assert sh.is_valid
 put(O/'checks.json',checks);put(O/'errors.json',errors);put(O/'all_original_shared_CORE5_contacts.json',contactrows);put(O/'literal-T4-T1-pad-endpoints.json',endpoint);put(O/'precision-restoration.json',replay);(O/'proposed-discrete.pkl').write_bytes(pickle.dumps({'tracks':adds,'vias':[],'removed_original_track_UUIDs':sorted(removed)},protocol=5));(O/'exact-parent-with-only-owned-track-nomination.pkl').write_bytes(pickle.dumps((g,current_h,b,z,c),protocol=5));put(O/'receipt.json',{'verdict':'SCOPED_TRUE_GEOMETRY_NOMINATION_CLEAR_PENDING_ALL_SHARED_CONTACTS_REFERENCE_CURRENT_NATIVE'if not errors else'REJECTED_SCOPED_T4_TRUNK_GROUND_DETOUR_NOMINATION_ERRORS_VISIBLE','exact_current_R246_model_sha256':sha(mp),'exact_two_duplicated_original_tracks':old,'only_removed_original_UUIDs':sorted(removed),'new_tracks':adds,'same_full_CORE5_width_mm':1.25,'original_length_mm':13.1,'detour_length_mm':LineString(corepoints).length,'ground_fullwidth_mm':.2,'ground_length_mm':LineString(groundpoints).length,'new_vias':0,'old_source_pad_local_and_actual_native_masks_unchanged':True,'checked_pairs':len(checks),'errors':len(errors),'old_shared_contacts_with_no_current_detour_touch':[r for r in contactrows if r['new_contact_mm2']==0],'all77_relationships_each_shared_oldtrack_piece_all_roots_strict_reference_addedpowerbody_0p8CORE_2AIO3_7p882CORE5_current_loop_voltage_native':'OPEN','R7_original_ground_obligation_NOT_hidden':True,'no_BGA_clearance_hole_or_width_rule_exception_added':True,'native_jobs':0,'board_written':False,'script_sha256':sha(__file__)})
 print('R255_COMPLETE',len(checks),len(errors),sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
