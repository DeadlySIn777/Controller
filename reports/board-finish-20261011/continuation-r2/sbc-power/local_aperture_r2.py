"""Conservative local Cu/mask/paste envelope check from unchanged source pads."""
import re,json,hashlib
from shapely.geometry import Point
import core_lane_r2 as R
L=R.L;p=R.p
def main():
    g,h,scope,native,*_=R.model();local=json.loads((L.OUT/'local-copper-r2.json').read_text())
    wanted={'C15001','C15002','C11061','C11062','C11063','U11012'};chunks={}
    pattern=re.compile(rb'\(property\s+"Reference"\s+"([^"\n]+)"')
    for chunk in native.values():
        m=pattern.search(chunk)
        if chunk.lstrip().startswith(b'(footprint') and m and m.group(1).decode() in wanted:chunks[m.group(1).decode()]=chunk
    margins={ref:[float(v) for v in re.findall(rb'\(solder_mask_margin\s+([-\d.eE]+)\)',chunk)] for ref,chunk in chunks.items()}
    # Mask defaults to board pad_to_mask_clearance=0. Native overrides are
    # conservatively extended to every pad of the footprint for this host check.
    pad_mask={ref:max([0.]+values) for ref,values in margins.items()}
    candidates=list(local['new_vias'])+[v for v in h['vias'] if v['uuid'] in {'45617979-cdc6-42db-9b78-94c762d1aff4','7cb8b8f4-41dd-4467-b9bf-968886ddbdc6'}]
    rows=[];fail=[]
    for via in candidates:
        pt=Point(via['x'],via['y']);near=[]
        for pad in h['pads']:
            if pad['ref'] not in wanted or not pad['smd']:continue
            for layer,recs in pad['layers'].items():
                for cu in p.base.polygons(recs):
                    if pt.distance(cu)>2.:continue
                    mask=cu.buffer(pad_mask.get(pad['ref'],0.),join_style=2)
                    gap=pt.distance(mask)-via['drill']/2
                    row={'ref':pad['ref'],'pad':pad['num'],'layer':layer,'drill_to_conservative_Cu_mask_paste_envelope_mm':gap,'required_mm':.25,'mask_expansion_mm':pad_mask.get(pad['ref'],0.),'pass':gap>=.25-1e-8}
                    near.append(row)
                    if not row['pass']:fail.append({'via_uuid':via['uuid'],'via_at':[via['x'],via['y']],**row})
        rows.append({'via_uuid':via['uuid'],'at':[via['x'],via['y']],'near_pad_aperture_checks':near})
    result={'source_board_sha256':L.live.SHA,'board_pad_to_mask_clearance_mm':0.,'footprint_mask_overrides':margins,'positive_paste_overrides':{ref:[float(v) for v in re.findall(rb'\(solder_paste_margin\s+([-\d.eE]+)\)',chunk) if float(v)>0] for ref,chunk in chunks.items()},'all_local_aperture_checks_pass':not fail,'failures':fail,'checks':rows,'no_VIPPO_or_mask_waiver':True,'native_mask_paste_and_drill_DRC_gate_open':True,'board_written':False,'native_jobs':0}
    (L.OUT/'local-aperture-r2.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
if __name__=='__main__':main()
