"""Preserve R176 compiler failure; derive the literal inner canonicalizer."""
from pathlib import Path
import ast
P=Path(__file__).resolve().parent
wrapper=(P/'normalize_SAFE_repaired_owned_zones_r160.py').read_text()
tail="exec(compile(s,str(p/'normalize_final_owned_zones_r55.py'),'exec'))"
assert wrapper.endswith(tail+'\n')
ns={'__file__':str(Path(__file__).resolve())};exec(compile(wrapper[:-len(tail+'\n')],str(P/'normalize_SAFE_repaired_owned_zones_r160.py'),'exec'),ns)
s=ns['s'];s=s.replace("SAFE-repaired-owned-zone-normalization-r160","original-IO3-full-owned-zone-normalization-r177")
load="g,h,binding,zones,_=pickle.loads(prior.read_bytes());original_ids={q['uuid'] for q in h['zones']}"
restore="g,h,binding,zones,_=pickle.loads(prior.read_bytes());import restore_SAFE_generated_precision_states_r168 as PS;PS.restore_bound_generated_precision_states(binding,zones);original_ids={q['uuid'] for q in h['zones']}"
assert load in s;s=s.replace(load,restore)
uidline="uid=str(uuid.uuid5(NAMESPACE,label))"
assert uidline in s;s=s.replace(uidline,"uid=members[0]['uuid'] if len(members)==1 and members[0].get('constituent_proposal_UUIDs') else str(uuid.uuid5(NAMESPACE,label))")
cline="'constituent_proposal_UUIDs':sorted(z['uuid'] for z in members)"
assert cline in s;s=s.replace(cline,"'constituent_proposal_UUIDs':sorted({uid for z in members for uid in [z['uuid']]+z.get('constituent_proposal_UUIDs',[])})")
ast.parse(s)
exec(compile(s,str(P/'normalize_final_owned_zones_r55.py'),'exec'))
