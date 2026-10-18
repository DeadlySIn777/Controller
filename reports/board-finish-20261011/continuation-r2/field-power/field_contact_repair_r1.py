"""Repair exact field ground cuts from GND proposal using physical endpoints."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
pr=psutil.Process();pr.cpu_affinity(list(range(16,28)));pr.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
from pathlib import Path
import json,pickle
HERE=Path(__file__).resolve().parent;path=HERE/'logic_return_repair_r1.py';text=path.read_text()
text=text.replace("OUT=HERE/'logic-return-repair-r1'","OUT=HERE/'field-contact-repair-r1'")
start="assert not OUT.exists();OUT.mkdir();base=HERE/'coupled-logic-base-r1';"
i=text.index(start);j=text.index('    for layer in h[',i)
initial="""assert not OUT.exists();OUT.mkdir();base=HERE/'logic-return-contact-audit-r1';br=json.loads((base/'receipt.json').read_text());assert sha(base/'geometry.pkl')==br['geometry_sha256'];h=pickle.loads((base/'geometry.pkl').read_bytes());assert sha(base/'groups.pkl')==br['groups_sha256'];allgroups=pickle.loads((base/'groups.pkl').read_bytes());mm=pickle.loads((HERE/'coupled-logic-base-r1/model.pkl').read_bytes());zones=mm['new_zones']+pickle.loads((HERE/'logic-return-repair-r2/proposed-zones.pkl').read_bytes());outline=unary_union(C.poly(h['outline'])).buffer(-.526);rows=[];adds=[]
    for bank,NET,rootref,wanted in [('FAG','/motherboard_motors/FIELD_GND','J11003',[0]),('FBG','/motherboard_do/FIELD_B_0V','J11005',[4,5,15])]:
        dom=h['domains_normalized'][NET];groups=allgroups[NET];main_group=next(i for i,g in enumerate(groups) if any(q['kind']=='pad' and (q['ref'],q['pin'])==(rootref,'2') for q in g));source_group=-1;obs={};trees={};gaps={'rows':[]};own_new_zone_ids={q['uuid'] for q in zones if C.norm(q['net'])==NET}
        for gi in wanted:
            layergaps=[]
            for layer in h['copper_layers']:
                src=unary_union([r['shape'] for r in groups[gi] if r['layer']==layer and r['kind']!='fill']);dst=unary_union([r['shape'] for r in groups[main_group] if r['layer']==layer and (r['kind']!='fill' or r['uuid'] in own_new_zone_ids)])
                if src.is_empty or dst.is_empty:continue
                aa,bb=nearest_points(src,dst);layergaps.append({'layer':layer,'gap_mm':aa.distance(bb),'from_mm':list(aa.coords[0]),'to_mm':list(bb.coords[0])})
            gaps['rows'].append({'group':gi,'pads':sorted({(q['ref'],q['pin'],q['uuid']) for q in groups[gi] if q['kind']=='pad'}),'layer_gaps':sorted(layergaps,key=lambda q:q['gap_mm'])})
"""
text=text[:i]+initial+text[j:]
# Indent the construction body inside each exact field-bank task.
i=text.index('    for layer in h[',text.index("gaps['rows'].append"));j=text.index('    raw=pickle.dumps',i);text=text[:i]+''.join('    '+line+'\n' for line in text[i:j].splitlines())+text[j:]
text=text.replace("selected=[q for q in gaps['rows'] if q['group']==source_group]\n        if '--all' in sys.argv:selected+= [q for q in gaps['rows'] if q['group']!=source_group]","selected=list(gaps['rows'])")
text=text.replace("widths=[2.,1.5,1.] if sourcecase else [.5,.35,.25]","widths=[1.,.75,.5,.35,.25]")
text=text.replace("src=unary_union([r['shape'] for r in groups[gi] if r['layer']==layer]);target=unary_union([r['shape'] for r in groups[main_group] if r['layer']==layer])","src=unary_union([r['shape'] for r in groups[gi] if r['layer']==layer and r['kind']!='fill']);target=unary_union([r['shape'] for r in groups[main_group] if r['layer']==layer and (r['kind']!='fill' or r['uuid'] in own_new_zone_ids)])")
old="points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]));line=LineString(points);"
new="""inside=part.buffer(-.00002);sa=inside.intersection(src);tb=inside.intersection(target)
                        if sa.is_empty or tb.is_empty:attempts.append({'layer':layer,'width_mm':w,'verdict':'NO_POSITIVE_PHYSICAL_ENDPOINT_ATTACHMENT'});continue
                        start,end=nearest_points(sa,tb)
                        try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))
                        except AssertionError:
                            attempts.append({'layer':layer,'width_mm':w,'verdict':'EXACT_ROUTE_PRECISION_REJECTED'});continue
                        line=LineString(points);"""
assert old in text;text=text.replace(old,new)
text=text.replace("controller-field-logic-return-r1-'+str(gi)","controller-field-lost-contact-r1-'+bank+'-'+str(gi)")
text=text.replace("'source_external_return_repair':sourcecase","'source_external_return_repair':sourcecase,'field_bank':bank,'actual_source':rootref+'.2','source_endpoint_requirement':'Native physical pad/track/via, no cached-fill-only start','target_endpoint_requirement':'Native physical Cu or already source-rooted frozen new return Cu, no old cached-fill-only goal'")
text=text.replace("rows.append({'group':gi,","rows.append({'bank':bank,'net_raw':NET,'group':gi,")
text=text.replace("'gap_receipt_sha256':sha(HERE/'logic-group-gaps-r1/receipt.json'),","")
text=text.replace("'exact_existing_raw_token':NET,","'exact_existing_raw_tokens':[q['net'] for q in adds],")
text=text.replace("'frozen_r7_field_and_CORE_shapes_unchanged':True","'frozen_r7_field_and_CORE_and_24_GND_shapes_unchanged':True")
exec(compile(text,str(path),'exec'))
