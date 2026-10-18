"""Exact CORE landing and field-overlap ledger after final foreign antipads."""
import json,hashlib
from shapely import from_wkb,set_precision
from shapely.geometry import Point
import complete_geometry_r2 as G
L=G.L;p=G.p
def main():
    g,h,tail,binding,zones=G.model(True,True,'r6');bank=json.loads((L.OUT/'joint-power-planes-r3.json').read_text());bulk=json.loads((L.OUT/'C94-bulk-feeds-r3.json').read_text());plane=next(q['shape'] for q in zones if q['label']=='CORE-main-In2');parts=p.hubs.components(plane);rows=[];out=L.OUT/'CORE-field-mutual-ledger-r6';out.mkdir(exist_ok=True)
    for name,sites in [(q['name'],[s['at'] for s in q['sites']]) for q in bank['CORE_banks']]+[('C94',bulk['C94_banks'][0]['sites'])]:rows.append({'name':name,'sites':[{'at':at,'components':[i for i,s in enumerate(parts) if s.covers(Point(at))]} for at in sites]})
    old=from_wkb((L.OUT/'CORE-In2-with-C94-arm-r3.wkb').read_bytes());overlaps=[]
    for q in zones:
        if not q.get('field_return_proposal') or q['layer']!='In2.Cu':continue
        overlap=set_precision(old.intersection(q['shape'].buffer(.63)),1e-6)
        if overlap.is_empty:continue
        f=out/(q['uuid']+'-CORE-overlap.wkb');f.write_bytes(overlap.wkb);overlaps.append({'field_zone_uuid':q['uuid'],'field_net_raw':q['net'],'field_zone_geometry_file':q['geometry_file'],'overlap_geometry_file':str(f.resolve()),'overlap_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'overlap_area_mm2':overlap.area,'bounds':overlap.bounds,'CORE_sites_in_field_clearance':[{'bank':row['name'],'at':s['at']} for row in rows for s in row['sites'] if q['shape'].distance(Point(s['at']))<.63]})
    result={'combined_parent_binding':binding,'parts':[{'area':q.area,'bounds':q.bounds} for q in parts],'CORE_In2_landing_groups':rows,'field_CORE_overlap_ledger':overlaps,'full_current_and_all_remaining_sinks_open':True,'board_written':False,'native_jobs':0};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
