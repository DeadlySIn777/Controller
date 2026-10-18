"""Native pcbnew stock PW16 geometry inspection against TI's example."""
from pathlib import Path
import hashlib
import json
import math
import shutil
import pcbnew

HERE=Path(__file__).resolve().parent
LIB=Path('C:/Program Files/KiCad/10.0/share/kicad/footprints/Package_SO.pretty')
NAME='TSSOP-16_4.4x5mm_P0.65mm'
source=LIB/(NAME+'.kicad_mod')
copy=HERE/'sources'/source.name
shutil.copyfile(source,copy)
fp=pcbnew.FootprintLoad(str(LIB),NAME)
rows=[]
for pad in fp.Pads():
    pos=pad.GetPosition();size=pad.GetSize()
    rows.append({'pin':int(pad.GetNumber()),'x_mm':pcbnew.ToMM(pos.x),'y_mm':pcbnew.ToMM(pos.y),
                 'width_mm':pcbnew.ToMM(size.x),'height_mm':pcbnew.ToMM(size.y),
                 'shape':pad.GetShape(),'roundrect_ratio':pad.GetRoundRectRadiusRatio()})
rows.sort(key=lambda r:r['pin'])
assert [r['pin'] for r in rows]==list(range(1,17))
for row in rows:
    pin=row['pin'];x=-2.8625 if pin<=8 else 2.8625
    y=-2.275+(pin-1)*.65 if pin<=8 else 2.275-(pin-9)*.65
    assert math.isclose(row['x_mm'],x,abs_tol=1e-8) and math.isclose(row['y_mm'],y,abs_tol=1e-8)
    assert math.isclose(row['width_mm'],1.475,abs_tol=1e-8) and math.isclose(row['height_mm'],.4,abs_tol=1e-8)
radius=.1
stock_area=1.475*.4-(4-math.pi)*radius**2
ti_area=1.5*.45-(4-math.pi)*.05**2
result={'status':'source_and_native_geometry_inspected_candidate','manufacturer':'TI AM26LV32EIPWR PW0016A',
        'manufacturer_source':'https://www.ti.com/lit/ds/symlink/am26lv32e.pdf',
        'source_pdf_sha256':hashlib.sha256((HERE/'sources/am26lv32e-reve.pdf').read_bytes()).hexdigest(),
        'stock_footprint_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'stock_footprint':NAME,
        'pins':rows,'pin1_top_left_pin16_top_right_correct':True,'pitch_mm':.65,
        'TI_example_land':{'width_mm':1.5,'height_mm':.45,'x_centres_mm':[-2.9,2.9],'corner_radius_mm':.05},
        'stock_difference':{'width_mm':-.025,'height_mm':-.05,'abs_x_centre_mm':-.0375,
                            'rounded_copper_area_reduction_fraction_vs_TI_example':1-stock_area/ti_area},
        'manufacturer_body_max_mm':[4.5,5.1],'body_height_max_mm':1.2,
        'selection':'Preserve reviewed stock PW16 family as a prototype candidate; no silent pad change to historical source.',
        'process_approved':False,
        'open_gate':'Stock IPC-style lands differ from TI example. Fabricator land/mask/stencil/assembly approval, body courtyard/mechanical context and actual solder-joint qualification remain required.'}
(HERE/'footprint-review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ['status','pin1_top_left_pin16_top_right_correct','stock_difference','process_approved']},indent=2))
