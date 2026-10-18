"""Explicit CORE-priority local crossing carve of the proposed FAG In2 return."""
import json,hashlib,copy
from pathlib import Path
from shapely import from_wkb,set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
import complete_geometry_r2 as G
import continuous_path_r2 as CP
L=G.L;p=G.p;R=G.B.J.R
def main():
    g,h,tail,binding,zones=G.model(True,True,'r6');base=json.loads((L.OUT/'full-power-geometry-frozen-r4/receipt.json').read_text());row=next(q for q in base['zones'] if q['label']=='CORE-main-In2');core=from_wkb(Path(row['geometry_file']).read_bytes());bulk=json.loads((L.OUT/'C94-bulk-feeds-r3.json').read_text());sites=bulk['C94_banks'][0]['sites'];window=box(242,94,263,110);p.WINDOW=window;free=R.free_layer(h,L.stage.caps.CORE,'In2.Cu',window,('/IO_3V3',),reference_guard=None,allow_own_via_connection=True);part=next(q for q in p.hubs.components(free.buffer(-.3)) if q.covers(Point(sites[0])));lines=[];routes=[]
    for pt in sites:
        route=CP.path(part,sites[0],pt);assert route['verdict']=='HOST_PATH';routes.append(route);lines.append(LineString(route['points']).buffer(1.))
    hub=unary_union(lines).intersection(free);core=set_precision(core.union(hub),1e-6);out=L.OUT/'coupled-power-geometry-frozen-r7';out.mkdir(exist_ok=True);rows=[];ledger=[]
    for z in zones:
        sh=z['shape']
        if z['label']=='CORE-main-In2':sh=core
        elif z['uuid']=='ded2b949-0c87-5603-874b-a41f2f152e69':
            before=sh;sh=set_precision(sh.difference(core.buffer(.63)),1e-6);delta=before.difference(sh);f=out/'FAG-In2-CORE-crossing-removed.wkb';f.write_bytes(delta.wkb);ledger.append({'field_zone_uuid':z['uuid'],'layer':z['layer'],'removed_area_mm2':delta.area,'removed_geometry_file':str(f.resolve()),'removed_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'prior_field_geometry_sha256':z['sha256'],'CORE_priority_geometry_bound':True,'FAG_In1_In4_source_paths_retained':'Exact r6 shapes retained; full sharing/current guard required'})
        f=out/(z['label']+'.wkb');f.write_bytes(sh.wkb);parts=p.hubs.components(sh);rows.append({'label':z['label'],'uuid':z['uuid'],'net_raw':z['net'],'layer':z['layer'],'geometry_file':str(f.resolve()),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'area_mm2':sh.area,'component_count':len(parts),'component_areas_mm2':sorted([q.area for q in parts],reverse=True),'prior_geometry_sha256':z['sha256'],'field_return_proposal':bool(z.get('field_return_proposal'))})
        print('CORE_CROSSING_R7',z['label'],len(parts),flush=True)
    allsites=[(q['name'],s['at']) for q in json.loads((L.OUT/'joint-power-planes-r3.json').read_text())['CORE_banks'] for s in q['sites']]+[('C94',q) for q in sites];coreparts=p.hubs.components(core);landing=[{'bank':name,'at':at,'components':[i for i,q in enumerate(coreparts) if q.covers(Point(at))]} for name,at in allsites]
    result={'verdict':'CORE_PRIORITY_CROSSING_CONSTRUCTION_ONLY_CONTACT_CURRENT_NATIVE_GATES_OPEN','exact_source_board_sha256':L.live.SHA,'combined_parent_binding':binding,'native_coordinate_grid_nm':1,'zones':rows,'explicit_CORE_crossing_carve_ledger':ledger,'C94_all_four_site_In2_hub_routes':routes,'all_CORE_bank_landing_components':landing,'native_jobs':0,'board_written':False};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print('CORE_CROSSING_LANDINGS',[(name,{tuple(q['components']) for q in landing if q['bank']==name}) for name in ('source','load','C94')],flush=True)
if __name__=='__main__':main()
