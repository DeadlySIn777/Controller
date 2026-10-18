"""Reject R32 and require every signal annulus to clear new ground stub Cu."""
from pathlib import Path
P=Path(__file__).resolve().parent;s=(P/'repair_u11015_inner_ilim_r32.py').read_text()
s=s.replace("OUT=HERE/'u11015-three-net-inner-ILIM-repair-r32'", "OUT=HERE/'u11015-three-net-mutual-fix-r36'")
s=s.replace("disk.distance(grounddisk)<.175-1e-9 or hole.distance", "disk.distance(grounddisk)<.175-1e-9 or disk.distance(groundbody)<.175-1e-9 or hole.distance")
a=s.index(' def outer_ilim(');b=s.index(' def ilim_dive(',a);part=s[a:b]
part=part.replace("pts=[[round(x,6),round(y,6)] for x,y in points]", "pts=[[round(x,6),round(y,6)] for x,y in points];a0=nearest_points(src,Point(pts[0]))[0];b0=nearest_points(dst,Point(pts[-1]))[0];pts[0]=[round(a0.x,6),round(a0.y,6)];pts[-1]=[round(b0.x,6),round(b0.y,6)]")
s=s[:a]+part+s[b:]
s=s.replace("sum(C.body(t).length for t in ts)", "sum(LineString([t['a'],t['b']]).length for t in ts)")
s=s.replace('controller-U11015-ILIM-dive-r32/', 'controller-U11015-ILIM-dive-r36/').replace('controller-U11015-three-net-inner-r32/', 'controller-U11015-three-net-inner-r36/')
s=s.replace("'scoped_r24_failed_receipt_sha256':sha(prior/'receipt.json')", "'scoped_r24_failed_receipt_sha256':sha(prior/'receipt.json'),'rejected_R32_independent_clearance_receipt_sha256':sha(HERE/'u11015-r32-independent-discrete-audit-r33/receipt.json'),'signal_via_annuIi_clear_every_new_ground_stub_Cu':True,'ILIM_stub_endpoint_centers_on_actual_pad_and_via_Cu_boundary':True")
(P/'repair_u11015_mutual_r36.py').write_text(s,encoding='utf-8');compile(s,'repair_u11015_mutual_r36.py','exec');print('derived',len(s))
