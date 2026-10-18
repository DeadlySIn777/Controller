"""Independent all-net/true-aperture audit of the concrete static+bleed repair."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_u17_u10017_coupled_power_repairs_r155.py').read_text(encoding='utf-8')
s=s.replace("O=H/'u17-u10017-coupled-incremental-audit-r155'","O=H/'R11054-static-and-bleed-full-contact-audit-r204'")
start=s.index(' assert not O.exists();O.mkdir();baseline=');end=s.index('rec,trees=F.build',start)
pre=r''' assert not O.exists();O.mkdir()
 from shapely import set_precision,get_precision
 from restore_SAFE_generated_precision_states_r168 import restore_bound_generated_precision_states
 baseline=H/'U10017-wider-on-exact-IO3-audit-r195';assert sha(baseline/'model.pkl')=='103f9dbba8ac50bd90a913d4a7004cd94c3a06ed07d7ab5262c84de6c358f8ab'
 g,h,b,z,prior=pickle.loads((baseline/'model.pkl').read_bytes());h=copy.deepcopy(h);b=copy.deepcopy(b);z=copy.deepcopy(z);states=restore_bound_generated_precision_states(b,z);write(O/'baseline-restored-precision-state-ledger.json',states)
 print('R204 exact latest IO3/U10017 paired baseline',flush=True);before,basecuts=P.projected(g,h,z);zoneset=sorted({C.norm(q['net']) for q in before['zones']});oldgroups={net:F.graph(before,net) for net in zoneset}
 Q=H/'R11054-fault-preserving-exact-AUX-wall-r192';r=json.loads((Q/'receipt.json').read_text(encoding='utf-8'));nd=pickle.loads((Q/'nomination.pkl').read_bytes());oldpad=next(q for q in h['pads'] if q['uuid']==nd['pad1']['uuid']);assert oldpad==r['old_pad1'];oldfp=next(q for q in h['footprints'] if q['ref']=='R11054');assert oldfp==r['old_FP'];newfp=copy.deepcopy(nd['footprint']);newfp['rot']=90;h['footprints']=[newfp if q['ref']=='R11054' else q for q in h['footprints']];h['pads']=[nd['pad1'] if q['uuid']==oldpad['uuid'] else q for q in h['pads']]
 removed={q['uuid'] for q in r['owned_original_two_tracks']};assert all(next(q for q in h['tracks'] if q['uuid']==row['uuid'])==row for row in r['owned_original_two_tracks'])
 R=H/'R11054-and-AUX-bleed-source-feed-r202';assert sha(R/'receipt.json')=='6692a33a6e9e3afda32eeca87140a7150dc7207ba5bc39f4181dc28b1edd9258';nom=json.loads((R/'receipt.json').read_text(encoding='utf-8'));d=pickle.loads((R/'proposed-discrete.pkl').read_bytes());strap=pickle.loads((H/'R11054-static-strap-AUX-bleed-search-base-r202/new-FIELD5-static-strap.pkl').read_bytes());adds=d['tracks']+strap;assert len(d['vias'])==1 and len(adds)==3;h['tracks']=[q for q in h['tracks'] if q['uuid'] not in removed]+adds;h['vias']+=d['vias'];newq=pickle.loads((R/'proposed-zones.pkl').read_bytes());assert len(newq)==1
 current={q['uuid']:q for q in z};base_owned=copy.deepcopy(current);replays=[]
 for row in nom['owned_return_carves']:
  q=current[row['owned_new_return_uuid']];cf=Path(row['cutter_file']);assert sha(cf)==row['cutter_sha256'];from shapely import from_wkb
  cutter=from_wkb(cf.read_bytes());assert row['clearance_and_guard_mm']==.175
  oldsh=q['shape'];oldout=q['zone_outline_shape'];q['shape']=set_precision(oldsh.difference(cutter),1e-6);q['zone_outline_shape']=set_precision(oldout.difference(cutter),1e-6);replays.append({'owned_UUID':q['uuid'],'same_frozen_cutter_SHA256':sha(cf),'required_guard_mm':.175,'actual_latest_physical_before_SHA256':P.digest(oldsh),'actual_latest_physical_after_SHA256':P.digest(q['shape']),'actual_latest_intended_before_SHA256':P.digest(oldout),'actual_latest_intended_after_SHA256':P.digest(q['zone_outline_shape']),'stale_source_shape_was_not_substituted':True})
 z,viafix=P.normalize_owned_via_guards({**h,'vias':d['vias']},z);z,trackfix,geoms=TG.normalize_owned_track_guards({**h,'tracks':adds},z);newq,nvg=P.normalize_owned_via_guards(h,newq);newq,ntg,ng=TG.normalize_owned_track_guards(h,newq);viafix+=nvg;trackfix+=ntg;geoms.update(ng);updates={q['uuid']:q for q in z if any(P.digest(q[role])!=P.digest(base_owned[q['uuid']][role]) for role in ('shape','zone_outline_shape'))};z+=newq
 precision=[]
 for q in z:
  for role in ('shape','zone_outline_shape'):
   raw=q[role].wkb;loaded=get_precision(q[role]);q[role]=set_precision(q[role],1e-6,mode='pointwise');assert raw==q[role].wkb;precision.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':P.digest(q[role]),'loaded_grid_mm':loaded,'exact_WKB_unchanged':True})
 b['generated_precision_state_ledger']=precision;write(O/'derived-generated-precision-state-ledger.json',precision);write(O/'exact-latest-owned-return-cutter-replay.json',replays);write(O/'exact-moved-FP-pad-contact-ledger.json',{'old_FP':oldfp,'new_FP':newfp,'native_old_pose':[221,41.25,-90],'native_new_pose':[221,42.9,90],'old_pad1':oldpad,'new_pad1':nd['pad1'],'pin2_unchanged':r['old_pad2'],'old_2_tracks':r['owned_original_two_tracks'],'old_pin1_discrete_contacts':[],'source_BOM_node_roles_FAULT_control_and_all_output_limits_unchanged':True})
 print('R204 full candidate projection',flush=True);after,retreat=P.projected(g,h,z)
 '''
s=s[:start]+pre+s[end:]
s=s.replace("oldgroups=pickle.loads((baseline/'REG_R130-regional-groups.pkl').read_bytes());newgroups={}","newgroups={}")
# Treat the moved SMD pad as a new aperture exposure, even to an old same-net via.
mark=" write(O/'analytic-checks.json',checks)"
extra=r''' moved=nd['pad1'];sh=unary_union(C.poly(moved['layers']['F.Cu']))
 for j in trees['F.Cu'].query(sh.buffer(.627),predicate='intersects'):
  a=rec['F.Cu'][int(j)]
  if a['uuid']==moved['uuid'] or C.norm(a['net'])==C.norm(moved['net']):continue
  gap=sh.distance(a['shape'])
  if a['kind']=='track':t=tm[a['uuid']];gap=sh.distance(LineString([t['a'],t['b']]))-t['w']/2
  if a['kind']=='via':v=vm[a['uuid']];gap=sh.distance(Point(v['x'],v['y']))-v['d']/2
  record({'owned':moved['uuid'],'foreign':a['uuid'],'kind':'moved_supply_pad_to_'+a['kind'],'layer':'F.Cu','required_mm':G.gap(h,moved['net'],a['net'])+.025,'actual_mm':gap})
 for v in h['vias']:
  gap=Point(v['x'],v['y']).distance(sh)-v['drill']/2
  if gap<.285:record({'owned':moved['uuid'],'foreign':v['uuid'],'kind':'moved_SMD_to_every_old_new_drill','required_mm':.275,'actual_mm':gap})
 from shapely.geometry import box
 for p in h['pads']:
  for hole in C.poly(p.get('hole') or []):
   gap=box(*hole.bounds).distance(sh)
   if gap<.285:record({'owned':moved['uuid'],'foreign':p['uuid'],'kind':'moved_SMD_to_pad_drill_conservative_box','required_mm':.275,'actual_mm':gap})
 for other in h['footprints']:
  if other['ref']=='R11054':continue
  courtyard=unary_union(C.poly(other['courtyard'].get('F',[])));area=nd['new_courtyard'].intersection(courtyard).area
  if area>1e-12:record({'owned':'R11054','foreign':other['ref'],'kind':'moved_courtyard_overlap','required_mm':0,'actual_mm':-area})
 '''
s=s.replace(mark,extra+mark)
old="[('/motherboard_power_entry/FIELD_5V','L11003','2',[('U11017','8'),('U11017','5')]),('DOB_DO_FIELD_3V3','U11038','1',[('U10017','4')]),('/motherboard_power_entry/FIELD_B_24V_PROTECTED','U11006','17',[('U10017',str(i)) for i in (34,35,36,37)])]"
new="[('/motherboard_power_entry/FIELD_5V','L11003','2',[('R11054','1')]),('/motherboard_motors/AUX_5V_B','U11014','6',[('R11055','1')]),('/motherboard_motors/FIELD_GND','J11003','2',[('U11014','2'),('R11055','2')])]"
assert old in s;s=s.replace(old,new)
start=s.index(" b['U11017_owned_dead_spur_local_join_r138']");end=s.index(";(O/'model.pkl')",start)
s=s[:start]+" b['R11054_rotated_static_and_AUX_bleed_repair_r204']={'exact_FP_pad_and_track_ledger_file':str((O/'exact-moved-FP-pad-contact-ledger.json').resolve()),'exact_ledger_sha256':sha(O/'exact-moved-FP-pad-contact-ledger.json'),'native_root_only_rotation_and_two_track_delete_adapters_required':True,'current_model_full16DO_12motor_limits_unchanged':True,'independent_native_pose_plus_full_graph_current_fault_gates':'OPEN'}"+s[end:]
s=s.replace("'baseline_sha256':sha(baseline/'REG_R130-regional-model.pkl'),'baseline_known_R142_IO3_split_UNRESOLVED_AND_NOT_WAIVED':True,'baseline_grid_primitive_R153_review_separate':True","'baseline_sha256':sha(baseline/'model.pkl'),'exact_latest_IO3_R183_and_U10017_R195_baseline':True,'no_failed_REG6_or_U17_appended':True")
s=s.replace('INCREMENTAL_U17_U10017_SOURCE_CONTACT_REFERENCE_ANALYTIC_PASS','R11054_STATIC_AND_AUX_BLEED_SOURCE_CONTACT_REFERENCE_ANALYTIC_PASS').replace('COUPLED_U17_U10017_REPAIR_REQUIRED','R11054_STATIC_AND_AUX_BLEED_REPAIR_REQUIRED').replace('R155','R204')
exec(compile(s,str(H/'audit_u17_u10017_coupled_power_repairs_r155.py'),'exec'))
