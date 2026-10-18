"""Actual one-motherboard field headers and separated chassis HF couplings.

Existing power-entry connectors are reused. Mating plugs and M4 bond hardware
are purchased accessories, not new custom cards or components soldered here.
Native circuit/export checks do not certify final placement or an earth bond.
"""
from __future__ import annotations
import csv, hashlib, json, uuid
from pathlib import Path
from hardware_build_assembly import parse, dump
from hardware_build_tx_schematic import symbol, quote, effects

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/motherboard_terminals'
NS=uuid.UUID('fc36ee5a-7329-57dd-bb5e-a7b9581c1d7e')
HEADERS={2:('1844210','1840366'),3:('1844223','1840379'),
         6:('1844252','1840405'),10:('1844294','1840447'),
         12:('1844317','1840463'),14:('1844333','1840489')}
KINDS={'C':{1:('','passive'),2:('','passive')},'MOUNT':{1:('CHASSIS','passive')}}


def connector_footprint(n):
    return f'Connector_Phoenix_MC:PhoenixContact_MC_1,5_{n}-G-3.5_1x{n:02d}_P3.50mm_Horizontal'


def description():
    components={}; ledger=[]; aliases={'FIELD_GND':'motherboard_motors/FIELD_GND',
        'FIELD_A_0V':'motherboard_motors/FIELD_GND','FIELD_B_0V':'motherboard_do/FIELD_B_0V',
        'MPG_ENABLE':'motherboard_operator/MPG_ENABLE'}; accessories=[]; ji=19500
    def add(logical, nets, source_block, source_positions=None):
        nonlocal ji
        ji+=1;ref=f'J{ji}';n=len(nets);mpn,plug=HEADERS[n]
        positions=source_positions or list(range(1,n+1))
        pins={str(i+1):net for i,net in enumerate(nets)}
        components[ref]=dict(kind='Header'+str(n),mpn=mpn,value=f'{logical} / {mpn}',
            footprint=connector_footprint(n),physical=True,pins=pins,
            role='Actual polarized horizontal field header '+logical,
            logical_connector=logical,header_pitch_mm=3.5,header_hole_mm=1.2,
            header_body_mm=[3.5*(n-1)+4.9,9.2,7.25],
            nominal_component_current_a=8,board_rating_unchanged=True,
            mating_plug_mpn=plug,mated_total_length_mm=18.7,
            placement_mating_verified=False)
        accessories.append(dict(MPN=plug,quantity=1,for_header=ref,logical_connector=logical,
            category='purchased field-wire plug; separate from soldered motherboard BOM'))
        for i,net in enumerate(nets):
            sid=f'{logical}.{positions[i]}'
            parent=None if net is None else ('CHASSIS' if net=='CHASSIS' else
                'LOGIC_GND' if net=='LOGIC_GND' else source_block+'/'+net)
            if net is not None:
                prior=aliases.get(net)
                if prior is not None:parent=prior
                aliases[net]=parent
            ledger.append(dict(source_id=sid,reference=ref,pin=str(i+1),
                source_net=net,parent_net=parent,
                NC_reason='Deliberate motor logic/field separation position; no signal or test connection' if net is None else None))
    for i in range(12):
        bank='A' if i<8 else 'B'
        add(f'XM{i}',[f'STEP{i}_P',f'STEP{i}_N',f'DIR{i}_P',f'DIR{i}_N',
            'LOGIC_GND','CHASSIS',None,f'EN{i}_NO',f'EN{i}_COM',f'EN{i}_NC',
            f'AUX_5V_{bank}',f'AUX_24V_{bank}','FIELD_GND',f'ALM{i}_FIELD'],'motherboard_motors')
    for i in range(4):
        add(f'XE{i}',[f'ENC{i}_5V_LIMITED','LOGIC_GND',f'ENC{i}_A_P',f'ENC{i}_A_N',
            f'ENC{i}_B_P',f'ENC{i}_B_N',f'ENC{i}_Z_P',f'ENC{i}_Z_N',
            'LOGIC_GND','CHASSIS'],'motherboard_fast_inputs')
    add('XH1',['MPG_5V_LIMITED','LOGIC_GND','MPG_A_P','MPG_A_N','MPG_B_P','MPG_B_N',
        'MPG_VREF_2V5','MPG_ENABLE','LOGIC_GND','CHASSIS'],'motherboard_fast_inputs')
    aliases['MPG_ENABLE']='motherboard_operator/MPG_ENABLE'
    for row in ledger:
        if row['source_net']=='MPG_ENABLE':row['parent_net']=aliases['MPG_ENABLE']
    add('XH2',[f'MPG_SEL_{a}' for a in 'XYZABC']+['MPG_MUL_X1','MPG_MUL_X10',
        'MPG_MUL_X100','MPG_PEND_AUX','LOGIC_GND','CHASSIS'],'motherboard_operator')
    for i in range(3):
        add(f'XDI{i}',[f'DI{k}_FIELD' for k in range(i*8,i*8+8)]+
            [f'SENS24_G{i}',f'SENS24_G{i}','FIELD_B_0V','FIELD_B_0V'],'motherboard_di')
        aliases[f'SENS24_G{i}']='motherboard_safety_sensor/'+f'SENS24_G{i}'
    for i in range(2):
        add(f'XDO{i}',[f'DO{k:02d}' for k in range(i*8,i*8+8)]+
            [f'FIELD_{"A" if i==0 else "B"}_0V']*4,'motherboard_do')
    aliases['FIELD_GND']='motherboard_motors/FIELD_GND'
    aliases['FIELD_A_0V']='motherboard_motors/FIELD_GND'
    aliases['FIELD_B_0V']='motherboard_do/FIELD_B_0V'
    add('XPR',['PRB0_IN','PRB0_24V','FIELD_GND','PRB1_IN','PRB1_24V','FIELD_GND'],'motherboard_operator')
    add('XF',['FREQ_5V_LIMITED','LOGIC_GND','FREQ0_P','FREQ0_N','FREQ1_P','FREQ1_N',
        'FREQ_MOD_ID_TO_FRONTEND','FREQ_MOD_PRESENT_TO_FRONTEND','LOGIC_GND','CHASSIS'],'motherboard_fast_inputs')
    add('XPW',['PWM0','LOGIC_GND','PWM1','LOGIC_GND','PWM_5V_AUX','CHASSIS'],'motherboard_process')
    for i in range(2):add(f'XPC{i}',[f'PEN{i}_1',f'PEN{i}_2'],'motherboard_process')
    for i in range(2):add('XAO',[f'AO{i}_OUT',f'AO{i}_COM','CHASSIS'],
        'motherboard_analog_output',[1+3*i,2+3*i,3+3*i])
    add('XAI',[f'AI{i}_{s}' for i in range(4) for s in ('P','N')]+
        ['AI_REF_10V','AI_SENS_24V','AI_AGND','CHASSIS'],'motherboard_analog_input')
    add('XB1',['RS485_B','RS485_A','RS485_COM','RS485_TERM','CHASSIS','RS485_COM'],'motherboard_comms')
    add('XB2',['CAN_H','CAN_L','CAN_GND','CAN_TERM','CHASSIS','CAN_GND'],'motherboard_comms')
    add('XS1',['SAFE_24V','EXT_PERMIT_IN','PROCESS_PERMIT_IN','SAFETY_STATUS_IN','RESET_ARM_IN',
        'ARM_LAMP','CONTACTOR_FB_IN','STO_FB_IN','FIELD_B_0V','PERMIT_OUT_1','PERMIT_OUT_2','CHASSIS'],
        'motherboard_safety_sensor')
    # XPE1 is a real plated M4 mounting/bond pad. It has no purchased silicon
    # or soldered terminal. The machine's protective-earth stud and shield rail
    # bond directly to the enclosure; PCB copper is not the earth fault path.
    components['H19501']=dict(kind='MOUNT',mpn='',value='XPE1 / M4 chassis bond',
        footprint='MountingHole:MountingHole_4.3mm_M4_Pad',physical=True,
        pins={'1':'CHASSIS'},role='Bare PCB chassis bond pad; separate M4 assembly hardware',
        purchased=False,exclude_from_bom=True,exclude_from_position=True,
        drill_mm=4.3,annulus_outer_mm=8.6,washer_clearance_mm=12,
        bond_resistance_target_ohm=.1,physical_bond_qualified=False)
    ledger.append(dict(source_id='XPE1.1',reference='H19501',pin='1',source_net='CHASSIS',parent_net='CHASSIS',NC_reason=None))
    domains=[('LOGIC_GND','logic/compute'),('LOGIC_GND','logic/motion'),
        ('FIELD_GND','field A'),('FIELD_B_0V','field B'),('AO0_COM','analog output0'),
        ('AO1_COM','analog output1'),('AI_AGND','analog input'),('RS485_COM','RS485'),('CAN_GND','CAN')]
    for i,(net,role) in enumerate(domains,19501):
        ref=f'C{i}';components[ref]=dict(kind='C',mpn='VY2472M49Y5US63V7',
            value='4.7nF 20% X1/Y2 HF coupling',footprint='Capacitor_THT:C_Disc_D12.5mm_W5.0mm_P7.50mm',
            physical=True,pins={'1':net,'2':'CHASSIS'},role='AC-only chassis return near '+role,
            capacitance_f=4.7e-9,capacitance_tolerance=.2,lead_pitch_mm=7.5,
            body_diameter_max_mm=12.5,body_thickness_max_mm=5,
            component_Y2_vac=300,component_X1_vac=440,board_voltage_rating_unchanged=True)
    # Reuse the six existing 10 A power-entry headers without duplicating them.
    for i,domain in enumerate(('C','FA','FB')):
        for pos,(ref,pin) in enumerate(((f'J{11001+2*i}','1'),(f'J{11001+2*i}','2'),
            (f'J{11002+2*i}','1'),(f'J{11002+2*i}','2')),1):
            ledger.append(dict(source_id=f'XP{i+1}.{pos}',reference=ref,pin=pin,
                reused_existing_power_entry=True,NC_reason=None))
    for row in ledger:
        if row.get('source_net') is not None:row['parent_net']=aliases[row['source_net']]
    requirements=json.loads((ROOT/'hardware/motherboard/requirements.json').read_text(encoding='utf8'))
    required={r['source_id'] for r in requirements['terminal_function_mapping'] if r['scope']=='motherboard_standard'}
    actual=[r['source_id'] for r in ledger]
    if required!=set(actual) or len(actual)!=len(set(actual)):raise ValueError('Terminal function coverage differs from frozen specification')
    accessories.extend([dict(category='M4 chassis attachment kit',quantity=1,
        specification='M4 bolt, 9 mm OD washer, locking hardware and enclosure boss; reserve12mm washer tool circle; <0.1ohm measured assembled bond',MPN=None)])
    boundaries={f'BT195{i}':dict(kind='Boundary1',mpn='',value='PARENT: '+net,
        footprint='',physical=False,pins={'1':net},role='schematic_boundary_not_orderable')
        for i,net in enumerate(sorted(aliases))}
    return dict(schema_version=1,revision='motherboard-terminals-r01',components=components,
        boundaries=boundaries,parent_aliases=aliases,terminal_ledger=ledger,
        purchased_accessories=accessories,physical_part_count=len(components),
        manufactured_custom_boards=1,manufacturing_ready=False,physical_qualification=False,
        scope='Actual field headers and shield bond; final edge placement and mating/tool clearances remain native PCB work',
        required_parent_sources=['motherboard_safety_sensor','motherboard_analog_input','motherboard_comms'],
        required_parent_frontends=['FREQ_MOD_ID_TO_FRONTEND must reach real protected1Wire interface'],
        primary_sources=['https://www.phoenixcontact.com/en-us/products/pcb-header-mc-1514-g-35-1844333',
            'https://www.phoenixcontact.com/en-us/products/pcb-header-mc-15-3-g-35-1844223',
            'https://www.vishay.com/docs/28535/vy2series.pdf'])


