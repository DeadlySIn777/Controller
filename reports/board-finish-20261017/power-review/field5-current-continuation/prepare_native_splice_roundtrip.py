"""Freeze exact integer polygons and source chunks for six-zone native roundtrip."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity([16,17])
from pathlib import Path
import hashlib,importlib.util,json,shapely
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
CON=HERE/'native-50um-splice-construction-r3';OUT=HERE/'native-50um-splice-roundtrip-r1'
BASE=ROOT/'reports/board-finish-20261017/combined-route-stage-r1/native/board.kicad_pcb'
OLD=ROOT/'reports/board-finish-20261011/continuation-r2/combined-R753-one-full-native-fill-cached-DRC-r299/copy/board.kicad_pcb'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
hp=ROOT/'reports/board-finish-20261011/parity-repair/root106/tools/pcbtext.py'
sp=importlib.util.spec_from_file_location('exact_pcbtext',hp);H=importlib.util.module_from_spec(sp);sp.loader.exec_module(H)
assert not OUT.exists();OUT.mkdir()
r=json.loads((CON/'receipt.json').read_text());ids=[r['field_zone_UUID']]+[q['uuid']for q in r['FG_native_negative_splices']]
def chunks(p):return{H.chunk_uuid(c):c for c in H.split(p.read_bytes())[1]if H.chunk_uuid(c)}
a,b=chunks(OLD),chunks(BASE);assert sha(BASE)=='758f3968589948ce6550d30586818a5ffaa673d8dad7fe8c9a7e402598cff1ad'
rows=[]
for uid in ids:
    assert a[uid]==b[uid];(OUT/(uid+'-old.exact-native-zone-chunk')).write_bytes(b[uid])
    p=CON/('field-native-positive-intent.wkb'if uid==ids[0]else uid+'-native-negative-intent.wkb');s=shapely.from_wkb(p.read_bytes());poly=[]
    for g in ([s]if s.geom_type=='Polygon'else list(s.geoms)):
        rings=[]
        for ring in [g.exterior,*g.interiors]:
            rr=[]
            for x,y in list(ring.coords)[:-1]:
                xi,yi=round(x*1e6),round(y*1e6);assert abs(x-xi/1e6)<1e-12 and abs(y-yi/1e6)<1e-12;rr.append([xi,yi])
            rings.append(rr)
        poly.append(rings)
    rows.append({'uuid':uid,'polygons_integer_IU':poly,'input_WKB':str(p),'input_WKB_SHA256':sha(p),'old_chunk_SHA256':hashlib.sha256(b[uid]).hexdigest()})
inputs={str(p):sha(p)for p in(BASE,OLD,CON/'receipt.json',hp,Path(__file__))}
(OUT/'native-integer-outline-input.json').write_text(json.dumps({'source_board':str(BASE),'source_board_SHA256':sha(BASE),'output_board':str(OUT/'roundtrip-only-not-adopted.kicad_pcb'),'zones':rows,'input_sha256':inputs,'new_holes':0,'fill_called':False,'adopted':False},indent=2)+'\n')
print(json.dumps({'six_exact_native_outline_inputs':str(OUT/'native-integer-outline-input.json'),'native_source_input_unchanged':True}))
