"""Replay the strict ground constructor on the proven local health bend."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=H/'nominate_field_ground_health_opening_r35.py';target=H/'nominate_field_ground_bulge_opening_r40.py';assert not target.exists();s=source.read_text();old="healthdir=H/'field-health-wall-reroute-r34'";assert s.count(old)==1;s=s.replace(old,"healthdir=H/'field-health-wall-bulge-r39'");s=s.replace('controller-ground-bare-r35','controller-ground-bare-r40').replace('controller-ground-bare-r24','controller-ground-bare-r40');compile(s,str(target),'exec');target.write_text(s);(H/'field-ground-bulge-r40-derivation.json').write_text(json.dumps({'source_sha256':sha(source),'derived_sha256':sha(target),'only_exact_health_nominee_and_UUID_seed_changed':True,'all_physical_native_drill_SMD_foreign_clearance_minimum_width_guards_unchanged':True,'no_acceptance_or_new_slot':True},indent=1)+'\n')
