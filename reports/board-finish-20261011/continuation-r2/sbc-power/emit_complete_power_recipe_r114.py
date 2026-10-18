"""Deterministic owned-only native recipe on exact eedf discrete geometry.

Run after the final host model/contact audit is frozen. No existing native
board is serialized, altered or saved by this emitter. Native API/refill/DRC
and electrical qualification remain separate gates in the receipt.
"""
import json,pickle,hashlib,uuid,sys,re
from decimal import Decimal
from pathlib import Path
from shapely import STRtree,set_precision
from shapely.geometry import Polygon,Point
import complete_geometry_r2 as G
L=G.L;p=G.p;FIELD=L.OUT.parent/'field-power'
sys.path.insert(0,str(FIELD))
from emit_logic_zones_r1 import render,PRIMARY
from verify_source import parse,children,child,atom
import owned_native_delta_r49 as OWNED
import owned_native_footprint_delta_r86 as FP
import owned_native_cu_replacements_r100 as CR
import owned_native_additional_flashes_r113 as EF
OUT=L.OUT/'complete-power-native-recipe-r114'
NAMESPACE=uuid.uuid5(uuid.NAMESPACE_DNS,'controller-board-finish-20261011-complete-power-owned-zones')
PARENT_SHA='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
SOURCE_SHA='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def native_uuid(token):
    try:return str(uuid.UUID(token))
    except ValueError:return str(uuid.uuid5(NAMESPACE,token))
def nm(x):
    scaled=Decimal(str(x))*1000000
    assert scaled==scaled.to_integral_value(),('non_integer_nm',x)
    return int(scaled)
