"""Generate assembly/BOM/review records from saved native CAD. No fab export."""
from pathlib import Path
import csv
import hashlib
import html
import json
import math
import xml.etree.ElementTree as ET
import zipfile
import pcbnew as p

R = Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
board = p.LoadBoard(str(R/'adapter.kicad_pcb'))
parts = json.loads((R/'parts.json').read_text())['parts']
fps = {f.GetReference():f for f in board.GetFootprints()}
assert set(fps)==set(parts)
assert len(fps)==12
native = ET.parse(R/'adapter.net.xml').getroot()
expected = {(n.attrib['ref'],n.attrib['pin']):net.attrib['name']
    for net in native.findall('./nets/net') for n in net.findall('node')}
observed = {(f.GetReference(),a.GetNumber()):a.GetNetname()
    for f in fps.values() for a in f.Pads()}
assert observed==expected and len(observed)==43
def xy(a):return (p.ToMM(a.x)-100,p.ToMM(a.y)-100)
for ref,start,count in [('J1',1.27,8),('J2',3.81,7)]:
    f=fps[ref];assert f.GetLayer()==p.B_Cu
    for pad in f.Pads():
        x,y=xy(pad.GetPosition())
        assert abs(x-({'J1':1.27,'J2':13.97}[ref]))<1e-5
        assert abs(y-(start+(int(pad.GetNumber())-1)*2.54))<1e-5
        assert abs(p.ToMM(pad.GetDrillSizeX())-1.1)<1e-6
assert all(math.dist(xy(a.GetPosition()),(13.97,1.27))>2 for f in fps.values() for a in f.Pads())
assert all(not t.GetNetname().startswith('unconnected-') for t in board.GetTracks())
for name in ['pcb-final-drc.json','schematic-final-erc.json']:
    report=json.loads((R/'evidence'/name).read_text())
    assert report['ignored_checks']==[]
    if name.startswith('pcb'):
        assert not report['violations'] and not report['unconnected_items'] and not report['schematic_parity']
    else:
        assert all(not sheet['violations'] for sheet in report['sheets'])
assert len(board.Zones())==2
assert all(z.IsFilled() for z in board.Zones())

