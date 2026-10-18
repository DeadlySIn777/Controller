"""Separate frozen API correction; only prospective path vertices canonicalize."""
from pathlib import Path
import hashlib,json,traceback
H=Path(__file__).resolve().parent.parent
p=H/'sbc-power/nominate_R353_IO3_existing_actual_annulus_no_hole_bypass_r358.py'
failed=H/'sbc-power/CM79-R353-IO3-existing-actual-annulus-no-hole-fixed-Cu-bypass-nomination-r358/failure.json'
assert not failed.exists();failed.write_text(json.dumps({'script_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'failure':"AttributeError: module 'tri_route' has no attribute 'route_poly'",'model_or_source_changes':0,'finite_census_preserved':True},indent=1)+'\n',encoding='utf-8')
s=p.read_text(encoding='utf-8').replace('r358','r359').replace('R358','R359')
needle="direct=LineString([start,end]);path=[start,end]if face.covers(direct)else TR.route_poly(face,start,end)"
assert needle in s
s=s.replace(needle,"routeface=next((p for p in parts(face.buffer(-.000002,quad_segs=64))if p.covers(Point(start))and p.covers(Point(end))),None)\n    if routeface is None:continue\n    direct=LineString([start,end]);path=[start,end]if routeface.covers(direct)else TR.route(routeface,start,end)[0]")
s=s.replace("if __name__=='__main__':main()", "if __name__=='__main__':\n try:main()\n except Exception:\n  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__),'source_model_board_or_native_changes':0})\n  raise")
exec(compile(s,str(__file__),'exec'))
