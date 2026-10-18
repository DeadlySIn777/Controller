"""Characterize native collision semantics, including tangency, without waivers."""
from pathlib import Path
import json,hashlib
import pcbnew as p
out=Path('reports/motherboard-pcb-integration-20261001/native-SMD-drill-audit-controls-r02');out.mkdir(exist_ok=False)
b=p.BOARD();fp=p.FOOTPRINT(b);b.Add(fp);pad=p.PAD(fp);fp.Add(pad)
pad.SetAttribute(p.PAD_ATTRIB_SMD);pad.SetShape(p.PAD_SHAPE_RECT)
pad.SetSize(p.VECTOR2I(p.FromMM(1),p.FromMM(.6)));pad.SetPosition(p.VECTOR2I(0,0))
ls=p.LSET();ls.AddLayer(p.F_Cu);ls.AddLayer(p.F_Paste);pad.SetLayerSet(ls)
rows=[]
for angle,xy,gap,expected,label in [
    (0,(0,0),0,True,'inside'),(0,(.59,0),0,True,'edge_overlap'),
    (0,(.61,0),0,False,'outside_10um'),(0,(.6,0),0,False,'exact_tangent_excluded_by_native_zero_clearance'),
    (90,(0,.59),0,True,'rotated_overlap'),(90,(.59,0),0,False,'rotated_clear'),
    (0,(.6,0),.15,True,'tangent_detected_by_explicit_gap_screen'),
    (0,(.74,0),.15,True,'gap140um_below150um'),(0,(.76,0),.15,False,'gap160um_above150um')]:
    pad.SetOrientationDegrees(angle)
    circle=p.SHAPE_CIRCLE(p.VECTOR2I(p.FromMM(xy[0]),p.FromMM(xy[1])),p.FromMM(.1))
    actual=pad.GetEffectiveShape(p.F_Cu).Collide(circle,p.FromMM(gap))
    rows.append(dict(label=label,angle=angle,center_mm=xy,drill_mm=.2,requested_gap_mm=gap,expected=expected,actual=actual,passed=actual==expected))
audit=Path('reports/motherboard-pcb-integration-20261001/two-cap-full-drill-SMD-audit-r01/receipt.json')
script=Path('reports/motherboard-pcb-integration-20261001/audit_actual_SMD_drill_intersections_r01.py')
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
r=dict(passed=all(r['passed']for r in rows),cases=rows,input_sha256={str(f):sha(f)for f in [audit,script,Path(__file__)]},
    scope='Positive-area native drill/SMD collisions are identified. Exact tangent is NOT identified at zero clearance: first attempted expectation was wrong and is retained separately. A manufacturing registration-clearance guard must additionally use an explicit process-qualified gap.',
    previous_attempt='native-SMD-drill-audit-controls-r01: five expected controls matched, exact tangency expectation failed; no PCB/source changes.',
    original_audit_279_is_lower_bound_for_assembly_clearance_screen=True,physical_qualification=False)
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=r['passed'],cases=len(rows),tangency_at_zero_clearance_is_excluded=True)))
assert r['passed']
