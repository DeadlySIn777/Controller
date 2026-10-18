"""Literal .20F R7 stub/.5-.2 via, two full1.25 B-trunk local bends.

Existing .125 U1001 pad-via rule applies; every added planner reserve deficit
is retained separately. Normal foreign-fill antipads/source/current/native
remain obligations and no native PASS or board write follows this nomination.
"""
import copy,hashlib,json,pickle,sys,uuid,traceback
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as GP
O=H/'sbc-power/R7-NW-fullwidth-two-B-trunk-detour-nominations-r259'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,r):Path(p).write_text(json.dumps(r,indent=1)+'\n')
def main():
 assert not O.exists();O.mkdir();mp=H/'CORE-wide-reserved-IO3-immutable-R214-materialized-r112/model.pkl';assert sha(mp)=='6312b10a88b2d3614e21760d1709866d2417b419d418e20e09055eb13b8e3b7e';g,h,b,z,c=pickle.loads(mp.read_bytes())
 dru=H/'sbc-native-contract-r1/copy/board.kicad_dru';assert sha(dru)=='159c4614968368a7d88946cc71cc341f886fd22b356ced1d0738252dbeb65fe4';text=dru.read_text();assert "A.memberOfFootprint('U1001') && B.Type == 'Via'"in text
 removed={'c161da3b-e8ef-42cc-b51e-f7e2f2df45ff','7a7efa56-f9f9-4efa-b31d-3ceed21fa937'};old=[t for t in h['tracks']if t['uuid']in removed];assert len(old)==2 and all(t['net']=='/CORE_1V2'and t['w']==1.25 and t['layer']=='B.Cu'for t in old)
 oldbody=unary_union([GP.bounded_buffer(LineString([t['a'],t['b']]),.625)for t in old]);records,trees=F.build({**h,'tracks':[t for t in h['tracks']if t['uuid']not in removed],'zones':[]});rr,_=F.build(c,nets={'/CORE_1V2'},layers={'B.Cu'});smd=[(p,sh)for p in h['pads']if p['smd']for l,rs in p['layers'].items()if l in('F.Cu','B.Cu')for sh in C.poly(rs)];st=STRtree([sh for p,sh in smd]);hole=[(v['uuid'],GP.bounded_disk(v,v['drill']/2+.00000002))for v in h['vias']]+[(p['uuid'],sh.buffer(.00000002))for p in h['pads']for sh in C.poly(p.get('hole')or[])];ht=STRtree([s for u,s in hole]);vp=[Point(v['x'],v['y'])for v in h['vias']];vt=STRtree(vp)
 v={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'R7-NW-R259-ordinary-ground')),'net':'/LOGIC_GND','x':159.69,'y':94.477,'d':.5,'drill':.2,'flashed':['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']};p=Point(v['x'],v['y']);vbody=GP.bounded_disk(v,.25);stub={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'R7-NW-R259-.20F-stub')),'net':'/LOGIC_GND','layer':'F.Cu','w':.2,'a':[160.09,94.877],'b':[159.69,94.477]};variants=[];accepted=[]
 for bx in (160.5,160.525,160.55,160.575,160.6,160.65,160.7,160.75):
  bends=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'R7-R259-fullwidth-B:'+str(bx)+':'+str(i))),'net':'/CORE_1V2','layer':'B.Cu','w':1.25,'a':a,'b':bb}for i,(a,bb)in enumerate(zip([[161.15,95.15],[bx,95.15]],[[bx,95.15],[160.05,95.55]]))];adds=[*bends,stub];checks=[];errors=[];planner=[]
  for t in adds:
   axis=LineString([t['a'],t['b']]);body=GP.bounded_buffer(axis,t['w']/2);nov=body.difference(oldbody)if t['net']=='/CORE_1V2'else body
   for j in trees[t['layer']].query(body.buffer(.8),predicate='intersects'):
    r=records[t['layer']][int(j)]
    if C.norm(r['net'])==C.norm(t['net']):continue
    if r['kind']=='track':q=r['source'];target=GP.bounded_buffer(LineString([q['a'],q['b']]),q['w']/2);gap=axis.distance(LineString([q['a'],q['b']]))-(t['w']+q['w'])/2
    elif r['kind']=='via':q=r['source'];target=GP.bounded_disk(q,q['d']/2);gap=axis.distance(Point(q['x'],q['y']))-(t['w']+q['d'])/2
    else:target=r['shape'];gap=axis.distance(target)-t['w']/2
    req=GP.G.gap(h,t['net'],r['net'])+.025;ng=nov.distance(target)if not nov.is_empty else float('inf');row={'new_UUID':t['uuid'],'kind':'fullwidth_true_track_to_'+r['kind'],'foreign_UUID':r['uuid'],'native_mm':req-.025,'planning_mm':req,'gap_mm':gap,'novel_body_gap_mm':ng,'inherited_original_anchor_only':gap<req and ng>=req};checks.append(row)
    if gap<req and ng<req:errors.append(row)
   if t['net']=='/CORE_1V2':
    gap=axis.distance(p)-t['w']/2-.25;row={'new_UUID':t['uuid'],'kind':'new_B_CORE_trunk_to_new_GND_via','foreign_UUID':v['uuid'],'native_mm':.15,'planning_mm':.175,'gap_mm':gap};checks.append(row)
    if gap<.175:errors.append(row)
  # Every literal via/discrete pair uses existing native rules; +.025 remains
  # a separate named failed planning gate, never reduced to native PASS.
  for l in v['flashed']:
   for j in trees[l].query(p.buffer(1),predicate='intersects'):
    r=records[l][int(j)]
    if C.norm(r['net'])=='/LOGIC_GND':continue
    bga=r['kind']=='pad'and r.get('ref')=='U1001';req=.125 if bga else GP.G.gap(h,v['net'],r['net'])
    if r['kind']=='track':t=r['source'];gap=p.distance(LineString([t['a'],t['b']]))-.25-t['w']/2
    elif r['kind']=='via':q=r['source'];gap=p.distance(Point(q['x'],q['y']))-.25-q['d']/2
    else:gap=p.distance(r['shape'])-.25
    row={'new_UUID':v['uuid'],'kind':'ordinary_via_to_'+r['kind'],'layer':l,'foreign_UUID':r['uuid'],'foreign_raw_net':r['net'],'gap_mm':gap,'existing_native_rule_mm':req,'planning_with_added_reserve_mm':req+.025,'U1001_native_pad_via_predicate':bga};checks.append(row)
    if gap<req:errors.append(row)
    if gap<req+.025:planner.append(row)
  sj=int(st.nearest(p));smdd=p.distance(smd[sj][1])-.1-.005;hj=int(ht.nearest(p));hd=p.distance(hole[hj][1])-.1-.005;vi=int(vt.nearest(p));pitch=p.distance(vp[vi]);guards={'every_SMD_guarded_mm':smdd,'nearest_SMD_UUID':smd[sj][0]['uuid'],'every_drill_guarded_mm':hd,'nearest_drill_UUID':hole[hj][0],'native_existing_via_pitch_mm':pitch,'nearest_existing_via_UUID':h['vias'][vi]['uuid'],'required_SMD_drill_mm':.275,'required_ordinary_pitch_mm':.815}
  if smdd<.275 or hd<.275 or pitch<.815:errors.append({'kind':'ordinary_via_SMD_drill_pitch_guard','guards':guards})
  cb=unary_union([GP.bounded_buffer(LineString([t['a'],t['b']]),.625)for t in bends]);contacts=[]
  for r in rr['B.Cu']:
   if r['uuid']in removed or r['shape'].intersection(oldbody).area<=0:continue
   ps=[r['shape']]if r['shape'].geom_type=='Polygon'else list(r['shape'].geoms)
   for i,sh in enumerate(ps):
    if sh.intersection(oldbody).area>0:contacts.append({'kind':r['kind'],'UUID':r['uuid'],'contour':r.get('contour'),'piece':i,'whole_old_piece_WKB_sha256':hashlib.sha256(sh.wkb).hexdigest(),'old_contact_mm2':sh.intersection(oldbody).area,'new_contact_mm2':sh.intersection(cb).area})
  if any(r['new_contact_mm2']<=0 for r in contacts):errors.append({'kind':'old_shared_physical_contact_lost','contacts':[r for r in contacts if r['new_contact_mm2']<=0]})
  conflicts=[]
  for q in z:
   if q['net']=='/LOGIC_GND':continue
   if q['layer']in v['flashed']and vbody.distance(q['shape'])<max(.15,q['clearance_mm'])+.025:conflicts.append({'kind':'new_via_needs_explicit_owned_foreign_plane_antipad','UUID':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'physical_WKB_sha256':hashlib.sha256(q['shape'].wkb).hexdigest(),'outline_WKB_sha256':hashlib.sha256(q['zone_outline_shape'].wkb).hexdigest(),'native_refill_contact_source_current_gate':'OPEN'})
  row={'bend_x_mm':bx,'new_tracks':adds,'new_via':v,'removed_original_track_UUIDs':sorted(removed),'discrete_true_checks':len(checks),'native_or_new_trunk_full_planner_errors':errors,'via_extra_planner_reserve_deficits':planner,'SMD_drill_pitch_guards':guards,'every_shared_old_CORE_B_contact_piece':contacts,'prospective_owned_plane_antipad_obligations':conflicts,'status':'DISCRETE_NATIVE_EFFECTIVE_GEOMETRY_NOMINEE_WITH_RETAINED_EXTRA_PLANNER_FAILURES_PENDING_FULL_PROOF'if not errors else'REJECTED_NATIVE_OR_TRUNK_MARGIN_OR_SHARED_CONTACT_ERRORS'};variants.append(row)
  if not errors:accepted.append(row)
  put(O/'matrix-progress.json',variants);print('R259_BEND',bx,len(checks),len(errors),len(planner),len(contacts),flush=True)
 put(O/'receipt.json',{'verdict':'DISCRETE_ONLY_R7_NOMINEES_EXTRA_PLANNER_RESERVE_DEFICITS_RETAINED_FULL_GATES_OPEN'if accepted else'NO_R7_DISCRETE_NOMINEE_IN_DECLARED_B_TRUNK_MATRIX','exact_R112_model_sha256':sha(mp),'exact_original_native_DRU_sha256':sha(dru),'existing_U1001_pad_via_rule_predicate':"(A.memberOfFootprint('U1001') && B.Type == 'Via') || (B.memberOfFootprint('U1001') && A.Type == 'Via')",'existing_U1001_pad_via_native_min_mm':.125,'ground_track_width_mm':.2,'ordinary_via_diameter_drill_mm':[.5,.2],'two_rerouted_CORE_B_width_mm':1.25,'accepted_discrete_only_nominees':accepted,'full_planner_PASS':False,'full_native_PASS':False,'all77_source25_sevenroots_strict_oldrefs_current_drop_normal_antipads_native':'OPEN','no_rule_source_pad_footprint_native_mask_mutation':True,'whole_stale_failed_R246_overlay_used':False,'native_jobs':0,'board_written':False,'script_sha256':sha(__file__)})
 if accepted:(O/'first-nominee-discrete.pkl').write_bytes(pickle.dumps({'tracks':accepted[0]['new_tracks'],'vias':[v],'removed_original_track_UUIDs':sorted(removed)},protocol=5))
 print('R259_COMPLETE',len(accepted),sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
