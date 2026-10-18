"""Independently qualify the useful U10017 correction, with full-current neck."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_u17_u10017_coupled_power_repairs_r155.py').read_text(encoding='utf-8')
s=s.replace("O=H/'u17-u10017-coupled-incremental-audit-r155'","O=H/'SAFE-U10017-wider-full-branch-audit-r178'")
start=s.index(' assert not O.exists();O.mkdir();baseline=');end=s.index('rec,trees=F.build',start)
pre=''' assert not O.exists();O.mkdir()
 from shapely import set_precision,get_precision
 from restore_SAFE_generated_precision_states_r168 import restore_bound_generated_precision_states
 baseline=H.parent/'sbc-power/SAFE-repaired-owned-zone-normalization-r160';assert sha(baseline/'model.pkl')=='d7e0fe77a8ee25fef4e45538da29aa72809c102192879330c7a5b32a200e711b'
 g,h,b,z,frozen_global=pickle.loads((baseline/'model.pkl').read_bytes());h=copy.deepcopy(h);b=copy.deepcopy(b);z=copy.deepcopy(z)
 states=restore_bound_generated_precision_states(b,z);write(O/'baseline-restored-precision-state-ledger.json',states)
 print('R178 exact SAFE paired regional baseline',flush=True);before,basecuts=P.projected(g,h,z)
 zoneset=sorted({C.norm(q['net']) for q in before['zones']});oldgroups={net:F.graph(before,net) for net in zoneset}
 (O/'baseline-regional-model.pkl').write_bytes(pickle.dumps((g,h,b,z,before),protocol=5));(O/'baseline-regional-groups.pkl').write_bytes(pickle.dumps(oldgroups,protocol=5))
 R=H/'u17-u10017-reference-safe-incremental-audit-r162';assert sha(R/'receipt.json')=='10bae09e7343683d918e333a19e43b90906b15fb794fcdd7be401ef7176b609a';orig=pickle.loads((R/'proposed-discrete.pkl').read_bytes())
 d={'vias':[v for v in orig['vias'] if v['uuid']=='c55416b9-e522-5cbf-9523-ddb093be9249'],'tracks':[t for t in orig['tracks'] if C.norm(t['net'])!='/motherboard_power_entry/FIELD_5V']};assert len(d['vias'])==1 and len(d['tracks'])==3
 W=H/'u10017-wider-owned-source-neck-screen-r172';assert sha(W/'receipt.json')=='bd8a903b82d9dd304f8ba5d77cf8240c31fecdda07f907a1f4d7d392d65d8b9b';w=pickle.loads((W/'owned-replacement-track.pkl').read_bytes());old=next(t for t in d['tracks'] if t['uuid']==w['uuid']);assert old['w']==.3 and w['w']==.6 and {k:v for k,v in old.items() if k!='w'}=={k:v for k,v in w.items() if k!='w'}
 write(O/'exact-new-owned-neck-width-replacement.json',{'uuid':w['uuid'],'old_width_mm':.3,'new_width_mm':.6,'all_other_record_fields_exact':True,'old_nominee_receipt_sha256':sha(R/'receipt.json'),'wider_screen_receipt_sha256':sha(W/'receipt.json'),'full_current_interval_A':[.26061632158690984,2.2686163215869097],'current_bound_receipt_sha256':sha(H.parent/'u10017-nine-pad-protected-bypass-current-bound-r48/receipt.json'),'not_equal_VS_sharing':True})
 adds=[w if t['uuid']==w['uuid'] else t for t in d['tracks']];d['tracks']=adds
 removed={'5c6ebac9-c76a-41f1-8cb8-45e2321f2e89'};assert removed<={t['uuid'] for t in h['tracks']};h['tracks']=[t for t in h['tracks'] if t['uuid'] not in removed]+adds;assert not({v['uuid'] for v in h['vias']}&{v['uuid'] for v in d['vias']});h['vias']+=d['vias']
 newq=pickle.loads((R/'new-owned-zones.pkl').read_bytes());assert len(newq)==1 and newq[0]['uuid'].startswith('e8ec0287')
 base_owned={q['uuid']:copy.deepcopy(q) for q in z}
 z,viafix=P.normalize_owned_via_guards({**h,'vias':d['vias']},z);z,trackfix,geoms=TG.normalize_owned_track_guards({**h,'tracks':adds},z)
 newq,nvg=P.normalize_owned_via_guards(h,newq);newq,ntg,ng=TG.normalize_owned_track_guards(h,newq);viafix+=nvg;trackfix+=ntg;geoms.update(ng)
 updates={q['uuid']:q for q in z if any(P.digest(q[role])!=P.digest(base_owned[q['uuid']][role]) for role in ('shape','zone_outline_shape'))};z+=newq
 precision=[]
 for q in z:
  for role in ('shape','zone_outline_shape'):
   raw=q[role].wkb;loaded=get_precision(q[role]);q[role]=set_precision(q[role],1e-6,mode='pointwise');assert raw==q[role].wkb;precision.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':P.digest(q[role]),'loaded_grid_mm':loaded,'exact_WKB_unchanged':True})
 b['restored_generated_grid_UUIDs']=[q['uuid'] for q in z];b['generated_precision_state_ledger']=precision;write(O/'derived-generated-precision-state-ledger.json',precision)
 print('R178 U10017-only candidate full projection',flush=True);after,retreat=P.projected(g,h,z)
 r154=H/'u10017-reference-safe-source-bypass-nominee-r160';nom=json.loads((r154/'receipt.json').read_text(encoding='utf-8'))
 '''
s=s[:start]+pre+s[end:]
s=s.replace("oldgroups=pickle.loads((baseline/'REG_R130-regional-groups.pkl').read_bytes());newgroups={}","newgroups={}")
s=s.replace("[('/motherboard_power_entry/FIELD_5V','L11003','2',[('U11017','8'),('U11017','5')]),('DOB_DO_FIELD_3V3'","[('DOB_DO_FIELD_3V3'")
start=s.index(" b['U11017_owned_dead_spur_local_join_r138']");end=s.index(";(O/'model.pkl')",start)
s=s[:start]+" b['U10017_reference_safe_wider_source_bypass_r178']={'native_exact_delete_adapter_required':True,'native_old_recipe_file':str((H/'u10017-reference-safe-native-owned-recipe-r166/receipt.json').resolve()),'native_old_recipe_sha256':sha(H/'u10017-reference-safe-native-owned-recipe-r166/receipt.json'),'explicit_new_neck_width_override_file':str((O/'exact-new-owned-neck-width-replacement.json').resolve()),'new_barrel_UUID':'c55416b9-e522-5cbf-9523-ddb093be9249','new_root_owned_R9_barrel_UUID':'a7ee4fd8-3850-567a-b9d7-3b25a458757a','all_output_limits_and_full9pad_current_preserved':True}"+s[end:]
s=s.replace("'baseline_sha256':sha(baseline/'REG_R130-regional-model.pkl'),'baseline_known_R142_IO3_split_UNRESOLVED_AND_NOT_WAIVED':True,'baseline_grid_primitive_R153_review_separate':True","'baseline_sha256':sha(baseline/'model.pkl'),'exact_SAFE_R160_no_failed_REG6_or_U17_added':True,'paired_regional_baseline_and_all_bound_precision_tags_restored':True")
s=s.replace("'INCREMENTAL_U17_U10017_SOURCE_CONTACT_REFERENCE_ANALYTIC_PASS'","'SAFE_U10017_ONLY_WIDER_FULL_BRANCH_SOURCE_CONTACT_REFERENCE_ANALYTIC_PASS'").replace("'COUPLED_U17_U10017_REPAIR_REQUIRED'","'SAFE_U10017_ONLY_REPAIR_REQUIRED'").replace('R155','R178')
exec(compile(s,str(H/'audit_u17_u10017_coupled_power_repairs_r155.py'),'exec'))
