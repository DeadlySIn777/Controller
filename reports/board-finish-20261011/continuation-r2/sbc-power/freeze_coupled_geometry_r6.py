"""Finalize discrete antipads before mutually separating new power polygons."""
import json,hashlib
from shapely import set_precision
from shapely.ops import unary_union
from shapely.strtree import STRtree
import complete_geometry_r2 as G
import raw_net_tokens_r2 as N
L=G.L;p=G.p
def main():
    g,h,tail,binding,zones=G.model(with_field=True);out=L.OUT/'coupled-power-geometry-frozen-r6';out.mkdir(exist_ok=True);cache={};first=[];rows=[];changes=[]
    for z in zones:
        key=(z['net'],z['layer'])
        if key not in cache:
            obs=G.foreign_discrete(h,*key);cache[key]=(obs,STRtree([s for _,s in obs]))
        obs,tree=cache[key];hits=[obs[int(i)] for i in tree.query(z['shape'],predicate='intersects')];after=set_precision(z['shape'].difference(unary_union([s for _,s in hits])),1e-6);first.append({**z,'shape':after,'discrete_cutters':[uid for uid,_ in hits]})
    for old,z in zip(zones,first):
        hits=[]
        if not z.get('field_geometry_sha256'):
            hits=[(q['uuid'],q['shape'].buffer(G.gap(h,z['net'],q['net'])+.030)) for q in first if q.get('field_geometry_sha256') and q['layer']==z['layer'] and p.norm(q['net'])!=p.norm(z['net']) and q['shape'].buffer(.65).intersects(z['shape'])]
        after=set_precision(z['shape'].difference(unary_union([s for _,s in hits])),1e-6);f=out/(z['label']+'.wkb');f.write_bytes(after.wkb);components=p.hubs.components(after)
        rows.append({'label':z['label'],'uuid':z['uuid'],'net_raw':N.raw(z['net']),'layer':z['layer'],'geometry_file':str(f.resolve()),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'area_mm2':after.area,'component_count':len(components),'component_areas_mm2':sorted([q.area for q in components],reverse=True),'prior_geometry_sha256':old.get('sha256',old.get('field_geometry_sha256')),'field_return_proposal':bool(z.get('field_geometry_sha256'))})
        delta=old['shape'].difference(after)
        if not delta.is_empty:changes.append({'label':z['label'],'removed_area_mm2':delta.area,'discrete_cutters':z['discrete_cutters'],'foreign_field_cutters':[uid for uid,_ in hits]})
        print('COUPLED_R6',z['label'],len(components),round(delta.area,6),flush=True)
    result={'verdict':'COUPLED_CONSTRUCTION_ONLY_CONTACT_CURRENT_NATIVE_GATES_OPEN','exact_source_board_sha256':L.live.SHA,'combined_parent_binding':binding,'native_coordinate_grid_nm':1,'zones':rows,'final_discrete_and_foreign_field_cut_ledger':changes,'original_fill_retreats_recomputed_from_exact_source':True,'native_jobs':0,'board_written':False};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print('COUPLED_R6_FREEZE',len(rows),len(changes),flush=True)
if __name__=='__main__':main()
