"""Separate scoped SAME_PLANE geometric proposal for the two retained barrels.

No entire-ring rule is invented. A finite .20-mm physical In1 conductor is
required between actual adjacent F and In2 signal sides; native/SI stays open.
"""
from pathlib import Path
import sys,pickle,json,hashlib,math,time
H=Path(__file__).resolve().parent;P=H.parent
for d in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import tri_route as T
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
out=H/'Q0-R504-SENSE-same-plane-finite-paths-r510';assert not out.exists();out.mkdir();start=time.monotonic();ad=H/'Q0-R504-explicit-final-current-r506';ar=ad/'receipt.json';assert sha(ar)=='8eeddecee7280d2e881282eca828c3e2a209a82c89601e38bfc61fd82c88f38a';audit=json.loads(ar.read_bytes());assert audit['actual_final_owned_roles_and_filled_model_sha256']=='f738f9a4891664324f3e09511276036e77d94e12471713762d7998121d10593a';assert audit['actual_old_contact_group_losses']==audit['ten_actual_prior_source_keys_lost']==audit['retained_track_raw_reference_loss_rows']==0;mp=H/'Q0-owned-actual-fill-strict-local-negative-successor-r504/model.pkl';assert sha(mp)=='f738f9a4891664324f3e09511276036e77d94e12471713762d7998121d10593a';g,h,b,q,current=pickle.loads(mp.read_bytes());banksfile=ad/'actual-before-and-after-source-banks.pkl';banks=pickle.loads(banksfile.read_bytes());GND='/motherboard_motors/FIELD_GND';NET='/motherboard_do/DOA_Q0_ISNS';root=banks['after'][GND];plane=unary_union([r['shape']for r in root if r['kind']=='fill'and r['layer']=='In1.Cu']);policy=H/'DI15-exact-same-plane-source-r144.json';policydata=json.loads(policy.read_bytes());source=P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(source)==policydata['source_parent_sha256'];stackup=policydata['test']['native_stackup_adjacent_order'];assert stackup==['F.Cu','In1.Cu','In2.Cu'];op=pickle.loads((H/'Q0-R474-ground-contact-pose-native-r476/exact-owned-discrete-and-pose-nomination.pkl').read_bytes());newids={t['uuid']for t in op['tracks']};rows=[]
for sig0 in op['existing_SENSE_vias']:
 sig=next(v for v in h['vias']if v['uuid']==sig0['uuid']);centre=Point(sig['x'],sig['y']);assert sig['flashed']==['F.Cu','In2.Cu','B.Cu'];rad=sig['drill']/2+.25+.025;own=K.Z.bounded_disk(sig,rad);local=plane.intersection(centre.buffer(1.8,quad_segs=128));finite=local.difference(own).buffer(-.105,quad_segs=128);by={l:[]for l in('F.Cu','In2.Cu')}
 for t in h['tracks']:
  if t['layer']not in by or K.L.norm(t['net'])!=NET:continue
  if t['layer']=='In2.Cu'and t['uuid']not in newids:continue
  line=LineString([t['a'],t['b']]);endindex=next((i for i,xy in enumerate((t['a'],t['b']))if math.dist(xy,[sig['x'],sig['y']])<1e-8),None)
  if endindex is None:continue
  end=(t['a'],t['b'])[1-endindex];dx,dy=end[0]-sig['x'],end[1]-sig['y'];ll=math.hypot(dx,dy)
  for distance in(.515,.55,.6,.65,.7,.75,.8,.9,1.0):
   if distance>=ll:continue
   xy=[round(sig['x']+dx/ll*distance,9),round(sig['y']+dy/ll*distance,9)];pp=Point(xy)
   if not finite.covers(pp):continue
   if pp.distance(line)>t['w']/2:continue
   by[t['layer']].append({'track_UUID':t['uuid'],'actual_native_or_new_serialized_axis':[t['a'],t['b']],'probe_mm':xy,'distance_from_exact_barrel_mm':distance,'actual_signal_body_membership':True,'finite_actual_source_plane_eroded_contains':True})
 selected=None
 for part in K.RF.parts(finite):
  ff=[p for p in by['F.Cu']if part.covers(Point(p['probe_mm']))];ii=[p for p in by['In2.Cu']if part.covers(Point(p['probe_mm']))]
  if not ff or not ii:continue
  for pf in ff:
   for pi in ii:
    path,search=T.route(part,tuple(pf['probe_mm']),tuple(pi['probe_mm']));axis=LineString(path)
    if not part.covers(axis):continue
    conductor=K.Z.bounded_buffer(axis,.100)
    if not conductor.difference(local).is_empty:continue
    if conductor.intersects(own):continue
    selected={'actual_F_side':pf,'actual_In2_side':pi,'finite_path_mm':path,'finite_path_length_mm':axis.length,'minimum_constructed_physical_conductor_width_mm':.20,'additional_source_boundary_guard_mm':.005,'path_body_WKB_sha256':K.C.sha(conductor.wkb),'source_piece_eroded_WKB_sha256':K.C.sha(part.wkb),'local_source_ground_WKB_sha256':K.C.sha(local.wkb),'no_foreign_or_own_aperture_crossed':True,'search':search};(out/(sig['uuid']+'-finite-same-plane-source-path.wkb')).write_bytes(conductor.wkb);break
   if selected:break
  if selected:break
 row={'signal_UUID':sig['uuid'],'exact_position_diameter_drill_mm':[sig['x'],sig['y'],sig['d'],sig['drill']],'unchanged_native_old_reference_flash':False,'old_reference_width_mm':sig['drill'],'exact_own_aperture_radius_mm':rad,'actual_used_signal_sides':['F.Cu','In2.Cu'],'same_actual_source_plane':'In1.Cu','actual_functional_ground_source':['J11003','2'],'finite_width_constructor_requirement_mm':.20,'requirement_scope':'Explicit geometric constructor screen, not a universal electrical/SI limit','native_stackup_order':stackup,'actual_adjacent_probe_counts':{l:len(x)for l,x in by.items()},'PASS_GEOMETRIC_SAME_CONTINUOUS_SOURCE_CONDUCTOR':selected is not None,'witness':selected,'all_probes':by,'inherited_blanket_no_paired_return_checker':'FAIL preserved','native_actual_plane_refill_mandatory_masks_and_electrical_edge_SI_qualification':'OPEN'};rows.append(row)
