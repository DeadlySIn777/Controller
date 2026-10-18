from pathlib import Path
p=Path('reports/motherboard-critical-routing-20261001/route_actual_FPGA_CCK_ROOT84_F_In2_r03.py');s=p.read_text()
line="moved_cap=next(f for f in b.GetFootprints()if f.GetReference()=='C1022');moved_cap.SetOrientationDegrees(90);moved_cap.SetPosition(xy((94.5,48.0)))\n"
assert line in s;s=s.replace(line,'')
anchor=";g=w.Geometry(b)\npads="
assert anchor in s;s=s.replace(anchor,"\n# Search uses the original frozen reference subset; a fresh candidate map and\n# native Source witness review are mandatory before any adoption.\n"+line+"g=w.Geometry(b)\npads=")
Path('reports/motherboard-critical-routing-20261001/route_actual_FPGA_CCK_ROOT84_F_In2_r04.py').write_text(s)
