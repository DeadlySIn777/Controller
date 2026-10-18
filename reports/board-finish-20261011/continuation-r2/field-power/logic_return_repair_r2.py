"""Resume preserved partial repairs; interior endpoint precision and parallel source."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
pr=psutil.Process();pr.cpu_affinity(list(range(16,28)));pr.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
failed=HERE/'logic-return-repair-r1'
if not (failed/'aborted.json').exists():
    (failed/'aborted.json').write_text(json.dumps({'exit_code':1,'condition':'nearest_points endpoint on the legal polygon boundary failed exact covers due to floating coordinate representation','partial_proposals_preserved':True,'checkpoint':'checkpoint.json','native_jobs':0,'board_written':False},indent=1)+'\n')
path=HERE/'logic_return_repair_r1.py';text=path.read_text()
text=text.replace("OUT=HERE/'logic-return-repair-r1'","OUT=HERE/'logic-return-repair-r2'")
text=text.replace("rows=[];adds=[];obs={}","rows=json.loads((HERE/'logic-return-repair-r1/checkpoint.json').read_text());adds=[]\n    for row in rows:\n        rr=row['repair']\n        if rr:\n            ff=Path(rr['geometry_file']);assert sha(ff)==rr['sha256'];adds.append({'uuid':rr['uuid'],'layer':rr['layer'],'net':NET,'shape':__import__('shapely').from_wkb(ff.read_bytes())})\n    obs={}")
old="selected=[q for q in gaps['rows'] if q['group']==source_group]\n    if '--all' in sys.argv:selected+= [q for q in gaps['rows'] if q['group']!=source_group]"
new="""completed={q['group'] for q in rows if q['repair']}
    # Deliberate second source branch, on an actual J11001 plated layer.
    source_row=next(q for q in gaps['rows'] if q['group']==source_group)
    source_row={**source_row,'layer_gaps':[q for q in source_row['layer_gaps'] if q['layer']=='In4.Cu']}
    selected=[source_row]+[q for q in gaps['rows'] if q['group'] not in completed]
    # A retained .5/.2 old GND barrel also lost its only filled-plane contact.
    extra=98;extra_gaps=[]
    for layer in h['copper_layers']:
        src=unary_union([q['shape'] for q in groups[extra] if q['layer']==layer]);dst=unary_union([q['shape'] for q in groups[main_group] if q['layer']==layer])
        if src.is_empty or dst.is_empty:continue
        aa,bb=nearest_points(src,dst);extra_gaps.append({'layer':layer,'gap_mm':aa.distance(bb),'from_mm':list(aa.coords[0]),'to_mm':list(bb.coords[0])})
    selected.append({'group':extra,'pads':[],'layer_gaps':sorted(extra_gaps,key=lambda q:q['gap_mm'])})"""
assert old in text;text=text.replace(old,new)
text=text.replace("if sourcecase:layergaps=sorted(layergaps,key=lambda q:(q['layer']!='In3.Cu',q['gap_mm']))","if sourcecase:layergaps=sorted(layergaps,key=lambda q:q['gap_mm'])")
old="points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]));line=LineString(points);"
new="""inside=part.buffer(-.00002)
                    sa=inside.intersection(src);tb=inside.intersection(target)
                    if sa.is_empty or tb.is_empty:attempts.append({'layer':layer,'window_margin_mm':margin,'width_mm':w,'verdict':'NO_POSITIVE_INTERIOR_ATTACHMENT'});continue
                    start,end=nearest_points(sa,tb)
                    try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))
                    except AssertionError as exc:
                        attempts.append({'layer':layer,'window_margin_mm':margin,'width_mm':w,'verdict':'EXACT_ROUTE_ENDPOINT_PRECISION_REJECTED'});continue
                    line=LineString(points);"""
assert old in text;text=text.replace(old,new)
text=text.replace("controller-field-logic-return-r1-","controller-field-logic-return-r2-")
text=text.replace("'source_external_return_repair':sourcecase","'source_external_return_repair':sourcecase,'actual_power_return_pad':'J11001.2' if sourcecase else None,'J11002_ground_role':'RETAINED_SHUTDOWN_CONTACT_ONLY_NO_POWER_CURRENT' if sourcecase else None")
text=text.replace("'SOURCE_BOUND_PENDING_SIGNED_INPUT_RETURN_LEDGER'","'ENTRY_RETURN_3.993114989_A_CONDITIONAL_PLANNING_CASE; signed lower-rail/local allocations pending'")
text=text.replace("'base_receipt_sha256':sha(base/'receipt.json'),'gap_receipt", "'superseded_partial_r1_checkpoint_sha256':sha(HERE/'logic-return-repair-r1/checkpoint.json'),'partial_r1_abort_receipt_sha256':sha(HERE/'logic-return-repair-r1/aborted.json'),'base_receipt_sha256':sha(base/'receipt.json'),'gap_receipt")
exec(compile(text,str(path),'exec'))
