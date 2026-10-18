"""Freeze an exact raw-native-net, 1 nm PG neck rule-area proposal."""
import json,hashlib,math,uuid,re
from pathlib import Path
from shapely import from_wkb,set_precision
from shapely.geometry import LineString
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'PG-native-rule-proposal-r7'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir()
    owned=ROOT/'owned-native-parts-r4/receipt.json';r=json.loads(owned.read_text())
    pg=json.loads((ROOT/'PG-local-dive-r5.json').read_text())
    native=ROOT.parent/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb'
    assert sha(native)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
    text=native.read_text(encoding='utf-8')
    names=set(re.findall(r'\(net "([^"\n]*)"\)',text))
    matches=[s for s in names if s.replace('{slash}','/')=='/motherboard_power_entry/SBC_SWITCH_PG']
    assert len(matches)==1
    raw=matches[0]
    tracks=[q for q in pg['new_tracks'] if q['w']==.125]
    assert len(tracks)==3 and all(q['layer']=='F.Cu' for q in tracks)
    total=sum(math.dist(q['a'],q['b']) for q in tracks);assert total<=1.5
    sh=set_precision(from_wkb(Path(pg['named_area']['geometry_file']).read_bytes()),1e-6)
    assert sh.geom_type=='Polygon' and not sh.interiors
    for q in tracks:assert sh.covers(LineString([q['a'],q['b']]).buffer(.0625))
    f=OUT/'U11012_LITERAL_PG_NECK.wkb';f.write_bytes(sh.wkb)
    name='U11012_LITERAL_PG_NECK';uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-r2-PG-literal-area-r6'))
    poly=' '.join('(xy %.6f %.6f)'%(x,y) for x,y in list(sh.exterior.coords)[:-1])
    chunk=(f'\t(zone\n\t\t(layer "F.Cu")\n\t\t(uuid "{uid}")\n\t\t(name "{name}")\n\t\t(hatch edge 0.5)\n\t\t(connect_pads (clearance 0))\n\t\t(min_thickness 0.25)\n\t\t(keepout (tracks allowed) (vias allowed) (pads allowed) (copperpour allowed) (footprints allowed))\n\t\t(placement (enabled no) (sheetname ""))\n\t\t(fill (thermal_gap 0.5) (thermal_bridge_width 0.5) (island_removal_mode 0))\n\t\t(polygon (pts {poly}))\n\t)\n')
    area=OUT/'rule-area.chunk';area.write_text(chunk,encoding='utf-8',newline='\n')
    condition=f"A.Type == 'Track' && A.Layer == 'F.Cu' && A.NetName == '{raw}' && A.Width == 0.125mm && A.enclosedByArea('{name}')"
    rule=f'(rule "U11012 exact PG fine-pitch neck only"\n (condition "{condition}")\n (constraint track_width (min 0.125mm) (max 0.125mm))\n (constraint track_segment_length (max 0.9mm)))\n'
    rf=OUT/'proposed-rule.kicad_dru';rf.write_text(rule,encoding='utf-8',newline='\n')
    receipt={'verdict':'NATIVE_RULE_PARSE_EFFECTIVE_CONSTRAINT_AND_FULL_DRC_REQUIRED','exact_native_discrete_board_sha256':sha(native),'owned_native_recipe_sha256':sha(owned),'native_coordinate_grid_nm':1,'area_name':name,'area_uuid':uid,'area_geometry_file':str(f),'area_geometry_sha256':sha(f),'area_chunk_file':str(area),'area_chunk_sha256':sha(area),'rule_file':str(rf),'rule_sha256':sha(rf),'exact_raw_native_net':raw,'fine_track_uuids':[q['uuid'] for q in tracks],'fine_track_lengths_mm':[math.dist(q['a'],q['b']) for q in tracks],'cumulative_fine_length_mm':total,'cumulative_owned_limit_mm':1.5,'bulk_minimum_width_mm':.20,'expected_exactly_three_owned_tracks_match':True,'all_fine_bodies_wholly_area_covered':True,'native_rule_installed':False,'native_jobs':0,'board_written':False}
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('PG_RULE_FROZEN',total,sha(OUT/'receipt.json'))
if __name__=='__main__':main()
