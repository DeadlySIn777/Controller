"""Preserve the eight-join proof; replan only the .25mm group6 bridge at >=.30."""
from pathlib import Path
import ast,hashlib,json
P=Path(__file__).resolve().parent
old=P/'construct_original_IO3_physical_port_bridges_r172.py';s=old.read_text()
s=s.replace('original-IO3-physical-port-bridges-r172','IO3-group6-wider-existing-port-r193')
needle="groups=cache['new_groups'];parts=cache['new_parts'];assign=cache['new_assign'];ri=root;keys=rootkeys\n selected={**h,'zones':[q for q in h['zones'] if q['net']==RAW]};new=[];attempts=[];accepted=[];rejections=[]\n target_groups=sorted([d['group'] for d in split['new_groups'] if d['group']!=root],key=lambda i:-len(cache['new_groups'][i]))"
replacement="""qf=H/'sbc-power/original-IO3-r172-positive-snapshot-8/proposed-zones.pkl';assert sha(qf)=='d576613bad70e94d04e47822b0b7c42f30e7f1a72e91d4a4a9cf1f8335eac16c'
 held=[q for q in pickle.loads(qf.read_bytes()) if q['uuid']!='e1ca93bf-40e7-5ec0-8482-bcd115ce3838'];assert len(held)==7
 for q in held:
  for role in ('shape','zone_outline_shape'):
   before=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert q[role].wkb==before
 z=z+held
 selected={**h,'zones':[q for q in h['zones'] if q['net']==RAW]};new=[];attempts=[];accepted=[];rejections=[]
 before_trial,_=GP.projected(g,selected,z);groups,parts,assign,ri,keys=model_source(before_trial)
 required_target={r['uuid'] for r in cache['new_groups'][6]}
 assert not required_target & keys,'Nominated replacement branch already source joined; do not duplicate'
 target_groups=[6]
 write(O/'held-seven-and-group6-replacement-contract.json',{'held_seven_file':str(qf.resolve()),'held_seven_sha256':sha(qf),'withdraw_only_prior_nominee_UUID':'e1ca93bf-40e7-5ec0-8482-bcd115ce3838','required_group6_original_contacts':sorted(required_target),'held_source_key_count':len(keys),'guaranteed_width_candidates_mm':[.5,.35,.3],'no_current_derating_or_source_mutation':True})"""
assert needle in s;s=s.replace(needle,replacement)
s=s.replace("for width in (.5,.35,.25):","for width in (.5,.35,.3):")
s=s.replace("controller/original-IO3-physical-port-r172/","controller/original-IO3-physical-port-r193/")
# Full final minimal canonicalization and fresh all76 gates are mandatory;
# this constructor grants only its actual selected-layer source joins.
s=s.replace("'hard_only_peer_binding':peer_binding,","'hard_only_peer_binding':peer_binding,'held_exact_seven_from_sha256':sha(qf),'replacement_of_prior_nominee_UUID':'e1ca93bf-40e7-5ec0-8482-bcd115ce3838','full_R183_593_IO3_source_scope_retention_required_on_composition':True,")
ast.parse(s)
(P/'IO3-group6-wider-constructor-r193-derivation.json').write_text(json.dumps({'original_constructor_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'derived_literal_source_sha256':hashlib.sha256(s.encode()).hexdigest(),'only_group6_replan':True,'other_seven_exact_source_bridges_held':True,'no_new_holes_or_source_entities':True,'guaranteed_minimum_search_width_mm':.3,'historical_R192_width_failure_retained':True},indent=1)+'\n')
exec(compile(s,str(old),'exec'))
