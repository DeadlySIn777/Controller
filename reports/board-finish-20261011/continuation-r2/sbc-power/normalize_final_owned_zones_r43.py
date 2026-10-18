"""Canonical integer-nm union of same-raw/layer/equal-setting NEW zones.

Run only after all owned geometry is composed. Original native zone
definitions remain untouched. All representation/union deltas are ledgered
before fresh geometry/contact audits, never hidden by an area tolerance.
"""
import json,pickle,hashlib,uuid,sys
from pathlib import Path
from collections import defaultdict
from shapely import set_precision
from shapely.geometry import Polygon,MultiPolygon,GeometryCollection
from shapely.ops import unary_union
import core_inner_feed_r18 as I
import guarded_power_projection_r44 as P
L=I.L;p=I.p
OUT=L.OUT/'final-owned-zone-normalization-r43'
NAMESPACE=uuid.uuid5(uuid.NAMESPACE_DNS,'controller-final-owned-equal-settings-native-zone-union')
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def ring_integer(r):return [(int(round(x*1e6)),int(round(y*1e6))) for x,y in list(r.coords)[:-1]]
def canonical(sh):
    pieces=[];rows=[]
    for s in p.hubs.components(set_precision(sh,1e-6)):
        rr=[ring_integer(s.exterior)]+[ring_integer(r) for r in s.interiors]
        q=Polygon([(x/1e6,y/1e6) for x,y in rr[0]],[[(x/1e6,y/1e6) for x,y in r] for r in rr[1:]])
        assert q.is_valid
        pieces.append(q);rows.append(rr)
    if not pieces:return GeometryCollection(),rows
    q=pieces[0] if len(pieces)==1 else MultiPolygon(pieces)
    assert q.is_valid
    return q,rows
def examine_exact_parent_equal_priority(zones):
    """Inspect prior native definitions; never silently union old outlines."""
    import sys
    field=L.OUT.parent/'field-power';sys.path.insert(0,str(field))
    import contact_layout as C
    from verify_source import parse,children,child,atom
    parent=L.OUT.parent/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb'
    assert sha(parent)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
    _,chunks,_=C.O.C.pcbtext.split(parent.read_bytes());examined=[];overlaps=[]
    for ch in chunks:
        if C.O.C.pcbtext.chunk_kind(ch)!='zone':continue
        a=parse(ch.decode('utf-8'))
        if children(a,'rule_area'):continue
        priority=int(atom(a,'priority') or 0);raw=atom(a,'net');layer=atom(a,'layer')
        if not layer:
            ls=child(a,'layers');layers=ls[1:] if ls else []
        else:layers=[layer]
        row={'native_original_uuid':atom(a,'uuid'),'raw_net':raw,'layers':layers,'priority':priority,'exact_original_chunk_sha256':hashlib.sha256(ch).hexdigest()};examined.append(row)
        possible=[z for z in zones if z['net']==raw and z['layer'] in layers and int(z.get('priority',124))==priority]
        if not possible:continue
        rings=[[(float(v[1]),float(v[2])) for v in child(q,'pts')[1:]] for q in children(a,'polygon')]
        assert rings,('native_parent_zone_without_outline',row)
        old=Polygon(rings[0],rings[1:]);assert old.is_valid,('native_parent_zone_outline_invalid',row)
        for z in possible:
            current=z.get('zone_outline_shape',z['shape'])
            if current.intersects(old):overlaps.append({**row,'new_proposal_uuid':z['uuid'],'intended_outline_overlap_area_mm2':current.intersection(old).area,'ownership_bound_old_zone_correction_required':True})
    return {'parent_file':str(parent.resolve()),'parent_sha256':sha(parent),'examined_ordinary_native_zone_count':len(examined),'maximum_parent_priority':max(r['priority'] for r in examined),'all_native_original_definition_rows':examined,'same_raw_layer_equal_priority_contacts':overlaps,'original_definitions_not_silently_merged':True,'all_overlaps_require_explicit_owned_recipe':True}
