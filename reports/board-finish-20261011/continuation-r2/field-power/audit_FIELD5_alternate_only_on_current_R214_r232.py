"""Independent fresh all-net audit of only the R225 alternate FIELD5 proposal."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_u17_u10017_coupled_power_repairs_r155.py').read_text(encoding='utf-8')
s=s.replace("O=H/'u17-u10017-coupled-incremental-audit-r155'","O=H/'FIELD5-alternate-only-current-R214-full-audit-r232'")
start=s.index(' assert not O.exists();O.mkdir();baseline=');end=s.index('rec,trees=F.build',start)
pre=r''' assert not O.exists();O.mkdir()
 from shapely import set_precision
 from restore_SAFE_generated_precision_states_r168 import restore_bound_generated_precision_states
 baseline=H/'R54-native-wider-IO3-monitor-joint-audit-r214';assert sha(baseline/'model.pkl')=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e'
 g,h,b,z,before=pickle.loads((baseline/'model.pkl').read_bytes());h=copy.deepcopy(h);b=copy.deepcopy(b);z=copy.deepcopy(z);restore_bound_generated_precision_states(b,z)
 N=H/'FIELD5-actual-IO3-preserving-alternate-r225';assert sha(N/'receipt.json')=='51e820a0274706c295b936e3a4124f2f38b7707752abcccd7a46b394a9ce80ac';newq=pickle.loads((N/'proposed-zones.pkl').read_bytes());assert len(newq)==1 and newq[0]['uuid']=='61cb8179-7754-5031-bbea-0da464bf816f'
 for q in newq:
  for role in ('shape','zone_outline_shape'):raw=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert raw==q[role].wkb
 d={'vias':[],'tracks':[]};adds=[];removed=set();replays=[];updates={};viafix=[];trackfix=[];base_owned=copy.deepcopy({q['uuid']:q for q in z})
 for q in z:
  if q['layer']!='In4.Cu' or C.norm(q['net'])!='/motherboard_motors/FIELD_GND':continue
  cutter=P.bounded_buffer(newq[0]['zone_outline_shape'],.175)
  for role in ('shape','zone_outline_shape'):
   old=q[role];q[role]=set_precision(old.difference(cutter),1e-6)
   if old.wkb!=q[role].wkb:replays.append({'owned_UUID':q['uuid'],'role':role,'before_sha256':P.digest(old),'after_sha256':P.digest(q[role]),'cutter_sha256':P.digest(cutter),'required_gap_mm':.175,'removed_mm2':old.difference(q[role]).area,'added_mm2':q[role].difference(old).area})
  if q['shape'].wkb!=base_owned[q['uuid']]['shape'].wkb or q['zone_outline_shape'].wkb!=base_owned[q['uuid']]['zone_outline_shape'].wkb:updates[q['uuid']]=q
 newq,viafix=P.normalize_owned_via_guards(h,newq);newq,trackfix,geoms=TG.normalize_owned_track_guards(h,newq);z+=newq
 precision=[]
 for q in z:
  for role in ('shape','zone_outline_shape'):
   raw=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert raw==q[role].wkb;precision.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':P.digest(q[role]),'exact_WKB_unchanged':True})
 b['generated_precision_state_ledger']=precision;b['restored_generated_grid_UUIDs']=sorted(q['uuid'] for q in z);write(O/'owned-return-cutter-replay.json',replays);write(O/'generated-precision-state-ledger.json',precision)
 print('R232 FIELD5 alternate only full projection',flush=True);after,retreat=P.projected(g,h,z);
 '''
s=s[:start]+pre+s[end:]
s=s.replace("oldgroups=pickle.loads((baseline/'REG_R130-regional-groups.pkl').read_bytes())","oldgroups=pickle.loads((baseline/'groups.pkl').read_bytes())")
start=s.index(" for net,ref,pin,expected in [");end=s.index(':\n  root=',start)
s=s[:start]+" for net,ref,pin,expected in [('/motherboard_power_entry/FIELD_5V','L11003','2',[('R11071','1'),('C11064','1'),('R9039','1'),('C11080','1'),('U11013','1'),('U11013','3'),('R11051','1')])]"+s[end:]
start=s.index(" b['U11017_owned_dead_spur_local_join_r138']");end=s.index(";(O/'model.pkl')",start)
s=s[:start]+" b['FIELD5_R225_exact_current_replay']={'nomination_receipt_sha256':sha(N/'receipt.json'),'only_new_zone_UUID':newq[0]['uuid'],'no_failed_REG_or_whole_model_substitution':True,'original_native_definitions_unchanged':True}"+s[end:]
s=s.replace("'baseline_sha256':sha(baseline/'REG_R130-regional-model.pkl'),'baseline_known_R142_IO3_split_UNRESOLVED_AND_NOT_WAIVED':True,'baseline_grid_primitive_R153_review_separate':True","'baseline_sha256':sha(baseline/'model.pkl'),'nomination_receipt_sha256':sha(N/'receipt.json'),'only_FIELD5_alternate_replayed':True")
s=s.replace('INCREMENTAL_U17_U10017_SOURCE_CONTACT_REFERENCE_ANALYTIC_PASS','FIELD5_ALTERNATE_CURRENT_R214_HOST_PASS').replace('COUPLED_U17_U10017_REPAIR_REQUIRED','FIELD5_ALTERNATE_CURRENT_R214_REPAIR_REQUIRED').replace('R155','R232')
exec(compile(s,str(H/'audit_u17_u10017_coupled_power_repairs_r155.py'),'exec'))
