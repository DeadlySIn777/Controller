"""All-net current-head audit of seven corrected feeds and conservative guard delta."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_u17_u10017_coupled_power_repairs_r155.py').read_text(encoding='utf-8')
s=s.replace("O=H/'u17-u10017-coupled-incremental-audit-r155'","O=H/'REG-seven-corrected-current-head-conservative-delta-audit-r242'")
start=s.index(' assert not O.exists();O.mkdir();baseline=');end=s.index('rec,trees=F.build',start)
pre=r''' assert not O.exists();O.mkdir()
 from shapely import set_precision,from_wkb
 from restore_SAFE_generated_precision_states_r168 import restore_bound_generated_precision_states
 import immutable_baseline_guard_delta_projection_r236 as IP
 baseline=H/'R54-native-wider-IO3-monitor-joint-audit-r214';assert sha(baseline/'model.pkl')=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e'
 bg,bh,bb,bz,before=pickle.loads((baseline/'model.pkl').read_bytes());restore_bound_generated_precision_states(bb,bz)
 parent=H/'B3-envelope-scoped-LOGIC-projection-r233';assert sha(parent/'derived-full-input-model.pkl')=='0c1c16abb3814bb18b4cd0faa6e002022a72e72863d4249ed58528c19da07367';g,h,b,z,_=pickle.loads((parent/'derived-full-input-model.pkl').read_bytes());restore_bound_generated_precision_states(b,z)
 d=pickle.loads((H/'REG-safe-subset-on-current-R214-full-audit-r227/proposed-discrete.pkl').read_bytes());adds=d['tracks'];assert len(d['vias'])==4 and len(adds)==10
 u17=H/'u11017-dead-spur-native-owned-recipe-r138';removed={r['uuid'] for r in json.loads((u17/'receipt.json').read_text(encoding='utf-8'))['delete_rows']};assert len(removed)==3 and {t['uuid'] for t in bh['tracks']}-removed=={t['uuid'] for t in h['tracks']}-{t['uuid'] for t in adds}
 correction=H/'B3-subset-inherited-FBG-native-LOGIC-guard-correction-r241';assert sha(correction/'receipt.json')=='e5ff45971197b25eb36397bf77f567ecfdfa725195addc98506636aed8928aac';cq=pickle.loads((correction/'corrected-owned-FBG-zone.pkl').read_bytes())[0];prior=next(q for q in z if q['uuid']==cq['uuid']);cr=json.loads((correction/'receipt.json').read_text(encoding='utf-8'))
 for row in cr['role_operations']:assert P.digest(prior[row['role']])==row['before_sha256'];cq[row['role']]=set_precision(cq[row['role']],1e-6,mode='pointwise');assert P.digest(cq[row['role']])==row['after_sha256']
 z=[cq if q['uuid']==cq['uuid'] else q for q in z]
 field=H/'FIELD5-current-reference-envelope-correction-r238';assert sha(field/'receipt.json')=='b9758dfc590a221b0e755639bb6d5460971b089a59af712bc472003802dd07c9';fq=pickle.loads((field/'proposed-corrected-zone.pkl').read_bytes())[0]
 for role in ('shape','zone_outline_shape'):raw=fq[role].wkb;fq[role]=set_precision(fq[role],1e-6,mode='pointwise');assert raw==fq[role].wkb
 replays=[];viafix=[];trackfix=[]
 for q in z:
  if q['layer']!='In4.Cu' or C.norm(q['net'])!='/motherboard_motors/FIELD_GND':continue
  cut=P.bounded_buffer(fq['zone_outline_shape'],.175)
  for role in ('shape','zone_outline_shape'):
   old=q[role];q[role]=set_precision(old.difference(cut),1e-6)
   if old.wkb!=q[role].wkb:replays.append({'UUID':q['uuid'],'role':role,'old_sha256':P.digest(old),'new_sha256':P.digest(q[role]),'cutter_sha256':P.digest(cut),'required_gap_mm':.175,'removed_mm2':old.difference(q[role]).area,'added_mm2':q[role].difference(old).area})
 [fq],viafix=P.normalize_owned_via_guards(h,[fq]);[fq],trackfix,geoms=TG.normalize_owned_track_guards(h,[fq]);z.append(fq)
 oldowned={q['uuid']:q for q in bz};newq=[q for q in z if q['uuid'] not in oldowned];assert len(newq)==7 and '938b9038-0f65-5de2-99ed-d6781afcb116' not in {q['uuid'] for q in z};updates={q['uuid']:q for q in z if q['uuid'] in oldowned and any(P.digest(q[role])!=P.digest(oldowned[q['uuid']][role]) for role in ('shape','zone_outline_shape'))}
 precision=[]
 for q in z:
  for role in ('shape','zone_outline_shape'):
   raw=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert raw==q[role].wkb;precision.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':P.digest(q[role]),'exact_WKB_unchanged':True})
 b['generated_precision_state_ledger']=precision;b['restored_generated_grid_UUIDs']=sorted(q['uuid'] for q in z);write(O/'generated-precision-state-ledger.json',precision);write(O/'FIELD5-current-owned-return-cut-replay.json',replays)
 print('R242 complete exact current inputs, conservative all-net projection',flush=True);after,retreat,guard_checks=IP.projected(g,h,z,bh,bz,before);guard_errors=[row for row in guard_checks if not row['PASS']];write(O/'native-actual-fill-vs-new-required-guard-checks.json',guard_checks);write(O/'native-actual-fill-vs-new-required-guard-errors.json',guard_errors);print('R242 actual guard checks',len(guard_checks),len(guard_errors),flush=True)
 # Later additive C1022 remains separate. Its literal source-reference body and
 # physical segment are exact mutual obligations, never appended silently.
 cpacket=H.parent/'sbc-power/C1022-validated-native-integration-packet-r222';assert sha(cpacket/'receipt.json')=='ab63866ae63e1aff6da41f96630346989bdc4d92e9eb2feee499173b37f3ab02';cp=json.loads((cpacket/'receipt.json').read_text(encoding='utf-8'));cb=from_wkb(Path(cp['exact_full_reference_body_file']).read_bytes());assert sha(Path(cp['exact_full_reference_body_file']))==cp['exact_full_reference_body_sha256'];lg=F.graph(after,'/LOGIC_GND');lgr=next(xs for xs in lg if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11001','2') for q in xs));source_ref=unary_union([q['shape'] for q in lgr if q['kind']=='fill' and q['layer']=='In4.Cu']);c_ref_gap=cb.difference(source_ref).area;write(O/'C1022-later-mutual-reference-check.json',{'packet_sha256':sha(cpacket/'receipt.json'),'actual_full_body_sha256':P.digest(cb),'required_body_missing_actual_J1_source_In4_mm2':c_ref_gap,'C1022_not_appended':True});print('R242 C1022 exact later reference gap',c_ref_gap,flush=True)
 '''
s=s[:start]+pre+s[end:]
s=s.replace("oldgroups=pickle.loads((baseline/'REG_R130-regional-groups.pkl').read_bytes())","oldgroups=pickle.loads((baseline/'groups.pkl').read_bytes())")
start=s.index(" for net,ref,pin,expected in [");end=s.index(':\n  root=',start)
s=s[:start]+" for net,ref,pin,expected in [('/motherboard_power_entry/FIELD_5V','L11003','2',[('U11017','8'),('U11017','5'),('R11071','1'),('C11064','1'),('R9039','1'),('C11080','1'),('U11013','1'),('U11013','3'),('R11051','1')]),('/motherboard_do/DOB_FIELD_3V3','U11018','1',[('U19008','10')]),('DOB_DO_FIELD_3V3','U11038','1',[('U10017','4')])]"+s[end:]
start=s.index(" b['U11017_owned_dead_spur_local_join_r138']");end=s.index(";(O/'model.pkl')",start)
s=s[:start]+" b['REG_R242_explicit_guard_delta_projection']={'parent_passing_model_sha256':sha(baseline/'model.pkl'),'projection_interface_file':str((H/'immutable_baseline_guard_delta_projection_r236.py').resolve()),'projection_interface_sha256':sha(H/'immutable_baseline_guard_delta_projection_r236.py'),'native_original_definition_unchanged':True,'conservative_host_only_no_reclaimed_old_Cu_credit':True,'owned_FBG_guard_correction_sha256':sha(correction/'receipt.json'),'FIELD5_reference_correction_sha256':sha(field/'receipt.json'),'failed_FIELD5_938_and_old_C5_excluded':True,'actual_new_required_guard_checks':len(guard_checks),'actual_new_required_guard_errors':len(guard_errors),'parent_independent_and_native_checks_required':True}"+s[end:]
s=s.replace("ok=not errors and", "ok=not errors and not guard_errors and c_ref_gap<1e-9 and")
s=s.replace("'baseline_sha256':sha(baseline/'REG_R130-regional-model.pkl'),'baseline_known_R142_IO3_split_UNRESOLVED_AND_NOT_WAIVED':True,'baseline_grid_primitive_R153_review_separate':True","'baseline_sha256':sha(baseline/'model.pkl'),'explicit_alternative_conservative_host_projection_only':True,'projection_interface_sha256':sha(H/'immutable_baseline_guard_delta_projection_r236.py'),'actual_required_guard_errors':len(guard_errors),'actual_required_guard_checks':len(guard_checks),'C1022_later_reference_gap_mm2':c_ref_gap")
s=s.replace('INCREMENTAL_U17_U10017_SOURCE_CONTACT_REFERENCE_ANALYTIC_PASS','REG_SEVEN_CURRENT_HEAD_CONSERVATIVE_HOST_PASS').replace('COUPLED_U17_U10017_REPAIR_REQUIRED','REG_SEVEN_CURRENT_HEAD_CONSERVATIVE_REPAIR_REQUIRED').replace('R155','R242')
exec(compile(s,str(H/'audit_u17_u10017_coupled_power_repairs_r155.py'),'exec'))
