"""Refine the saved .6-mm near miss without changing any guard."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
s=H/'nominate_field_health_wall_reroute_r32.py';d=H/'nominate_field_health_wall_reroute_r33.py';assert not d.exists();text=s.read_text();changes=[('field-health-wall-reroute-r32','field-health-wall-reroute-r33'),('controller-health-wall-r32','controller-health-wall-r33'),('R32_','R33_'),('for dx in (.6,.8,1.,1.2,1.5,1.8,2.,2.5,3.):','for dx in (.1,.2,.3,.4,.45,.48,.49,.50,.51,.52,.53,.54,.55):')]
for old,new in changes:assert old in text;text=text.replace(old,new)
compile(text,str(d),'exec');d.write_text(text);(H/'field-health-wall-r33-derivation.json').write_text(json.dumps({'source_sha256':sha(s),'derived_sha256':sha(d),'only_finite_dx_samples_names_changed':True,'strict_guards_and_reference_policy_unchanged':True},indent=1)+'\n')
