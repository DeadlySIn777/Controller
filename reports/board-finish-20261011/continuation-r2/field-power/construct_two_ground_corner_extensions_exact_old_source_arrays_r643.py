"""Preserve the R641 pre-geometry syntax failure, then correct its token spacing."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent
p=H/'construct_two_ground_corner_extensions_exact_old_source_arrays_r641.py'
f=H/'two-owned-ground-union-positive-corners-exact-source-array-restoration-r641'
assert not f.exists();f.mkdir();(f/'failure.json').write_text(json.dumps({'status':'SYNTAX_FAILURE_BEFORE_GEOMETRY','helper_SHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'reason':'Missing space in else 1e-6 conditional token; no model/native/source changes.'},indent=1)+'\n',encoding='utf-8')
s=p.read_text(encoding='utf-8');assert s.count('else1e-6')==1;s=s.replace('else1e-6','else 1e-6').replace('r641','r643').replace('R641','R643')
exec(compile(s,str(Path(__file__)),'exec'))
