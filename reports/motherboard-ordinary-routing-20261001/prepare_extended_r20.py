"""Fix a search-only absent manifest-layer lookup using native zone clearances."""
from pathlib import Path
p=Path(__file__).parent
s=(p/'route_In2_extended_search_r13.py').read_text()
old="critical_rows=e.read('reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/prototype-route-geometry-review.json')['nets']"
new=old+"\nactual_reference_clearance=max([*check.zone_clearance.values(),*[z.GetLocalClearance()for z in b.Zones()if not z.GetIsRuleArea()and z.GetNetname()=='/LOGIC_GND'and any(z.IsOnLayer(l)for l in(pcbnew.In1_Cu,pcbnew.In4_Cu))]])\nassert actual_reference_clearance>0"
assert s.count(old)==1;s=s.replace(old,new)
old="max(check.zone_clearance['/LOGIC_GND',l]for l in(pcbnew.In1_Cu,pcbnew.In4_Cu))"
assert s.count(old)==1;s=s.replace(old,'actual_reference_clearance')
out=p/'route_In2_extended_search_r20.py';assert not out.exists();out.write_text(s)
