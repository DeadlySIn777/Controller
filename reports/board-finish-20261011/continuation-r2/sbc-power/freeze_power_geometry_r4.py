"""Apply final cross-agent discrete antipads and freeze nanometre power shapes."""
import json,hashlib
from shapely import set_precision
from shapely.geometry import Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
import complete_geometry_r2 as G
L=G.L;p=G.p
def main():
    g,h,tail,binding,zones=G.model();out=L.OUT/'full-power-geometry-frozen-r4';out.mkdir(exist_ok=True);cache={};rows=[];changes=[]
    for z in zones:
        key=(z['net'],z['layer'])
        if key not in cache:
            obs=G.foreign_discrete(h,*key);cache[key]=(obs,STRtree([s for _,s in obs]))
        obs,tree=cache[key];hits=[obs[int(i)] for i in tree.query(z['shape'],predicate='intersects')];cut=unary_union([s for _,s in hits]);before=z['shape'];after=set_precision(before.difference(cut),1e-6);f=out/(z['label']+'.wkb');f.write_bytes(after.wkb)
        rows.append({'label':z['label'],'uuid':z['uuid'],'net_raw':z['net'],'layer':z['layer'],'geometry_file':str(f.resolve()),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'area_mm2':after.area,'component_count':len(p.hubs.components(after)),'prior_geometry_sha256':z['sha256']})
        if before.area-after.area>1e-9:changes.append({'label':z['label'],'removed_area_mm2':before.area-after.area,'cutters':[uid for uid,_ in hits]})
        print('FROZEN_ZONE',z['label'],len(p.hubs.components(after)),round(before.area-after.area,6),flush=True)
    # Raw names are source-authoritative, including the literal {slash} token.
    import raw_net_tokens_r2 as N
    for row in rows:row['net_raw']=N.raw(row['net_raw'])
    result={'verdict':'QUANTIZED_GEOMETRY_CONSTRUCTION_ONLY_CONTACT_CURRENT_NATIVE_GATES_OPEN','exact_source_board_sha256':L.live.SHA,'combined_parent_binding':binding,'native_coordinate_grid_nm':1,'zones':rows,'final_discrete_cut_ledger':changes,'native_jobs':0,'board_written':False}
    (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print('FROZEN_POWER_GEOMETRY',len(rows),len(changes),flush=True)
if __name__=='__main__':main()
