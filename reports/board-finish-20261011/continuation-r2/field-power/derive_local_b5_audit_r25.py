"""Derive explicit R23+B5 complete mutual audit from preserved R19 verifier."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'audit_repaired_local_returns_r19.py').read_text(encoding='utf-8')
def change(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
change("OUT=HERE/'repaired-local-return-audit-r19'","OUT=HERE/'local-and-b5-return-audit-r25'")
marker=" smd=[{'uuid':q['uuid']"
assert s.count(marker)==1
injection=""" for label in('remaining-field-ground-feeds-r23','b5-source-rooted-feeds-r4'):
  extra=HERE/label;er=json.loads((extra/'receipt.json').read_text());assert sha(extra/'proposed-discrete.pkl')==er['proposed_discrete_sha256'];ed=pickle.loads((extra/'proposed-discrete.pkl').read_bytes());assert sha(extra/'proposed-zones.pkl')==er['proposed_zones_sha256'];ez=pickle.loads((extra/'proposed-zones.pkl').read_bytes());nv+=ed['vias'];nt+=ed['tracks'];zones+=ez;inputs[label]=sha(extra/'receipt.json');h={**h,'tracks':h['tracks']+ed['tracks'],'vias':h['vias']+ed['vias']}
 assert len(nv)==25 and len(nt)==108
"""
s=s.replace(marker,injection+marker)
marker=" print('projecting',len(zones),'planes',flush=True)"
assert s.count(marker)==1
cucheck=""" records,trees=F.build({**h,'zones':[]});cufail=[]
 for v in nv:
  net=C.norm(v['net']);dom=h['domains_normalized'][net];disk=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=32)
  for l in v['flashed']:
   for j in trees[l].query(disk.buffer(.65),predicate='intersects'):
    q=records[l][int(j)]
    if C.norm(q['net'])==net:continue
    required=(.15 if q['domain']==dom else .6)+.025;d=disk.distance(q['shape'])
    if d<required-1e-7:cufail.append({'kind':'via','uuid':v['uuid'],'layer':l,'other_UUID':q['uuid'],'other_raw_net':q['net'],'distance_mm':d,'required_mm':required})
 for t in nt:
  net=C.norm(t['net']);dom=h['domains_normalized'][net];body=C.body(t);l=t['layer']
  for j in trees[l].query(body.buffer(.65),predicate='intersects'):
   q=records[l][int(j)]
   if C.norm(q['net'])==net:continue
   required=(.15 if q['domain']==dom else .6)+.025;d=body.distance(q['shape'])
   if d<required-1e-7:cufail.append({'kind':'segment','uuid':t['uuid'],'layer':l,'other_UUID':q['uuid'],'other_raw_net':q['net'],'distance_mm':d,'required_mm':required})
 write(OUT/'ordinary-Cu-clearance-receipt.json',{'verdict':'PASS' if not cufail else 'REJECT','failures':cufail,'all25_vias_all_screened_layers':True,'all108_segment_exact_body_checks':True,'native_domain_receipt':str((HERE.parent/'native-raw-domain-contract-r1/receipt.json').resolve())});print('ordinary-Cu',len(cufail),'foreign-zone-collisions',len(collisions),flush=True)
"""
s=s.replace(marker,cucheck+marker)
change("sources.append({'domain':bank,'net':net,'source_root':rootref+'.2','source_group':ri,'rooted_named_physical_pads':len(rooted),'unrooted_named_groups':bare})", "sources.append({'domain':bank,'net':net,'source_root':rootref+'.2','source_group':ri,'rooted_named_physical_pads':len(rooted),'unrooted_named_groups':bare})\n b5net='/motherboard_safety_sensor/FIELD_B_5V_PRE';bg=gg[b5net];bri=next(i for i,xs in enumerate(bg) if any(q['kind']=='pad' and(q['ref'],q['pin'])==('L19001','2') for q in xs));b5bare=[{'group':i,'physical_pads':[C.identity(q) for q in xs if q['kind']=='pad' and q['pin']]} for i,xs in enumerate(bg) if i!=bri and any(q['kind']=='pad' and q['pin'] for q in xs)];sources.append({'domain':'FB_B5PRE','net':b5net,'local_converter_output_root':'L19001.2','external_source':'J11005.1 via U11006 and U19028; upstream protected24 still separate root obligation','source_group':bri,'rooted_named_physical_pads':len({q['uuid'] for q in bg[bri] if q['kind']=='pad' and q['pin']}),'unrooted_named_groups':b5bare})")
change("if apreceipt['verdict']=='PASS' and not collisions and all(q['verdict']=='PASS' for q in rows)","if apreceipt['verdict']=='PASS' and not collisions and not cufail and not b5bare and all(q['verdict']=='PASS' for q in rows)")
change("'aperture_receipt_sha256':sha(OUT/'aperture-receipt.json')","'aperture_receipt_sha256':sha(OUT/'aperture-receipt.json'),'ordinary_Cu_clearance_receipt_sha256':sha(OUT/'ordinary-Cu-clearance-receipt.json')")
change("'B5_root_positive24_and_new_CORE_feeds_not_composed':True","'B5_source_complete_but_native_refill_current_still_pending':True,'root_positive24_and_new_CORE_feeds_not_composed':True,'U11015_companion_wall_and_other5_ground_groups_not_composed':True")
out=HERE/'audit_local_and_b5_returns_r25.py';assert not out.exists();out.write_text(s,encoding='utf-8')