def main():
    assert len(sys.argv)==2;prior=Path(sys.argv[1]);assert not OUT.exists();OUT.mkdir()
    g,h,binding,zones,_=pickle.loads(prior.read_bytes());original_ids={q['uuid'] for q in h['zones']}
    assert not original_ids & {q['uuid'] for q in zones}
    keys=defaultdict(list)
    for z in zones:
        # Every currently emitted proposal uses these exact native settings;
        # differing future effective settings must form a separate union key.
        key=(z['net'],z['layer'],float(z.get('clearance_mm',.15)),float(z.get('min_thickness_mm',.15)),z.get('pad_connect_mode','FULL_SOLID'),int(z.get('priority',124)),int(z.get('island_removal_mode',1)))
        assert key[2:]==(.15,.15,'FULL_SOLID',124,1),('unrecognized_native_zone_settings',key)
        keys[key].append(z)
    output=[];ledger=[]
    for key,members in sorted(keys.items()):
        label='|'.join(map(str,key))+'|'+'|'.join(sorted(z['uuid'] for z in members));uid=str(uuid.uuid5(NAMESPACE,label))
        physical_input=unary_union([z['shape'] for z in members]);outline_input=unary_union([z.get('zone_outline_shape',z['shape']) for z in members])
        physical,rings=canonical(physical_input);outline,outline_rings=canonical(outline_input)
        paths={}
        for role,shape in (('physical-before',physical_input),('outline-before',outline_input),('physical-after',physical),('outline-after',outline)):
            f=OUT/(uid+'.'+role+'.wkb');f.write_bytes(shape.wkb);paths[role]={'file':str(f.resolve()),'sha256':sha(f),'area_mm2':shape.area}
        constituents=[]
        for z in members:
            constituents.append({'proposal_uuid':z['uuid'],'label':z.get('label'),'physical_WKB_sha256':hashlib.sha256(z['shape'].wkb).hexdigest(),
                'intended_outline_WKB_sha256':hashlib.sha256(z.get('zone_outline_shape',z['shape']).wkb).hexdigest(),
                'physical_area_mm2':z['shape'].area,'intended_outline_area_mm2':z.get('zone_outline_shape',z['shape']).area,
                'preserved_metadata':{k:v for k,v in z.items() if k not in ('shape','zone_outline_shape','contacts','route')}})
        # All constituent contact/current obligations survive by explicit
        # mapping, including previously carved main field returns.
        output.append({'uuid':uid,'label':'owned-equal-settings-union-'+uid,'net':key[0],'layer':key[1],'shape':physical,'zone_outline_shape':outline,
            'clearance_mm':key[2],'min_thickness_mm':key[3],'pad_connect_mode':key[4],'priority':key[5],'island_removal_mode':key[6],
            'constituent_proposal_UUIDs':sorted(z['uuid'] for z in members),'integer_nm_physical_rings':rings,'integer_nm_native_outline_rings':outline_rings})
        ledger.append({'merged_uuid':uid,'raw_net':key[0],'layer':key[1],'settings':list(key[2:]),'constituents':constituents,'geometry_files':paths,
            'precanonical_union_has_no_net_or_shape_additions':True,'physical_integer_quantization_added_area_mm2':physical.difference(physical_input).area,
            'physical_integer_quantization_removed_area_mm2':physical_input.difference(physical).area,
            'outline_integer_quantization_added_area_mm2':outline.difference(outline_input).area,
            'outline_integer_quantization_removed_area_mm2':outline_input.difference(outline).area,
            'all_deltas_explicit_and_require_new_audit':True,'native_detached_outer_count':len(outline_rings),
            'native_same_priority_point_touch_between_detached_outers_requires_check':any(a.intersects(b) for i,a in enumerate(p.hubs.components(outline)) for b in p.hubs.components(outline)[i+1:])})
    lp=OUT/'constituent-union-and-integer-ledger.json';lp.write_text(json.dumps(ledger,indent=2)+'\n')
    parent_screen=examine_exact_parent_equal_priority(output);psf=OUT/'exact-native-parent-equal-priority-screen.json';psf.write_text(json.dumps(parent_screen,indent=2)+'\n')
    assert not parent_screen['same_raw_layer_equal_priority_contacts'],'Explicit owned old native-zone correction required before final emission'
    binding.update({'final_owned_zone_union_parent_model_sha256':sha(prior),'final_owned_zone_union_integer_ledger_file':str(lp.resolve()),'final_owned_zone_union_integer_ledger_sha256':sha(lp),
        'restored_generated_grid_UUIDs':[],'final_new_zone_coords_integer_nm_canonical_before_audit':True,
        'final_integer_union_projector_file':str(Path(P.__file__).resolve()),'final_integer_union_projector_sha256':sha(Path(P.__file__)),
        'final_exact_native_parent_equal_priority_screen_file':str(psf.resolve()),'final_exact_native_parent_equal_priority_screen_sha256':sha(psf),
        'original_native_zone_definitions_unchanged':True,'all_original_constituent_contact_and_current_obligations_retained_in_union_ledger':True})
    candidate,cuts=P.projected(g,h,output);model=OUT/'model.pkl';model.write_bytes(pickle.dumps((g,h,binding,output,candidate),protocol=5))
    receipt={'verdict':'FINAL_NEW_ZONE_INTEGER_UNION_FROZEN_FRESH_ALL_GATES_REQUIRED','model_sha256':sha(model),'parent_model_sha256':sha(prior),
        'union_ledger_file':str(lp.resolve()),'union_ledger_sha256':sha(lp),'original_new_proposal_count':len(zones),'merged_net_layer_settings_count':len(output),
        'original_zone_UUIDs_count':len(original_ids),'old_fill_retreats':cuts,'binding':binding,'all_geometry_original_contacts_current_native_gates':'REQUIRED_AFTER_THIS_FREEZE','native_jobs':0,'board_written':False}
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('FINAL_OWNED_INTEGER_ZONE_UNION',len(zones),len(output),sha(model),flush=True)
if __name__=='__main__':main()
