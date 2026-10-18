"""Fresh full-contact replay: exact wider IO3, retained REG feeds and new B3 pair."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_u17_u10017_coupled_power_repairs_r155.py').read_text(encoding='utf-8')
s=s.replace("O=H/'u17-u10017-coupled-incremental-audit-r155'","O=H/'REG-rebuilt-B3-on-wider-IO3-full-audit-r209'")
start=s.index(' assert not O.exists();O.mkdir();baseline=');end=s.index('rec,trees=F.build',start)
pre=r''' assert not O.exists();O.mkdir()
 from shapely import set_precision,get_precision
 from restore_SAFE_generated_precision_states_r168 import restore_bound_generated_precision_states
 baseline=H/'U10017-wider-on-exact-IO3-audit-r195';assert sha(baseline/'model.pkl')=='103f9dbba8ac50bd90a913d4a7004cd94c3a06ed07d7ab5262c84de6c358f8ab'
 g,h,b,z,_=pickle.loads((baseline/'model.pkl').read_bytes());h=copy.deepcopy(h);b=copy.deepcopy(b);z=copy.deepcopy(z);restore_bound_generated_precision_states(b,z)
 W=H.parent/'sbc-power/IO3-wider-minimal-validated-integration-packet-r201';assert sha(W/'receipt.json')=='cee3eacedd73ba63788decafd0a3b169afee6a0fbfa76f76e5acc60e8cc83e2d';wr=json.loads((W/'receipt.json').read_text(encoding='utf-8'));row=wr['only_one_owned_host_group_replacement'][0];oldq=next(q for q in z if q['uuid']==row['old_UUID'])
 for role,proof in row['roles'].items():assert P.digest(oldq[role])==proof['old_sha256'],('old exact IO3 group mismatch',role)
 replacement=pickle.loads((W/'exact-owned-IO3-one-In3-group-replacement.pkl').read_bytes());replacement=replacement[0] if isinstance(replacement,list) else replacement;assert replacement['uuid']==row['new_UUID']
 for role,proof in row['roles'].items():assert P.digest(replacement[role])==proof['new_sha256'];replacement[role]=set_precision(replacement[role],1e-6,mode='pointwise')
 # Preserve newly owned U10017 barrel clearances on the later IO3 group explicitly.
 c554=next(v for v in h['vias'] if v['uuid']=='c55416b9-e522-5cbf-9523-ddb093be9249');rq,rebased_via=P.normalize_owned_via_guards({**h,'vias':[c554]},[replacement]);assert len(rq)==1;z=[rq[0] if q['uuid']==oldq['uuid'] else q for q in z]
 b['IO3_R201_exact_one_group_wider_replacement']={'packet':str((W/'receipt.json').resolve()),'sha256':sha(W/'receipt.json'),'actual_U10017_barrel_guard_replay':rebased_via};print('R209 exact widened IO3 baseline',flush=True);before,basecuts=P.projected(g,h,z);oldgroups={net:F.graph(before,net) for net in sorted({C.norm(q['net']) for q in before['zones']})}
 R=H/'SAFE-regulated-u17-u10017-paired-regional-audit-r171';assert sha(R/'receipt.json')=='6be34443033d35d918f6ecebd4ca2d123b6f34cf01d81190153d7812bb8b5a0c';reg=pickle.loads((R/'proposed-discrete.pkl').read_bytes());d={'vias':[v for v in reg['vias'] if v['uuid']!='c55416b9-e522-5cbf-9523-ddb093be9249'],'tracks':[t for t in reg['tracks'] if C.norm(t['net'])=='/motherboard_power_entry/FIELD_5V']};assert len(d['vias'])==3 and len(d['tracks'])==10
 Q=H/'B3-exact-cross-layer-pair-r206';assert sha(Q/'cross-layer-receipt.json')=='3d428acae6b187050fbe6aa5c9f8a79fae6d692df65ce2186302d1fc6f956659';bd=pickle.loads((Q/'cross-layer-discrete.pkl').read_bytes());assert len(bd['vias'])==1 and not bd['tracks'];d['vias']+=bd['vias'];adds=d['tracks'];u17=H/'u11017-dead-spur-native-owned-recipe-r138';u17r=json.loads((u17/'receipt.json').read_text(encoding='utf-8'));removed={q['uuid'] for q in u17r['delete_rows']};assert len(removed)==3 and removed<={q['uuid'] for q in h['tracks']};h['tracks']=[q for q in h['tracks'] if q['uuid'] not in removed]+adds;assert not({v['uuid'] for v in h['vias']}&{v['uuid'] for v in d['vias']});h['vias']+=d['vias']
 newq=[q for q in pickle.loads((R/'new-owned-zones.pkl').read_bytes()) if q['uuid'] not in ('c5ba529f-a864-5662-be39-9d5cf864ee62','e8ec0287-e6d1-597d-8ad8-c4ab74280f6c')];assert len(newq)==5;newq+=pickle.loads((Q/'cross-layer-zones.pkl').read_bytes());assert len(newq)==7 and 'c5ba529f-a864-5662-be39-9d5cf864ee62' not in {q['uuid'] for q in z+newq}
 current={q['uuid']:q for q in z};base_owned=copy.deepcopy(current);replays=[]
 # Derive fresh declared cutters from exact new bodies, never restore stale R171 returns.
 for q in z:
  if q['layer'] not in ('In1.Cu','In2.Cu','In3.Cu','In4.Cu') or C.norm(q['net']) not in ('/motherboard_motors/FIELD_GND','/motherboard_do/FIELD_B_0V') or float(q.get('clearance_mm',.15))!=.15:continue
  foreign=[n['zone_outline_shape'] for n in newq if n['layer']==q['layer'] and C.norm(n['net'])!=C.norm(q['net']) and G.gap(h,n['net'],q['net'])==.15]
  if not foreign:continue
  cutter=P.bounded_buffer(unary_union(foreign),.175);oldsh=q['shape'];oldout=q['zone_outline_shape'];q['shape']=set_precision(oldsh.difference(cutter),1e-6);q['zone_outline_shape']=set_precision(oldout.difference(cutter),1e-6)
  if oldsh.wkb!=q['shape'].wkb or oldout.wkb!=q['zone_outline_shape'].wkb:
   cf=O/(q['uuid']+'.fresh-owned-return-cut.wkb');cf.write_bytes(cutter.wkb);replays.append({'owned_UUID':q['uuid'],'cutter_file':str(cf.resolve()),'cutter_sha256':sha(cf),'physical_before_sha256':P.digest(oldsh),'physical_after_sha256':P.digest(q['shape']),'intended_before_sha256':P.digest(oldout),'intended_after_sha256':P.digest(q['zone_outline_shape']),'required_gap_mm':.175,'added_physical_mm2':q['shape'].difference(oldsh).area,'stale_return_shape_substituted':False})
 z,viafix=P.normalize_owned_via_guards({**h,'vias':d['vias']},z);z,trackfix,geoms=TG.normalize_owned_track_guards({**h,'tracks':adds},z);newq,nvg=P.normalize_owned_via_guards(h,newq);newq,ntg,ng=TG.normalize_owned_track_guards(h,newq);viafix+=nvg;trackfix+=ntg;geoms.update(ng);updates={q['uuid']:q for q in z if any(P.digest(q[role])!=P.digest(base_owned[q['uuid']][role]) for role in ('shape','zone_outline_shape'))};z+=newq
 precision=[]
 for q in z:
  for role in ('shape','zone_outline_shape'):
   raw=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert raw==q[role].wkb;precision.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':P.digest(q[role]),'exact_WKB_unchanged':True})
 b['generated_precision_state_ledger']=precision;write(O/'derived-generated-precision-state-ledger.json',precision);write(O/'actual-latest-owned-return-cutter-replay.json',replays);print('R209 rebuilt pair + retained regulated full projection',flush=True);after,retreat=P.projected(g,h,z)
 '''
s=s[:start]+pre+s[end:]
s=s.replace("oldgroups=pickle.loads((baseline/'REG_R130-regional-groups.pkl').read_bytes());newgroups={}","newgroups={}")
old="[('/motherboard_power_entry/FIELD_5V','L11003','2',[('U11017','8'),('U11017','5')]),('DOB_DO_FIELD_3V3','U11038','1',[('U10017','4')]),('/motherboard_power_entry/FIELD_B_24V_PROTECTED','U11006','17',[('U10017',str(i)) for i in (34,35,36,37)])]"
new="[('/motherboard_power_entry/FIELD_5V','L11003','2',[('U11017','8'),('U11017','5'),('U9002','10'),('R11053','1')]),('/motherboard_do/DOB_FIELD_3V3','U11018','1',[('U19008','10'),('U10013','4')]),('DOB_DO_FIELD_3V3','U11038','1',[('U10017','4')])]"
assert old in s;s=s.replace(old,new)
start=s.index(" b['U11017_owned_dead_spur_local_join_r138']");end=s.index(";(O/'model.pkl')",start)
s=s[:start]+" b['REG_rebuilt_B3_exact_R206_on_wider_IO3_R209']={'U17_remove_only_recipe_file':str((u17/'remove-only-recipe.json').resolve()),'U17_remove_only_recipe_sha256':sha(u17/'remove-only-recipe.json'),'B3_cross_layer_nomination_sha256':sha(Q/'cross-layer-receipt.json'),'failed_C5_withdrawn_exactly':True,'actual_fresh_same_domain_owned_return_cutter_file':str((O/'actual-latest-owned-return-cutter-replay.json').resolve()),'all_device_and_output_limits_current_fault_native_GATES':'OPEN'}"+s[end:]
s=s.replace("'baseline_sha256':sha(baseline/'REG_R130-regional-model.pkl'),'baseline_known_R142_IO3_split_UNRESOLVED_AND_NOT_WAIVED':True,'baseline_grid_primitive_R153_review_separate':True","'baseline_sha256':sha(baseline/'model.pkl'),'exact_IO3_R201_one_q_replay_and_wide_U10017_R195':True,'no_R171_whole_model_or_failed_C5_substitution':True")
s=s.replace('INCREMENTAL_U17_U10017_SOURCE_CONTACT_REFERENCE_ANALYTIC_PASS','REG_REBUILT_B3_WIDER_IO3_SOURCE_CONTACT_REFERENCE_ANALYTIC_PASS').replace('COUPLED_U17_U10017_REPAIR_REQUIRED','REG_REBUILT_B3_WIDER_IO3_REPAIR_REQUIRED').replace('R155','R209')
exec(compile(s,str(H/'audit_u17_u10017_coupled_power_repairs_r155.py'),'exec'))
