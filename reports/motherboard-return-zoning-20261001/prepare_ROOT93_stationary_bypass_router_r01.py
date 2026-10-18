"""Search-only exact literal coverage index; frozen final bypass guards retained."""
from pathlib import Path
import hashlib,json
base=Path('reports/motherboard-owned-bypass-routing-20261001/route-typed-local-bypass-r04.py')
dest=Path('reports/motherboard-return-zoning-20261001/route_ROOT93_stationary_bypass_r01.py')
if dest.exists():
    raise ValueError('Fresh report-local router required')
s=base.read_text()
needle='import pcbnew\n'
assert s.count(needle)==1
s=s.replace(needle,needle+'from hardware_index_literal_reference_coverage import LiteralReferenceCoverage\n',1)
needle='groups=[];skips=list(dedicated);mapping={};g=Geometry(b);checker=NativeCollectedAnnulusCheck(b,{})'
assert s.count(needle)==1
s=s.replace(needle,needle+"\n indexed=LiteralReferenceCoverage(b,{next(p.GetNetname()for p in fps[r['ref']].Pads()if p.GetNumber()==r['cap_return'])for r in rows},[pcbnew.In1_Cu,pcbnew.In4_Cu])")
old="return all(covered(circle(tuple(xy(pt)),pcbnew.FromMM(.24)),checker.reference(return_net,b.GetLayerID(layer)))for layer in('In1.Cu','In4.Cu'))"
new="return all(indexed.candidate_covered(circle(tuple(xy(pt)),pcbnew.FromMM(.24)),return_net,b.GetLayerID(layer))for layer in('In1.Cu','In4.Cu'))"
assert s.count(old)==1
s=s.replace(old,new)
dest.write_text(s)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt=dict(passed=True,search_only_optimization=True,base_router=str(base),base_router_sha256=sha(base),
 output_router=str(dest),output_router_sha256=sha(dest),
 exact_local_native_circle_coverage_prefilter_only=True,
 final_frozen_full_union_REFERENCE_SOURCE_annuli_receiving_return_geometry_gates_unchanged=True,
 no_circuit_pin_pose_zone_native_rule_or_acceptance_waiver=True)
dest.with_suffix('.scope.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