def exact_ring(r):return [[nm(x),nm(y)] for x,y in list(r.coords)[:-1]]
def write_json(path,data):path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def main():
    assert len(sys.argv)==3,'model.pkl audit/receipt.json'
    model=Path(sys.argv[1]);auditpath=Path(sys.argv[2]);ar=json.loads(auditpath.read_text());assert sha(model)==ar['model_sha256']
    g,h,binding,zones,candidate=pickle.loads(model.read_bytes());native=L.OUT.parent/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(native)==PARENT_SHA
    basefile=FIELD/'native-bound-field-base-r5/model.pkl';baser=json.loads((basefile.parent/'receipt.json').read_text());assert sha(basefile)==baser['model_sha256'];base=pickle.loads(basefile.read_bytes())['discrete']
    source=FIELD/'combined-power-source-r3-hierarchy/source-export/fresh.net';assert sha(source)==SOURCE_SHA
    flashfile=FIELD/'additive-ground-b5-native-recipe-r27/native-flash-obligations.json';assert sha(flashfile)=='9c0970316e1a455efa2dbea86716df532a88fb73e2a6c7964f43f33009884e90';flashledger=json.loads(flashfile.read_text())
    logicreceipt=FIELD/'logic-island-repair-r18/receipt.json';assert sha(logicreceipt)=='d7d9fc1ba8bdbd40d2de8c13d80089e58a40949e7e8761302372838b04696950';logicledger=json.loads(logicreceipt.read_text())
    text=native.read_text(encoding='utf-8');rawnames=set(json.loads('"'+m+'"') for m in re.findall(r'\(net\s+"((?:[^"\\]|\\.)*)"\)',text));by_norm={}
    for raw in rawnames:by_norm.setdefault(p.norm(raw),set()).add(raw)
    assert all(len(names)==1 for names in by_norm.values()),'original raw net normalization collision'
    assert len({q['uuid'] for q in zones})==len(zones),'duplicate proposal zone UUID'
    original_zone_ids={q['uuid'] for q in base['zones']};assert not original_zone_ids & {native_uuid(q['uuid']) for q in zones}
    owned_removed,owned_recipes=OWNED.collect(binding,base)
    native_FP_rows,owned_FP_pads,owned_FP_recipes=FP.collect(binding,base,h)
    native_Cu_replacement_rows,owned_Cu_replaced,owned_Cu_replacement_recipes=CR.collect(binding,base,h)
    assert not set(owned_removed)&set(owned_Cu_replaced),'Existing item cannot be both removed and replaced'
    extra_flash_rows,extra_flash_recipes=EF.collect(binding,base,h)
    assert not set(extra_flash_rows)&(set(owned_removed)|set(owned_Cu_replaced)), 'Extra flash cannot hide a deleted or moved barrel'
    delta={};unchanged_existing={};prospective_flashes=[]
    for kind in ('pads','tracks','vias'):
        old={q['uuid']:q for q in base[kind]};new={q['uuid']:q for q in h[kind]}
        missing=set(old)-set(new)
        allowed={uid for uid,row in owned_removed.items() if row['kind']==('segment' if kind=='tracks' else 'via' if kind=='vias' else 'pad')}
        assert missing==allowed,('unlisted_or_not_applied_exact_owned_deletions',kind,missing-allowed,allowed-missing)
        for uid in old:
            if uid in missing:continue
            prior=old[uid];now=dict(new[uid]);extra=now.get('prospective_new_flash_requires_native_refill');booleanflag=now.get('prospective_extra_flash_native_required');consumed={}
            if extra is not None or booleanflag is not None:
                if uid in extra_flash_rows:
                    er=extra_flash_rows[uid]
                    assert kind=='vias' and booleanflag is None and extra==er['prospective_additional_flash_layer']
                    assert EF.canonical(prior)==er['expected_original_host_geometry'] and EF.canonical(now)==er['expected_prospective_host_geometry']
                    consumed['prospective_new_flash_requires_native_refill']=now.pop('prospective_new_flash_requires_native_refill')
                    ledger_file=er['explicit_ledger_file'];ledger_sha=er['explicit_ledger_sha256']
                else:
                    assert kind=='vias' and uid==logicledger['existing_via_UUID']
                    assert prior['flashed']==logicledger['existing_native_flash_mask']
                    assert extra is None or extra==logicledger['prospective_additional_flash_layer']
                    assert booleanflag is None or booleanflag is True
                    if extra is not None:consumed['prospective_new_flash_requires_native_refill']=now.pop('prospective_new_flash_requires_native_refill')
                    if booleanflag is not None:consumed['prospective_extra_flash_native_required']=now.pop('prospective_extra_flash_native_required')
                    extra=logicledger['prospective_additional_flash_layer'];ledger_file=str(logicreceipt.resolve());ledger_sha=sha(logicreceipt)
            if extra is not None:
                assert kind=='vias' and extra not in prior['flashed'] and set(now['flashed'])==set(prior['flashed'])|{extra}
                prospective_flashes.append({'uuid':uid,'original_native_flashes':prior['flashed'],'required_after_refill':now['flashed'],'same_existing_serialized_via':True,'exact_consumed_prospective_metadata':consumed,'explicit_ledger_file':ledger_file,'explicit_ledger_sha256':ledger_sha});now['flashed']=prior['flashed']
            if kind=='pads' and uid in owned_FP_pads:
                assert prior==owned_FP_pads[uid]['original_geometry'] and FP.canonical_record(now)==owned_FP_pads[uid]['replacement_geometry']
            elif kind in ('tracks','vias') and uid in owned_Cu_replaced:
                assert CR.canonical_record(prior)==owned_Cu_replaced[uid]['expected_original_geometry'] and CR.canonical_record(now)==owned_Cu_replaced[uid]['expected_replacement_geometry']
            else:assert now==prior,('unexpected_existing_native_discrete_change',kind,uid)
        unchanged_existing[kind]=len(old)-len(missing);delta[kind]=[q for q in h[kind] if q['uuid'] not in old]
    assert not delta['pads'],'New/moved footprints must receive a separate exact native/source-owned recipe'
    sourcepad=next(q for q in base['pads'] if q['uuid']=='44d821af-78a8-4535-84fa-6c94a3ab4d55')
    assert (sourcepad['ref'],sourcepad['num'])==('L19001','2') and sourcepad['smd'] and set(sourcepad['layers'])=={'F.Cu'}
    for obligation in flashledger:
        via=next(q for q in delta['vias'] if q['uuid']==obligation['uuid']);assert via['net']==obligation['net_raw']
        assert set(obligation['required_native_postfill_flash'])<=set(via['flashed'])
    assert all(q['net'] in rawnames for q in zones+delta['vias']+delta['tracks'])
    assert not OUT.exists();OUT.mkdir();rows=[];curows=[];contacts=[];physical={}
    # Existing eedf bytes are never reserialized. Root verifies these exact
    # original chunks before deleting them from its isolated contract copy.
    native_delete_rows=[]
    for row in owned_removed.values():
        path=OUT/(row['uuid']+'.delete-original-'+row['kind']+'-chunk');path.write_bytes(Path(row['chunk_path']).read_bytes())
        native_delete_rows.append({**row,'chunk_file':str(path.resolve()),'chunk_sha256':sha(path)})
    for layer in h['copper_layers']:
        rec=[]
        for q in h['pads']:
            for shape in p.base.polygons(q['layers'].get(layer,[])):rec.append({'kind':'pad','uuid':q['uuid'],'net':q['net'],'ref':q['ref'],'pin':q['num'],'shape':shape})
        rec += [{'kind':'segment','uuid':q['uuid'],'net':q['net'],'shape':p.base.body(q)} for q in h['tracks'] if q['layer']==layer]
        rec += [{'kind':'via','uuid':q['uuid'],'net':q['net'],'shape':Point(q['x'],q['y']).buffer(q['d']/2).difference(Point(q['x'],q['y']).buffer(q['drill']/2))} for q in h['vias'] if layer in q['flashed']]
        physical[layer]=(rec,STRtree([q['shape'] for q in rec]))
    allids=set(re.findall(r'\(uuid\s+"([^"]+)"\)',text));emitted=set();mapping=[]
    for z in zones:
        native_shape=z.get('zone_outline_shape',z['shape'])
        # The separately frozen canonical integer-nm union owns the exact
        # representation. Re-running GEOS precision here can change its
        # precision model by one binary ULP; exact integer-ring roundtrip
        # below is the serializer gate, without an area tolerance.
        assert binding.get('final_new_zone_coords_integer_nm_canonical_before_audit') is True
        shapes=sorted(p.hubs.components(native_shape),key=lambda s:(-s.area,s.bounds));parent_uid=native_uuid(z['uuid']);mapping.append({'proposal_uuid':z['uuid'],'native_parent_uuid':parent_uid,'detached_native_outers':len(shapes)})
        geometry_file=OUT/(parent_uid+'.physical-Cu.wkb');geometry_file.write_bytes(z['shape'].wkb)
        outline_file=OUT/(parent_uid+'.native-outline.wkb');outline_file.write_bytes(native_shape.wkb)
        for i,part in enumerate(shapes):
            uid=parent_uid if i==0 else str(uuid.uuid5(uuid.UUID(parent_uid),'separate-native-outer-'+str(i)));assert uid not in allids and uid not in emitted;emitted.add(uid)
            rings=[exact_ring(part.exterior)]+[exact_ring(r) for r in part.interiors]
            settings={'priority':int(z.get('priority',124)),'local_clearance_mm':float(z.get('clearance_mm',.15)),'min_thickness_mm':float(z.get('min_thickness_mm',.15)),'pad_connect_mode':z.get('pad_connect_mode','FULL_SOLID'),'island_removal_mode':int(z.get('island_removal_mode',1)),'thermal_gap_mm':float(z.get('thermal_gap_mm',.15)),'thermal_bridge_width_mm':float(z.get('thermal_bridge_width_mm',.3))}
            assert settings['pad_connect_mode']=='FULL_SOLID' and settings['local_clearance_mm']>=.15 and settings['min_thickness_mm']>=.15
            chunk=render(uid,z['net'],z['layer'],part).replace('(priority 20)','(priority %d)'%settings['priority']).replace('(clearance 0.15)','(clearance %.6f)'%settings['local_clearance_mm']).replace('(min_thickness 0.15)','(min_thickness %.6f)'%settings['min_thickness_mm']).replace('(thermal_gap 0.15)','(thermal_gap %.6f)'%settings['thermal_gap_mm']).replace('(thermal_bridge_width 0.3)','(thermal_bridge_width %.6f)'%settings['thermal_bridge_width_mm']).replace('(island_removal_mode 1)','(island_removal_mode %d)'%settings['island_removal_mode']).replace('Retained LOGIC_GND return repair','Complete power and retained-contact plane')
            path=OUT/(uid+'.zone-chunk');path.write_text(chunk,encoding='utf-8',newline='\n');ast=parse(chunk)
            assert atom(ast,'uuid')==uid and atom(ast,'net')==z['net'] and atom(ast,'layer')==z['layer'] and int(atom(ast,'priority'))==settings['priority']
            assert float(atom(child(ast,'connect_pads'),'clearance'))==settings['local_clearance_mm']
            assert float(atom(ast,'min_thickness'))==settings['min_thickness_mm']
            assert int(atom(child(ast,'fill'),'island_removal_mode'))==settings['island_removal_mode']
            assert float(atom(child(ast,'fill'),'thermal_gap'))==settings['thermal_gap_mm']
            assert float(atom(child(ast,'fill'),'thermal_bridge_width'))==settings['thermal_bridge_width_mm']
            roundtrip_rings=[[[nm(float(v[1])),nm(float(v[2]))] for v in child(poly,'pts')[1:]] for poly in children(ast,'polygon')]
            assert roundtrip_rings==rings,'serialized integer ring mismatch'
            rt=Polygon([(x/1e6,y/1e6) for x,y in rings[0]],[[(x/1e6,y/1e6) for x,y in r] for r in rings[1:]])
            assert rt.is_valid and rt.equals(part),'exact geometric roundtrip failed'
            assert not children(ast,'filled_polygon') and not children(ast,'fill_segments')
            rec,tree=physical[z['layer']];hit=[]
            for j in tree.query(part,predicate='intersects'):
                q=rec[int(j)]
                if q['net']==z['net']:hit.append({k:v for k,v in q.items() if k!='shape'}|{'physical_Cu_intersection_area_mm2':q['shape'].intersection(part).area})
            contacts.append({'uuid':uid,'proposal_uuid':z['uuid'],'raw_net':z['net'],'layer':z['layer'],'physical_contacts':hit})
            rows.append({'uuid':uid,'proposal_uuid':z['uuid'],'part_index':i,'raw_net':z['net'],'layer':z['layer'],'area_mm2':part.area,'outer_integer_nm':rings[0],'hole_integer_nm':rings[1:],'min_0p15_interior_nonempty':not part.buffer(-.075).is_empty,'chunk_file':str(path.resolve()),'chunk_sha256':sha(path),'physical_Cu_wkb_sha256':sha(geometry_file),'intended_native_outline_wkb_sha256':sha(outline_file),'native_refilled_geometry_and_contacts_attested':False,'declared_native_settings':settings,'declared_min_thickness_interior_nonempty':not part.buffer(-settings['min_thickness_mm']/2).is_empty})
    for kind,objects in [('via',delta['vias']),('segment',delta['tracks'])]:
        for q in objects:
            uid=q['uuid'];assert str(uuid.UUID(uid))==uid and uid not in allids and uid not in emitted;emitted.add(uid)
            path=OUT/(uid+'.'+kind+'-chunk')
            if kind=='via':
                nm(q['x']);nm(q['y']);chunk='\t(via\n\t\t(at %.6f %.6f)\n\t\t(size %.6f)\n\t\t(drill %.6f)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net %s)\n\t\t(uuid %s)\n\t)\n'%(q['x'],q['y'],q['d'],q['drill'],json.dumps(q['net']),json.dumps(uid))
            else:
                assert q['w']>=.20
                for point in (q['a'],q['b']):
                    for v in point:nm(v)
                chunk='\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.6f)\n\t\t(layer %s)\n\t\t(net %s)\n\t\t(uuid %s)\n\t)\n'%(*q['a'],*q['b'],q['w'],json.dumps(q['layer']),json.dumps(q['net']),json.dumps(uid))
            path.write_text(chunk,encoding='utf-8',newline='\n');ast=parse(chunk);assert atom(ast,'net')==q['net'] and atom(ast,'uuid')==uid
            curows.append({'kind':kind,'uuid':uid,'raw_net':q['net'],'geometry':q,'chunk_file':str(path.resolve()),'chunk_sha256':sha(path)})
    write_json(OUT/'physical-contact-ledger.json',contacts);write_json(OUT/'native-UUID-mapping.json',mapping)
    (OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(zones,protocol=5));(OUT/'new-owned-discrete.pkl').write_bytes(pickle.dumps(delta,protocol=5))
    host_retained_pass=all(not r['unowned_missing_old_contacts'] and not r['old_group_splits'] and r['all_native_dc936_loss_groups_restored'] for r in ar['rows'])
    host_all_supply_rooted=all(r['all_named_pads_rooted'] and r['all_new_polygons_rooted'] for r in ar['rows'])
    receipt={'verdict':'EXACT_OWNED_NATIVE_FORMAT_RECIPE_HOST_CONTACT_GATES_RECORDED_NATIVE_ELECTRICAL_PENDING','parent_native_board_file':str(native.resolve()),'parent_native_board_sha256':PARENT_SHA,'fresh_source_file':str(source.resolve()),'fresh_source_sha256':SOURCE_SHA,'frozen_host_model_file':str(model.resolve()),'frozen_host_model_sha256':sha(model),'full_original198b_and_dc936_contact_audit_file':str(auditpath.resolve()),'full_original198b_and_dc936_contact_audit_sha256':sha(auditpath),'host_retained_relationships_pass':host_retained_pass,'host_all_supply_pad_and_proposed_components_rooted':host_all_supply_rooted,'native_zone_rows':rows,'native_discrete_rows':curows,'new_zone_chunks':len(rows),'owned_proposal_shapes':len(zones),'new_vias':len(delta['vias']),'new_segments':len(delta['tracks']),'unchanged_existing_native_discrete_counts':unchanged_existing,'existing_via_prospective_new_flashes':prospective_flashes,'UUID_mapping_sha256':sha(OUT/'native-UUID-mapping.json'),'physical_contact_ledger_sha256':sha(OUT/'physical-contact-ledger.json'),'proposed_zones_sha256':sha(OUT/'proposed-zones.pkl'),'new_owned_discrete_sha256':sha(OUT/'new-owned-discrete.pkl'),'old_zone_removals':[],'old_zone_replacements':[],'old_zone_design_outline_config_net_priority_UUID_bytes_preserved':True,'raw_net_aliases':[],'all_new_coordinates_integer_nm_before_emit':True,'exact_AST_integer_ring_roundtrip':True,'new_zone_priority':'Per native_zone_rows declared_native_settings; no blanket override','pad_connect_mode':'FULL_SOLID; original overrides still require native validation','native_local_clearance_mm':'Per native_zone_rows declared_native_settings','native_min_thickness_mm':'Per native_zone_rows declared_native_settings','island_removal_mode':'Per native_zone_rows declared_native_settings','native_hole_semantics':'first polygon outer; subsequent polygons holes; detached outers each separate zone','native_parser_primary_source':PRIMARY,'native_API_full_Cu_source_pose_annulus_gate':'OPEN','native_refill_and_complete_original_baseline_no_loss_guard':'OPEN','native_ordinary_DRC_and_rule_effectiveness':'OPEN','complete_full_load_current_drop_barrel_thermal_transient_and_compute_contact_qualification':'OPEN','board_written':False,'board_adopted':False,'native_jobs':0}
    receipt.update({'authoritative_field_R27_native_flash_obligation_file':str(flashfile.resolve()),'authoritative_field_R27_native_flash_obligation_sha256':sha(flashfile),'authoritative_new_field_via_native_postfill_flash_obligations':flashledger,'B5_original_source_pad_obligation':{'uuid':sourcepad['uuid'],'ref':'L19001','pin':'2','actual_original_raw_net':sourcepad['net'],'actual_original_native_layer_mask':['F.Cu'],'no_existing_source_pad_mask_change':True},'B5_initial_In3_seed_label_superseded_by_explicit_F_In4_physical_ledger':True,'exact_known_LOGIC_extra_flash_ledger_sha256':sha(logicreceipt)})
    receipt.update({'native_existing_owned_footprint_replacement_rows':native_FP_rows,'existing_native_owned_footprint_replacement_recipes':owned_FP_recipes,'exact_changed_existing_physical_pad_UUIDs':sorted(owned_FP_pads),'all_other_existing_FP_metadata_and_courtyards_unchanged':True})
    receipt.update({'existing_native_owned_additional_flash_recipes':extra_flash_recipes,'no_unknown_prospective_mask_metadata_cleared':True})
    receipt.update({'native_existing_owned_Cu_replacement_rows':native_Cu_replacement_rows,'existing_native_owned_Cu_replacement_recipes':owned_Cu_replacement_recipes,'exact_changed_existing_Cu_UUIDs':sorted(owned_Cu_replaced),'same_UUID_existing_Cu_replacements_not_counted_as_additions':True})
    receipt.update({'native_existing_owned_Cu_delete_rows':native_delete_rows,'existing_native_owned_Cu_removal_recipes':owned_recipes,'exact_existing_native_deleted_segments':sum(row['kind']=='segment' for row in native_delete_rows),'exact_existing_native_deleted_vias':sum(row['kind']=='via' for row in native_delete_rows),'all_unlisted_existing_native_discrete_unchanged':True,'all_deleted_items_outside_contact_obligations_required':True})
    write_json(OUT/'receipt.json',receipt);print('EXACT_COMPLETE_POWER_RECIPE',len(rows),len(delta['vias']),len(delta['tracks']),host_retained_pass,host_all_supply_rooted,sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
