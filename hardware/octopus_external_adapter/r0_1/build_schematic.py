"""Build a standalone editable engineering-candidate schematic. No fabrication output.

Only writes inside this script's folder. KiCad CLI exports/checks are run separately.
"""
from pathlib import Path
import json
import uuid
import re

OUT = Path(__file__).resolve().parent
NS = uuid.UUID('7262d496-f228-443a-a5b9-5a74e33471f8')
ROOT_UUID = str(uuid.uuid5(NS, 'adapter-root'))

def uid(name):
    return str(uuid.uuid5(NS, name))

def q(s):
    return json.dumps(str(s), ensure_ascii=False)

def fx(size=1.0, extra=''):
    return f'(effects (font (size {size} {size})) {extra})'

def remove_header_silk_lines(footprint):
    """Omit only the six body-outline lines at the flush StepStick board edges.

    Keep fabrication, courtyard, pads, user text and models byte-for-byte intact.
    The mounted underside headers retain the board's separate orientation marks.
    """
    spans = []
    for match in re.finditer(r'\(fp_line\s', footprint):
        depth = 0
        for end in range(match.start(), len(footprint)):
            if footprint[end] == '(':
                depth += 1
            elif footprint[end] == ')':
                depth -= 1
                if depth == 0:
                    block = footprint[match.start():end+1]
                    if '(layer "F.SilkS")' in block:
                        spans.append((match.start(), end+1))
                    break
    assert len(spans) == 6, f'Expected six generic header silk lines, got {len(spans)}'
    for start, end in reversed(spans):
        footprint = footprint[:start] + footprint[end:]
    return footprint

RFP = 'Resistor_SMD:R_0603_1608Metric'
HFP = 'Adapter:Wurth_61300811121_1x08_P2.54mm'
HFP7 = 'Adapter:Wurth_61300711121_1x07_P2.54mm'
PARTS = []

def part(ref, value, mpn, fp, pins, manufacturer=''):
    p = dict(reference=ref, value=value, mpn=mpn, manufacturer=manufacturer,
             footprint=fp, uuid=uid(ref), pins={str(k):v for k,v in pins.items()})
    PARTS.append(p)
    return p

part('J1', 'StepStick logic row', '61300811121', HFP,
     {1:'EN',2:None,3:None,4:None,5:None,6:None,7:'STEP',8:'DIR'}, 'Wurth Elektronik')
part('J2', 'Power row; VM omitted', '61300711121', HFP7,
     {1:'GND',2:None,3:None,4:None,5:None,6:'+5V',7:'GND'}, 'Wurth Elektronik')
part('J3', 'B4B-XH-A', 'B4B-XH-A(LF)(SN)',
     'Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical',
     {1:'+5V',2:'PUL_MINUS',3:'DIR_MINUS',4:'ENA_MINUS'}, 'JST')
part('U1', 'SN74LVC3G06DCUR', 'SN74LVC3G06DCUR',
     'Package_SO:VSSOP-8_2.3x2mm_P0.5mm',
     {1:'STEP_G',2:'ENA_MINUS',3:'DIR_G',4:'GND',5:'DIR_MINUS',6:'EN_G',7:'PUL_MINUS',8:'+5V'},
     'Texas Instruments')
for i, a, b in [(1,'STEP','STEP_G'), (2,'DIR','DIR_G'), (3,'EN','EN_G')]:
    part(f'R{i}', '1k 1%', 'RC0603FR-071KL', RFP, {1:a,2:b}, 'Yageo')
for i, a, b in [(4,'STEP_G','GND'), (5,'DIR_G','GND'), (6,'EN_G','+5V')]:
    part(f'R{i}', '47k 1%', 'RC0603FR-0747KL', RFP, {1:a,2:b}, 'Yageo')
part('C1','100nF 50V X7R','CL10B104KB8NNNC','Capacitor_SMD:C_0603_1608Metric',
     {1:'+5V',2:'GND'},'Samsung Electro-Mechanics')
