"""All-net incremental audit; preserve the earlier REG8b IO3 failure."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
import contact_layout as C
import fast_contacts as F
from inventory import sha
from audit_field_io3_crossings_r15e import losses
H=Path(__file__).resolve().parent
for name in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/name))
import regional_guarded_declared_projection_r140 as P
import owned_analytic_track_guards_r75 as TG
import complete_geometry_r2 as G
import physical_reference_losses_r1 as REF
O=H/'REG-seven-minimal-owned-replay-analytic-guard-audit-r254'
def write(p,d):p.write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir()
 from shapely import set_precision,from_wkb
 from restore_SAFE_generated_precision_states_r168 import restore_bound_generated_precision_states
 import immutable_baseline_analytic_guard_supplements_r252 as IP
 baseline=H/'R54-native-wider-IO3-monitor-joint-audit-r214';assert sha(baseline/'model.pkl')=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e'
 bg,bh,bb,bz,before=pickle.loads((baseline/'model.pkl').read_bytes());restore_bound_generated_precision_states(bb,bz)
 parent=H/'B3-envelope-scoped-LOGIC-projection-r233';assert sha(parent/'derived-full-input-model.pkl')=='0c1c16abb3814bb18b4cd0faa6e002022a72e72863d4249ed58528c19da07367';g,h,b,z,_=pickle.loads((parent/'derived-full-input-model.pkl').read_bytes());restore_bound_generated_precision_states(b,z)
 d=pickle.loads((H/'REG-safe-subset-on-current-R214-full-audit-r227/proposed-discrete.pkl').read_bytes());adds=d['tracks'];assert len(d['vias'])==4 and len(adds)==10
 u17=H/'u11017-dead-spur-native-owned-recipe-r138';removed={r['uuid'] for r in json.loads((u17/'receipt.json').read_text(encoding='utf-8'))['delete_rows']};assert len(removed)==3 and {t['uuid'] for t in bh['tracks']}-removed=={t['uuid'] for t in h['tracks']}-{t['uuid'] for t in adds}
 # Preserve the pre-trim FBG primitive. R240/R241 erase required old
 # reference copper and cannot be silently reused as clearance repairs.
 correction=H/'B3-envelope-scoped-LOGIC-projection-r233'
 field=H/'FIELD5-current-reference-envelope-correction-r238';assert sha(field/'receipt.json')=='b9758dfc590a221b0e755639bb6d5460971b089a59af712bc472003802dd07c9';fq=pickle.loads((field/'proposed-corrected-zone.pkl').read_bytes())[0]
 for role in ('shape','zone_outline_shape'):raw=fq[role].wkb;fq[role]=set_precision(fq[role],1e-6,mode='pointwise');assert raw==fq[role].wkb
 replays=[];viafix=[];trackfix=[]
 for q in z:
  if q['layer']!='In4.Cu' or C.norm(q['net'])!='/motherboard_motors/FIELD_GND':continue
  cut=P.bounded_buffer(fq['zone_outline_shape'],.175)
  for role in ('shape','zone_outline_shape'):
   old=q[role];q[role]=set_precision(set_precision(old,0).difference(set_precision(cut,0)),1e-6,mode='pointwise')
   # Resolve any positive intersection snap gain only in its exact local
   # neighbourhood; every unaffected old boundary coordinate stays exact.
   local_cuts=[]
   for iteration in range(8):
    gain=set_precision(q[role],0).difference(set_precision(old,0))
    if gain.area<1e-12:break
    local_cut=P.bounded_buffer(gain,.000003);q[role]=set_precision(set_precision(q[role],0).difference(set_precision(local_cut,0)),1e-6,mode='pointwise');local_cuts.append({'gain_sha256':P.digest(gain),'gain_mm2':gain.area,'exact_local_3nm_reserve_cutter_sha256':P.digest(local_cut)})
   assert q[role].difference(old).area<1e-12,('owned replay snap gained Cu',q['uuid'],role)
   if old.wkb!=q[role].wkb:replays.append({'UUID':q['uuid'],'role':role,'old_sha256':P.digest(old),'new_sha256':P.digest(q[role]),'cutter_sha256':P.digest(cut),'required_gap_mm':.175,'removed_mm2':old.difference(q[role]).area,'added_mm2':q[role].difference(old).area})
 [fq],viafix=P.normalize_owned_via_guards(h,[fq]);[fq],trackfix,geoms=TG.normalize_owned_track_guards(h,[fq]);z.append(fq)
 oldowned={q['uuid']:q for q in bz};newq=[q for q in z if q['uuid'] not in oldowned];assert len(newq)==7 and '938b9038-0f65-5de2-99ed-d6781afcb116' not in {q['uuid'] for q in z};updates={q['uuid']:q for q in z if q['uuid'] in oldowned and any(P.digest(q[role])!=P.digest(oldowned[q['uuid']][role]) for role in ('shape','zone_outline_shape'))}
 precision=[]
 for q in z:
  for role in ('shape','zone_outline_shape'):
   raw=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert raw==q[role].wkb;precision.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':P.digest(q[role]),'exact_WKB_unchanged':True})
 b['generated_precision_state_ledger']=precision;b['restored_generated_grid_UUIDs']=sorted(q['uuid'] for q in z);write(O/'generated-precision-state-ledger.json',precision);write(O/'FIELD5-current-owned-return-cut-replay.json',replays)
 print('R254 complete exact current inputs, conservative all-net projection',flush=True);after,retreat,guard_checks=IP.projected(g,h,z,bh,bz,before);guard_errors=[row for row in guard_checks if not row['PASS']];write(O/'native-actual-fill-vs-new-required-guard-checks.json',guard_checks);write(O/'native-actual-fill-vs-new-required-guard-errors.json',guard_errors);print('R254 actual guard checks',len(guard_checks),len(guard_errors),flush=True)
 # Later additive C1022 remains separate. Its literal source-reference body and
 # physical segment are exact mutual obligations, never appended silently.
 cpacket=H.parent/'sbc-power/C1022-validated-native-integration-packet-r222';assert sha(cpacket/'receipt.json')=='ab63866ae63e1aff6da41f96630346989bdc4d92e9eb2feee499173b37f3ab02';cp=json.loads((cpacket/'receipt.json').read_text(encoding='utf-8'));cb=from_wkb(Path(cp['exact_full_reference_body_file']).read_bytes());assert sha(Path(cp['exact_full_reference_body_file']))==cp['exact_full_reference_body_sha256'];lg=F.graph(after,'/LOGIC_GND');lgr=next(xs for xs in lg if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11001','2') for q in xs));source_ref=unary_union([q['shape'] for q in lgr if q['kind']=='fill' and q['layer']=='In4.Cu']);c_ref_gap=cb.difference(source_ref).area;write(O/'C1022-later-mutual-reference-check.json',{'packet_sha256':sha(cpacket/'receipt.json'),'actual_full_body_sha256':P.digest(cb),'required_body_missing_actual_J1_source_In4_mm2':c_ref_gap,'C1022_not_appended':True});print('R254 C1022 exact later reference gap',c_ref_gap,flush=True)
 rec,trees=F.build({**h,'zones':[]});tm={q['uuid']:q for q in h['tracks']};vm={q['uuid']:q for q in h['vias']};checks=[];errors=[]
 def record(row):
  checks.append(row)
  if row['actual_mm']+1e-10<row['required_mm']:errors.append(row)
 for t in adds:
  line=LineString([t['a'],t['b']]);body=P.bounded_buffer(line,t['w']/2);l=t['layer']
  for j in trees[l].query(body.buffer(.627),predicate='intersects'):
   a=rec[l][int(j)]
   if C.norm(a['net'])==C.norm(t['net']):continue
   gap=line.distance(a['shape'])-t['w']/2
   if a['kind']=='track':other=tm[a['uuid']];gap=line.distance(LineString([other['a'],other['b']]))-(t['w']+other['w'])/2
   if a['kind']=='via':v=vm[a['uuid']];gap=line.distance(Point(v['x'],v['y']))-(t['w']+v['d'])/2
   record({'owned':t['uuid'],'foreign':a['uuid'],'kind':'track_to_'+a['kind'],'layer':l,'required_mm':G.gap(h,t['net'],a['net'])+.025,'actual_mm':gap})
  for q in z:
   if q['layer']!=l or C.norm(q['net'])==C.norm(t['net']):continue
   req=max(G.gap(h,t['net'],q['net']),float(q.get('clearance_mm',.15)))+.025;gap=line.distance(q['shape'])-t['w']/2
   if gap<req+.01:record({'owned':t['uuid'],'foreign':q['uuid'],'kind':'track_to_newplane','layer':l,'required_mm':req,'actual_mm':gap})
 for v in d['vias']:
  pt=Point(v['x'],v['y'])
  for l in ('F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'):
   for j in trees[l].query(pt.buffer(v['d']/2+.627),predicate='intersects'):
    a=rec[l][int(j)]
    if C.norm(a['net'])==C.norm(v['net']):continue
    gap=pt.distance(a['shape'])-v['d']/2
    if a['kind']=='track':t=tm[a['uuid']];gap=pt.distance(LineString([t['a'],t['b']]))-(v['d']+t['w'])/2
    if a['kind']=='via':other=vm[a['uuid']];gap=pt.distance(Point(other['x'],other['y']))-(v['d']+other['d'])/2
    record({'owned':v['uuid'],'foreign':a['uuid'],'kind':'barrel_to_'+a['kind'],'layer':l,'required_mm':G.gap(h,v['net'],a['net'])+.025,'actual_mm':gap})
  for pad in h['pads']:
   if pad['smd']:
    for l,rs in pad['layers'].items():
     if l not in ('F.Cu','B.Cu'):continue
     sh=unary_union(C.poly(rs));gap=pt.distance(sh)-v['drill']/2
     if gap<.285:record({'owned':v['uuid'],'foreign':pad['uuid'],'kind':'drill_to_every_SMD','layer':l,'required_mm':.275,'actual_mm':gap})
   for sh in C.poly(pad.get('hole') or []):
    gap=pt.distance(sh)-v['drill']/2
    if gap<.285:record({'owned':v['uuid'],'foreign':pad['uuid'],'kind':'drill_to_pad_hole','required_mm':.275,'actual_mm':gap})
  for other in h['vias']:
   if other['uuid']==v['uuid']:continue
   gap=pt.distance(Point(other['x'],other['y']))-(v['drill']+other['drill'])/2
   if gap<.285:record({'owned':v['uuid'],'foreign':other['uuid'],'kind':'drill_to_every_via_hole','required_mm':.275,'actual_mm':gap})
 for q in z:
  if q['uuid'] not in {x['uuid'] for x in newq}|set(updates):continue
  sh=q['shape'];l=q['layer']
  for j in trees[l].query(sh.buffer(.627),predicate='intersects'):
   a=rec[l][int(j)]
   if C.norm(a['net'])==C.norm(q['net']):continue
   gap=sh.distance(a['shape'])
   if a['kind']=='track':t=tm[a['uuid']];gap=sh.distance(LineString([t['a'],t['b']]))-t['w']/2
   if a['kind']=='via':v=vm[a['uuid']];gap=sh.distance(Point(v['x'],v['y']))-v['d']/2
   record({'owned':q['uuid'],'foreign':a['uuid'],'kind':'plane_to_'+a['kind'],'layer':l,'required_mm':max(G.gap(h,q['net'],a['net']),float(q.get('clearance_mm',.15)))+.025,'actual_mm':gap})
  for peer in z:
   if peer['uuid']==q['uuid'] or peer['layer']!=l or C.norm(peer['net'])==C.norm(q['net']):continue
   req=max(G.gap(h,q['net'],peer['net']),float(q.get('clearance_mm',.15)),float(peer.get('clearance_mm',.15)))+.025;gap=sh.distance(peer['shape'])
   if gap<req+.01:record({'owned':q['uuid'],'foreign':peer['uuid'],'kind':'plane_to_newplane','layer':l,'required_mm':req,'actual_mm':gap})
 write(O/'analytic-checks.json',checks);write(O/'analytic-errors.json',errors);print('R254 analytic',len(checks),len(errors),flush=True);oldgroups=pickle.loads((baseline/'groups.pkl').read_bytes());newgroups={};contacts=[]
 for net in sorted(oldgroups):
  old=oldgroups[net];new=F.graph(after,net);newgroups[net]=new;oldret=[[q for q in xs if not(q['kind']=='track' and q['uuid'] in removed)] for xs in old];bad=losses(oldret,new);contacts.append({'net':net,'baseline_retained_relationship_losses':bad});write(O/'contact-checkpoint.json',contacts);print('R254 contact',net,len(bad),flush=True)
 sources=[];refs=[]
 for net,ref,pin in [('/motherboard_motors/FIELD_GND','J11003','2'),('/motherboard_do/FIELD_B_0V','J11005','2'),('/LOGIC_GND','J11001','2'),('/motherboard_power_entry/FIELD_A_24V_PROTECTED','U11004','17'),('/motherboard_power_entry/FIELD_B_24V_PROTECTED','U11006','17')]:
  root=lambda gs:next(xs for xs in gs if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin) for q in xs));old,new=root(oldgroups[net]),root(newgroups[net]);lost=F.discrete_keys(old)-{('track',uid) for uid in removed}-F.discrete_keys(new);sources.append({'net':net,'source':ref+'.'+pin,'prior_source_keys_lost':[list(k) for k in sorted(lost)]})
  if pin=='2':
   a={out:unary_union([q['shape'] for q in old if q['kind']=='fill' and q['layer']==inner]) for out,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};bb={out:unary_union([q['shape'] for q in new if q['kind']=='fill' and q['layer']==inner]) for out,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};bad,diag=REF.audit(before,a,bb,net,removed=removed);refs.append({'ground':net,'retained_outer_reference_losses':bad,'proof':diag});print('R254 ref',net,len(bad),flush=True)
 memberships=[]
 for net,ref,pin,expected in [('/motherboard_power_entry/FIELD_5V','L11003','2',[('U11017','8'),('U11017','5'),('R11071','1'),('C11064','1'),('R9039','1'),('C11080','1'),('U11013','1'),('U11013','3'),('R11051','1')]),('/motherboard_do/DOB_FIELD_3V3','U11018','1',[('U19008','10')]),('DOB_DO_FIELD_3V3','U11038','1',[('U10017','4')])]:
  root=next(xs for xs in newgroups[net] if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin) for q in xs));memberships.append({'net':net,'source':ref+'.'+pin,'expected':expected,'all_expected_actual_source_rooted':all(any(q['kind']=='pad' and(q['ref'],q['pin'])==tuple(pair) for q in root) for pair in expected)})
 b['REG_R254_explicit_guard_delta_projection']={'parent_passing_model_sha256':sha(baseline/'model.pkl'),'projection_interface_file':str((H/'immutable_baseline_analytic_guard_supplements_r252.py').resolve()),'projection_interface_sha256':sha(H/'immutable_baseline_analytic_guard_supplements_r252.py'),'native_original_definition_unchanged':True,'conservative_host_only_no_reclaimed_old_Cu_credit':True,'untrimmed_FBG_R233_receipt_sha256':sha(correction/'receipt.json'),'FIELD5_reference_correction_sha256':sha(field/'receipt.json'),'failed_FIELD5_938_and_old_C5_excluded':True,'actual_new_required_guard_checks':len(guard_checks),'actual_new_required_guard_errors':len(guard_errors),'parent_independent_and_native_checks_required':True};(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,after),protocol=5));(O/'groups.pkl').write_bytes(pickle.dumps(newgroups,protocol=5));(O/'proposed-discrete.pkl').write_bytes(pickle.dumps({'vias':d['vias'],'tracks':adds},protocol=5));(O/'new-owned-zones.pkl').write_bytes(pickle.dumps([q for q in z if q['uuid'] in {p['uuid'] for p in newq}],protocol=5));write(O/'contact-rows.json',contacts);write(O/'source-rows.json',sources);write(O/'reference-rows.json',refs);write(O/'memberships.json',memberships);write(O/'oldfill-retreats.json',retreat);write(O/'owned-via-normalization.json',viafix);write(O/'owned-track-normalization.json',trackfix);ok=not errors and not guard_errors and c_ref_gap<1e-9 and not any(q['baseline_retained_relationship_losses'] for q in contacts) and not any(q['prior_source_keys_lost'] for q in sources) and not any(q['retained_outer_reference_losses'] for q in refs) and all(q['all_expected_actual_source_rooted'] for q in memberships);write(O/'receipt.json',{'verdict':'REG_SEVEN_CURRENT_HEAD_CONSERVATIVE_HOST_PASS' if ok else 'REG_SEVEN_CURRENT_HEAD_CONSERVATIVE_REPAIR_REQUIRED','baseline_sha256':sha(baseline/'model.pkl'),'explicit_alternative_conservative_host_projection_only':True,'projection_interface_sha256':sha(H/'immutable_baseline_analytic_guard_supplements_r252.py'),'actual_required_guard_errors':len(guard_errors),'actual_required_guard_checks':len(guard_checks),'C1022_later_reference_gap_mm2':c_ref_gap,'model_sha256':sha(O/'model.pkl'),'groups_sha256':sha(O/'groups.pkl'),'analytic_checks':len(checks),'analytic_errors':len(errors),'checked_zone_nets':len(contacts),'contact_rows_sha256':sha(O/'contact-rows.json'),'source_rows_sha256':sha(O/'source-rows.json'),'reference_rows_sha256':sha(O/'reference-rows.json'),'memberships_sha256':sha(O/'memberships.json'),'exact_removed_original_UUIDs':sorted(removed),'new_vias':len(d['vias']),'new_tracks':len(adds),'new_plane_UUIDs':[q['uuid'] for q in newq],'all_original_unknown_sharing_full_TPS274_current_barrel_mesh_native_fault_thermal_GATES':'OPEN','board_written':False,'native_jobs':0});print('R254 complete',ok,sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
