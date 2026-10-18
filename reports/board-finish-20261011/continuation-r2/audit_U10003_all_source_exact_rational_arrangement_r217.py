"""Complete provenance and exact bounding-envelope coverage for R212."""
from pathlib import Path
H=Path(__file__).resolve().parent;src=H/'audit_U10003_old_reference_exact_rational_arrangement_r212.py';code=src.read_text().replace('rational-arrangement-r212','all-source-rational-arrangement-r217').replace('U10003-old-antipad-individual-source-array-diagnosis-r210/receipt.json','U10003-all-source-exact-bbox-reference-witness-binding-r216/receipt.json').replace('cd4db8c1edcb8b54f249cf3b6d1756882a8c2018aa25bd2c6a1fb3d7218378a2','61ba472cb0f172bed2296c3697285e1bb7a865cb6db8c8bd13764140ce66a81d')
needle="polygons[row['side']+'_'+row['UUID']]";assert code.count(needle)==1
code=code.replace(needle,"polygons[row['side']+'_'+row['UUID']+'_'+row['individual_actual_drilled_shape_WKB_sha256']]")
needle="r=json.loads(rp.read_bytes());polygons={};inputs=[]";assert code.count(needle)==1
code=code.replace(needle,"r=json.loads(rp.read_bytes());assert r['all_omitted_pieces_excluded_only_by_exact_rational_disjoint_vertex_envelope'];assert all(sha(p)==v for p,v in r['inputs_sha256'].items());polygons={};inputs=[{'file':str(Path(p).resolve()),'sha256':sha(p)}for p in(Path(__file__),src,Path(X.__file__),rp)]")
code=code.replace("'scope':'only six raw R199 witness polygons and their individual actual J3-rooted source support; does not clear any other reference or native/current gate'","'scope':'only six raw R199 witness polygons; all157 actual J3-rooted In1 pieces bound,5 bbox-relevant pieces individually classified, all omitted pieces exact rational envelope-disjoint; no other reference/native/current gate cleared'")
exec(compile(code,str(src),'exec'))
