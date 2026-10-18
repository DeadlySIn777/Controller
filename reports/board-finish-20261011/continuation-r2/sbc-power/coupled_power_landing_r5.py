"""Component membership of all power landing sites after the field overlay."""
import json
from shapely.geometry import Point
import complete_geometry_r2 as G
L=G.L;p=G.p
def main():
    g,h,tail,binding,zones=G.model(True,True);bank=json.loads((L.OUT/'joint-power-planes-r3.json').read_text());bulk=json.loads((L.OUT/'C94-bulk-feeds-r3.json').read_text());plane=next(q['shape'] for q in zones if q['label']=='CORE-main-In2');parts=p.hubs.components(plane);rows=[]
    for name,sites in [(q['name'],[s['at'] for s in q['sites']]) for q in bank['CORE_banks']]+[('C94',bulk['C94_banks'][0]['sites'])]:
        rows.append({'name':name,'sites':[{'at':at,'components':[i for i,s in enumerate(parts) if s.covers(Point(at))]} for at in sites]})
    result={'parts':[{'area':q.area,'bounds':q.bounds} for q in parts],'CORE_In2_landing_groups':rows,'full_current_and_all_remaining_sinks_open':True,'board_written':False,'native_jobs':0};(L.OUT/'coupled-power-landing-r5.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
