"""Exact R54 native-pad replay with one IO3 delta and actual root monitor additions."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_u17_u10017_coupled_power_repairs_r155.py').read_text(encoding='utf-8')
s=s.replace("O=H/'u17-u10017-coupled-incremental-audit-r155'","O=H/'R54-native-wider-IO3-monitor-joint-audit-r213'")
start=s.index(' assert not O.exists();O.mkdir();baseline=');end=s.index('rec,trees=F.build',start)
pre=r''' assert not O.exists();O.mkdir()
 from shapely import set_precision,get_precision
 from restore_SAFE_generated_precision_states_r168 import restore_bound_generated_precision_states
 baseline=H/'R11054-static-and-bleed-full-contact-audit-r205';assert sha(baseline/'receipt.json')=='99d211934c834887b8ec697f7c2e1ad7210bd7e23f8381339668dbf257ec5b3b';assert sha(baseline/'model.pkl')=='110299c8ef1bc459960e62cda2b637fc0a84bb1548fa6c7814f581069c7b11c6';g,h,b,z,_=pickle.loads((baseline/'model.pkl').read_bytes());h=copy.deepcopy(h);b=copy.deepcopy(b);z=copy.deepcopy(z);restore_bound_generated_precision_states(b,z);base_owned={q['uuid']:copy.deepcopy(q) for q in z}
 print('R213 actual R205 paired baseline',flush=True);before,basecuts=P.projected(g,h,z);oldgroups={net:F.graph(before,net) for net in sorted({C.norm(q['net']) for q in before['zones']}|{'/motherboard_motors/AUX_5V_B'})}
 N=H.parent/'field-R11054-native-fault-pin-rotation-r75';assert sha(N/'receipt.json')=='8c1576328972121a3fbc391c63088dc43dc6ce651153d079fe62e62243bb780c';native=json.loads((N/'native-attestation.json').read_text(encoding='utf-8'));assert native['verdict']=='PASS_NATIVE_EXACT_FAULT_PIN_FIXED_R11054_PAD_POSE';nativepads={p['UUID']:p for p in native['native_pads']};padreplay=[]
 for p in h['pads']:
  if p['uuid'] not in nativepads:continue
  n=nativepads[p['uuid']];assert p['ref']==n['ref'] and p['num']==n['num'] and p['net']==n['net'] and [p['x'],p['y']]==[n['x'],n['y']];old=copy.deepcopy(p);p['layers']=n['layers'];p['native_R75_actual_polygon_attestation']=str((N/'native-attestation.json').resolve());padreplay.append({'UUID':p['uuid'],'old_pad':old,'new_actual_native_pad':copy.deepcopy(p),'native_attestation_sha256':sha(N/'native-attestation.json'),'center_raw_node_and_number_unchanged':True})
 assert len(padreplay)==2;write(O/'R54-actual-native-pad-overlay-ledger.json',padreplay)
 W=H.parent/'sbc-power/IO3-wider-minimal-validated-integration-packet-r201';assert sha(W/'receipt.json')=='cee3eacedd73ba63788decafd0a3b169afee6a0fbfa76f76e5acc60e8cc83e2d';wr=json.loads((W/'receipt.json').read_text(encoding='utf-8'));row=wr['only_one_owned_host_group_replacement'][0];oldq=next(q for q in z if q['uuid']==row['old_UUID'])
 for role,proof in row['roles'].items():assert P.digest(oldq[role])==proof['old_sha256'],('old exact IO3 group mismatch',role)
 nq=pickle.loads((W/'exact-owned-IO3-one-In3-group-replacement.pkl').read_bytes());nq=nq[0] if isinstance(nq,list) else nq;assert nq['uuid']==row['new_UUID']
 for role,proof in row['roles'].items():assert P.digest(nq[role])==proof['new_sha256'];nq[role]=set_precision(nq[role],1e-6,mode='pointwise')
 z=[nq if q['uuid']==oldq['uuid'] else q for q in z]
 ROOT=H.parent/'SAFE-monitor-real-source-reference-patch-r73';assert sha(ROOT/'model.pkl')=='719da50c88dc6e2c64b988f81c850875f5f228e9f7407eab5c3cd17e8a44f011';rg,rh,rb,rz,_=pickle.loads((ROOT/'model.pkl').read_bytes());monitor=H.parent/'field-monitor-R9026-rotation-source-termination-r66/owned-delta.pkl';assert sha(monitor)=='2669504846249102a6afe479c78f627b7729d0992c48bc64f79a330f431149c5';md=pickle.loads(monitor.read_bytes());removed={md['removed_old_track']['uuid']};assert next(q for q in h['tracks'] if q['uuid'] in removed)==md['removed_old_track'];adds=md['tracks'];d={'tracks':adds,'vias':md['vias']};h['tracks']=[q for q in h['tracks'] if q['uuid'] not in removed]+adds;assert not({v['uuid'] for v in h['vias']}&{v['uuid'] for v in d['vias']});h['vias']+=d['vias'];rootpads={q['uuid']:q for q in rh['pads'] if q['ref']=='R9026'};assert len(rootpads)==2;h['pads']=[copy.deepcopy(rootpads.get(q['uuid'],q)) for q in h['pads']];rootfp=next(q for q in rh['footprints'] if q['ref']=='R9026');h['footprints']=[copy.deepcopy(rootfp) if q['ref']=='R9026' else q for q in h['footprints']]
 L=H.parent/'SAFE-logic-four-return-restoration-r55/proposed-zones.pkl';assert sha(L)=='b0e3766d17138741ae1f4ab6d2a574e55da6634734b03bec93d6a6abb891e065';lg=pickle.loads(L.read_bytes());assert len(lg)==1;newq=[copy.deepcopy(q) for q in rz if q['uuid'] in {lg[0]['uuid'],'93bd9369-a6ff-537a-8678-5c84db255e75'}];assert len(newq)==2 and not({q['uuid'] for q in newq}&{q['uuid'] for q in z})
 c554=next(v for v in h['vias'] if v['uuid']=='c55416b9-e522-5cbf-9523-ddb093be9249');aux=next(v for v in h['vias'] if v['uuid']=='443de1bc-e954-5a27-b716-da009070c6fb');nqrows,IO3barrelfix=P.normalize_owned_via_guards({**h,'vias':[c554,aux]+d['vias']},[q for q in z if q['uuid']==row['new_UUID']]);assert len(nqrows)==1;z=[nqrows[0] if q['uuid']==row['new_UUID'] else q for q in z]
 z,viafix=P.normalize_owned_via_guards({**h,'vias':d['vias']},z);z,trackfix,geoms=TG.normalize_owned_track_guards({**h,'tracks':adds},z);newq,nvg=P.normalize_owned_via_guards(h,newq);newq,ntg,ng=TG.normalize_owned_track_guards(h,newq);viafix+=nvg+IO3barrelfix;trackfix+=ntg;geoms.update(ng);updates={q['uuid']:q for q in z if q['uuid'] not in base_owned or any(P.digest(q[role])!=P.digest(base_owned[q['uuid']][role]) for role in ('shape','zone_outline_shape'))};z+=newq
 precision=[]
 for q in z:
  for role in ('shape','zone_outline_shape'):
   raw=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert raw==q[role].wkb;precision.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':P.digest(q[role]),'exact_WKB_unchanged':True})
 b['generated_precision_state_ledger']=precision;write(O/'derived-generated-precision-state-ledger.json',precision);print('R213 monitor + native R54 + wider IO3 exact projection',flush=True);after,retreat=P.projected(g,h,z)
 '''
s=s[:start]+pre+s[end:]
s=s.replace("oldgroups=pickle.loads((baseline/'REG_R130-regional-groups.pkl').read_bytes());newgroups={}","newgroups={}")
mark=" write(O/'analytic-checks.json',checks)"
extra=r''' # Every already owned new barrel also sees the actual late peer planes.
 for v in d['vias']+[aux,c554]:
  pt=Point(v['x'],v['y'])
  for q in z:
   if C.norm(q['net'])==C.norm(v['net']):continue
   req=max(G.gap(h,v['net'],q['net']),float(q.get('clearance_mm',.15)))+.025;gap=pt.distance(q['shape'])-v['d']/2
   if gap<req+.01:record({'owned':v['uuid'],'foreign':q['uuid'],'kind':'ordinary_barrel_to_all_actual_newplanes','layer':q['layer'],'required_mm':req,'actual_mm':gap})
 # Actual native moved SMD copper checks every nearby old/new drill, same net included.
 for p in h['pads']:
  if p['ref']!='R11054':continue
  sh=unary_union(C.poly(p['layers']['F.Cu']))
  for v in h['vias']:
   gap=Point(v['x'],v['y']).distance(sh)-v['drill']/2
   if gap<.285:record({'owned':p['uuid'],'foreign':v['uuid'],'kind':'actual_native_R54_pad_to_every_drill','required_mm':.275,'actual_mm':gap})
 '''
s=s.replace(mark,extra+mark)
old="[('/motherboard_power_entry/FIELD_5V','L11003','2',[('U11017','8'),('U11017','5')]),('DOB_DO_FIELD_3V3','U11038','1',[('U10017','4')]),('/motherboard_power_entry/FIELD_B_24V_PROTECTED','U11006','17',[('U10017',str(i)) for i in (34,35,36,37)])]"
new="[('/motherboard_power_entry/FIELD_5V','L11003','2',[('R11054','1')]),('/motherboard_motors/AUX_5V_B','U11014','6',[('R11055','1')]),('/motherboard_motors/FIELD_GND','J11003','2',[('U11014','2'),('R11055','2'),('R9026','2')]),('/IO_3V3','R18001','2',[('R11049','1')])]"
assert old in s;s=s.replace(old,new)
start=s.index(" b['U11017_owned_dead_spur_local_join_r138']");end=s.index(";(O/'model.pkl')",start)
s=s[:start]+" b['R54_native_R75_with_wider_IO3_R201_root_monitor_R73']={'R54_exact_native_pose_file':str((N/'receipt.json').resolve()),'R54_native_pose_sha256':sha(N/'receipt.json'),'R201_one_group_packet_sha256':sha(W/'receipt.json'),'R66_monitor_delta_sha256':sha(monitor),'R73_only_actual_new_planes_and_exact_R9026_native_pads_used':True,'R205_R54_AUX_recipe_still_authoritative':True,'complete_current_fault_and_native_refill_GATES':'OPEN'}"+s[end:]
s=s.replace("'baseline_sha256':sha(baseline/'REG_R130-regional-model.pkl'),'baseline_known_R142_IO3_split_UNRESOLVED_AND_NOT_WAIVED':True,'baseline_grid_primitive_R153_review_separate':True","'baseline_sha256':sha(baseline/'model.pkl'),'native_R54_actual_pad_polygons_and_exact_latest_peer_deltas':True,'no_failed_REG6_or_whole_stale_source_model_appended':True")
s=s.replace('INCREMENTAL_U17_U10017_SOURCE_CONTACT_REFERENCE_ANALYTIC_PASS','R54_NATIVE_WIDER_IO3_MONITOR_SOURCE_CONTACT_REFERENCE_ANALYTIC_PASS').replace('COUPLED_U17_U10017_REPAIR_REQUIRED','R54_NATIVE_WIDER_IO3_MONITOR_REPAIR_REQUIRED').replace('R155','R213')
exec(compile(s,str(H/'audit_u17_u10017_coupled_power_repairs_r155.py'),'exec'))
