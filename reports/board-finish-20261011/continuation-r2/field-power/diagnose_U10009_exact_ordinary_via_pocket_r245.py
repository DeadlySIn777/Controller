"""Keep R244 exporter failure; represent empty legal geometry explicitly."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'diagnose_U10009_exact_ordinary_via_pocket_r244.py').read_text(encoding='utf-8')
s=s.replace('U10009-current-exact-ordinary-via-pocket-r244','U10009-current-exact-ordinary-via-pocket-r245')
s=s.replace("parts=[legal] if legal.geom_type=='Polygon' else", "parts=[] if legal.is_empty else [legal] if legal.geom_type=='Polygon' else").replace('R244 complete','R245 complete')
exec(compile(s,str(H/'diagnose_U10009_exact_ordinary_via_pocket_r244.py'),'exec'))
