"""Original198b retained contacts and actual post-filter power-source markers.

Authorized old removals are explicit obligations, not silent census exclusions.
Every named pad and new polygon must join its actual electrical source. Each
original layer Cu union component's remaining positive area is also assigned
to all final physical groups, exposing pad-free retained branch splits.
"""
import json,pickle,hashlib,sys
from pathlib import Path
from shapely import set_precision,STRtree
from shapely.ops import unary_union
import complete_geometry_r2 as G
import io3_contact_restore_r2 as Q
L=G.L;p=G.p;OUT=L.OUT/'full-power-source-contact-audit-r89'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
SOURCES={p.norm(L.stage.caps.CORE):('R11022','2'),'/motherboard_power_entry/SBC_5V':('U11012','8'),'/CORE_1V2':('L2001','2'),'/IO_3V3':('R18001','2'),'/mc_local_power/IO_3V3_REG_LOCAL':('L2002','2')}
def main():
    model=Path(sys.argv[1]) if len(sys.argv)>1 else L.OUT/'core-inner-feed-r24/model.pkl'
    assert model.exists();assert not OUT.exists();OUT.mkdir();g,h,binding,zones,candidate=pickle.loads(model.read_bytes());ownedpath=L.OUT/'owned-native-parts-r4/receipt.json';owned=json.loads(ownedpath.read_text());removed={q['uuid']:q for q in owned['old_Cu_removals']};rows=[];saved={}
    native_diag_path=L.OUT.parent/'field-native-partition-diagnostic-r1/receipt.json';native_diag=json.loads(native_diag_path.read_text())
    assert native_diag['candidate_sha256']=='dc93656a303d8a507369617ef60ac4f3aaf5b78e6f8bb699a391ed5a8b6ccb6b'
    fp_ledger_path=L.OUT/'r17031-translated-source-composition-r78/exact-host-footprint-translation-ledger.json'
    fp_ledger=json.loads(fp_ledger_path.read_text());relocated=[r for r in fp_ledger if r['kind']=='pad']
    for net,source in SOURCES.items():
        Q.NET=net;before,bparts,bassign=Q.groups(g,return_details=True);after,parts,assign=Q.groups(candidate,return_details=True);saved[net]={'old_groups':before,'new_groups':after,'new_parts':parts,'new_assign':assign}
        lookup={q['uuid']:i for i,rs in enumerate(after) for q in rs};sourcepad=next(q for q in h['pads'] if (q['ref'],q['num'])==source);assert p.norm(sourcepad['net'])==net,(source,sourcepad['net'],net);root=lookup[sourcepad['uuid']]
        native_losses=[]
        for loss in native_diag['unchanged_1beb_relationships']['losses']:
            if p.norm(loss['net_before'])!=net:continue
            matched=[];ambiguous=[]
            for native_id in loss['old_retained_group']:
                refpin,occurrence=native_id.rsplit('#',1);ref,pin=refpin.rsplit('.',1)
                matches=[q for q in h['pads'] if (q['ref'],q['num'])==(ref,pin)]
                if len(matches)!=1 or occurrence!='0':
                    ambiguous.append({'native_pad_id':native_id,'matching_physical_UUIDs':[q['uuid'] for q in matches],'native_pad_order_binding_required':True});continue
                pad=matches[0];matched.append({'native_pad_id':native_id,'physical_pad_UUID':pad['uuid'],'actual_raw_net':pad['net'],'candidate_group':lookup.get(pad['uuid']),'source_connected':lookup.get(pad['uuid'])==root})
            divisions={q['candidate_group'] for q in matched}
            native_losses.append({'native_raw_net':loss['net_before'],'old_native_retained_group':loss['old_retained_group'],'native_measured_after_groups':loss['after_groups'],'exact_unique_physical_pad_matches':matched,'ambiguous_native_ordinal_bindings':ambiguous,'restored_old_relationship':not ambiguous and len(matched)==len(loss['old_retained_group']) and len(divisions)==1 and None not in divisions,'full_source_rooted':not ambiguous and len(matched)==len(loss['old_retained_group']) and all(q['source_connected'] for q in matched)})
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
        newzones=[];new_union_components=[]
        for layer,layerparts in parts.items():
            for partindex,piece in enumerate(layerparts):
                group=assign[layer][partindex]
                new_union_components.append({'layer':layer,'part_index':partindex,'group':group,'area_mm2':piece.area,'source_connected':group==root,'shape_wkb_sha256':hashlib.sha256(piece.wkb).hexdigest()})
        for z in zones:
            if p.norm(z['net'])!=net:continue
            detached=[]
            for component_index,piece in enumerate(p.hubs.components(z['shape'])):
                hits={j for s,j in zip(parts[z['layer']],assign[z['layer']]) if s.intersection(piece).area>0}
                detached.append({'component_index':component_index,'area_mm2':piece.area,'groups':sorted(hits,key=lambda j:(j is None,-1 if j is None else j)),'source_connected':hits=={root},'shape_wkb_sha256':hashlib.sha256(piece.wkb).hexdigest(),'minimum_web_0p15_eroded_interior_nonempty':not piece.buffer(-.075).is_empty})
            newzones.append({'uuid':z['uuid'],'label':z.get('label',z['uuid']),'layer':z['layer'],'detached_components':detached,'source_connected':bool(detached) and all(c['source_connected'] for c in detached),'shape_wkb_sha256':hashlib.sha256(z['shape'].wkb).hexdigest()})
        branchsplits=[];entirelylost=[];authorized_relocated_old_parts=[]
        for layer,oldparts in bparts.items():
            tree=STRtree(parts[layer])
            for oldindex,oldpiece in enumerate(oldparts):
                pieces=[]
                for ii in tree.query(oldpiece,predicate='intersects'):
                    j=int(ii);overlap=oldpiece.intersection(parts[layer][j])
                    if overlap.area>0:pieces.append({'candidate_part':j,'candidate_group':assign[layer][j],'retained_area_mm2':overlap.area,'retained_WKB_sha256':hashlib.sha256(overlap.wkb).hexdigest()})
                groups={q['candidate_group'] for q in pieces}
                if len(groups)>1:branchsplits.append({'layer':layer,'old_union_part':oldindex,'old_group':bassign[layer][oldindex],'old_area_mm2':oldpiece.area,'remaining_parts':pieces})
                if not pieces:
                    owned_moved=[r for r in relocated if p.norm(r['original_geometry']['net'])==net and layer in r['original_geometry']['layers']]
                    matches=[r for r in owned_moved if oldpiece.difference(unary_union(p.base.polygons(r['original_geometry']['layers'][layer]))).is_empty]
                    record={'layer':layer,'old_union_part':oldindex,'old_group':bassign[layer][oldindex],'old_area_mm2':oldpiece.area}
                    if matches:
                        assert len(matches)==1;rr=matches[0];assert lookup[rr['uuid']]==root
                        record.update({'exact_original_moved_pad_UUID':rr['uuid'],'exact_authorized_pose_ledger_file':str(fp_ledger_path.resolve()),'exact_authorized_pose_ledger_sha256':sha(fp_ledger_path),'original_component_contains_only_exact_owned_moved_pad_geometry':True,'replacement_named_pad_actual_source_rooted':True});authorized_relocated_old_parts.append(record)
                    else:entirelylost.append(record)
        row={'net_normalized_for_lookup_only':net,'actual_raw_source_net':sourcepad['net'],'actual_source':source,'actual_source_pad_UUID':sourcepad['uuid'],'source_group':root,'old_groups':len(before),'new_groups':len(after),'unowned_missing_old_contacts':missing,'authorized_owned_removed_contacts':ownedremovals,'old_group_splits':split,'all_named_pads':named,'new_zones':newzones,'all_final_Cu_union_components':new_union_components,'old_Cu_union_branch_splits':branchsplits,'entirely_lost_old_Cu_union_parts':entirelylost,'authorized_relocated_original_pad_only_union_parts':authorized_relocated_old_parts,'native_dc936_measured_power_loss_closure':native_losses,'all_native_dc936_loss_groups_restored':all(q['restored_old_relationship'] for q in native_losses),'all_native_dc936_loss_pads_source_rooted':all(q['full_source_rooted'] for q in native_losses),'all_named_pads_rooted':all(q['source_connected'] for q in named),'all_new_polygons_rooted':all(q['source_connected'] for q in newzones),'native_current_minimum_web_and_thermal':'OPEN'};rows.append(row)
        (OUT/'checkpoint.json').write_text(json.dumps(rows,indent=2)+'\n');print('ACTUAL_SOURCE',net,source,'oldsplit',len(split),'missing',len(missing),'unrootedpads',sum(not q['source_connected'] for q in named),'branches',len(branchsplits),'removedUnion',len(entirelylost),flush=True)
    (OUT/'groups.pkl').write_bytes(pickle.dumps(saved,protocol=5));(OUT/'receipt.json').write_text(json.dumps({'verdict':'INDEPENDENT_ORIGINAL198B_ACTUAL_SOURCE_CONTACT_GUARD','model_path':str(model.resolve()),'model_sha256':sha(model),'owned_discrete_receipt_sha256':sha(ownedpath),'actual_native_field_trial_loss_diagnostic_file':str(native_diag_path.resolve()),'actual_native_field_trial_loss_diagnostic_sha256':sha(native_diag_path),'actual_native_field_trial_board_sha256':native_diag['candidate_sha256'],'binding':binding,'rows':rows,'old_removals_not_silently_ignored':True,'each_detached_proposed_component_checked_including_pad_free_groups':True,'native_jobs':0,'board_written':False,'full_source_current_return_harness_and_native_gates':'OPEN'},indent=2)+'\n')
if __name__=='__main__':main()
