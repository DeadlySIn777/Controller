"""Evaluate every strict small same-F shift and retain the widest legal one."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=H/'nominate_field_health_wall_reroute_r33.py';d=H/'nominate_field_health_wall_reroute_r34.py';assert not d.exists();text=s.read_text();changes=[('field-health-wall-reroute-r33','field-health-wall-reroute-r34'),('controller-health-wall-r33','controller-health-wall-r34'),('R33_','R34_'),("'candidate':r};break","'candidate':r}")]
for old,new in changes:assert old in text;text=text.replace(old,new)
compile(text,str(d),'exec');d.write_text(text);(H/'field-health-wall-r34-derivation.json').write_text(json.dumps({'source_sha256':sha(s),'derived_sha256':sha(d),'only_all_finite_samples_evaluated_names_changed':True,'strict_guards_and_reference_policy_unchanged':True},indent=1)+'\n')
