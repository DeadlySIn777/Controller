"""Independent exact owned-role clearance and current direct-contact audit.

No whole-model projection, coordinate snapping, threshold or current claim.
The R496 actual source/contact/reference result is a separate bound input.
"""
from pathlib import Path
import sys,pickle,json,hashlib,time
H=Path(__file__).resolve().parent;P=H.parent
for d in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
from shapely import set_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
out=H/'Q0-R526-plane-roles-and-direct-contacts-r530';assert not out.exists();out.mkdir();start=time.monotonic()
mp=H/'Q0-only-new-FA-recess-explicit-100nm-margin-r526/model.pkl';assert sha(mp)=='97e6f5193c9102102ec86a50c7d142def2d9c498495c8acdbd7202f466f84e14'
bm=P/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl';assert sha(bm)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
_,h0,_,q0,before=pickle.loads(bm.read_bytes());_,h,b,q,after=pickle.loads(mp.read_bytes())
ad=H/'Q0-R526-full-current-contacts-source-reference-r528';ar=ad/'receipt.json';assert sha(ar)=='0fe1fbdb213915cadf704785bccd755c13d8048745b07bc5f8e60ff4d0b69721';audit=json.loads(ar.read_bytes());assert audit['actual_final_owned_roles_and_filled_model_sha256']==sha(mp)
pp=H/'Q0-R474-ground-contact-pose-native-r476/exact-owned-discrete-and-pose-nomination.pkl';assert sha(pp)=='b226073ec3597d7115d9216bb1a6ff3c1fd9904d25652cd3d518df216cd1a067';op=pickle.loads(pp.read_bytes());removed=set(op['exact_deleted_track_UUIDs']);dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(K.L.norm(a))==dom.get(K.L.norm(bb))else .6
checks=[];nativebad=[];plannerbad=[]
for item in op['tracks']+op['vias']+[{**v,'added_layer_only':'In2.Cu'}for v in op['existing_SENSE_vias']]:
 via='d'in item;net=K.L.norm(item['net']);axis=Point(item['x'],item['y'])if via else LineString([item['a'],item['b']]);rad=item['d']/2 if via else item['w']/2;layers=[item['added_layer_only']]if'added_layer_only'in item else K.LAYERS if via else[item['layer']]
 for z in q:
  if z['layer']not in layers or K.L.norm(z['net'])==net:continue
  sh=set_precision(z['shape'],0)
  if axis.distance(sh)-rad>.9:continue
  d=axis.distance(sh)-rad;native=max(float(z['clearance_mm']),gap(item['net'],z['net']));row={'new_UUID':item['uuid'],'owned_UUID':z['uuid'],'layer':z['layer'],'gap_mm':d,'exact_declared_native_requirement_mm':native,'planner_requirement_mm':native+.025};checks.append(row)
  if d<native:nativebad.append(row)
  if d<native+.025:plannerbad.append(row)
# The only positive new plane uses its literal nm physical boundary and
# current actual native flash masks; every foreign cap is measured exactly.
ground=next(z for z in q if z['uuid']=='637c65c4-b144-5c66-8c11-42e9f8bf96bc');plane=set_precision(ground['shape'],0);GND=K.L.norm(ground['net']);layer=ground['layer'];assert layer=='In1.Cu';positiveChecks=[]
def positive(kind,other,raw,d,local=.25):
 requirement=max(.25,float(local),gap(ground['net'],raw));row={'kind':kind,'new_owned_ground_UUID':ground['uuid'],'other_UUID':other,'raw_net':raw,'layer':layer,'true_gap_mm':d,'native_requirement_mm':requirement,'planner_requirement_mm':requirement+.025};positiveChecks.append(row)
 if d<requirement:nativebad.append(row)
 if d<requirement+.025:plannerbad.append(row)
