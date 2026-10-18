"""Draw two separate-domain TPS26630 entry circuits; never generate PCB data."""
import csv
import hashlib
import json
from pathlib import Path
import uuid

from hardware_build_tx_schematic import effects, quote, symbol

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'hardware/power_entry'
NS = uuid.UUID('ab7ecacb-c768-4446-a057-d7b5d50edcf2')


def uid(name):
    return str(uuid.uuid5(NS, name))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    root_id = uid('power-entry')
    two = [(1, '', 0, 5.08, 270, 'passive'), (2, '', 0, -5.08, 90, 'passive')]
    rect = '(rectangle (start -1.016 2.54) (end 1.016 -2.54) (stroke (width 0.254) (type default)) (fill (type none)))'
    cap = '(polyline (pts (xy -2.54 0.762) (xy 2.54 0.762)) (stroke (width 0.3) (type default)) (fill (type none)))' \
          '(polyline (pts (xy -2.54 -0.762) (xy 2.54 -0.762)) (stroke (width 0.3) (type default)) (fill (type none)))' \
          '(polyline (pts (xy 0 2.54) (xy 0 0.762)) (stroke (width 0.254) (type default)) (fill (type none)))' \
          '(polyline (pts (xy 0 -0.762) (xy 0 -2.54)) (stroke (width 0.254) (type default)) (fill (type none)))'
    efuse = []
    # RGE0024H, TI SLVSE94G Figure5-1/Table5-1. Pad25 is the grounded thermal pad.
    left = [(1, 'IN'), (2, 'IN'), (3, 'B_GATE'), (4, 'DRV'), (5, 'IN_SYS'),
            (6, 'UVLO'), (7, 'OVP'), (9, 'dVdT'), (10, 'ILIM'), (12, 'SHDN')]
    right = [(18, 'OUT'), (17, 'OUT'), (16, 'PGOOD'), (15, 'PGTH'), (14, '~{FLT}'),
             (13, 'IMON'), (11, 'MODE'), (8, 'GND'), (25, 'EP_GND')]
    for number, name in left:
        i = len(efuse)
        kind = 'power_in' if number in (1, 2, 5) else 'output' if number in (3, 4) else 'input'
        efuse.append((number, name, -15.24, 48.26-i*10.16, 0, kind))
    for i, (number, name) in enumerate(right):
        # OUT17/18 share the same internal switch: one ERC source, one passive contact.
        kind = 'power_out' if number == 18 else 'passive' if number == 17 else 'open_collector' if number in (14, 16) else 'power_in' if number in (8, 25) else 'output' if number == 13 else 'input'
        efuse.append((number, name, 15.24, 48.26-i*10.16, 180, kind))
    for i, number in enumerate(range(19, 25)):
        efuse.append((number, 'NC', -12.7+i*5.08, -58.42, 90, 'no_connect'))
    body = '(rectangle (start -12.7 53.34) (end 12.7 -55.88) (stroke (width 0.254) (type default)) (fill (type background)))'
    # Drain is one combined KiCad pad5, matching the installed NexFET footprint;
    # manufacturer drain contacts5/6/7/8 and large drain land are internally common.
    q1pins = [(1,'S1',-12.7,15.24,0,'passive'),(2,'S2',-12.7,10.16,0,'passive'),
              (3,'S3',-12.7,5.08,0,'passive'),(4,'G',-12.7,-5.08,0,'input'),
              (5,'D5-8/land',12.7,5.08,180,'passive')]
    qbody = '(rectangle (start -10.16 20.32) (end 10.16 -10.16) (stroke (width 0.254) (type default)) (fill (type background)))'
    q2pins = [(1,'G',-7.62,0,0,'input'),(2,'S',0,-7.62,90,'passive'),(3,'D',0,7.62,270,'passive')]
    q2body = '(rectangle (start -5.08 5.08) (end 5.08 -5.08) (stroke (width 0.254) (type default)) (fill (type background)))'
    tvsbody = '(rectangle (start -2.54 2.54) (end 2.54 -2.54) (stroke (width 0.254) (type default)) (fill (type background)))'
    diodepins = [(1,'K',0,5.08,270,'passive'),(2,'A',0,-5.08,90,'passive')]
    library = [symbol('TPS26630RGER',efuse,body), symbol('CSD19537Q3',q1pins,qbody,'Q'),
               symbol('BSS138P',q2pins,q2body,'Q'), symbol('R',two,rect,'R'), symbol('C',two,cap,'C'),
               symbol('Fuse',two,rect,'F'),symbol('TVS_BI',two,tvsbody,'D'),symbol('Schottky',diodepins,tvsbody,'D')]
    connectors = {}
    for count in (2, 5):
        pins = [(i,str(i),-5.08,-(i-1)*5.08,0,'passive') for i in range(1,count+1)]
        connectors[count] = pins
        library.append(symbol(f'Conn{count}',pins,f'(rectangle (start -2.54 2.54) (end 2.54 {-count*5.08}) (stroke (width 0.254) (type default)) (fill (type background)))','J'))
    library.append(symbol('PWR_FLAG',[(1,'pwr',0,0,90,'power_out')],'','#FLG'))
    items, coordinates, components, pinmaps = [], {}, [], {}

    def place(name, ref, value, x, y, pins, nets, footprint='', mpn=''):
        coordinates[ref] = {str(n):(round(x+px,4),round(y-py,4)) for n,_,px,py,_,_ in pins}
        prop_y = y-max(pin[3] for pin in pins)-10.16 if ref.startswith(('U','Q')) else y-7.62
        props = f'(property "Reference" {quote(ref)} (at {x+5.08} {prop_y} 0) {effects()})' \
                f'(property "Value" {quote(value)} (at {x+5.08} {prop_y+2.54} 0) {effects(0.9)})' \
                f'(property "Footprint" {quote(footprint)} (at {x} {y} 0) {effects(extra="hide")})' \
                f'(property "MPN" {quote(mpn)} (at {x} {y} 0) {effects(extra="hide")})'
        items.append(f'(symbol (lib_id "CNC:{name}") (at {x} {y} 0) (unit 1) (in_bom {"no" if ref.startswith("#") else "yes"}) (on_board {"no" if ref.startswith("#") else "yes"}) (dnp no) (uuid "{uid(ref)}") {props}'
                     f'(instances (project "power_entry" (path "/{root_id}" (reference {quote(ref)}) (unit 1)))))')
        pinmaps[ref] = {str(k):v for k,v in nets.items()}
        for number, _, px, py, _, _ in pins:
            sx,sy = coordinates[ref][str(number)]
            net = nets.get(number)
            if net is None:
                items.append(f'(no_connect (at {sx} {sy}) (uuid "{uid(ref+str(number)+"nc")}"))')
                continue
            dx = -17.78 if px < 0 else 7.62 if px > 0 else 0
            dy = 0 if px else -5.08 if py >= 0 else 5.08
            ex,ey = round(sx+dx,4),round(sy+dy,4)
            items.append(f'(wire (pts (xy {sx} {sy}) (xy {ex} {ey})) (stroke (width 0) (type default)) (uuid "{uid(ref+str(number)+"w")}"))')
            items.append(f'(label {quote(net)} (at {ex} {ey} 0) {effects(0.9,"(justify left bottom)")} (uuid "{uid(ref+str(number)+"l")}"))')
        if not ref.startswith('#'):
            components.append({'reference':ref,'value':value,'mpn':mpn,'footprint':footprint,'status':'candidate' if mpn else 'selection_required'})

    def note(x,y,value,size=1.2):
        items.append(f'(text {quote(value)} (at {x} {y} 0) {effects(size,"(justify left top)")} (uuid "{uid(value+str(x)+str(y))}"))')

    for b,(prefix,ground,diag,output,ilim) in enumerate([
            ('C','LOGIC_GND','IO_3V3','CORE_24V_PROTECTED','8.20k 0.1%'),
            ('F','FIELD_GND','FIELD_5V','FIELD_24V_PROTECTED','3.65k 0.1%')]):
        offset = b*406.4
        def n(v):return prefix+'_'+v
        def r(number,value,x,y,a,z):
            place('R',f'R{b*20+number}',value,offset+x,y,two,{1:a,2:z},'Resistor_SMD:R_0603_1608Metric')
        note(offset+20.32,43.18,('CORE / LOGIC DOMAIN' if not b else 'FIELD DOMAIN - KEEP ISOLATED'),1.9)
        note(offset+20.32,53.34,'Draft19-30V entry; normal load '+('1.81A; input path target>=3A' if not b else '4.36A; input path target>=6A')+'.\nDisplay/AI/motor power excluded. Fuse and wiring selection remains open.')
        place('Conn2',f'JIN{b+1}','DC INPUT BOUNDARY',offset+60.96,83.82,connectors[2],{1:n('INPUT'),2:ground})
        place('Fuse',f'F{b+1}','DC FUSE / RATING TBD',offset+116.84,88.9,two,{1:n('INPUT'),2:n('RAW')})
        place('TVS_BI',f'D{b*2+1}','SMCJ30CA / CANDIDATE',offset+177.8,88.9,two,{1:n('RAW'),2:ground},'Diode_SMD:D_SMC','SMCJ30CA')
        place('C',f'C{b*4+1}','2.2uF 100V X7R / CANDIDATE',offset+259.08,88.9,two,{1:n('RAW'),2:ground},'Capacitor_SMD:C_1210_3225Metric')
        place('Conn2',f'JOUT{b+1}','TO CONVERTER / LOADS',offset+350.52,83.82,connectors[2],{1:output,2:ground})
        place('CSD19537Q3',f'Q{b*2+1}','CSD19537Q3',offset+81.28,152.4,q1pins,
              {1:n('RAW'),2:n('RAW'),3:n('RAW'),4:n('BG'),5:n('IN')},'Package_SON:VSON-8_3.3x3.3mm_P0.65mm_NexFET','CSD19537Q3')
        place('BSS138P',f'Q{b*2+2}','BSS138P,215',offset+81.28,203.2,q2pins,
              {1:n('DRV'),2:n('RAW'),3:n('BG')},'Package_TO_SOT_SMD:SOT-23','BSS138P,215')
        unets={1:n('IN'),2:n('IN'),3:n('BG'),4:n('DRV'),5:n('RAW'),6:n('UV'),7:n('OV'),8:ground,
               9:n('DVDT'),10:n('ILIM'),12:n('SHDN'),13:n('IMON'),14:n('FAULT_N'),15:n('PGTH'),16:n('PGOOD'),17:output,18:output,25:ground}
        place('TPS26630RGER',f'U{b+1}','TPS26630RGER',offset+233.68,195.58,efuse,unets,
              'Package_DFN_QFN:Texas_RGE0024H_VQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm','TPS26630RGER')
        place('Conn2',f'JRESET{b+1}','DRY CONTACT: SHUTDOWN/CLEAR',offset+81.28,256.54,connectors[2],{1:n('SHDN'),2:ground})
        note(offset+20.32,276.86,'Q1 source faces input; Q2 source also references RAW, not GND.\nMODE intentionally open: overcurrent latch-off. Voltage faults can recover.\nSHDN floats high internally; dry contact low shuts down/resets the latch.\nPower restoration is NOT machine rearm. Permission circuit is separate.',1.15)
        r(1,'887k 0.1%',40.64,337.82,n('RAW'),n('UV'))
        r(2,'29.4k 0.1%',101.6,337.82,n('UV'),n('OV'))
        r(3,'34.0k 0.1%',162.56,337.82,n('OV'),ground)
        r(4,ilim,223.52,337.82,n('ILIM'),ground)
        place('C',f'C{b*4+2}','100nF 5% C0G / dVdT',offset+304.8,337.82,two,{1:n('DVDT'),2:ground},'Capacitor_SMD:C_1206_3216Metric')
        r(5,'140k 0.1%',40.64,403.86,output,n('PGTH'))
        r(6,'10.0k 0.1%',101.6,403.86,n('PGTH'),ground)
        r(7,'10.0k 0.1%',162.56,403.86,n('IMON'),ground)
        r(8,'10k 1%',223.52,403.86,diag,n('FAULT_N'))
        r(9,'10k 1%',304.8,403.86,diag,n('PGOOD'))
        place('C',f'C{b*4+3}','1uF 100V X7R',offset+40.64,464.82,two,{1:n('IN'),2:ground},'Capacitor_SMD:C_1206_3216Metric')
        place('C',f'C{b*4+4}','1uF 100V X7R',offset+121.92,464.82,two,{1:output,2:ground},'Capacitor_SMD:C_1206_3216Metric')
        place('Schottky',f'D{b*2+2}','OUTPUT CLAMP / MPN TBD',offset+213.36,464.82,diodepins,{1:output,2:ground})
        place('Conn5',f'JSTAT{b+1}','LOCAL DIAGNOSTIC BOUNDARY',offset+350.52,441.96,connectors[5],{1:diag,2:ground,3:n('PGOOD'),4:n('FAULT_N'),5:n('IMON')})
        for index,net in enumerate((n('RAW'),n('IN'),ground,diag)):
            place('PWR_FLAG',f'#FLG{b}{index}','NORMAL SUPPLY',offset+50.8+index*81.28,520.7,[(1,'pwr',0,0,90,'power_out')],{1:net})
        note(offset+20.32,544.83,'External diagnostic supply only; FIELD signals must be isolated before logic.\nEffective RAW bypass >=1uF; IN/OUT >=0.1uF. Candidate MPN/bias curves unresolved.\nTotal downstream capacitance <=1000uF; loads held off by separate, unimplemented EN circuit.\nTVS/clamp/fuse/thermal qualification open. Power flags declare normal paths only.',1.1)
    note(20.32,12.7,'DUAL DC POWER ENTRY - PARTIAL ENGINEERING CIRCUIT r0.1',2.5)
    note(20.32,25.4,'TPS26630 + reverse-blocking FETs; separate LOGIC/FIELD grounds. No PCB or manufacturing release. Exact ratings require the companion review.',1.3)
    schematic = f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{root_id}") (paper "A1")\n' \
                '(title_block (title "Core and field DC power entry") (date "2026-09-28") (rev "r0.1") (comment 1 "Partial circuit; physical fuse/clamp selection and qualification open"))\n' \
                f'(lib_symbols {"".join(library)})\n'+'\n'.join(items)+'\n)\n'
    (OUT/'power_entry.kicad_sch').write_text(schematic,encoding='utf-8')
    libtext='\n'.join(v.replace('(symbol "CNC:', '(symbol "',1) for v in library)
    (OUT/'CNC.kicad_sym').write_text(f'(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor") {libtext})\n',encoding='utf-8')
    (OUT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "Power entry review symbols")))\n')
    (OUT/'power_entry.kicad_pro').write_text('{"meta":{"filename":"power_entry.kicad_pro","version":1}}\n')
    with (OUT/'bom.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(components[0]));writer.writeheader();writer.writerows(components)
    (OUT/'pin-map.json').write_text(json.dumps({'schema_version':1,'manufacturing_ready':False,'pins':pinmaps,
        'q1_drain_pad':'KiCad pad5 groups manufacturer drain contacts5/6/7/8 and exposed drain land',
        'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2)+'\n')
    print(OUT/'power_entry.kicad_sch')


if __name__ == '__main__':
    main()
