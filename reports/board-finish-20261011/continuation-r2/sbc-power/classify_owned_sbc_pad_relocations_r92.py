"""Classify R89 two missing old SBC components against exact owned pad moves.

The original part is reconstructed at the same declared 1 nm grid used by
Q.groups. It must equal a union of originally isolated, moved pad copper;
no original trace, via, zone fill, or nonowned pad may be excluded.
"""
import json,pickle,hashlib
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point
from shapely.ops import unary_union
import complete_geometry_r2 as G
L=G.L;p=G.p;O=L.OUT/'sbc-owned-pad-only-relocation-proof-r92'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    assert not O.exists();O.mkdir()
    prior=L.OUT/'r17031-translated-source-composition-r78/model.pkl';g,h,b,z,c=pickle.loads(prior.read_bytes())
    af=L.OUT/'full-power-source-contact-audit-r89/receipt.json';audit=json.loads(af.read_text());row=next(r for r in audit['rows'] if r['net_normalized_for_lookup_only']=='/motherboard_power_entry/SBC_5V')
    rf=L.OUT/'owned-native-parts-r4/receipt.json';recipe=json.loads(rf.read_text());refs={r['ref']:r for r in recipe['footprint_replacements']};n=row['net_normalized_for_lookup_only'];out=[]
    for r in row['entirely_lost_old_Cu_union_parts']:
        layer=r['layer'];pads=[pad for pad in g['pads'] if p.norm(pad['net'])==n]
        owned=[pad for pad in pads if pad['ref'] in refs]
        all_shapes=[s for q in g['zones'] if p.norm(q['net'])==n for s in p.base.polygons(q['fills'].get(layer,[]))]
        all_shapes += [s for pad in pads for s in p.base.polygons(pad['layers'].get(layer,[]))]
        all_shapes += [p.base.body(t) for t in g['tracks'] if p.norm(t['net'])==n and t['layer']==layer]
        all_shapes += [Point(v['x'],v['y']).buffer(v['d']/2) for v in g['vias'] if p.norm(v['net'])==n and layer in v['flashed']]
        oldparts=p.hubs.components(set_precision(unary_union(all_shapes),1e-6));old=oldparts[r['old_union_part']]
        assert old.area==r['old_area_mm2'],(old.area,r)
        matching=[pad for pad in owned if not set_precision(unary_union(p.base.polygons(pad['layers'].get(layer,[]))),1e-6).intersection(old).is_empty]
        pure= set_precision(unary_union([s for pad in matching for s in p.base.polygons(pad['layers'].get(layer,[]))]),1e-6)
        assert old.equals(pure),('old_piece_not_exact_owned_pad_union',old.symmetric_difference(pure).area)
        foreign_parts=[]
        for kind in ('tracks','vias','zones'):
            for q in g[kind]:
                if p.norm(q['net'])!=n:continue
                if kind=='tracks':ss=[p.base.body(q)] if q['layer']==layer else []
                elif kind=='vias':ss=[Point(q['x'],q['y']).buffer(q['d']/2)] if layer in q['flashed'] else []
                else:ss=p.base.polygons(q['fills'].get(layer,[]))
                for s in ss:
                    if set_precision(s,1e-6).intersection(old).area>0:foreign_parts.append({'kind':kind,'uuid':q['uuid']})
        assert not foreign_parts,foreign_parts
        details=[]
        for pad in matching:
            new=next(q for q in h['pads'] if q['uuid']==pad['uuid']);auth=refs[pad['ref']]
            assert (new['x'],new['y'])!=(pad['x'],pad['y'])
            actual=next(r for r in row['all_named_pads'] if r['uuid']==pad['uuid']);assert actual['source_connected']
            f=Path(auth['new_chunk_path']);assert sha(f)==auth['new_chunk_sha256'];assert auth['BOM_source_UUID_pad_nums_nets_local_geometry_preserved']
            details.append({'ref':pad['ref'],'pin':pad['num'],'uuid':pad['uuid'],'actual_raw_net':pad['net'],'exact_original_geometry':pad,'exact_replacement_geometry':new,'actual_replacement_source_rooted':True,'authorizing_footprint_row':auth})
        oldf=O/(layer+'.old-isolated-pad-union.wkb');oldf.write_bytes(old.wkb)
        out.append({**r,'old_WKB_file':str(oldf.resolve()),'old_WKB_sha256':sha(oldf),'exact_integer_grid_original_union_equals_only_authorized_moved_pads':True,'no_original_track_via_zone_fill_excluded':True,'owned_moved_pads':details})
    assert len(out)==2
    (O/'receipt.json').write_text(json.dumps({'verdict':'EXACT_TWO_ORIGINAL_ISOLATED_SBC_PAD_ONLY_COMPONENTS_AUTHORIZED_RELOCATIONS_ALL_REPLACEMENT_PADS_SOURCE_ROOTED','parent_model_sha256':sha(prior),'authorizing_owned_recipe_file':str(rf.resolve()),'authorizing_owned_recipe_sha256':sha(rf),'original_failed_audit_sha256':sha(af),'rows':out,'not_a_copper_loss_waiver':True,'full_new_current_native_and_foreign_contact_gates':'OPEN','native_jobs':0,'board_written':False},indent=2)+'\n')
    print('EXACT_SBC_PAD_RELOCATION_CLASSIFIED',[(r['layer'],[(q['ref'],q['pin']) for q in r['owned_moved_pads']]) for r in out],flush=True)
if __name__=='__main__':main()
