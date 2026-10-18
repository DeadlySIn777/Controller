"""Original198b retained contacts and actual post-filter power-source markers.

Authorized old removals are explicit obligations, not silent census exclusions.
Every named pad and new polygon must join its actual electrical source. Each
original layer Cu union component's remaining positive area is also assigned
to all final physical groups, exposing pad-free retained branch splits.
"""
import json,pickle,hashlib
from pathlib import Path
from shapely import set_precision,STRtree
from shapely.ops import unary_union
import complete_geometry_r2 as G
import io3_contact_restore_r2 as Q
L=G.L;p=G.p;OUT=L.OUT/'full-power-source-contact-audit-r22'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
SOURCES={p.norm(L.stage.caps.CORE):('R11022','2'),'/motherboard_power_entry/SBC_5V':('U11012','8'),'/CORE_1V2':('L2001','2'),'/IO_3V3':('R18001','2'),'/mc_local_power/IO_3V3_REG_LOCAL':('L2002','2')}
def main():
    assert not OUT.exists();OUT.mkdir();model=L.OUT/'core-inner-feed-r24/model.pkl';g,h,binding,zones,candidate=pickle.loads(model.read_bytes());ownedpath=L.OUT/'owned-native-parts-r4/receipt.json';owned=json.loads(ownedpath.read_text());removed={q['uuid']:q for q in owned['old_Cu_removals']};rows=[];saved={}
    for net,source in SOURCES.items():
        Q.NET=net;before,bparts,bassign=Q.groups(g,return_details=True);after,parts,assign=Q.groups(candidate,return_details=True);saved[net]={'old_groups':before,'new_groups':after,'new_parts':parts,'new_assign':assign}
        lookup={q['uuid']:i for i,rs in enumerate(after) for q in rs};sourcepad=next(q for q in h['pads'] if (q['ref'],q['num'])==source);assert p.norm(sourcepad['net'])==net,(source,sourcepad['net'],net);root=lookup[sourcepad['uuid']]
        missing=[];split=[];ownedremovals=[]
        for oldi,rs in enumerate(before):
            divides={}
            for q in rs:
                if q['uuid'] not in lookup:
                    if q['uuid'] in removed:ownedremovals.append({'old_group':oldi,'contact':q,'exact_owned_removal':removed[q['uuid']],'shared_contact_restoration_required':True})
                    else:missing.append(q)
                else:divides.setdefault(lookup[q['uuid']],[]).append(q)
            if len(divides)>1:split.append({'old_group':oldi,'old_contact_count':len(rs),'new_groups':[{'group':j,'contacts':xs} for j,xs in divides.items()]})
        named=[{'group':i,**q,'source_connected':i==root} for i,rs in enumerate(after) for q in rs if not q['ref'].startswith('@')]
        newzones=[]
        for z in zones:
            if p.norm(z['net'])!=net:continue
            hits={j for s,j in zip(parts[z['layer']],assign[z['layer']]) if s.intersection(z['shape']).area>0 and j is not None};newzones.append({'uuid':z['uuid'],'label':z.get('label',z['uuid']),'layer':z['layer'],'groups':sorted(hits),'source_connected':hits=={root},'shape_wkb_sha256':hashlib.sha256(z['shape'].wkb).hexdigest()})
        branchsplits=[];entirelylost=[]
        for layer,oldparts in bparts.items():
            tree=STRtree(parts[layer])
            for oldindex,oldpiece in enumerate(oldparts):
                pieces=[]
                for ii in tree.query(oldpiece,predicate='intersects'):
                    j=int(ii);overlap=oldpiece.intersection(parts[layer][j])
                    if overlap.area>0:pieces.append({'candidate_part':j,'candidate_group':assign[layer][j],'retained_area_mm2':overlap.area,'retained_WKB_sha256':hashlib.sha256(overlap.wkb).hexdigest()})
                groups={q['candidate_group'] for q in pieces}
                if len(groups)>1:branchsplits.append({'layer':layer,'old_union_part':oldindex,'old_group':bassign[layer][oldindex],'old_area_mm2':oldpiece.area,'remaining_parts':pieces})
                if not pieces:entirelylost.append({'layer':layer,'old_union_part':oldindex,'old_group':bassign[layer][oldindex],'old_area_mm2':oldpiece.area})
        row={'net_normalized_for_lookup_only':net,'actual_raw_source_net':sourcepad['net'],'actual_source':source,'actual_source_pad_UUID':sourcepad['uuid'],'source_group':root,'old_groups':len(before),'new_groups':len(after),'unowned_missing_old_contacts':missing,'authorized_owned_removed_contacts':ownedremovals,'old_group_splits':split,'all_named_pads':named,'new_zones':newzones,'old_Cu_union_branch_splits':branchsplits,'entirely_lost_old_Cu_union_parts':entirelylost,'all_named_pads_rooted':all(q['source_connected'] for q in named),'all_new_polygons_rooted':all(q['source_connected'] for q in newzones),'native_current_minimum_web_and_thermal':'OPEN'};rows.append(row)
        (OUT/'checkpoint.json').write_text(json.dumps(rows,indent=2)+'\n');print('ACTUAL_SOURCE',net,source,'oldsplit',len(split),'missing',len(missing),'unrootedpads',sum(not q['source_connected'] for q in named),'branches',len(branchsplits),'removedUnion',len(entirelylost),flush=True)
    (OUT/'groups.pkl').write_bytes(pickle.dumps(saved,protocol=5));(OUT/'receipt.json').write_text(json.dumps({'verdict':'INDEPENDENT_ORIGINAL198B_ACTUAL_SOURCE_CONTACT_GUARD','model_sha256':sha(model),'owned_discrete_receipt_sha256':sha(ownedpath),'binding':binding,'rows':rows,'old_removals_not_silently_ignored':True,'native_jobs':0,'board_written':False,'full_source_current_return_harness_and_native_gates':'OPEN'},indent=2)+'\n')
if __name__=='__main__':main()
