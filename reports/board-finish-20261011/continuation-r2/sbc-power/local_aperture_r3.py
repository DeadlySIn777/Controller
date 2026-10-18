"""Ordinary drilled-via Cu/mask/paste envelope check for final C63 pose."""
import re,json
from shapely.geometry import Point
import local_copper_r3 as T
L=T.L;p=T.p
def main():
    g,h,tail=T.model();native=tail[1];wanted={'C15001','C15002','C11061','C11062','C11063','U11012'}
    chunks={p.base.ref_of(ch):ch for ch in native.values() if p.base.pcbtext.chunk_kind(ch)=='footprint' and p.base.ref_of(ch) in wanted}
    mask={ref:max([0.]+[float(v) for v in re.findall(rb'\(solder_mask_margin\s+([-\d.eE]+)\)',ch)]) for ref,ch in chunks.items()}
    paste={ref:max([0.]+[float(v) for v in re.findall(rb'\(solder_paste_margin\s+([-\d.eE]+)\)',ch)]) for ref,ch in chunks.items()}
    oldids={v['uuid'] for v in g['vias']};vv=[v for v in h['vias'] if v['uuid'] not in oldids or v['uuid'] in {'45617979-cdc6-42db-9b78-94c762d1aff4','7cb8b8f4-41dd-4467-b9bf-968886ddbdc6'}]
    rows=[];fail=[]
    for v in vv:
        checks=[];pt=Point(v['x'],v['y'])
        for pad in h['pads']:
            if pad['ref'] not in wanted or not pad['smd']:continue
            for layer,records in pad['layers'].items():
                for cu in p.base.polygons(records):
                    if pt.distance(cu)>2:continue
                    envelope=cu.buffer(max(mask[pad['ref']],paste[pad['ref']]),join_style=2);gap=pt.distance(envelope)-v['drill']/2
                    q={'ref':pad['ref'],'pad':pad['num'],'layer':layer,'actual_gap_mm':gap,'required_mm':.25,'pass':gap>=.25-1e-8};checks.append(q)
                    if not q['pass']:fail.append({'via_uuid':v['uuid'],**q})
        rows.append({'via_uuid':v['uuid'],'at':[v['x'],v['y']],'checks':checks})
    result={'exact_board':L.live.SHA,'all_apertures_pass':not fail,'failures':fail,'checks':rows,'mask_expansion_mm':mask,'paste_positive_mm':paste,'C11063_pose':[115.75,165.325,-90],'native_mask_drill_body_courtyard_gate_open':True,'board_written':False,'native_jobs':0}
    (L.OUT/'local-aperture-r3.json').write_text(json.dumps(result,indent=2)+'\n');print('APERTURE_R3',not fail,len(fail),flush=True)
if __name__=='__main__':main()
