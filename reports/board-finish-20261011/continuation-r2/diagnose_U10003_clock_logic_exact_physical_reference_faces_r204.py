"""Diagnose the failed one-wall clock route without editing the scene or gates."""
from pathlib import Path
H=Path(__file__).resolve().parent
src=H/'nominate_U10003_clock_and_exact_logic_wall_rework_r203.py'
prefix=src.read_text().split("compile(code,str(source),'exec');")[0]
exec(compile(prefix,str(src),'exec'))
code=code.replace('clock-and-exact-logic-wall-rework-nomination-r203','clock-logic-exact-physical-reference-face-diagnosis-r204')
needle="free=win.difference(unary_union(cuts));\n   if net=='/FPGA_OUTPUT_REQUEST':"
assert code.count(needle)==1
code=code.replace(needle,"free=win.difference(unary_union(cuts));physical_free=free;\n   if net=='/FPGA_OUTPUT_REQUEST':")
needle="free=free.intersection(logic_reference)\n   faces="
assert code.count(needle)==1
code=code.replace(needle,"""free=free.intersection(logic_reference)
    physical_faces=polys(physical_free)
    debug={'margin_mm':margin,'a':a,'b':bb,'physical_a_inside':physical_free.covers(Point(a)),'physical_b_inside':physical_free.covers(Point(bb)),'physical_common_faces':sum(p.covers(Point(a)) and p.covers(Point(bb)) for p in physical_faces),'reference_a_inside':logic_reference.covers(Point(a)),'reference_b_inside':logic_reference.covers(Point(bb)),'reference_a_distance_mm':Point(a).distance(logic_reference),'reference_b_distance_mm':Point(bb).distance(logic_reference),'strict_full_body_axis_note':'R203 axis reference intersection is only a failed diagnostic; any accepted new full body requires its complete drilled source qualification'}
    (OUT/('logic-margin-'+str(margin)+'-cause.json')).write_text(json.dumps(debug,indent=1)+'\\n')
    (OUT/('logic-margin-'+str(margin)+'-physical-free.wkb')).write_bytes(physical_free.wkb)
    (OUT/('logic-margin-'+str(margin)+'-actual-rooted-reference.wkb')).write_bytes(logic_reference.intersection(win).wkb)
   faces=""")
code=code.replace("'native_jobs':0","'diagnostic_only_no_reference_relaxation':True,'native_jobs':0")
exec(compile(code,str(src),'exec'))