with (R/'PCBWay_BOM_DRAFT.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['Designator','Quantity per board','Value','Manufacturer','MPN','Footprint','Assembly side','Type','Assembly note'])
    for ref,spec in parts.items():
        side='Bottom' if fps[ref].GetLayer()==p.B_Cu else 'Top'
        note='Long mating pins point DOWN; VM position omitted on right row' if ref in ('J1','J2') else 'Cable entry UP' if ref=='J3' else ''
        w.writerow([ref,1,spec['value'],spec['manufacturer'],spec['mpn'],spec['footprint'],side,'THT' if ref.startswith('J') else 'SMT',note])
cpl=list(csv.DictReader((R/'PCBWay_CPL_DRAFT.csv').open(encoding='utf-8-sig')))
assert {a['Ref'] for a in cpl}==set(parts)-{'J1','J2','J3'}
assert all(a['Side']=='top' for a in cpl)

out=['<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="910" viewBox="0 0 1280 910">',
     '<rect width="1280" height="910" fill="#f6f7f9"/>',
     '<style>text{font-family:Arial,sans-serif;fill:#202b3a}.small{font-size:15px}.label{font-size:18px}.head{font-size:25px;font-weight:bold}</style>']
def txt(s,x,y,cl='label',extra=''):
    fs={'small':15,'label':18,'head':25}[cl]
    weight='bold' if cl=='head' else 'normal'
    out.append(f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{fs}" font-weight="{weight}" {extra}>{html.escape(s)}</text>')
txt('OEA r0.1 — assembly review',40,48,'head')
txt('ENGINEERING CANDIDATE • NOT RELEASED FOR MANUFACTURE',40,82,'label','fill="#a83018"')
scale=17
for ox,mirror,title in [(55,False,'COMPONENT SIDE'),(405,True,'UNDERSIDE — mirrored view')]:
    oy=150
    def xx(x):return ox+(15.24-x if mirror else x)*scale
    def yy(y):return oy+y*scale
    txt(title,ox,126)
    out.append(f'<rect x="{ox}" y="{oy}" width="{15.24*scale}" height="{20.32*scale}" rx="1" fill="#286d50" stroke="#163e2c" stroke-width="2"/>')
    if not mirror:
        # Source-derived body envelopes; connector exact JST drawing.
        for ref in parts:
            f=fps[ref]
            if f.GetLayer()==p.B_Cu:continue
            x,y=xy(f.GetPosition())
            if ref=='J3':x,y=7.095,6.85;w,h=5.75,12.4;color='#f4eee2'
            elif ref=='U1':w,h=2.3,2;color='#181d24'
            elif ref=='C2':w,h=1.25,2;color='#bb9873'
            else:w,h=.8,1.6;color='#1f2228' if ref.startswith('R') else '#bfa787'
            out.append(f'<rect x="{xx(x-w/2)}" y="{yy(y-h/2)}" width="{w*scale}" height="{h*scale}" fill="{color}" stroke="#b8c4bc"/>')
            if ref!='J3':txt(ref,xx(x)+10,yy(y)+5,'small')
    else:
        for ref,cy,h in [('J1',10.16,20.32),('J2',11.43,17.78)]:
            x=1.27 if ref=='J1' else 13.97
            out.append(f'<rect x="{xx(x+1.27)}" y="{yy(cy-h/2)}" width="{2.54*scale}" height="{h*scale}" fill="#171e24"/>')
    for ref in ['J1','J2','J3']:
        for pad in fps[ref].Pads():
            x,y=xy(pad.GetPosition())
            out.append(f'<circle cx="{xx(x)}" cy="{yy(y)}" r="{.7*scale}" fill="#c6ac63" stroke="#6e633e"/>')
            txt(pad.GetNumber(),xx(x),yy(y)+5,'small','text-anchor="middle"')
    out.append(f'<circle cx="{xx(13.97)}" cy="{yy(1.27)}" r="{.8*scale}" fill="none" stroke="#fff" stroke-dasharray="3 3"/>')
    txt('VM blank',xx(11.5 if not mirror else 10.7),yy(1.35),'small','text-anchor="middle"')
    txt('15.24 × 20.32 mm; 1.60 mm PCB',ox,533,'small')
    txt('12.70 mm rows; 2.54 mm row pitch',ox,557,'small')
txt('J1: 8 pins, logic row',735,150)
txt('Würth 61300811121 — below PCB',735,177,'small')
txt('J2: 7 pins, starts at GND',735,221)
txt('Würth 61300711121 — below PCB',735,248,'small')
txt('Upper VM contact and plated hole are absent.',735,275,'small')
txt('J3: keyed JST XH, 2.50 mm pitch',735,319)
txt('B4B-XH-A(LF)(SN) — above PCB',735,346,'small')
for i,s in enumerate(['1  +5V common','2  PUL−','3  DIR−','4  ENA−']):txt(s,760,382+i*29)
txt('SIDE VIEW — schematic dimensions',55,588)
out.append('<rect x="100" y="720" width="410" height="28" fill="#286d50"/>')
out.append('<rect x="230" y="601" width="120" height="119" fill="#f4eee2" stroke="#665f52"/>')
for x in [130,455]:
    out.append(f'<rect x="{x}" y="748" width="30" height="43" fill="#171e24"/>')
    out.append(f'<rect x="{x+11}" y="791" width="8" height="80" fill="#c6ac63"/>')
txt('J3 body: 7 mm above PCB',565,647,'small')
txt('Mated housing nominal height: 9.8 mm above PCB',565,675,'small')
txt('PCB: 1.6 mm',565,724,'small')
txt('Header body: 2.54 mm below PCB',565,763,'small')
txt('Long 6 mm mating pins point DOWN into host sockets.',565,802,'small')
txt('3 mm solder tails traverse PCB; nominal top projection 1.4 mm.',565,830,'small')
txt('Drawing checks orientation. Actual host fit, tolerances and first article remain unverified.',55,895,'small')
out.append('</svg>')
(R/'assembly-review.svg').write_text('\n'.join(out),encoding='utf-8')

status=dict(revision='r0.1 engineering candidate',manufacturing_ready=False,
    prototype_order_ready=False,pcbway_submission='not submitted',gerbers_and_drills='not generated',
    intended_host='Octopus Pro V1.0 F429/F446 — not user confirmed',
    intended_driver='CL57T V4.1 — not user confirmed',
    board_mm=[15.24,20.32,1.6],layers=2,footprints=12,schematic_pin_assignments=43,
    fitted_header_contacts=dict(J1=8,J2=7,J3=4),vm_contact='physically absent',
    source_inspection='PASS for named provisional host/driver sources',
    native_erc=dict(errors=0,warnings=0,ignored=0),
    native_drc=dict(errors=0,warnings=0,unconnected=0,schematic_parity=0,ignored=0),
    native_filled_ground_zones=2,
    verification='Native CAD and independent pin/geometry/parts checks only',
    physical_measurements='NOT RUN',electrical_simulation='NOT RUN',
    host_tests='Only CAD/package structural checks; no host firmware test',
    target_compilation='NOT APPLICABLE; adapter has no programmable processor',
    hdl_simulation='NOT APPLICABLE',fpga_synthesis='NOT APPLICABLE',
    release_holds=['Exact board revision/logic supply and exact drive confirmation',
        'Populated fit in selected host and adjacent slots',
        'Driver terminal/ferrule specification, final cable length and quantity',
        'ENA polarity/startup and host timing review including 200 ms lead time',
        'PCBWay DFM, BOM/CPL/assembly review and complete quotation'],
    before_machine_use=['First-article inspection','Loaded pulse/current/voltage tests',
        'Power/reset/disconnect/enable tests','Actual cable/timing/EMC qualification'],
    files={name:sha(R/name) for name in ['adapter.kicad_pcb','adapter.kicad_sch','adapter.kicad_pro',
        'parts.json','routes.json','PCBWay_BOM_DRAFT.csv','PCBWay_CPL_DRAFT.csv',
        'evidence/pcb-final-drc.json','evidence/schematic-final-erc.json']})
(R/'verification.json').write_text(json.dumps(status,indent=2)+'\n')
print(json.dumps({k:status[k] for k in ['footprints','schematic_pin_assignments','native_erc','native_drc','manufacturing_ready']}))