records,trees=K.F.build({**h,'zones':[]})
for j in trees[layer].query(plane.buffer(.9),predicate='intersects'):
 r=records[layer][int(j)]
 if K.L.norm(r['net'])==GND:continue
 if r['kind']=='track'and not r['source'].get('m'):t=r['source'];d=LineString([t['a'],t['b']]).distance(plane)-t['w']/2
 elif r['kind']=='via':v=r['source'];width=v['d']if layer in v['flashed']else v['drill'];d=Point(v['x'],v['y']).distance(plane)-width/2
 else:d=r['shape'].distance(plane)
 positive('true_new_ground_to_native_'+r['kind'],r['uuid'],r['net'],d)
for z in q:
 if z['layer']!=layer or K.L.norm(z['net'])==GND or z['shape'].distance(plane)>.9:continue
 positive('true_new_ground_to_current_owned_physical_role',z['uuid'],z['net'],set_precision(z['shape'],0).distance(plane),z['clearance_mm'])
for z in after['zones']:
 if K.L.norm(z['net'])==GND:continue
 for p in K.L.poly(z['fills'].get(layer,[])):
  if p.distance(plane)>.9:continue
  positive('true_new_ground_to_current_actual_filled_piece',z['uuid'],z['net'],p.distance(plane),z['clearance_mm'])
for v in h['vias']:
 if K.L.norm(v['net'])==GND:continue
 d=Point(v['x'],v['y']).distance(plane)-v['drill']/2
 if d>.9:continue
 row={'kind':'new_ground_every_foreign_drill','other_UUID':v['uuid'],'raw_net':v['net'],'layer':layer,'guarded_drill_edge_gap_mm':d-.005,'required_mm':.275};positiveChecks.append(row)
 if d-.005<.275:plannerbad.append(row)
for p in h['pads']:
 if K.L.norm(p['net'])==GND:continue
 for hole in K.L.poly(p.get('hole')or[]):
  d=hole.distance(plane)
  if d>.9:continue
  row={'kind':'new_ground_every_foreign_pad_drill','other_UUID':p['uuid'],'raw_net':p['net'],'layer':layer,'guarded_drill_edge_gap_mm':d-.005,'required_mm':.275};positiveChecks.append(row)
  if d-.005<.275:plannerbad.append(row)
for r in h['rule_areas']:
 if layer in r['layers']and r.get('no_zones')and any(s.distance(plane)<.025 for s in K.L.poly(r['outline'])):nativebad.append({'kind':'new_ground_native_no_zones','UUID':r['uuid']})
put(out/'only-positive-new-ground-true-cap-hole-pad-native-rule-and-current-peer-ledger.json',positiveChecks)
put(out/'all-new-primitives-to-actual-current-owned-physical-roles.json',checks);put(out/'true-native-owned-role-errors.json',nativebad);put(out/'extra-planner-owned-role-failures.json',plannerbad)
# Check actual current fill against the exact newly withdrawn physical role.
by0={z['uuid']:z for z in q0};rolealignment=[];alignmentbad=[]
for z in q:
 if z['uuid']=='637c65c4-b144-5c66-8c11-42e9f8bf96bc':continue
 a=by0[z['uuid']]
 if a['shape'].wkb==z['shape'].wkb:continue
 lost=set_precision(a['shape'],0).difference(set_precision(z['shape'],0));fills=unary_union([p for zz in after['zones']if zz['uuid']==z['uuid']for p in K.L.poly(zz['fills'].get(z['layer'],[]))]);residue=fills.intersection(lost).difference(set_precision(z['shape'],0))
 row={'UUID':z['uuid'],'layer':z['layer'],'exact_new_owned_physical_withdrawal_WKB_sha256':K.C.sha(lost.wkb),'actual_filled_Cu_inside_new_withdrawal_and_literal_exterior_to_after_role_empty':residue.is_empty,'raw_residue_kind':residue.geom_type,'raw_residue_mm2':residue.area,'raw_residue_bounds_mm':list(residue.bounds)if not residue.is_empty else None};rolealignment.append(row)
 if not residue.is_empty:alignmentbad.append(row);(out/(z['uuid']+'-raw-current-filled-inside-new-physical-withdrawal.wkb')).write_bytes(residue.wkb)
