"""Literal postguard width check of the R193 wider nomination."""
from pathlib import Path
import ast
P=Path(__file__).resolve().parent;s=(P/'inspect_IO3_group6_actual_width_r192.py').read_text()
s=s.replace('IO3-group6-literal-width-screen-r192','IO3-group6-wider-literal-width-screen-r194').replace('original-IO3-r172-positive-snapshot-8/proposed-zones.pkl','IO3-group6-wider-existing-port-r193/accepted-zones.pkl').replace('original-IO3-physical-port-bridges-r172/receipt.json','IO3-group6-wider-existing-port-r193/receipt.json').replace('e1ca93bf-40e7-5ec0-8482-bcd115ce3838','35a950a3-926c-5a71-9b06-1d072d672c5d').replace('R192_COMPLETE','R194_COMPLETE')
s=s.replace("(O/'receipt.json').write_text", "assert next(r for r in rows if r['width_mm']==.3)['literal_centerline_capsule_covered_by_actual_integer_intended_shape']\n(O/'receipt.json').write_text")
ast.parse(s);exec(compile(s,str(P/'inspect_IO3_group6_actual_width_r192.py'),'exec'))
