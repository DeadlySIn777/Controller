"""Fresh independent R196 audit; retain all R194 and reference failures."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'audit_U10003_compliant_coupled_drilled_geometry_source_r193.py';code=source.read_text().replace('r193','r197').replace('construction-r192','construction-r196').replace('d1efefc5d13afa5c7fc2e55a9e476c74bee0febf8df373ab63701023e6b58fa8','dfb8050d5f45f5602692f2f4bb11c4706937a7821d57fac55a6733042314cae5').replace('from shapely.geometry import Point','from shapely.geometry import Point,LineString')
needle="block=source[start:end]";assert code.count(needle)==1;code=code.replace(needle,"import textwrap;block=textwrap.dedent(source[start:end])")
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