put(out/'exact-new-physical-role-withdrawal-and-actual-filled-alignment.json',rolealignment)
# Every direct OLD drilled discrete-to-zone layer contact in a changed fill
# is checked against final pieces of that SAME zone, retaining actual keys.
oldgroups=pickle.loads((P/'field-power/REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r368/actual-drilled-current-groups.pkl').read_bytes());newgroups=pickle.loads((ad/'actual-new-groups.pkl').read_bytes());oldz={z['uuid']:z for z in before['zones']};newz={z['uuid']:z for z in after['zones']};cutkeys={(uid,l)for uid,z in oldz.items()for l,rs in z['fills'].items()if rs!=newz[uid]['fills'][l]};direct=[];directbad=[]
for net in sorted({K.L.norm(oldz[uid]['net'])for uid,l in cutkeys}):
 old=oldgroups[net];new=newgroups[net];final={key:[]for key in cutkeys}
 for xs in new:
  for r in xs:
   if r['kind']=='fill'and(r['uuid'],r['layer'])in cutkeys:final[r['uuid'],r['layer']].append(r['shape'])
 for l in K.LAYERS:
  metal=[r for xs in old for r in xs if r['layer']==l and r['kind']!='fill'and r['uuid']not in removed];tree=STRtree([r['shape']for r in metal])
  for f in(r for xs in old for r in xs if r['kind']=='fill'and r['layer']==l and(r['uuid'],l)in cutkeys):
   for j in tree.query(f['shape'],predicate='intersects'):
    r=metal[int(j)];hits=[K.C.sha(s.wkb)for s in final[f['uuid'],l]if s.intersects(r['shape'])];row={'net':net,'old_zone_UUID':f['uuid'],'layer':l,'old_actual_piece_WKB_sha256':K.C.sha(f['shape'].wkb),'exact_old_discrete_key':[r['kind'],r['uuid'],l],'new_same_zone_actual_intersection_piece_hashes':hits,'direct_literal_intersection_retained':bool(hits)};direct.append(row)
    if not hits:directbad.append(row)
put(out/'every-changed-layer-direct-literal-contact-ledger.json',direct);put(out/'direct-literal-contact-losses.json',directbad)
result={'verdict':'INDEPENDENT_OWNED_NATIVE_CLEARANCE_DIRECT_CONTACT_AND_FILLED_ALIGNMENT_PASS_NATIVE_CURRENT_OPEN'if not(nativebad or plannerbad or alignmentbad or directbad)else'OWNED_ROLE_OR_ACTUAL_DIRECT_CONTACT_REPAIR_REQUIRED','current_model_file':str(mp),'current_model_sha256':sha(mp),'baseline_model_sha256':sha(bm),'R528_actual_reference_source_contact_receipt_sha256':sha(ar),'current_owned_true_checks':len(checks),'new_positive_ground_true_checks':len(positiveChecks),'new_ground_UUID':ground['uuid'],'whole_moved_SMD_body_reference_gate_empty':all(r['new_whole_SMD_body_gap_empty']for r in audit['new_SMD_whole_body_reference_rows']),'current_owned_native_errors':len(nativebad),'current_owned_extra_planner_failures':len(plannerbad),'actual_fill_inside_new_role_withdrawal_raw_rows':len(alignmentbad),'direct_literal_old_contacts':len(direct),'direct_literal_old_contact_losses':len(directbad),'every_raw_nonempty_failure_retained_no_threshold':True,'R498_closed_boundary_intersection_raw_FAIL_preserved':True,'strict_exterior_probe_excludes_only_exact_after_role_membership_not_area_or_buffer':True,'all_R155_R368_Bterminal_SMD_CORE_ROOT42_DIC_policy_and_native_current_SI_failures_preserved':True,'native_jobs':0,'board_or_model_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-start}
put(out/'receipt.json',result);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),**result}),flush=True)