def build(out=OUT):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);d=description()
    kinds={**KINDS,'Boundary1':{1:('PARENT','passive')}}
    for n in HEADERS:kinds['Header'+str(n)]={i:(str(i),'passive') for i in range(1,n+1)}
    libs=[];layouts={};uid=lambda v:str(uuid.uuid5(NS,v));root=uid('root')
    for kind,table in kinds.items():
        if kind=='C':layout=[(1,'',0,5.08,270,'passive'),(2,'',0,-5.08,90,'passive')];body='(rectangle(start -1.016 2.54)(end 1.016 -2.54)(stroke(width .254)(type default))(fill(type none)))'
        else:
            layout=[(n,table[n][0],-12.7,5.08*(len(table)-1)/2-i*5.08,0,table[n][1]) for i,n in enumerate(sorted(table))]
            y=5.08*len(table)/2;body=f'(rectangle(start -10.16 {y})(end 10.16 {-y})(stroke(width .254)(type default))(fill(type background)))'
        layouts[kind]=layout;libs.append(symbol(kind,layout,body,'C' if kind=='C' else 'H' if kind=='MOUNT' else 'J'))
    items=[];netmap={}
    parts={**d['components'],**d['boundaries']}
    for i,(ref,p) in enumerate(parts.items()):
        x=50.8+(i%7)*152.4;y=76.2+(i//7)*109.22
        layout=layouts[p['kind']];rx=x;ry=y-5.08*max(2,len(layout))/2-7.62
        props=''.join(f'(property {quote(k)} {quote(v)}(at {rx} {ry+dy} 0){effects(.85,"hide" if hide else "")})' for k,v,dy,hide in [('Reference',ref,0,False),('Value',p['value'],2.54,False),('MPN',p['mpn'],0,True),('Footprint',p['footprint'],0,True)])
        physical='yes' if p['physical'] else 'no';purchased='no' if p.get('exclude_from_bom') or not p['physical'] else 'yes'
        items.append(f'(symbol(lib_id "CNC:{p["kind"]}")(at {x} {y} 0)(unit 1)(in_bom {purchased})(on_board {physical})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "motherboard_terminals"(path "/{root}"(reference {quote(ref)})(unit 1)))))')
        for n,_,px,py,_,_ in layout:
            sx,sy=round(x+px,4),round(y-py,4);net=p['pins'][str(n)]
            if net is None:items.append(f'(no_connect(at {sx} {sy})(uuid "{uid(ref+str(n)+"nc")}"))');continue
            ex,ey=round(sx-5.08 if px else sx,4),round(sy if px else sy+5.08,4)
            items.append(f'(wire(pts(xy {sx} {sy})(xy {ex} {ey}))(stroke(width 0)(type default))(uuid "{uid(ref+str(n)+"wire")}"))')
            items.append(f'(label {quote(net)}(at {ex} {ey} 0){effects(.65,"(justify right bottom)")}(uuid "{uid(ref+str(n)+"label")}"))');netmap.setdefault(net,[]).append([ref,str(n)])
    raw=f'(kicad_sch(version 20250114)(generator "controller_hardware")(uuid "{root}")(paper "User" 1189 3300)(title_block(title "Motherboard actual field headers and chassis HF coupling")(date "2026-09-30")(rev "r01"))(lib_symbols'+''.join(libs)+')'+''.join(items)+')'
    (out/'motherboard_terminals.kicad_sch').write_text(dump(parse(raw))+'\n',encoding='utf8')
    (out/'CNC.kicad_sym').write_text(dump(parse('(kicad_symbol_lib(version 20241209)(generator "controller_hardware")'+''.join(v.replace('(symbol "CNC:','(symbol "',1) for v in libs)+')'))+'\n',encoding='utf8')
    (out/'sym-lib-table').write_text(dump(parse('(sym_lib_table(version 7)(lib(name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "Actual field terminal symbols")))'))+'\n',encoding='utf8')
    (out/'motherboard_terminals.kicad_pro').write_text(json.dumps({'meta':{'filename':'motherboard_terminals.kicad_pro','version':1}},indent=2)+'\n',encoding='utf8')
    for name,value in [('design',d),('pin-map',netmap),('terminal-ledger',d['terminal_ledger']),('boundary-map',d['boundaries']),('parent-aliases',d['parent_aliases'])]:
        (out/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n',encoding='utf8')
    with (out/'bom.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=['Reference','Value','MPN','Footprint','Status']);w.writeheader()
        for ref,p in d['components'].items():
            if not p.get('exclude_from_bom'):w.writerow({**{k:p[k.lower()] for k in ('Value','MPN','Footprint')},'Reference':ref,'Status':'source_candidate_not_qualified'})
    (out/'accessories.json').write_text(json.dumps(d['purchased_accessories'],indent=2)+'\n',encoding='utf8')
    print(json.dumps({'physical_parts':len(d['components']),'headers':sum(p['kind'].startswith('Header') for p in d['components'].values()),'terminal_functions':len(d['terminal_ledger']),'manufacturing_ready':False}))
    return d


if __name__=='__main__':build()
