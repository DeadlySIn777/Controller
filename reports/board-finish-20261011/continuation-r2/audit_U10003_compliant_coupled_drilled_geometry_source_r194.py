"""Fresh independent audit with the extracted literal guard block dedented."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'audit_U10003_compliant_coupled_drilled_geometry_source_r193.py';code=source.read_text().replace('r193','r194').replace('from shapely.geometry import Point','from shapely.geometry import Point,LineString')
needle="block=source[start:end]";assert code.count(needle)==1;code=code.replace(needle,"import textwrap;block=textwrap.dedent(source[start:end])")
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