part('C2','4.7uF 10V X7R','CC0805KKX7R6BB475','Capacitor_SMD:C_0805_2012Metric',
     {1:'+5V',2:'GND'},'Yageo')

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # Preserve the established KiCad geometry; use the manufacturer's nominal PTH hole.
    # Mating post dimensions remain a physical qualification item, not a 3D-model claim.
    libroot = Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')
    (OUT/'Adapter.pretty').mkdir(exist_ok=True)
    for count, mpn in [(8, '61300811121'), (7, '61300711121')]:
        base_name = f'PinHeader_1x{count:02d}_P2.54mm_Vertical'
        local_name = f'Wurth_{mpn}_1x{count:02d}_P2.54mm'
        original = libroot/f'Connector_PinHeader_2.54mm.pretty/{base_name}.kicad_mod'
        footprint = original.read_text(encoding='utf-8')
        footprint = footprint.replace(base_name, local_name, 2)
        footprint = re.sub(r'\(descr "[^"]*"\)',
            f'(descr "Wurth {mpn}; 1x{count:02d} 2.54mm; 1.10mm finished PTH, 1.70mm pads. Manufacturer drawing https://www.we-online.com/components/products/datasheet/{mpn}.pdf; generic KiCad header geometry retained; underside assembly.")',
            footprint, count=1)
        footprint, holes = re.subn(r'\(drill 1\)', '(drill 1.1)', footprint)
        assert holes == count, f'Expected {count} generic 1mm drills, got {holes}'
        assert footprint.count('(size 1.7 1.7)') == count
        footprint = remove_header_silk_lines(footprint)
        (OUT/f'Adapter.pretty/{local_name}.kicad_mod').write_text(footprint,encoding='utf-8')
    fplibs = '(fp_lib_table (version 7)\n(lib (name "Adapter")(type "KiCad")(uri "${KIPRJMOD}/Adapter.pretty")(options "")(descr "Adapter candidate local footprints"))\n'
    for library in ['Connector_JST','Package_SO','Resistor_SMD','Capacitor_SMD']:
        fplibs += f'(lib (name "{library}")(type "KiCad")(uri "${{KICAD10_FOOTPRINT_DIR}}/{library}.pretty")(options "")(descr "KiCad 10 standard library"))\n'
    (OUT/'fp-lib-table').write_text(fplibs+')\n',encoding='utf-8')
    (OUT/'parts.json').write_text(json.dumps(dict(schema_version=1, status='ENGINEERING CANDIDATE - NOT RELEASED',
        root_uuid=ROOT_UUID, project='adapter', parts={p['reference']:p for p in PARTS}),indent=2)+'\n',encoding='utf-8')
    libraries=[]; items=[]; coordinates={}
    defs={}

    def library(name,pins,body,reference='U',hide_names=False):
        ps=''.join(f'(pin {kind} {shape} (at {x} {y} {angle}) (length {length}) '
                   f'(name {q(label)} {fx(0.95)}) (number {q(n)} {fx(0.85)}))'
                   for n,label,x,y,angle,kind,shape,length in pins)
        props=''.join(f'(property {q(k)} {q(v)} (at 0 0 0) {fx(extra="hide")})'
                      for k,v in [('Reference',reference),('Value',name)])
        sym=f'(symbol "Adapter:{name}" (pin_names (offset 0.508){" hide" if hide_names else ""}) (in_bom yes) (on_board yes) {props}' \
            f'(symbol "{name}_0_1" {body})(symbol "{name}_1_1" {ps}))'
        libraries.append(sym); defs[name]=pins

    def rect(x1,y1,x2,y2):
        return f'(rectangle (start {x1} {y1}) (end {x2} {y2}) (stroke (width 0.254) (type default)) (fill (type background)))'

    def line(x1,y1,x2,y2,w=0.254):
        return f'(polyline (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width {w}) (type default)) (fill (type none)))'

    def pin(n,label,x,y,angle,kind='passive',shape='line',length=2.54):
        return (n,label,x,y,angle,kind,shape,length)

    library('SocketLogic', [pin(i,n,-12.7,-(i-1)*5.08,0) for i,n in enumerate(
        ['EN','MS0 (NC)','MS1 (NC)','MS2 (NC)','RST (NC)','SLP (NC)','STEP','DIR'],1)],rect(-10.16,2.54,10.16,-38.1),'J')
    library('SocketPower', [pin(i,n,-12.7,-(i-1)*5.08,0) for i,n in enumerate(
        ['GND','2B (NC)','2A (NC)','1A (NC)','1B (NC)','VCC_IO','GND'],1)],rect(-10.16,2.54,10.16,-33.02),'J')
    library('Output4', [pin(i,n,-12.7,-(i-1)*7.62,0) for i,n in enumerate(
        ['COM +5V','PUL-','DIR-','ENA-'],1)],rect(-10.16,2.54,10.16,-25.4),'J')
    upins=[pin(1,'1A',-15.24,15.24,0,'input'),pin(3,'2A',-15.24,0,0,'input'),
           pin(6,'3A',-15.24,-15.24,0,'input'),pin(7,'1Y',15.24,15.24,180,'open_collector','inverted'),
           pin(5,'2Y',15.24,0,180,'open_collector','inverted'),pin(2,'3Y',15.24,-15.24,180,'open_collector','inverted'),
           pin(8,'VCC',0,25.4,270,'power_in'),pin(4,'GND',0,-25.4,90,'power_in')]
    library('SN74LVC3G06DCUR',upins,rect(-12.7,22.86,12.7,-22.86))
    library('R_horizontal',[pin(1,'',-5.08,0,0),pin(2,'',5.08,0,180)],rect(-2.54,1.016,2.54,-1.016),'R',True)
    library('R_vertical',[pin(1,'',0,5.08,270),pin(2,'',0,-5.08,90)],rect(-1.016,2.54,1.016,-2.54),'R',True)
    library('C',[pin(1,'',0,5.08,270),pin(2,'',0,-5.08,90)],
        line(-2.54,0.762,2.54,0.762,0.3)+line(-2.54,-0.762,2.54,-0.762,0.3)+line(0,2.54,0,0.762)+line(0,-0.762,0,-2.54),'C',True)
    library('PWR_FLAG',[pin(1,'',0,0,90,'power_out',length=0)],
        line(0,0,0,2.54)+line(0,2.54,-1.27,3.81)+line(-1.27,3.81,0,5.08)+line(0,5.08,1.27,3.81)+line(1.27,3.81,0,2.54),'#FLG',True)

    def place(name,ref,x,y,props_at=None):
        p=next((p for p in PARTS if p['reference']==ref),None)
        virtual=p is None
        p=p or dict(reference=ref,value='PWR_FLAG',mpn='',footprint='',manufacturer='',uuid=uid(ref),pins={})
        coordinates[ref]={str(n):(round(x+px,4),round(y-py,4)) for n,_,px,py,*_ in defs[name]}
        if props_at is None: props_at=(x,y-7.62)
        rx,ry=props_at
        props=''.join(f'(property {q(k)} {q(v)} (at {px} {py} 0) {fx(size,extra)})'
             for k,v,px,py,size,extra in [
                 ('Reference',ref,rx,ry,1.27,'hide' if virtual else ''),
                 ('Value',p['value'],rx,ry+2.54,1.0,'hide' if virtual else ''),
                 ('Footprint',p['footprint'],x,y,1,'hide'),('MPN',p['mpn'],x,y,1,'hide'),
                 ('Manufacturer',p['manufacturer'],x,y,1,'hide')])
        items.append(f'(symbol (lib_id "Adapter:{name}") (at {x} {y} 0) (unit 1) (in_bom {"no" if virtual else "yes"}) (on_board {"no" if virtual else "yes"}) (dnp no) (uuid {q(p["uuid"])}) {props}'
            f'(instances (project "adapter" (path "/{ROOT_UUID}" (reference {q(ref)}) (unit 1)))))')

    def wire(x,y,ex,ey,name):
        items.append(f'(wire (pts (xy {x} {y}) (xy {ex} {ey})) (stroke (width 0) (type default)) (uuid {q(uid(name))}))')

    def label(ref,pin,net,dx=0,dy=0):
        x,y=coordinates[ref][str(pin)]; ex=round(x+dx,4);ey=round(y+dy,4)
        if dx or dy: wire(x,y,ex,ey,f'{ref}.{pin}.wire')
        items.append(f'(label {q(net)} (at {ex} {ey} 0) {fx(1.0,"(justify left bottom)")} (uuid {q(uid(f"{ref}.{pin}.label"))}))')

    def nc(ref,pin):
        x,y=coordinates[ref][str(pin)]
        items.append(f'(no_connect (at {x} {y}) (uuid {q(uid(f"{ref}.{pin}.nc"))}))')

    def note(x,y,text,size=1.27):
        items.append(f'(text {q(text)} (at {x} {y} 0) {fx(size,"(justify left top)")} (uuid {q(uid("note:"+text))}))')

    note(15.24,12.7,'OCTOPUS / EXTERNAL DRIVER ADAPTER',2.0)
    note(15.24,19.05,'r0.1 ENGINEERING CANDIDATE - NOT RELEASED FOR ORDER',1.5)
    note(15.24,27.94,'Provisional profile: Octopus Pro V1.0 F429/F446, 5 V buffered socket signals; CL57T V4.1 in 5 V mode.',1.0)
    note(15.24,33.02,'Actual equipment identity, power limits, enable behavior and physical fit remain unverified.',1.0)

    place('SocketLogic','J1',43.18,53.34,(43.18,43.18))
    place('SocketPower','J2',43.18,109.22,(46.99,100.33))
    for p in PARTS[:2]:
        for n,net in p['pins'].items():
            if net is None: nc(p['reference'],n)
            else: label(p['reference'],n,net,-10.16,0)

    place('SN74LVC3G06DCUR','U1',152.4,80.01,(152.4,44.45))
    for i,y in [(1,64.77),(2,80.01),(3,95.25)]:
        place('R_horizontal',f'R{i}',99.06,y,(99.06,y-7.62))
        p=next(p for p in PARTS if p['reference']==f'R{i}')
        label(f'R{i}',1,p['pins']['1'],-10.16,0)
        label(f'R{i}',2,p['pins']['2'],7.62,0)
    for n,net in [(1,'STEP_G'),(3,'DIR_G'),(6,'EN_G')]: label('U1',n,net,-15.24,0)
    for n,net in [(7,'PUL_MINUS'),(5,'DIR_MINUS'),(2,'ENA_MINUS')]:label('U1',n,net,7.62,0)
    label('U1',8,'+5V',0,-2.54);label('U1',4,'GND',0,5.08)

    place('Output4','J3',246.38,64.77,(246.38,49.53))
    for n,net in [(1,'+5V'),(2,'PUL_MINUS'),(3,'DIR_MINUS'),(4,'ENA_MINUS')]:label('J3',n,net,-17.78,0)
    note(210.82,97.79,'One keyed XH 2.50 mm cable.\nJ3.1 fans out to PUL+, DIR+, ENA+.\nNo motor power on this connector.',1.0)

    for i,x in [(4,86.36),(5,115.57),(6,144.78)]:
        place('R_vertical',f'R{i}',x,130.81,(x+8.89,129.54))
        p=next(p for p in PARTS if p['reference']==f'R{i}')
        label(f'R{i}',1,p['pins']['1'],0,-5.08);label(f'R{i}',2,p['pins']['2'],0,5.08)
    for ref,x in [('C1',191.77),('C2',231.14)]:
        place('C',ref,x,130.81,(x+13.97,129.54))
        label(ref,1,'+5V',0,-5.08);label(ref,2,'GND',0,5.08)
    place('PWR_FLAG','#FLG01',177.8,55.88);label('#FLG01',1,'+5V',0,0)
    place('PWR_FLAG','#FLG02',198.12,55.88);label('#FLG02',1,'GND',0,0)
    note(76.2,112.395,'Input bias: STEP / DIR low; EN high when source is high impedance.',1.0)
    note(15.24,156.21,'CANDIDATE CONNECTION CONTRACT',1.27)
    note(15.24,162.56,'J1/J2: male pins on underside; numbering describes top-view socket rows. Confirm orientation mechanically.\n'
        'VM contact physically omitted: J2 begins at host GND below VM. Board uses only 5 V from VCC_IO.\n'
        'U1: inverting open-drain outputs. Input HIGH sinks the corresponding MINUS terminal; LOW releases it.\n'
        '5 V input profile only: U1 VIH >= 0.7 x VCC. This candidate does not support unbuffered 3.3 V sources.\n'
        'Do not apply 24 V to J3. Verify EN disable polarity, startup, loaded edge timing and host 5 V rail before release.\n'
        'No isolation or hardware safety function. Alarm wiring remains separate. ERC is not physical validation.',1.0)
    sch='(kicad_sch (version 20250114) (generator "eeschema") (generator_version "10.0")\n'
    sch+=f'(uuid {q(ROOT_UUID)}) (paper "A4")\n'
    sch+='(title_block (title "Octopus external driver adapter") (date "2026-10-05") (rev "r0.1 candidate") (company "ENGINEERING - NOT RELEASED") (comment 1 "Model / fit / bench qualification pending"))\n'
    sch+='(lib_symbols\n'+'\n'.join(libraries)+')\n'+'\n'.join(items)+'\n(embedded_fonts no))\n'
    (OUT/'adapter.kicad_sch').write_text(sch,encoding='utf-8')
    # Matching local symbols keep native library verification enabled without warnings.
    lib='(kicad_symbol_lib (version 20250114) (generator "kicad_symbol_editor")\n'
    lib+='\n'.join(s.replace('(symbol "Adapter:', '(symbol "',1) for s in libraries)+'\n)\n'
    (OUT/'Adapter.kicad_sym').write_text(lib,encoding='utf-8')
    (OUT/'sym-lib-table').write_text('(sym_lib_table (version 7)\n(lib (name "Adapter")(type "KiCad")(uri "${KIPRJMOD}/Adapter.kicad_sym")(options "")(descr "Adapter candidate source symbols")))\n',encoding='utf-8')
    print(f'Created {len(PARTS)} parts; root UUID {ROOT_UUID}')

if __name__=='__main__':
    main()
