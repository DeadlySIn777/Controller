from pathlib import Path
import json,sys
sys.path.insert(0,str(Path('tools').resolve()))
from hardware_build_assembly import parse,dump,children
from hardware_merge_bounded_pcb_delta import objects,reference,without_generated_fills,zone_definition
from hardware_route_current_delivery_native import sha
B=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-U25-C19033-merged-trial-r101/motherboard-bounded-merged-candidate.kicad_pcb');D=Path('reports/motherboard-power-entry-20261001/ROOT101-health-private-LED-power-repair-r252/motherboard-health-private-LED-power-repaired-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/ROOT101-two-health-complete-circuit-delta-r254');O.mkdir(exist_ok=False)
b=parse(without_generated_fills(B.read_text()));d=parse(without_generated_fills(D.read_text()));bf={reference(f):f for f in children(b,'footprint')};df={reference(f):f for f in children(d,'footprint')};assert set(bf)==set(df);refs=[r for r in bf if dump(bf[r])!=dump(df[r])];assert set(refs)=={'U11020','C11079','U11026','C11081'},refs;delta=[]
for kind in ['segment','via','arc']:
 old,new=objects(b,kind),objects(d,kind)
 for u in sorted(set(old)|set(new)):
  a,z=old.get(u),new.get(u)
  if a is not None and z is not None and dump(a)==dump(z):continue
  delta.append(dict(kind=kind,uuid=u,before=dump(a)if a is not None else None,after=dump(z)if z is not None else None))
old,new=objects(b,'zone'),objects(d,'zone');assert set(old)==set(new)and all(zone_definition(old[u])==zone_definition(new[u])for u in old)
scope=dict(electrical_source_unchanged=True,reviewed_scope_reason='Complete actual U20/U26 receiving circuit with four bounded owner poses, off-land Ground escapes, direct pad-to-pad inputs, and native-coexistence LED POWER graph correction. Source-backed Ground/reference qualification remains pending.',reviewed_footprint_references=refs,reviewed_copper_delta_UUIDs=[q['uuid']for q in delta],reviewed_added_zone_UUIDs=[])
(O/'bounded-scope.json').write_text(json.dumps(scope,indent=2));(O/'literal-delta.json').write_text(json.dumps(dict(before_board=str(B),before_sha256=sha(B),donor_board=str(D),donor_sha256=sha(D),part_count=len(df),exact_changed_references=refs,exact_copper_delta=delta,existing_zone_definitions_unchanged=True,native_electrical_source_unchanged=True,Source_Ground_and_reference_qualification_pending=True,passed=False,manufacturing_ready=False),indent=2));print(len(refs),len(delta),sum(q['before']is None for q in delta),sum(q['after']is None for q in delta))