put(out/'two-exact-SENSE-same-plane-finite-conductor-ledgers.json',rows);result={'verdict':'TWO_RETAINED_SENSE_BARRELS_FINITE_ACTUAL_SAME_PLANE_GEOMETRIC_PROPOSAL_PASS_NATIVE_SI_OPEN'if all(r['PASS_GEOMETRIC_SAME_CONTINUOUS_SOURCE_CONDUCTOR']for r in rows)else'SAME_PLANE_GEOMETRIC_SOURCE_CONDUCTOR_REPAIR_REQUIRED','current_model_sha256':sha(mp),'R506_incremental_receipt_sha256':sha(ar),'actual_source_bank_arrays_file':str(banksfile),'actual_source_bank_arrays_sha256':sha(banksfile),'source_native_parent_sha256':sha(source),'exact_inherited_policy_basis_file':str(policy),'exact_inherited_policy_basis_sha256':sha(policy),'finite_actual_same_source_path_failures':sum(not r['PASS_GEOMETRIC_SAME_CONTINUOUS_SOURCE_CONDUCTOR']for r in rows),'inherited_checker_flags_modified':False,'same_plane_minwidth_not_promoted_to_general_electrical_limit':True,'all_raw_R155_R368_CORE_ROOT42_DIC_Bterminal_and_SMD_current_native_failures_preserved':True,'native_jobs':0,'board_or_model_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-start};put(out/'receipt.json',result);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),**result}),flush=True)
