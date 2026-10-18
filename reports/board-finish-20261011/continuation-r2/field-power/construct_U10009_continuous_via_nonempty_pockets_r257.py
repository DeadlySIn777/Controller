"""Retain R255 empty-component failure; continue its exact frozen input."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'U10009-continuous-centre-source-search-base-r255/expanded-constructor.py').read_text(encoding='utf-8')
s=s.replace("OUT=HERE/'U10009-continuous-centre-ordinary-source-escape-r255'","OUT=HERE/'U10009-continuous-centre-ordinary-source-escape-r257'")
s=s.replace("def polys(s):return [s] if s.geom_type=='Polygon' else", "def polys(s):return [] if s.is_empty else [s] if s.geom_type=='Polygon' else")
s=s.replace('controller-u10009-continuous-source-r255/','controller-u10009-continuous-source-r257/')
exec(compile(s,str(H/'U10009-continuous-centre-source-search-base-r255/expanded-constructor.py'),'exec'))
