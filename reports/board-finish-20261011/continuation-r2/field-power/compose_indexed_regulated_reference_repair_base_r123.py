"""Reuse completed four masks; exact union-before-intersection for LOGIC mask."""
from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'compose_regulated_reference_repair_base_r120.py').read_text().replace("O=H/'regulated-reference-wall-repair-base-r120'","O=H/'regulated-indexed-reference-wall-repair-base-r123'")
s=s.replace('from shapely import STRtree','from shapely import STRtree,from_wkb\nfrom shapely.prepared import prep')
s=s.replace("ref=unary_union([q['shape'] for q in gs[ri] if q['kind']=='fill' and q['layer']==inner]);pieces=[];count=0", "ref=unary_union([q['shape'] for q in gs[ri] if q['kind']=='fill' and q['layer']==inner]);prepared=prep(ref);pieces=[];count=0;cached=H/'regulated-reference-wall-repair-base-r120'/(root+'-'+inner+'-full-original-reference-mask.wkb')")
s=s.replace("    if ref.intersects(env):\n     sh=C.body(t).intersection(ref)\n     if not sh.is_empty:pieces.append(sh)", "    if not cached.exists() and prepared.intersects(env):pieces.append(C.body(t))")
s=s.replace("mask=unary_union(pieces);masks[(net,inner)]=mask", "mask=from_wkb(cached.read_bytes()) if cached.exists() else unary_union(pieces).intersection(ref);masks[(net,inner)]=mask")
s=s.replace("'WKB_sha256':P.digest(mask)", "'WKB_sha256':P.digest(mask),'reused_completed_R120_file_sha256':sha(cached) if cached.exists() else None,'exact_union_intersection_distributive_identity':True")
s=s.replace("'source_contact_reference_current_native_gates':'OPEN'", "'preserved_owned_R120_stop_sha256':sha(H/'regulated-reference-wall-repair-base-r120/owned-termination-r1.json'),'LOGIC_mask_identity':'union(B_i intersect sourceRef) == union(B_i) intersect sourceRef; prepared broad phase skips only empty envelope intersections','source_contact_reference_current_native_gates':'OPEN'")
exec(compile(s,str(p/'compose_regulated_reference_repair_base_r120.py'),'exec'))
