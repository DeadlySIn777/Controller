"""Original pad/track/flashed-barrel groups after all prospective repours."""
import json,sys,hashlib
from shapely.geometry import Point
from shapely.strtree import STRtree
from shapely.ops import unary_union
import complete_geometry_r2 as G
import io3_contact_restore_r2 as Q
L=G.L;p=G.p
def main():
    net=sys.argv[1] if len(sys.argv)>1 else '/IO_3V3';Q.NET=p.norm(net);g,h,tail,binding,zones=G.model(True);candidate,ledger=G.projected(g,h,zones)
    before,bparts,bassign=Q.groups(g,return_details=True);after,aparts,aassign=Q.groups(candidate,return_details=True)
    ai={r['uuid']:i for i,group in enumerate(after) for r in group};removed=tail[-1]|set(binding['removed_parent_Cu']);lost=[];missing=[]
    for i,group in enumerate(before):
        present=[r for r in group if r['uuid'] in ai];absent=[r for r in group if r['uuid'] not in ai and r['uuid'].split('@')[0] not in removed]
        # Explicit source-owned field pad-net moves have a separate pin graph.
        oldpads={q['uuid']:q for q in g['pads']};newpads={q['uuid']:q for q in h['pads']}
        absent=[r for r in absent if r['uuid'] not in oldpads or r['uuid'] not in newpads or p.norm(oldpads[r['uuid']]['net'])==p.norm(newpads[r['uuid']]['net'])]
        if absent:missing.append({'baseline_group':i,'terminals':absent})
        groups={ai[r['uuid']] for r in present}
        if len(groups)>1:lost.append({'baseline_group':i,'old_contact_count':len(group),'new_groups':[{'group':j,'contacts':[r for r in present if ai[r['uuid']]==j]} for j in sorted(groups)]})
    trees={layer:STRtree(v) for layer,v in aparts.items()};plane_obligations=[];plane_losses=[]
    changed={(r['zone_uuid'],r['layer']) for r in ledger if p.norm(r['net_raw'])==Q.NET};byid={z['uuid']:z for z in candidate['zones']}
    for z in g['zones']:
        if p.norm(z['net'])!=Q.NET:continue
        for layer,rs in z['fills'].items():
            if (z['uuid'],layer) not in changed:continue
            remaining=unary_union(p.base.polygons(byid[z['uuid']]['fills'][layer]))
            for i,poly in enumerate(p.base.polygons(rs)):
                for j,piece in enumerate(p.hubs.components(poly)):
                    left=piece.intersection(remaining);groups=set();spieces=p.hubs.components(left)
                    for sh in spieces:
                        for hit in trees[layer].query(sh,predicate='intersects'):
                            k=int(hit);group=aassign[layer][k];groups.add(group if group is not None else f'plane-only-{layer}-{k}')
                    row={'old_zone_uuid':z['uuid'],'layer':layer,'old_piece_index':[i,j],'old_area_mm2':piece.area,'retained_area_mm2':left.area,'candidate_Cu_groups':sorted(groups,key=str),'remaining_piece_count':len(spieces)};plane_obligations.append(row)
                    if len(groups)>1 or (piece.area>.000001 and left.is_empty):plane_losses.append(row)
    padgroups=[{'group':i,'pads':[r for r in group if not r['ref'].startswith('@')]} for i,group in enumerate(after) if any(not r['ref'].startswith('@') for r in group)]
    result={'verdict':'HOST_GROUPS_PASS' if not lost and not missing and not plane_losses else 'HOST_GROUPS_REQUIRE_CORRECTION','net_raw':net,'exact_source_board_sha256':L.live.SHA,'combined_parent_binding':binding,'before_contact_groups':len(before),'after_contact_groups':len(after),'before_pad_count':sum(not r['ref'].startswith('@') for group in before for r in group),'after_pad_count':sum(not r['ref'].startswith('@') for group in after for r in group),'lost_original_contact_partitions':lost,'missing_original_contacts_without_owned_contract':missing,'changed_old_plane_piece_obligations':plane_obligations,'old_plane_piece_partition_failures':plane_losses,'candidate_pad_groups':padgroups,'projected_original_fill_cut_ledger':[r for r in ledger if p.norm(r['net_raw'])==Q.NET],'native_refill_and_full_dual_guard_open':True,'native_jobs':0,'board_written':False}
    name=Q.NET.strip('/').replace('/','-');f=L.OUT/(name+'-complete-contact-guard-r4.json');f.write_text(json.dumps(result,indent=2)+'\n');print('CONTACT_GUARD',name,len(before),len(after),'lost',len(lost),'missing',len(missing),'plane',len(plane_losses),flush=True);print(json.dumps(lost[:2]));print(json.dumps(plane_losses[:3]))
if __name__=='__main__':main()
