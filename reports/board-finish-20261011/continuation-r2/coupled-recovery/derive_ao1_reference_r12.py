"""Preserve r11 failed native-ring-format diagnostic; fix isolated adapter."""
from pathlib import Path
import json,py_compile,hashlib
here=Path(__file__).resolve().parent
old=here/'ao1_scoped_cache_nomination_r1.py'
source=old.read_text().replace('from shapely.geometry import Point','from shapely.geometry import Point,Polygon')
source=source.replace("outlines=unary_union([p for z in zones for p in S.poly(z['outline'])])", "outlines=unary_union([Polygon(rings[0],rings[1:]) for z in zones for rings in z['outline']])")
target=here/'ao1_scoped_cache_nomination_r2.py';assert not target.exists();target.write_text(source)
source=(here/'ao1_reference_coupled_r11.py').read_text().replace('import ao1_scoped_cache_nomination_r1 as SC','import ao1_scoped_cache_nomination_r2 as SC')
source=source.replace("OUT=HERE/'ao1-reference-coupled-r11.json'", "OUT=HERE/'ao1-reference-coupled-r12.json'")
source=source.replace("('ao1-r11-initial-'", "('ao1-r12-initial-'").replace("('ao1-r11-legal-centres-'", "('ao1-r12-legal-centres-'")
target=here/'ao1_reference_coupled_r12.py';assert not target.exists();target.write_text(source)
py_compile.compile(str(target),doraise=True,cfile=str(here/'ao1-reference-r12-syntax-only.pyc'))
(here/'ao1-reference-r11-native-ring-format-failure.json').write_text(json.dumps({'verdict':'PRESERVED_HOST_CONSTRUCTOR_FORMAT_FAILURE_NO_PROOF_CREDIT','source_helper':'ao1_scoped_cache_nomination_r1.py','helper_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'error':'Native plane_dump zone outline is [outer,hole,...], old S.poly requires [outer,holes]; ValueError before path construction','candidate_chunks_emitted':False,'board_emitted':False,'native_jobs':0,'gpu_jobs':0,'adopted':False},indent=1)+'\n')
print('Fresh r12 syntax PASS; exact native polygon-ring adapter')
