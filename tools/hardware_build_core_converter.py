"""Draw the LM70660 core converter candidate from its reviewed component contract."""
import csv
import hashlib
import json
from pathlib import Path
import re
import uuid
from hardware_build_tx_schematic import effects, quote, symbol
from hardware_build_assembly import parse, dump

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/core_converter'
NS=uuid.UUID('6b84213b-cb5c-45b5-a409-5b3d69457680')
def uid(s):return str(uuid.uuid5(NS,s))


def main():
    d=json.loads((OUT/'requirements.json').read_text())
    rootid=uid('core-converter')
    two=[(1,'',0,5.08,270,'passive'),(2,'',0,-5.08,90,'passive')]
    rect='(rectangle(start -1.016 2.54)(end 1.016 -2.54)(stroke(width 0.254)(type default))(fill(type none)))'
    cap='(polyline(pts(xy -2.54 0.762)(xy 2.54 0.762))(stroke(width 0.3)(type default))(fill(type none)))' \
        '(polyline(pts(xy -2.54 -0.762)(xy 2.54 -0.762))(stroke(width 0.3)(type default))(fill(type none)))' \
        '(polyline(pts(xy 0 2.54)(xy 0 0.762))(stroke(width 0.254)(type default))(fill(type none)))' \
        '(polyline(pts(xy 0 -0.762)(xy 0 -2.54))(stroke(width 0.254)(type default))(fill(type none)))'
    pins=[]
    for i in range(1,31):
        row=(i-1)%15;left=i<=15
        kind='power_in' if i in (1,2,3,6,17,23,24,25,26,27,28,29,30) else 'power_out' if i in (18,19,20) else 'passive' if i in (5,21,22) else 'open_collector' if i==7 else 'no_connect' if i==10 else 'input'
        pins.append((i,d['converter']['pins'][str(i)]['function'],-20.32 if left else 20.32,71.12-row*10.16,0 if left else 180,kind))
    body='(rectangle(start -17.78 76.2)(end 17.78 -76.2)(stroke(width 0.254)(type default))(fill(type background)))'
    polarized=cap+'(text "+"(at -3.81 2.54 0)'+effects(1.27)+')'
    library=[symbol('LM70660RRXR',pins,body),symbol('R',two,rect,'R'),symbol('C',two,cap,'C'),symbol('CP',two,polarized,'C'),symbol('L',two,rect,'L')]
    connectors={}
    for count in (2,3):
        cp=[(i,str(i),-5.08,-(i-1)*5.08,0,'passive') for i in range(1,count+1)]
        connectors[count]=cp
        library.append(symbol(f'Conn{count}',cp,f'(rectangle(start -2.54 2.54)(end 2.54 {-count*5.08})(stroke(width 0.254)(type default))(fill(type background)))','J'))
    library.append(symbol('PWR_FLAG',[(1,'pwr',0,0,90,'power_out')],'','#FLG'))
    items,components,pinmap=[],[],{}
    def note(x,y,text,size=1.2):items.append(f'(text {quote(text)}(at {x} {y} 0){effects(size,"(justify left top)")}(uuid "{uid(text)}"))')
    def place(name,ref,value,x,y,pins,nets,footprint='',mpn=''):
        top=y-max(p[3] for p in pins)-10.16
        props=''.join(f'(property {quote(k)} {quote(v)} (at {x+5.08} {top+dy} 0){effects(.95,"hide" if hide else "")})'
                      for k,v,dy,hide in [('Reference',ref,0,False),('Value',value,2.54,False),('Footprint',footprint,0,True),('MPN',mpn or '',0,True)])
        items.append(f'(symbol(lib_id "CNC:{name}")(at {x} {y} 0)(unit 1)(in_bom {"no" if ref.startswith("#") else "yes"})(on_board {"no" if ref.startswith("#") else "yes"})(dnp no)(uuid "{uid(ref)}"){props}'
                     f'(instances(project "core_converter"(path "/{rootid}"(reference {quote(ref)})(unit 1)))))')
        pinmap[ref]={str(k):v for k,v in nets.items()}
        for n,_,px,py,_,_ in pins:
            sx,sy=round(x+px,4),round(y-py,4)
            net=nets.get(n)
            if net is None:items.append(f'(no_connect(at {sx} {sy})(uuid "{uid(ref+str(n)+"nc")}"))');continue
            dx=-25.4 if px<0 else 10.16 if px>0 else 0
            dy=0 if px else -5.08 if py>=0 else 5.08
            ex,ey=round(sx+dx,4),round(sy+dy,4)
            items.append(f'(wire(pts(xy {sx} {sy})(xy {ex} {ey}))(stroke(width 0)(type default))(uuid "{uid(ref+str(n)+"w")}"))')
            items.append(f'(label {quote(net)}(at {ex} {ey} 0){effects(.95,"(justify left bottom)")}(uuid "{uid(ref+str(n)+"l")}"))')
        if not ref.startswith('#'):components.append({'reference':ref,'value':value,'mpn':mpn or '', 'footprint':footprint,'status':'candidate' if mpn else 'selection_required'})
    place('LM70660RRXR','U1','LM70660RRXR',127.0,165.1,pins,{int(n):p['net'] for n,p in d['converter']['pins'].items()},'','LM70660RRXR')
    expanded=[]
    for p in d['passives']:
        if '-' in p['id']:
            a,b=p['id'].split('-');m=re.match(r'(.+?)(\d+)$',a)
            refs=[m[1]+str(i) for i in range(int(m[2]),int(re.search(r'\d+$',b)[0])+1)]
        else:refs=[p['id'] if p['id'][-1].isdigit() else p['id']+'1']
        for ref in refs:expanded.append((ref,p))
    for i,(ref,p) in enumerate(expanded):
        x,y=round(299.72+(i%4)*127,4),round(91.44+(i//4)*66.04,4)
        typ='L' if ref.startswith('L') else 'R' if ref.startswith('R') else 'CP' if ref.startswith('CBULK') else 'C'
        fp='Inductor_SMD:L_Coilcraft_XAL7070-XXX' if typ=='L' else '' if ref=='RS1' else 'Resistor_SMD:R_0603_1608Metric' if typ=='R' else 'Capacitor_SMD:C_1210_3225Metric' if p.get('mpn') else 'Capacitor_SMD:C_0603_1608Metric'
        if ref=='CVCC1':fp='Capacitor_SMD:C_0805_2012Metric'
        if ref.startswith('CBULK'):fp=''
        place(typ,ref,p['value'],x,y,two,dict(enumerate(p['nets'],1)),fp,p.get('mpn'))
    for ref,value,x,y,cp,nets in [
        ('JIN1','PROTECTED INPUT',76.2,330.2,2,['CORE_24V_PROTECTED','LOGIC_GND']),
        ('JOUT1','CORE 5V OUTPUT',177.8,330.2,2,['CORE_5V','LOGIC_GND']),
        ('JCTRL1','ENTRY EN / GND / PG',76.2,391.16,3,['C_PGOOD','LOGIC_GND','CORE_5V_PG']),
        ('JDIAG1','DIAGNOSTIC PULLUP',177.8,391.16,2,['IO_3V3','LOGIC_GND'])]:
        place('Conn'+str(cp),ref,value,x,y,connectors[cp],dict(enumerate(nets,1)))
    for i,net in enumerate(['CORE_24V_PROTECTED','CORE_5V','LOGIC_GND','IO_3V3']):
        place('PWR_FLAG',f'#FLG{i+1}','NORMAL PATH',50.8+i*76.2,480.06,[(1,'pwr',0,0,90,'power_out')],{1:net})
    note(20.32,15.24,'CORE 5 V / 6 A CONVERTER CANDIDATE - ENGINEERING CIRCUIT',2.2)
    note(20.32,27.94,'LM70660: protected nominal24V input; no display/AI/drive power. C_PGOOD is analog enable, not GPIO.\nUpstream R9 must be absent. VIN powers internal startup bias; no running host/ESP is needed to enable this converter.',1.3)
    note(20.32,520.7,'Layout: Kelvin ISNS+/VOUT across RS1; separate quiet AGND returns join local power ground as TI specifies.\nSW4 bootstrap return is internally common with SW1-3; preserve local bootstrap loop. No external long SW4 strap.\nU1 RRX, RS1 long-side0612 and polarized bulk footprints unassigned; no generic substitutions.\nBulk + three MLCCs require delayed SBC branch and revised compensation. Transient margin is conditional.\nCompensation, negative clamps and reverse feed remain unqualified. No finished PCB or machine permission.',1.2)
    sch=f'(kicad_sch(version 20250114)(generator "controller_hardware")(uuid "{rootid}")(paper "A1")'
    sch+='(title_block(title "Core 5V converter candidate")(date "2026-09-28")(rev "r0.1"))'
    sch+='(lib_symbols'+''.join(library)+')'+''.join(items)+')\n'
    (OUT/'core_converter.kicad_sch').write_text(dump(parse(sch))+'\n',encoding='utf-8')
    lib=''.join(s.replace('(symbol "CNC:','(symbol "',1) for s in library)
    (OUT/'CNC.kicad_sym').write_text(dump(parse('(kicad_symbol_lib(version 20241209)(generator "controller_hardware")'+lib+')'))+'\n')
    (OUT/'sym-lib-table').write_text(dump(parse('(sym_lib_table(version 7)(lib(name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "Core converter symbols")))'))+'\n')
    (OUT/'fp-lib-table').write_text(dump(parse('(fp_lib_table(version 7)(lib(name "CNC_Power")(type "KiCad")(uri "${KIPRJMOD}/CNC_Power.pretty")(options "")(descr "Reviewed local footprints")))'))+'\n')
    (OUT/'core_converter.kicad_pro').write_text('{"meta":{"filename":"core_converter.kicad_pro","version":1}}\n')
    with (OUT/'bom.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(components[0]));w.writeheader();w.writerows(components)
    (OUT/'pin-map.json').write_text(json.dumps({'schema_version':1,'manufacturing_ready':False,'pins':pinmap,'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2)+'\n')
    print(OUT/'core_converter.kicad_sch')


if __name__=='__main__':main()
