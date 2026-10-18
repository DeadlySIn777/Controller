"""Exact latest SAFE replay, paired regional baseline, full76 contact gate."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_u17_u10017_coupled_power_repairs_r155.py').read_text(encoding='utf-8')
s=s.replace("O=H/'u17-u10017-coupled-incremental-audit-r155'","O=H/'SAFE-regulated-u17-u10017-paired-regional-audit-r170'")
start=s.index(' assert not O.exists();O.mkdir();baseline=');end=s.index('rec,trees=F.build',start)
pre=''' assert not O.exists();O.mkdir()
 from shapely import set_precision,from_wkb,get_precision
 from restore_SAFE_generated_precision_states_r168 import restore_bound_generated_precision_states
 baseline=H.parent/'sbc-power/SAFE-repaired-owned-zone-normalization-r160';assert sha(baseline/'model.pkl')=='d7e0fe77a8ee25fef4e45538da29aa72809c102192879330c7a5b32a200e711b'
 g,h,b,z,frozen_global=pickle.loads((baseline/'model.pkl').read_bytes());h=copy.deepcopy(h);b=copy.deepcopy(b);z=copy.deepcopy(z)
 states=restore_bound_generated_precision_states(b,z);write(O/'baseline-restored-precision-state-ledger.json',states)
 base_owned={q['uuid']:copy.deepcopy(q) for q in z}
 print('R170 exact SAFE paired regional baseline',flush=True);before,basecuts=P.projected(g,h,z)
 frozen_receipt=json.loads((baseline/'receipt.json').read_text(encoding='utf-8'))
 def primitive_map(rows):return {(r['zone_uuid'],r['layer'],c['uuid'],c['kind']):(c['clearance_mm_before_guard'],c['outward_cutter_WKB_SHA256']) for r in rows for c in r.get('cutters',[])}
 fm=primitive_map(frozen_receipt['old_fill_retreats']);rm=primitive_map(basecuts);badprim=[{'key':list(k),'frozen':fm.get(k),'regional':v} for k,v in rm.items() if fm.get(k)!=v]
 write(O/'baseline-regional-primitive-check.json',{'retained_primitive_hash_and_guard_mismatches':badprim,'regional_row_count':len(rm),'frozen_row_count':len(fm),'excluded_disjoint_row_count':len(set(fm)-set(rm)),'row_set_membership_distinguished_from_retained_primitive_identity':True});assert not badprim
 zoneset=sorted({C.norm(q['net']) for q in before['zones']});oldgroups={net:F.graph(before,net) for net in zoneset}
 (O/'baseline-regional-model.pkl').write_bytes(pickle.dumps((g,h,b,z,before),protocol=5));(O/'baseline-regional-groups.pkl').write_bytes(pickle.dumps(oldgroups,protocol=5));write(O/'baseline-regional-retreats.json',basecuts)
 region_changes=[];gg={q['uuid']:q for q in frozen_global['zones']}
 for q in before['zones']:
  prior=gg[q['uuid']]
  for layer,rings in q['fills'].items():
   a=unary_union(C.poly(prior['fills'][layer]));bb=unary_union(C.poly(rings));delta=a.symmetric_difference(bb).area
   if delta:region_changes.append({'zone_uuid':q['uuid'],'layer':layer,'global_to_regional_symmetric_difference_mm2':delta,'removed_mm2':a.difference(bb).area,'added_mm2':bb.difference(a).area})
 write(O/'baseline-global-to-regional-deltas.json',region_changes)
 R=H/'u17-u10017-reference-safe-incremental-audit-r162';assert sha(R/'receipt.json')=='10bae09e7343683d918e333a19e43b90906b15fb794fcdd7be401ef7176b609a';d=pickle.loads((R/'proposed-discrete.pkl').read_bytes());rd=pickle.loads((H/'regulated-four-retained-hard-snapshot-r127/proposed-discrete.pkl').read_bytes()) if (H/'regulated-four-retained-hard-snapshot-r127/proposed-discrete.pkl').exists() else pickle.loads((H/'regulated-peer-screen-hard-subset-r127/proposed-discrete.pkl').read_bytes())
 d={'tracks':d['tracks']+rd['tracks'],'vias':d['vias']+rd['vias']};assert len(d['vias'])==4 and len(d['tracks'])==13
 u17=H/'u11017-dead-spur-native-owned-recipe-r138';u17r=json.loads((u17/'receipt.json').read_text(encoding='utf-8'));removed={r['uuid'] for r in u17r['delete_rows']}|{'5c6ebac9-c76a-41f1-8cb8-45e2321f2e89'};assert removed<={t['uuid'] for t in h['tracks']};adds=d['tracks'];h['tracks']=[t for t in h['tracks'] if t['uuid'] not in removed]+adds;assert not ({v['uuid'] for v in h['vias']}&{v['uuid'] for v in d['vias']});h['vias']+=d['vias']
 r154=H/'u10017-reference-safe-source-bypass-nominee-r160';nom=json.loads((r154/'receipt.json').read_text(encoding='utf-8'))
 oldreg=pickle.loads((R/'model.pkl').read_bytes())[3];ids={'14623f29','1d678466','eafcf5b7','3b972691','c5ba529f'};newq=[q for q in oldreg if q['uuid'][:8] in ids]+pickle.loads((R/'new-owned-zones.pkl').read_bytes());assert len(newq)==6
 R169=H/'field5-exact-IO3-preserving-alternate-r169';assert sha(R169/'receipt.json')=='8348b2133371e1631ace540632bc153a1759b0752f1b2d4122f149a92c17722b';newq+=pickle.loads((R169/'proposed-zones.pkl').read_bytes());assert len(newq)==7
 carve=json.loads((R169/'receipt.json').read_text(encoding='utf-8'))['owned_return_carves'][0];cf=Path(carve['cutter_file']);assert sha(cf)==carve['cutter_sha256'];cutter=from_wkb(cf.read_bytes());canonical=next(q for q in z if 'ded2b949-0c87-5603-874b-a41f2f152e69' in q.get('constituent_proposal_UUIDs',[]));assert canonical['uuid']=='e2fe644a-2849-5c69-8ebb-d1e94909cd4c' and canonical['layer']=='In2.Cu' and C.norm(canonical['net'])=='/motherboard_motors/FIELD_GND'
 replay=[]
 for role in ('shape','zone_outline_shape'):
  prior=canonical[role];aftershape=set_precision(prior.difference(cutter),1e-6);file=O/(canonical['uuid']+'.'+role+'.removed.wkb');file.write_bytes(prior.difference(aftershape).wkb);(O/(canonical['uuid']+'.'+role+'.gained.wkb')).write_bytes(aftershape.difference(prior).wkb);replay.append({'canonical_owned_uuid':canonical['uuid'],'authorized_constituent':'ded2b949-0c87-5603-874b-a41f2f152e69','role':role,'before_WKB_SHA256':P.digest(prior),'after_WKB_SHA256':P.digest(aftershape),'exact_cutter_sha256':sha(cf),'removed_area_mm2':prior.difference(aftershape).area,'added_quantization_area_mm2':aftershape.difference(prior).area,'removed_file_sha256':sha(file)});canonical[role]=aftershape
 write(O/'canonical-FAG-In2-owned-cutter-replay.json',replay)
 z,viafix=P.normalize_owned_via_guards({**h,'vias':d['vias']},z);z,trackfix,geoms=TG.normalize_owned_track_guards({**h,'tracks':adds},z)
 for q in newq:
  for role in ('shape','zone_outline_shape'):
   if role in q:
    raw=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert q[role].wkb==raw
 newq,nvg=P.normalize_owned_via_guards(h,newq);newq,ntg,ng=TG.normalize_owned_track_guards(h,newq);viafix+=nvg;trackfix+=ntg;geoms.update(ng);updates={q['uuid']:q for q in z if any(P.digest(q[role])!=P.digest(base_owned[q['uuid']][role]) for role in ('shape','zone_outline_shape'))};z+=newq
 print('R170 candidate full regional projection',flush=True);after,retreat=P.projected(g,h,z);
'''
s=s[:start]+pre+s[end:]
s=s.replace("oldgroups=pickle.loads((baseline/'REG_R130-regional-groups.pkl').read_bytes());newgroups={}","newgroups={}")
s=s.replace("'baseline_sha256':sha(baseline/'REG_R130-regional-model.pkl'),'baseline_known_R142_IO3_split_UNRESOLVED_AND_NOT_WAIVED':True,'baseline_grid_primitive_R153_review_separate':True", "'baseline_sha256':sha(baseline/'model.pkl'),'paired_consistently_regional_baseline':True,'exact_bound_72_precision_tags_restored_WKB_unchanged':True,'retained_frozen_guard_primitive_hash_and_gap_check_pass':not badprim,'baseline_global_to_regional_deltas_explicit':True,'old_R142_IO3_split_remains_failed_history_NOT_WAIVED':True")
s=s.replace('R155','R170')
s=s.replace("'INCREMENTAL_U17_U10017_SOURCE_CONTACT_REFERENCE_ANALYTIC_PASS'", "'LATEST_SAFE_REG6_U17_U10017_FULL76_SOURCE_CONTACT_REFERENCE_ANALYTIC_PASS'")
s=s.replace("'COUPLED_U17_U10017_REPAIR_REQUIRED'", "'LATEST_SAFE_REGULATED_REPLAY_REPAIR_REQUIRED'")
s=s.replace("b['U10017_coupled_source_bypass_r154']", "b['U10017_reference_safe_bypass_r166']")
s=s.replace("'new_barrel_UUID':d['vias'][0]['uuid']", "'new_barrel_UUID':'c55416b9-e522-5cbf-9523-ddb093be9249'")
s=s.replace("'native_exact_delete_adapter_required':True", "'native_exact_delete_adapter_required':True,'recipe_file':str((H/'u10017-reference-safe-native-owned-recipe-r166/receipt.json').resolve()),'recipe_sha256':sha(H/'u10017-reference-safe-native-owned-recipe-r166/receipt.json')")
exec(compile(s,str(H/'audit_u17_u10017_coupled_power_repairs_r155.py'),'exec'))
