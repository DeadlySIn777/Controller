"""New load-port geography from actual right-anchor support; no port/path acceptance."""
import sys,json,pickle,time,hashlib,traceback
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
import physical_reference_losses_r3_zero_r208 as RF
K=N.K;L=N.L;sha=N.sha
B=H/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
S=H/'CORE5-current-new-transport-full1p25-In3-real-LGIn4-screen-r295'
O=H/'sbc-power/CORE5-actual-right-anchor-new-F-spur-load-port-LG4-component-attribution-r409'
NET='/mc_local_power/CORE_5V';LG='/LOGIC_GND'
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def ds(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'WKB_sha256':hashlib.sha256(s.wkb).hexdigest(),'bounds':list(s.bounds)if not s.is_empty else None}
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();N.assert_R157_actual_before();g,h,b,q,c=pickle.loads(B.read_bytes());native=json.loads((N.R157/'actual-full-refill-geometry.json').read_bytes());flashes=json.loads((N.R157/'actual-full-refill-via-flashes.json').read_bytes())['vias'];actual,ctx,padbindings=N.convert_selected_actual(h,c,native,flashes,{NET},source_pcb=N.R157/'copy/board.kicad_pcb');sb=json.loads((S/'source-binding.json').read_bytes());groupsfile=S/'actual-full-R157-CORE5-middle-withdrawn-all-drilled-groups.pkl';assert sha(groupsfile)==sb['CORE5_actual_groups_SHA256'];core=pickle.loads(groupsfile.read_bytes());coreRoot=K.root(core,'R11022','2');ledger=json.loads((S/'exact-original-middle-withdrawal-physical-source-ledger.json').read_text());right=ledger['two_full_width_source_test_anchors'][1];load=next(xs for xs in core if any(r['kind']=='track'and r['uuid']==right['uuid']for r in xs));anchor=unary_union([r['shape']for r in load if r['kind']=='track'and r['uuid']==right['uuid']and r['layer']=='F.Cu']);ground,_=N.bound_R663_before_groups({LG});lg=K.root(ground[LG],'J11001','2');ref1=K.source_refs(lg)['F.Cu'];ref4=K.source_refs(lg)['In3.Cu'];support=anchor.intersection(ref1);gap=anchor.difference(ref1);(O/'actual-retained-right-anchor-Cu.wkb').write_bytes(anchor.wkb);(O/'actual-before-supported-right-anchor-In1-subset.wkb').write_bytes(support.wkb);(O/'actual-right-anchor-fullbody-In1-gap-inherited.wkb').write_bytes(gap.wkb);put(O/'actual-right-anchor-source-and-reference-authority.json',{'right_anchor':right,'actual_LOAD_group_keys':len(K.keys(load)),'actual_LOAD_layers_and_kinds':{ly:{kind:sum(r['layer']==ly and r['kind']==kind for r in load)for kind in('pad','via','track','fill')}for ly in K.LAYERS},'actual_anchor':ds(anchor),'actual_J1_In1_before_supported':ds(support),'actual_inherited_fullbody_reference_gap':ds(gap),'source_root_keys_after_exact_middle_withdrawal':len(K.keys(coreRoot)),'right_anchor_already_SOURCE':any(r['uuid']==right['uuid']for r in coreRoot),'no_old_anchor_move_delete_or_reference_waiver':True});print('R409_ANCHOR',json.dumps(ds(support)),flush=True)
 region=box(10,145,215,228);roi=region.buffer(3);local=box(105,195,151,219);domain=h['domains_normalized'];gapFn=lambda net:.15 if domain.get(L.norm(net))==domain.get(NET)else .6;nativeIDs=K.C.inventory((N.R157/'copy/board.kicad_pcb').read_bytes())[3];reserve,exempt=K.A.reservations()
 def free(layer,reference,clip):
  cuts=[];wide=clip.buffer(3)
  for t in actual['tracks']:
   if t['layer']==layer and L.norm(t['net'])!=NET:
    sh=K.A.shape({'kind':'segment',**t})
    if sh.intersects(wide):cuts.append(sh.buffer(.625+gapFn(t['net'])+.025005,quad_segs=64))
  for v in actual['vias']:
   if L.norm(v['net'])==NET:continue
   if layer in v['flashed']:
    sh=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=128)
    if sh.intersects(wide):cuts.append(sh.buffer(.625+gapFn(v['net'])+.025005,quad_segs=64))
   hole=Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)
   if hole.intersects(wide):cuts.append(hole.buffer(.905005,quad_segs=64))
  for p in actual['pads']:
   if L.norm(p['net'])!=NET:
    for sh in L.poly(p['layers'].get(layer,[])):
     if sh.intersects(wide):cuts.append(sh.buffer(.625+gapFn(p['net'])+.025005,quad_segs=64))
    for sh in L.poly(p.get('hole')or[]):
     if sh.intersects(wide):cuts.append(sh.buffer(.905005,quad_segs=64))
  for z in native['zones']:
   if L.norm(z['net'])==NET or L.norm(z['net'])==LG and z['uuid']in nativeIDs:continue
   for sh in L.poly(N.O.polys(z['fills'].get(layer,[]))):
    if sh.intersects(wide):cuts.append(sh.buffer(.625+max(gapFn(z['net']),float(z['clearance_mm']))+.025005,quad_segs=64))
  for z in q:
   if z['layer']==layer and L.norm(z['net'])!=NET and z['shape'].intersects(wide):cuts.append(z['shape'].buffer(.625+max(gapFn(z['net']),float(z['clearance_mm']))+.025005,quad_segs=64))
  for rules,ex in((h['rule_areas'],False),(reserve['keepouts'],True)):
   for rr in rules:
    if layer not in rr['layers']or(not ex and not rr.get('no_tracks'))or(ex and NET in exempt.get(rr['name'],set())):continue
    cuts.extend(sh.buffer(.650005,quad_segs=64)for sh in L.poly(rr['outline'])if sh.intersects(wide))
  board=unary_union(L.poly(h['outline'])).buffer(-1.150005);return reference.intersection(wide).buffer(-.625005,quad_segs=64).intersection(clip).intersection(board).difference(unary_union(cuts))
 ff=free('F.Cu',ref1,local);fanchorContact=anchor.buffer(.624995,quad_segs=128);fFaces=[p for p in RF.parts(ff)if not p.intersection(fanchorContact).is_empty];fReach=unary_union(fFaces);(O/'actual-fullwidth-F-new-load-spur-reachable-centres.wkb').write_bytes(fReach.wkb);i3=free('In3.Cu',ref4,region);iFaces=RF.parts(i3);source2=unary_union([r['shape'].intersection(roi)for r in coreRoot if r['layer']=='In2.Cu'and r['shape'].intersects(roi)]);rows=[]
 for i,face in enumerate(iFaces):
  overlap=face.intersection(fReach)
  if overlap.is_empty:continue
  contact=source2.intersection(face.buffer(1.024995,quad_segs=128));pt=overlap.representative_point();fn=O/(str(i)+'-dual-F-In3-fullwidth-load-port-centre-region.wkb');fn.write_bytes(overlap.wkb);sn=O/(str(i)+'-same-component-actual-SOURCE-In2-Cu-side-port-region.wkb');sn.write_bytes(contact.wkb);near=nearest_points(face,source2)if not source2.is_empty else None;rows.append({'In3_component':i,'actual_fullwidth_F_spur_and_In3_source_LG_reference_centre_overlap':ds(overlap),'representative_point_mm':[pt.x,pt.y],'actual_source_In2_Cu_distance_mm':face.distance(source2),'actual_source_In2_Cu_within1p025_side_port_reach':ds(contact),'nearest_main_axis_and_actual_source_points_mm':[list(p.coords[0])for p in near]if near else None,'ordinary_PORT_PITCH_COURT_ALL6_Cu_mask_SOURCE_bothLG_returns_plating_current':'OPEN_NO_PORT_NOMINATION'});print('R409_COMPONENT',i,overlap.area,face.distance(source2),contact.area,flush=True)
 put(O/'new-load-port-reference-geography-components-not-nominations.json',rows);put(O/'receipt.json',{'verdict':'ACTUAL_RIGHT_ANCHOR_SUPPORTED_NEW_F_SPUR_AND_LGIn4_COMPONENT_GEOGRAPHY_NO_NOMINATION','native_R157_geometry_SHA256':sha(N.R157/'actual-full-refill-geometry.json'),'actual_source_R295_cache_SHA256':sha(groupsfile),'actual_anchor_before_supported_area_mm2':support.area,'fullwidth_F_spur_source_reference_and_Cu_free_face_count':len(fFaces),'dual_F_In3_load_port_geography_component_count':len(rows),'components_with_actual_In2_source_side_port_reach':sum(not x['actual_source_In2_Cu_within1p025_side_port_reach']['EMPTY']for x in rows),'all49CM_native_and_all_foreign_field_current_planes_remain_hard':True,'original_native_LG_F_In3_normal_retreat_only_pending_source_oldref_native_gates':True,'old_original_anchors_and_their_before_supported_masks_held':True,'new_port_actual_ordinary_SOURCE_return_and_all6_hole_masks_current_native':'OPEN','source_or_board_changes':0,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R409',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc()})
  raise
