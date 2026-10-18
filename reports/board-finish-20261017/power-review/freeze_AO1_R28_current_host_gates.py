from pathlib import Path
import hashlib,importlib.util,json,math,re,shutil
from datetime import datetime,timezone
from shapely.geometry import Point,Polygon
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
H=ROOT/'reports/board-finish-20261011/continuation-r2/coupled-recovery'
R299=ROOT/'reports/board-finish-20261011/continuation-r2/combined-R753-one-full-native-fill-cached-DRC-r299'
OUT=HERE/'AO1-R28-current-host-gates-r4'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    assert not OUT.exists();OUT.mkdir()
    rp=HERE/'AO1-R20-actual-full-R299-requalification-r2/receipt.json';gp=HERE/'AO1-R658-ground-actual-full-R299-requalification-r3/receipt.json'
    r=json.loads(rp.read_text());g=json.loads(gp.read_text())
    assert r['verdict']=='R20_ACTUAL_FULL_R299_HOST_SOURCE_CONTACT_REFERENCE_PASS_NATIVE_CURRENT_ANALOG_SI_OPEN'
    assert g['verdict']=='R658_GROUND_ACTUAL_R299_TRUE_GEOMETRY_SOURCE_CONTACT_OLDREF_PASS_NATIVE_CURRENT_SI_OPEN'
    r22=H/'AO1-R20-exact-MON3-VREF-b177-minimal-current-native-replay-r22/minimal-exact-AO1-current-native-replay-manifest.json'
    r28=H/'AO1-R22-with-R656-seven-ground-joint-sparse-native-supplement-r28/minimal-exact-AO1-with-seven-ground-joint-native-replay-supplement.json'
    a=json.loads(r22.read_text());b=json.loads(r28.read_text())
    rows=a['remove_rows']+a['add_rows']+b['additional_ground_add_rows']
    assert len(a['remove_rows'])==4 and len(a['add_rows'])==16 and len(b['additional_ground_add_rows'])==7
    files=[rp,gp,r22,r28,R299/'copy/board.kicad_pcb',R299/'native-full/actual-full-refill-geometry.json',R299/'native-full/before-native-all-FP-pad-pose.json',HERE/'AO1-R658-ground-actual-full-R299-requalification-r3/loaded-tool-dependency-provenance.json',Path(__file__)]
    inputs={str(p):sha(p) for p in files}
    helper=ROOT/'reports/board-finish-20261011/parity-repair/root106/tools/pcbtext.py'
    inputs[str(helper)]=sha(helper);s=importlib.util.spec_from_file_location('pcbtext',helper);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    _,chunks,_=m.split(files[4].read_bytes());byid={m.chunk_uuid(c):c for c in chunks if m.chunk_uuid(c)}
    pad_expansion={}
    for c in chunks:
        if m.chunk_kind(c)!='footprint':continue
        # Max across the footprint and its pads deliberately overbounds each
        # individual pad's override. Nonpositive paste margins cannot enlarge.
        mask=max([0.]+[float(v) for v in re.findall(rb'\(solder_mask_margin ([^)]+)\)',c)])
        paste=max([0.]+[float(v) for v in re.findall(rb'\(solder_paste_margin ([^)]+)\)',c)])
        ratios=[float(v) for v in re.findall(rb'\(solder_paste_margin_ratio ([^)]+)\)',c)]
        assert not any(v>0 for v in ratios),'Positive paste ratio needs dimension-aware bound'
        padids=re.findall(rb'\n\t\t\t\(uuid "([^"]+)"\)',c)
        for uid in padids:pad_expansion[uid.decode()]={'mask_mm':mask,'paste_mm':paste}
    geometry=json.loads(files[5].read_text());poses=json.loads(files[6].read_text())
    nativepads={}
    for uid,row in poses['pads'].items():nativepads[(row[0],row[1],row[2],row[3],tuple(k for k in row[4] if k.endswith('.Cu')))]=(uid,row[4])
    pads=[]
    for p in geometry['pads']:
        if p['attr']!='smd':continue
        key=(p['num'],p['net'],round(p['at'][0]*1e6),round(p['at'][1]*1e6),tuple(p['layers']))
        uid,layers=nativepads[key]
        sh=unary_union([Polygon(t[0],t[1:])for t in p['poly']])
        pads.append((p,uid,layers,sh,pad_expansion[uid]))
    additions=[]
    for row in rows:
        source=Path(row['exact_chunk_file']);assert sha(source)==row['exact_chunk_SHA256'];inputs[str(source)]=sha(source)
        if row['action']=='remove':assert byid[row['UUID']]==source.read_bytes()
        else:assert row['UUID']not in byid
        target=OUT/source.name;shutil.copyfile(source,target)
        additions.append({**row,'exact_chunk_file':str(target.resolve()),'exact_chunk_SHA256':sha(target)})
    via_rows=[q for q in a['add_rows']if q['kind']=='via'];assert len(via_rows)==2
    aperture=[]
    for row in via_rows:
        text=Path(row['exact_chunk_file']).read_text();x,y=map(float,re.search(r'\(at ([^ ]+) ([^)]+)\)',text).groups());drill=float(re.search(r'\(drill ([^)]+)\)',text)[1]);pt=Point(x,y)
        for typ in ('Cu','Mask','Paste'):
            candidates=[]
            for p,uid,layers,shape,margin in pads:
                if typ!='Cu' and not any(k.endswith('.'+typ)for k in layers):continue
                bound=0 if typ=='Cu' else math.sqrt(2)*margin['mask_mm'if typ=='Mask'else'paste_mm']
                distance=pt.distance(shape)-drill/2-.005-bound
                candidates.append((distance,p['ref'],p['num'],uid,bound))
            distance,ref,pin,uid,bound=min(candidates)
            assert distance>=.275,(row['UUID'],typ,distance,ref,pin)
            aperture.append({'via_UUID':row['UUID'],'aperture':typ,'nearest_ref':ref,'nearest_pin':pin,'nearest_pad_UUID':uid,'conservative_edge_gap_mm':distance,'native_inside_polygon_bound_mm':.005,'conservative_positive_margin_corner_bound_mm':bound,'required_mm':.275})
    assert all(sha(Path(p))==v for p,v in inputs.items())
    receipt={'utc':datetime.now(timezone.utc).isoformat(),'verdict':'R28_CURRENT_FULL_R299_ORIGINAL_SCOPED_HOST_GATES_PASS_NATIVE_AFTER_CURRENT_SI_OPEN','input_sha256':inputs,'operations':additions,'retired_original_tracks':4,'new_tracks':21,'new_ordinary_vias':2,'original_R20_signal_power_body_reference_gate':'PASS on actual R299','original_R658_additive_ground_SOURCE_geometry_old_reference_gate':'PASS on actual R299 + R20 context','raw_merged_ground_self_shadow_screen':'Preserved as FAIL in r1; it applied the signal/power reference-shadow requirement to new grounding conductors. The two original scopes are recorded separately without rewriting that raw result.','all_new_via_Cu_mask_paste_pad_aperture_source_bounds':aperture,'source_aperture_bound_scope':'Uses actual native pad polygons/layer flags and all positive recorded footprint/pad margins, bounding corner growth by sqrt(2). Native pad polygon inside-error 5um retained. Not Gerber/aperture output or process qualification.','no_new_SMD_drill_intersection_or_VIPPO_registry_extension':True,'genuine_positive_5V_source':r['genuine_positive_5V_source_proof'],'ordinary_return_pair':r['ordinary_pair'],'ground_SOURCE_keys_before':g['source_keys_before_R20'],'ground_SOURCE_keys_after':g['source_keys_after_ground_additions'],'all_original_bound_files_rehashed_unchanged':True,'native_AFTER_fill_DRC_all_masks_partitions_reference_current_analog_SI_thermal_physical':'REQUIRED_OPEN','native_jobs':0,'board_written':False,'adopted':False,'manufacturing_ready':False}
    (OUT/'current-gates-and-minimal-sparse-packet.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'verdict':receipt['verdict'],'operations':len(additions),'new_via_pad_aperture_checks':len(aperture),'min_gap_mm':min(q['conservative_edge_gap_mm']for q in aperture)}))

if __name__=='__main__':main()
