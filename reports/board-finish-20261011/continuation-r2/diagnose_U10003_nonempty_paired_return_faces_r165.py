"""Retain R164 partial proof and reject empty polygon components safely."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'diagnose_U10003_exact_paired_return_faces_r164.py';code=source.read_text()
code=code.replace('return-legal-faces-r164','return-legal-faces-r165')
old="def polys(s):return [s]if s.geom_type=='Polygon'else[p for p in getattr(s,'geoms',[])if p.geom_type=='Polygon']"
new="def polys(s):return [s]if s.geom_type=='Polygon'and not s.is_empty else[p for p in getattr(s,'geoms',[])if p.geom_type=='Polygon'and not p.is_empty]"
assert code.count(old)==1;code=code.replace(old,new)
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
