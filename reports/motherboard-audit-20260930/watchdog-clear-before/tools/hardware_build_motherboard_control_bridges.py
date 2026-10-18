"""Actual passive fanout/defaults for deliberate OPI and watchdog-clear GPIO.

The two retained motion-rearm and two watchdog-clear nets remain distinct.
Only newly allocated FPGA GPIO drive these through ordinary series resistors.
This circuit is not gateware, a watchdog timing test or a safe-start proof.
"""
import csv
import json
from pathlib import Path
import uuid
from hardware_build_assembly import parse,dump
from hardware_build_tx_schematic import symbol,quote,effects

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/motherboard_control_bridges'
NS=uuid.UUID('510a086b-15f8-4a4f-8e3e-577461428f71')
CONTRACT={
 'R12001':('OPI_REARM_M','OPI_REARM_TX',33,'CRCW060333R0FKEA'),
 'R12002':('OPI_REARM_M','OPI_REARM_BOE',33,'CRCW060333R0FKEA'),
 'R12003':('WATCHDOG_TRIP_CLEAR','WD_M_TRIP_CLEAR_N',33,'CRCW060333R0FKEA'),
 'R12004':('WATCHDOG_TRIP_CLEAR','WD_O_TRIP_CLEAR_N',33,'CRCW060333R0FKEA'),
 'R12005':('OPI_REARM_M','LOGIC_GND',100000,'CRCW0603100KFKEA'),
 'R12006':('WATCHDOG_TRIP_CLEAR','IO_3V3',47000,'CRCW060347K0FKEA'),
}

def build():
    OUT.mkdir(parents=True,exist_ok=True);uid=lambda s:str(uuid.uuid5(NS,s));root=uid('root')
    pins=[(1,'',0,5.08,270,'passive'),(2,'',0,-5.08,90,'passive')]
    body='(rectangle(start -1.016 2.54)(end 1.016 -2.54)(stroke(width .254)(type default))(fill(type none)))'
    lib=symbol('R',pins,body,'R');items=[];parts={}
    for i,(ref,(a,b,ohms,mpn)) in enumerate(CONTRACT.items()):
        x,y=50.8+(i%3)*86.36,63.5+(i//3)*66.04
        parts[ref]={'kind':'R','physical':True,'value':f'{ohms}R 1%','mpn':mpn,
                    'footprint':'Resistor_SMD:R_0603_1608Metric','resistance_ohm':ohms,
                    'pins':{'1':a,'2':b},'role':'defined common-stem bias' if i>=4 else 'bounded same-domain control fanout'}
        props=''.join(f'(property {quote(k)} {quote(v)}(at {x+5.08} {y+j*3.81-5.08} 0){effects(.95,extra="hide" if j>=2 else "")})'
                      for j,(k,v) in enumerate([('Reference',ref),('Value',parts[ref]['value']),('MPN',mpn),('Footprint',parts[ref]['footprint'])]))
        items.append(f'(symbol(lib_id "CNC:R")(at {x} {y} 0)(unit 1)(in_bom yes)(on_board yes)(dnp no)(uuid "{uid(ref)}"){props}(instances(project "motherboard_control_bridges"(path "/{root}"(reference "{ref}")(unit 1)))))')
        for n,net in enumerate((a,b),1):
            yy=round(y+(-5.08 if n==1 else 5.08),4);end=round(yy+(-5.08 if n==1 else 5.08),4)
            items.append(f'(wire(pts(xy {x} {yy})(xy {x} {end}))(stroke(width 0)(type default))(uuid "{uid(ref+str(n)+"wire")}"))')
            items.append(f'(label {quote(net)}(at {x} {end} 0){effects(.95,"(justify left bottom)")}(uuid "{uid(ref+str(n)+"label")}"))')
    note='SAME 3.3V LOGIC DOMAIN / DELIBERATE REARM AND ACTIVE-LOW TRIP CLEAR\nOPI_REARM_M default LOW; WATCHDOG_TRIP_CLEAR default HIGH. FPGA unconfigured GPIO must be high-impedance.\nSeparate receiving net names and existing latch/bias circuitry are preserved. No automatic restart or healthy bypass.\nGateware, pulldown/startup contention, IOZ at intermediate supplies and loaded response remain qualification gates.'
    items.append(f'(text {quote(note)}(at 15.24 15.24 0){effects(1.15,"(justify left top)")}(uuid "{uid("notes")}"))')
    raw=f'(kicad_sch(version 20250114)(generator "eeschema")(uuid "{root}")(paper "A4")(title_block(title "Motherboard deliberate-control fanout")(date "2026-09-30")(rev "r0.1"))(lib_symbols {lib})'+''.join(items)+')'
    (OUT/'motherboard_control_bridges.kicad_sch').write_text(dump(parse(raw))+'\n',encoding='utf-8')
    (OUT/'CNC.kicad_sym').write_text(dump(parse('(kicad_symbol_lib(version 20241209)(generator "kicad_symbol_editor")'+lib.replace('(symbol "CNC:','(symbol "',1)+')'))+'\n',encoding='utf-8')
    (OUT/'design.json').write_text(json.dumps({'schema_version':1,'manufacturing_ready':False,'physical_qualification':False,
        'scope':note,'components':parts,'one_custom_motherboard':True},indent=2)+'\n',encoding='utf-8')
    with (OUT/'bom.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['Reference','Value','MPN','Footprint','Status'])
        for ref,p in parts.items():w.writerow([ref,p['value'],p['mpn'],p['footprint'],'source candidate / not qualified'])
    (OUT/'motherboard_control_bridges.kicad_pro').write_text(json.dumps({'meta':{'filename':'motherboard_control_bridges.kicad_pro','version':1}},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'parts':len(parts),'manufacturing_ready':False}))

if __name__=='__main__':build()
