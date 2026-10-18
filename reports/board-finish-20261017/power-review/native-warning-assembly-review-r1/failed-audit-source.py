"""Read-only warning/nominal drill-vs-SMD review of saved full-native R299.

This creates engineering census evidence, not fabrication output or approval.
Native copper pad polygons and via dimensions are reused without board loads.
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv
import hashlib
import importlib.util
import json
import re
from datetime import datetime, timezone
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent/'native-warning-assembly-review-r1'
R299=ROOT/'reports/board-finish-20261011/continuation-r2/combined-R753-one-full-native-fill-cached-DRC-r299'
HELPER=ROOT/'reports/board-finish-20261011/parity-repair/root106/tools/pcbtext.py'
REGISTRY=Path('Z:/pcb-runs/fab-check/assembly/vippo.csv')
ROOT106=Path('Z:/pcb-runs/claude-finish/relayout/checks/vippo-root106.json')

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def poly(arr): return unary_union([Polygon(p[0],p[1:]) for p in arr])
def key(num,net,at): return (num,net,round(at[0]*1e6),round(at[1]*1e6))

def main():
    assert not OUT.exists()
    OUT.mkdir()
    files=[R299/'native-full/actual-full-refill-geometry.json',R299/'native-full/before-native-all-FP-pad-pose.json',R299/'native-full/receipt.json',R299/'copy/board.kicad_pcb',R299/'drc.json',REGISTRY,ROOT106,HELPER,Path(__file__)]
    inputs={str(p):sha(p) for p in files}
    g=json.loads(files[0].read_text())
    poses=json.loads(files[1].read_text())
    drc=json.loads(files[4].read_text())
    spec=importlib.util.spec_from_file_location('frozen_pcbtext',HELPER)
    h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
    _,chunks,_=h.split(files[3].read_bytes())
    viaflags={}
    for c in chunks:
        if h.chunk_kind(c)=='via':
            d={k.decode():v.decode() for k,v in re.findall(rb'\((filling|capping|covering|plugging) (yes|no)\)',c)}
            viaflags[h.chunk_uuid(c)]=d
    padposes=defaultdict(list)
    for uid,row in poses['pads'].items():
        padposes[(row[0],row[1],row[2],row[3])].append((uid,row[4]))
    pads=[p for p in g['pads'] if p['attr']=='smd']
    shapes=[poly(p['poly']) for p in pads]
    tree=STRtree(shapes)
    oldrows=list(csv.DictReader(REGISTRY.open()))
    oldreg={r['via_uuid']:r for r in oldrows}
    rootreg=json.loads(ROOT106.read_text())
    recorded={r['via_uuid']:r for r in rootreg['present']}
    rows=[]
    for v in g['vias']:
        drill=Point(v['at']).buffer(v['drill']/2,quad_segs=256)
        for index in tree.query(drill,predicate='intersects'):
            p=pads[int(index)];area=drill.intersection(shapes[int(index)]).area
            if area<=1e-10: continue
            matched=padposes[key(p['num'],p['net'],p['at'])]
            assert len(matched)==1,('Ambiguous actual native pad UUID',p['ref'],p['num'],matched)
            uid,layers=matched[0]
            flags=viaflags[v['uuid']]
            rec=recorded.get(v['uuid'])
            exact_rec=bool(rec and all(abs(a-b)<.0000005 for a,b in zip(rec['pos'],v['at'])) and rec['dia']==v['w'] and rec['drill']==v['drill'])
            rows.append({'via_uuid':v['uuid'],'x_mm':v['at'][0],'y_mm':v['at'][1],'via_diameter_mm':v['w'],'drill_mm':v['drill'],'locked':v['locked'],'pad_ref':p['ref'],'pad_pin':p['num'],'pad_uuid':uid,'pad_Cu_layers':'/'.join(p['layers']),'pad_has_native_paste_layer':any(k.endswith('.Paste') for k in layers),'same_raw_net':v['net']==p['net'],'raw_via_net':v['net'],'raw_pad_net':p['net'],'nominal_Cu_overlap_lower_bound_mm2':area,'old_291_registry_uuid_hit':v['uuid'] in oldreg,'ROOT106_present_uuid_hit':bool(rec),'ROOT106_recorded_pose_size_drill_exact':exact_rec,'native_filling':flags.get('filling','default'),'native_capping':flags.get('capping','default')})
    assert len(rows)==1605 and len({r['via_uuid'] for r in rows})==1538
    assert all(r['same_raw_net'] for r in rows)
    with (OUT/'actual-native-via-drill-SMD-Cu-intersections.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    # Every original warning is preserved with source identifiers.
    (OUT/'all-333-native-warnings.json').write_text(json.dumps(drc['violations'],indent=2)+'\n')
    warningcounts=Counter(v['type'] for v in drc['violations'])
    bynet=Counter()
    for w in drc['violations']:
        for i in w['items']:
            m=re.search(r'\[([^\]]+)\]',i['description'])
            if m: bynet[(w['type'],m[1])]+=1
    uuids={r['via_uuid'] for r in rows}
    withpaste={r['via_uuid'] for r in rows if r['pad_has_native_paste_layer']}
    filled={u for u in uuids if viaflags[u].get('filling')=='yes' and viaflags[u].get('capping')=='yes'}
    exactrecorded={r['via_uuid'] for r in rows if r['ROOT106_recorded_pose_size_drill_exact']}
    receipt={
        'utc':datetime.now(timezone.utc).isoformat(),
        'verdict':'SOURCE_REVIEW_COMPLETE_ASSEMBLY_AND_POWER_QUALIFICATION_OPEN',
        'input_sha256':inputs,
        'warning_count':len(drc['violations']),'warning_types':dict(warningcounts),
        'ordinary_errors':sum(v['severity']=='error' for v in drc['violations']),
        'native_sliver_warnings_without_items_or_coordinates':sum(v['type']=='copper_sliver' and not v['items'] for v in drc['violations']),
        'thermal_warning_entries':sum('thermal' in v['type'] for v in drc['violations']),
        'no_thermal_warning_is_not_current_or_temperature_qualification':True,
        'nominal_drill_SMD_Cu_census':{'positive_area_pairs':len(rows),'unique_vias':len(uuids),'foreign_net_pairs':sum(not r['same_raw_net'] for r in rows),'vias_touching_pads_with_actual_native_paste_layer':len(withpaste),'native_explicit_filling_and_capping_yes':len(filled),'remaining_intersecting_vias_without_both_explicit_yes':len(uuids-filled),'old_291_registry_uuid_hits':len(uuids&oldreg.keys()),'old_291_registry_uuid_absent':len(uuids-oldreg.keys()),'ROOT106_registry_present_rows':len(recorded),'ROOT106_registry_exact_pose_diameter_drill_hits':len(exactrecorded)},
        'method':{'saved_actual_native_pad_polygons':True,'actual_native_pad_UUID_Cu_Paste_Mask_binding':True,'drill_circle':'inscribed 1024-edge nominal circle, positive area >1e-10mm2','full_smd_pad_polygon':'exact saved native-export polygon; no bounding-box hit credit','tangencies_registration_tolerance_mask_and_paste_aperture_geometry':'excluded; census is nominal Cu lower bound','native_fill_cap_flags_are_not_vendor_process_qualification':True},
        'warning_net_counts':[{'type':k[0],'net':k[1],'items':v} for k,v in sorted(bynet.items())],
        'concrete_actions':['Apply separately reviewed two SCL hole corrections then rerun native DRC; no waiver of the overlap pair.','Use current exact board to regenerate a complete source-bound drill/pad/process review; reconcile every exposed paste overlap by layout correction or explicit qualified fill/cap process. Existing registry membership alone is not approval.','Retain source/current/neck/loop/thermal qualification for fitted power circuits; ordinary DRC warning absence supplies no current, temperature or transient bound.','Localize the 24 slivers with a provider that supplies geometry before attempting source edits; this JSON exposes no sliver UUID or position.'],
        'all_original_inputs_rehashed_unchanged':True,'native_jobs':0,'board_written':False,'fabrication_outputs_generated':False,'adopted':False,'manufacturing_ready':False,
    }
    assert len(drc['violations'])==333
    assert all(sha(Path(p))==v for p,v in inputs.items())
    (OUT/'review-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:receipt[k] for k in ['verdict','warning_count','nominal_drill_SMD_Cu_census']}))

if __name__=='__main__':main()
