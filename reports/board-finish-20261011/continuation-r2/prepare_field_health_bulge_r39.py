"""Keep original endpoints while bending only the middle away from the ground escape."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=H/'nominate_field_health_wall_reroute_r32.py';target=H/'nominate_field_health_wall_bulge_r39.py';assert not target.exists();s=source.read_text();changes=[('field-health-wall-reroute-r32','field-health-wall-bulge-r39'),('controller-health-wall-r32','controller-health-wall-r39'),('R32_','R39_'),('for dx in (.6,.8,1.,1.2,1.5,1.8,2.,2.5,3.):','for dx in (1.,1.1,1.2,1.3,1.4,1.5,1.6,1.8,2.):'),("points=[old['a'],[x,old['a'][1]],[x,old['b'][1]],old['b']]","points=[old['a'],[x,154.558],old['b']]")]
for old,new in changes:assert old in s;s=s.replace(old,new)
compile(s,str(target),'exec');target.write_text(s);(H/'field-health-bulge-r39-derivation.json').write_text(json.dumps({'source_sha256':sha(source),'derived_sha256':sha(target),'only_finite_geometry_and_names_changed':True,'original_endpoints_all_spacing_drill_areas_source_reference_rules_unchanged':True,'no_adoption':True},indent=1)+'\n')
