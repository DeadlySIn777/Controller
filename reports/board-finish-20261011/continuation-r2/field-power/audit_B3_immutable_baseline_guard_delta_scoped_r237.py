"""Test the conservative alternative on exact current LOGIC scope, with all guards."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_B3_envelope_scoped_LOGIC_r233.py').read_text(encoding='utf-8')
# Expand the frozen wrapper first, then replace only its explicit projection.
inner=(H/'audit_B3_envelope_scoped_LOGIC_r231.py').read_text(encoding='utf-8')
inner=inner.replace('B3-envelope-scoped-LOGIC-projection-r231','B3-immutable-baseline-guard-delta-scoped-r237').replace('import fast_contacts as F','import fast_contacts as F\nfrom audit_field_io3_crossings_r15e import losses as relationship_losses\nimport immutable_baseline_guard_delta_projection_r236 as IP').replace('losses=F.losses(oldgroups,groups)','losses=relationship_losses(oldgroups,groups)')
inner=inner.replace("after,cutledger=P.projected(g,hs,z);groups=F.graph(after,'/LOGIC_GND')","after,cutledger,guards=IP.projected(g,h,z,bh,bz,bc,only_nets={'/LOGIC_GND'});write(O/'actual-required-guard-checks.json',guards);assert all(row['PASS'] for row in guards),[row for row in guards if not row['PASS']];groups=F.graph(after,'/LOGIC_GND')")
inner=inner.replace("'full77_geometry_current_native_gates':'OPEN'","'full77_geometry_current_native_gates':'OPEN','projection_interface_sha256':sha(H/'immutable_baseline_guard_delta_projection_r236.py'),'explicit_alternative_conservative_host_projection_only':True,'actual_required_guard_checks':len(guards),'actual_required_guard_errors':sum(not row['PASS'] for row in guards)").replace('R231','R237')
exec(compile(inner,str(H/'audit_B3_envelope_scoped_LOGIC_r231.py'),'exec'))
