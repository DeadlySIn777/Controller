"""Run with KiCad's Python; inspect genuine loaded footprint copper pads."""
import hashlib
import json
from pathlib import Path
import pcbnew

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'hardware/motherboard_power_entry'
REPORT=Path(__file__).resolve().parent
STOCK=Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')

def review():
    model=json.loads((OUT/'design.json').read_text());errors=[];records={};total=0
    for ref,p in model['components'].items():
        if not p['physical']:continue
        lib,name=p['footprint'].split(':')
        folder=OUT/(lib+'.pretty') if lib=='CNC_MB_Entry' else STOCK/(lib+'.pretty')
        fp=pcbnew.FootprintLoad(str(folder),name)
        if fp is None:errors.append('Native load failed '+ref);continue
        pads=[x for x in fp.Pads() if x.GetNumber()]
        numbers={x.GetNumber() for x in pads}
        if numbers!=set(p['pins']):errors.append('Physical/schematic pad set differs '+ref)
        if p['kind']=='F':
            want=[('1',0,0),('1',0,3.4),('2',9.92,0),('2',9.92,3.4)]
            actual=sorted((x.GetNumber(),round(pcbnew.ToMM(x.GetPosition().x),5),round(pcbnew.ToMM(x.GetPosition().y),5)) for x in pads)
            if actual!=sorted(want):errors.append('Stock fuseholder current mounting geometry differs '+ref)
            if any(abs(pcbnew.ToMM(x.GetDrillSize().x)-1.78)>.00001 for x in pads):errors.append('Fuseholder drill differs '+ref)
        if p['kind']=='QREV':
            if len(pads)!=5:errors.append('NexFET combined drain land mismatch '+ref)
        if lib=='CNC_MB_Entry' and any(x.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD for x in pads):errors.append('Source-backed power pad is not SMD '+ref)
        detail=[]
        for x in pads:
            detail.append({'number':x.GetNumber(),'position_mm':[pcbnew.ToMM(x.GetPosition().x),pcbnew.ToMM(x.GetPosition().y)],'size_mm':[pcbnew.ToMM(x.GetSize().x),pcbnew.ToMM(x.GetSize().y)],'drill_mm':[pcbnew.ToMM(x.GetDrillSize().x),pcbnew.ToMM(x.GetDrillSize().y)],'attribute':int(x.GetAttribute()),'shape':int(x.GetShape())})
        total+=len(pads)
        path=folder/(name+'.kicad_mod')
        records[ref]={'footprint':p['footprint'],'source_hash':hashlib.sha256(path.read_bytes()).hexdigest(),'pads':detail,'mpn':p['mpn']}
    result={'native_kicad_major_version':10,'passed':not errors,'errors':errors,'fitted_components_loaded':len(records),'numbered_copper_pads_loaded':total,'records':records,'evidence':'Native load/pad mapping; source drawing review is separate. This is not whole-board DRC or assembly/thermal/stencil qualification.'}
    (REPORT/'native-footprint-review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('passed','errors','fitted_components_loaded','numbered_copper_pads_loaded')}))
    return bool(errors)

if __name__=='__main__':raise SystemExit(review())
