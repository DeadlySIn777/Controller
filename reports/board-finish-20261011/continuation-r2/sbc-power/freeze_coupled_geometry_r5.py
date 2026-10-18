"""Quantize mutual CORE/IO3/field return separation, retaining exact ledgers."""
import json,hashlib
from shapely import set_precision
from shapely.ops import unary_union
from shapely.strtree import STRtree
import complete_geometry_r2 as G
import raw_net_tokens_r2 as N
L=G.L;p=G.p
def main():
    g,h,tail,binding,zones=G.model(with_field=True);out=L.OUT/'coupled-power-geometry-frozen-r5';out.mkdir(exist_ok=True);cache={};rows=[];changes=[]
    for z in zones:
        key=(z['net'],z['layer'])
        if key not in cache:
            obs=G.foreign_discrete(h,*key);cache[key]=(obs,STRtree([s for _,s in obs]))
        obs,tree=cache[key];hits=[obs[int(i)] for i in tree.query(z['shape'],predicate='intersects')]
        # Field returns own their retained source proposal outlines. CORE/IO3
        # routing must explicitly clear all proposed field polygons. Field's
        # own mutual clearance was independently checked in its source receipt.
        if not z.get('field_geometry_sha256'):
            hits += [(q['uuid'],q['shape'].buffer(G.gap(h,z['net'],q['net'])+.030)) for q in zones if q.get('field_geometry_sha256') and q['layer']==z['layer'] and p.norm(q['net'])!=p.norm(z['net']) and q['shape'].buffer(.65).intersects(z['shape'])]
        before=z['shape'];after=set_precision(before.difference(unary_union([s for _,s in hits])),1e-6);f=out/(z['label']+'.wkb');f.write_bytes(after.wkb);components=p.hubs.components(after)
        rows.append({'label':z['label'],'uuid':z['uuid'],'net_raw':N.raw(z['net']),'layer':z['layer'],'geometry_file':str(f.resolve()),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'area_mm2':after.area,'component_count':len(components),'component_areas_mm2':sorted([q.area for q in components],reverse=True),'prior_geometry_sha256':z.get('sha256',z.get('field_geometry_sha256')),'field_return_proposal':bool(z.get('field_geometry_sha256'))})
        if before.area-after.area>1e-9:changes.append({'label':z['label'],'removed_area_mm2':before.area-after.area,'cutters':[uid for uid,_ in hits]})
        print('COUPLED_ZONE',z['label'],len(components),round(before.area-after.area,6),flush=True)
    result={'verdict':'COUPLED_CONSTRUCTION_ONLY_CONTACT_CURRENT_NATIVE_GATES_OPEN','exact_source_board_sha256':L.live.SHA,'combined_parent_binding':binding,'native_coordinate_grid_nm':1,'zones':rows,'final_discrete_and_foreign_field_cut_ledger':changes,'native_jobs':0,'board_written':False};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print('COUPLED_FREEZE',len(rows),len(changes),flush=True)
if __name__=='__main__':main()
