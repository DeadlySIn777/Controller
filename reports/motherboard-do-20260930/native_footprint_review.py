"""Read actual KiCad footprints; never create a PCB or fabrication output."""
import hashlib, json
from collections import Counter
from pathlib import Path
import pcbnew

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
model=json.loads((ROOT/'hardware/motherboard_do/design.json').read_text())
stock=Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')
rows=[]; errors=[]; named=empty=0
for ref,p in model['components'].items():
    lib,name=p['footprint'].split(':')
    directory=ROOT/'hardware/motherboard_do/CNC_MB_DO.pretty' if lib=='CNC_MB_DO' else stock/(lib+'.pretty')
    source=directory/(name+'.kicad_mod')
    footprint=pcbnew.FootprintLoad(str(directory),name)
    if footprint is None:
        errors.append(ref+': footprint could not load'); continue
    nums=Counter(pad.GetNumber() for pad in footprint.Pads() if pad.GetNumber())
    blank=[pad for pad in footprint.Pads() if not pad.GetNumber()]
    if set(nums)!=set(p['pins']): errors.append(ref+': numbered footprint pins disagree')
    if any(count!=1 for count in nums.values()): errors.append(ref+': repeated numbered pad')
    if any(pad.IsOnLayer(pcbnew.F_Cu) or not pad.IsOnLayer(pcbnew.F_Paste) for pad in blank):
        errors.append(ref+': unnamed aperture has electrical copper or no front paste')
    named+=sum(nums.values()); empty+=len(blank)
    rows.append({'reference':ref,'footprint':p['footprint'],'numbered_electrical_pads':sum(nums.values()),
                 'unnumbered_paste_only_apertures':len(blank),'native_file_sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
report={'ok':not errors,'errors':errors,'native_pcbnew_version':pcbnew.Version(),'fitted_components':len(rows),
        'numbered_electrical_pads':named,'unnumbered_paste_apertures':empty,
        'all_native_pad_objects':named+empty,'manufacturing_ready':False,
        'scope':'Native footprint loading and numbering only; no final board/stencil/clearance qualification.', 'rows':rows}
(OUT/'native-footprint-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='rows'}))
raise SystemExit(bool(errors))
