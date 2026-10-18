"""Generate the twelve fitted on-motherboard motor interfaces.

This source block is not a daughtercard, completed motherboard or fabrication
release. Explicit logical power and signal boundaries remain parent obligations.
"""
import csv
import hashlib
import json
from pathlib import Path
import uuid

from hardware_build_assembly import parse, dump
from hardware_build_tx_schematic import effects, quote, symbol

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/motherboard_motors'
SOURCE=ROOT/'reports/motherboard-motors-20260930/sources'
NS=uuid.UUID('d47e6d7a-4b80-40a0-af0d-c499514effc0')
PIN_FUNCTIONS={
 'AM26C31':{1:('1A','input'),2:('1Y','tri_state'),3:('1Z','tri_state'),4:('G','input'),5:('2Z','tri_state'),6:('2Y','tri_state'),7:('2A','input'),8:('GND','power_in'),9:('3A','input'),10:('3Y','tri_state'),11:('3Z','tri_state'),12:('G_N','input'),13:('4Z','tri_state'),14:('4Y','tri_state'),15:('4A','input'),16:('VCC','power_in')},
 'TLP3640A':{1:('A','passive'),2:('K','passive'),3:('D','passive'),4:('D','passive')},
 'TLP4176A':{1:('A','passive'),2:('K','passive'),3:('D','passive'),4:('D','passive')},
 'LVC07A':{1:('1A','input'),2:('1Y','open_collector'),3:('2A','input'),4:('2Y','open_collector'),5:('3A','input'),6:('3Y','open_collector'),7:('GND','power_in'),8:('4Y','open_collector'),9:('4A','input'),10:('5Y','open_collector'),11:('5A','input'),12:('6Y','open_collector'),13:('6A','input'),14:('VCC','power_in')},
 'TPS22918':{1:('VIN','power_in'),2:('GND','power_in'),3:('ON','input'),4:('CT','passive'),5:('QOD','passive'),6:('VOUT','passive')},
 'ISO1212':{1:('GND1','power_in'),2:('VCC1','power_in'),3:('EN','input'),4:('OUT1','output'),5:('OUT2','output'),6:('NC','no_connect'),7:('NC','no_connect'),8:('GND1','power_in'),9:('FGND2','passive'),10:('IN2','input'),11:('SENSE2','input'),12:('SUB2','passive'),13:('SUB1','passive'),14:('FGND1','passive'),15:('IN1','input'),16:('SENSE1','input')},
 'LVC2G17':{1:('1A','input'),2:('GND','power_in'),3:('2A','input'),4:('2Y','output'),5:('VCC','power_in'),6:('1Y','output')},
 'LVC2G08':{1:('1A','input'),2:('1B','input'),3:('2Y','output'),4:('GND','power_in'),5:('2A','input'),6:('2B','input'),7:('1Y','output'),8:('VCC','power_in')},
 'LVC2G74':{1:('CLK','input'),2:('D','input'),3:('Q_N','output'),4:('GND','power_in'),5:('Q','output'),6:('CLR_N','input'),7:('PRE_N','input'),8:('VCC','power_in')},
 'R':{1:('','passive'),2:('','passive')},'C':{1:('','passive'),2:('','passive')},'TVS':{1:('','passive'),2:('','passive')},
}
MPNS={
 'AM26C31':('AM26C31IPWR','Package_SO:TSSOP-16_4.4x5mm_P0.65mm'),
 'TLP3640A':('TLP3640A(TPL,E)','CNC_Motors:TLP3640A_SO4_11-3C1'),
 'TLP4176A':('TLP4176A(TP,F)','CNC_Motors:TLP4176A_2.54SOP4_11-5H1S'),
 'LVC07A':('SN74LVC07APWR','Package_SO:TSSOP-14_4.4x5mm_P0.65mm'),
 'TPS22918':('TPS22918DBVR','Package_TO_SOT_SMD:SOT-23-6'),
 'ISO1212':('ISO1212DBQR','Package_SO:SSOP-16_3.9x4.9mm_P0.635mm'),
 'LVC2G17':('SN74LVC2G17DBVR','Package_TO_SOT_SMD:SOT-23-6'),
 'LVC2G08':('SN74LVC2G08DCUR','Package_SO:VSSOP-8_2.3x2mm_P0.5mm'),
 'LVC2G74':('SN74LVC2G74DCUR','Package_SO:VSSOP-8_2.3x2mm_P0.5mm'),
}


def description():
    parts={};channels=[];u=r=c=d=6000
    def add(kind,pins,role,ref=None,**extra):
        nonlocal u
        if ref is None:u+=1;ref='U'+str(u)
        mpn,fp=MPNS[kind]
        parts[ref]={'kind':kind,'mpn':mpn,'value':mpn,'footprint':fp,'physical':True,'pins':{str(k):v for k,v in pins.items()},'role':role,**extra}
        return ref
    def resistor(a,b,ohms,role):
        nonlocal r
        r+=1;ref='R'+str(r)
        mpn={1000:'CRCW06031K00FKEA',10000:'CRCW060310K0FKEA',100000:'CRCW0603100KFKEA',220:'CRCW0603220RFKEA',562:'CRCW0603562RFKEA',820:'CRCW0603820RFKEA',4700:'CRCW06034K70FKEA'}[ohms]
        fp='Resistor_SMD:R_0603_1608Metric'
        if role=='alarm threshold pulse':mpn='SMM02040C1001FB300';fp='Resistor_SMD:R_MiniMELF_MMA-0204'
        parts[ref]={'kind':'R','mpn':mpn,'value':f'{ohms}R 1%','footprint':fp,'physical':True,'pins':{'1':a,'2':b},'resistance_ohm':ohms,'tolerance':.01,'role':role}
        return ref
    def cap(a,b,nf,role):
        nonlocal c
        c+=1;ref='C'+str(c)
        mpn,fp={100:('GRM188R72A104KA35D','Capacitor_SMD:C_0603_1608Metric'),1000:('GRM188R71H105KA12D','Capacitor_SMD:C_0603_1608Metric'),10:('C2012C0G2A103J125AA','Capacitor_SMD:C_0805_2012Metric'),1.5:('C0603C152J5GACTU','Capacitor_SMD:C_0603_1608Metric')}[nf]
        parts[ref]={'kind':'C','mpn':mpn,'value':f'{nf}nF','footprint':fp,'physical':True,'pins':{'1':a,'2':b},'capacitance_f':nf*1e-9,'tolerance':.05 if nf in (1.5,10) else .1,'role':role}
        return ref
    def tvs(a,b,role):
        nonlocal d
        d+=1;ref='D'+str(d)
        parts[ref]={'kind':'TVS','mpn':'SMBJ33CA-E3/52','value':'SMBJ33CA 33V bidirectional','footprint':'Diode_SMD:D_SMB','physical':True,'pins':{'1':a,'2':b},'role':role,'working_standoff_v':33,'clamp_v_at_rated_pulse_25c':53.3}
        return ref
    # Six line drivers, four differential channels each, every input rests LOW.
    pin_groups=[(1,2,3),(7,6,5),(9,10,11),(15,14,13)]
    tx_refs=[]
    for bank_i in range(6):
        bank='A' if bank_i<4 else 'B';pins={4:f'MOTOR_TX_GATE_{bank}',8:'LOGIC_GND',12:f'MOTOR_5V_{bank}',16:f'MOTOR_5V_{bank}'}
        for local,(a,y,z) in enumerate(pin_groups):
            i=bank_i*2+local//2;s='STEP' if local%2==0 else 'DIR';peer='MIA' if i<8 else 'MX4'
            pins.update({a:f'{s}{i}_TO_{peer}',y:f'{s}{i}_P',z:f'{s}{i}_N'})
            resistor(pins[a],'LOGIC_GND',10000,'receiving STEP/DIR idle low')
        ref=add('AM26C31',pins,'on-motherboard differential STEP/DIR',bank=bank)
        tx_refs.append(ref);cap(f'MOTOR_5V_{bank}','LOGIC_GND',100,'transmitter bypass '+ref)
    # Twelve independent sinks. Channels 0-7 and 8-11 remain separate inhibit
    # domains, although both are fitted directly on this one motherboard.
    sink_refs=[];sink_pin_pairs=[(1,2),(3,4),(5,6),(9,8),(11,10),(13,12)]
    for group in range(2):
        pins={7:'LOGIC_GND',14:'MOTOR_IO_3V3'}
        for j,(a,y) in enumerate(sink_pin_pairs):
            i=group*6+j;peer='MIA' if i<8 else 'MX4';pins[a]=f'EN{i}_N_TO_{peer}';pins[y]=f'MOTOR{i}_LED_SINK'
        ref=add('LVC07A',pins,'individual enable open-drain LED sinks')
        sink_refs.append(ref);cap('MOTOR_IO_3V3','LOGIC_GND',100,'enable driver bypass '+ref)
    for i in range(12):
        bank='A' if i<8 else 'B';peer='MIA' if i<8 else 'MX4'
        no=add('TLP3640A',{1:f'MOTOR_LED_5V_{bank}',2:f'MOTOR{i}_LED_MID',3:f'EN{i}_NO',4:f'EN{i}_COM'},'individual normally-open isolated contact',motor=i,form='A')
        nc=add('TLP4176A',{1:f'MOTOR{i}_LED_MID',2:f'MOTOR{i}_LED_K',3:f'EN{i}_NC',4:f'EN{i}_COM'},'individual normally-closed isolated contact',motor=i,form='B')
        led=resistor(f'MOTOR{i}_LED_K',f'MOTOR{i}_LED_SINK',220,'series photorelay LED current')
        pull=resistor(f'EN{i}_N_TO_{peer}','MOTOR_IO_3V3',10000,'receiver-own-rail enable default high')
        no_tvs=tvs(f'EN{i}_NO',f'EN{i}_COM','enable NO transient clamp')
        nc_tvs=tvs(f'EN{i}_NC',f'EN{i}_COM','enable NC transient clamp')
        channels.append({'motor':i,'bank':bank,'step_net':f'STEP{i}_TO_{peer}','dir_net':f'DIR{i}_TO_{peer}','enable_net':f'EN{i}_N_TO_{peer}','tx_ref':tx_refs[i//2],'enable_no_ref':no,'enable_nc_ref':nc,'led_resistor':led,'enable_pullup':pull,'enable_sink_ref':sink_refs[i//6],'enable_sink_input_pin':sink_pin_pairs[i%6][0],'enable_sink_output_pin':sink_pin_pairs[i%6][1],'enable_tvs_refs':[no_tvs,nc_tvs]})
    # Actual per-bank supply cuts, QOD and passive bleed. No upstream rails are
    # claimed by a PWR_FLAG: the parent must supply/monitor these named domains.
    for bank in ('A','B'):
        ref=add('TPS22918',{1:f'MOTOR_5V_{bank}',2:'LOGIC_GND',3:f'MOTOR_TX_GATE_{bank}',4:None,5:f'MOTOR_LED_5V_{bank}',6:f'MOTOR_LED_5V_{bank}'},'hardware enable supply cut; QOD tied VOUT; CT open',bank=bank)
        cap(f'MOTOR_5V_{bank}','LOGIC_GND',1000,'load-switch input '+ref)
        cap(f'MOTOR_LED_5V_{bank}','LOGIC_GND',100,'gated enable supply output '+ref)
        resistor(f'MOTOR_LED_5V_{bank}','LOGIC_GND',1000,'passive LED-supply bleed independent of QOD')
    # Dedicated motor alarms, not subtraction from the 24 general inputs.
    for pair in range(6):
        i=pair*2;pins={1:'LOGIC_GND',2:'MOTOR_IO_3V3',3:'MOTOR_IO_3V3',4:f'ALM{i}_FPGA',5:f'ALM{i+1}_FPGA',6:None,7:None,8:'LOGIC_GND'}
        for j,(sense,inp,gnd,sub) in enumerate(((16,15,14,13),(11,10,9,12))):
            m=i+j;pins.update({sense:f'ALM{m}_SENSE',inp:f'ALM{m}_IN',gnd:'FIELD_GND',sub:None})
            resistor(f'ALM{m}_FIELD',f'ALM{m}_SENSE',1000,'alarm threshold pulse')
            resistor(f'ALM{m}_SENSE',f'ALM{m}_IN',562,'alarm input current set')
            cap(f'ALM{m}_SENSE','FIELD_GND',10,'alarm front-end filter')
            resistor(f'ALM{m}_FPGA','LOGIC_GND',100000,'alarm logic output weak bias; not brownout guarantee')
            tvs(f'ALM{m}_FIELD','FIELD_GND','motor alarm field transient clamp')
        ref=add('ISO1212',pins,'two dedicated isolated motor alarm receivers',floating_substrate_pins=[12,13])
        cap('MOTOR_IO_3V3','LOGIC_GND',100,'alarm receiver bypass '+ref)
        for j in range(2):channels[i+j]['alarm_receiver_ref']=ref;channels[i+j]['alarm_output_pin']=4+j
    # Receiver-qualified permission is the ONLY physical gate net; it clears
    # the OPI latch and controls both line-driver G and LED-supply ON.
    add('LVC2G17',{1:'MOTOR_PERMIT_A_RC',2:'LOGIC_GND',3:'MOTOR_PERMIT_B_RC',4:'MOTOR_PERMIT_B_FILTERED',5:'MOTOR_IO_3V3',6:'MOTOR_PERMIT_A_FILTERED'},'two permission RC Schmitt receivers')
    add('LVC2G08',{1:'MOTOR_PERMIT_A_FILTERED',2:'MOTOR_POWER_OK_A_QUALIFIED',3:'MOTOR_TX_GATE_B',4:'LOGIC_GND',5:'MOTOR_PERMIT_B_FILTERED',6:'MOTOR_POWER_OK_B_QUALIFIED',7:'MOTOR_TX_GATE_A',8:'MOTOR_IO_3V3'},'receiver permission AND independently qualified local power')
    for bank,peer in (('A','MIA'),('B','MX4')):
        raw=f'TX_PERMIT_{bank}_TO_{peer}'
        resistor(raw,'LOGIC_GND',10000,'permission receiver absent default low')
        resistor(raw,f'MOTOR_PERMIT_{bank}_RC',820,'permission qualification series')
        cap(f'MOTOR_PERMIT_{bank}_RC','LOGIC_GND',1.5,'permission qualification C0G')
        resistor(f'MOTOR_POWER_OK_{bank}_QUALIFIED','LOGIC_GND',10000,'local power-good absent default low')
        resistor(f'OPI_REARM_{bank}','LOGIC_GND',4700,'OPI rearm unconfigured default low')
        add('LVC2G74',{1:f'OPI_REARM_{bank}',2:'MOTOR_IO_3V3',3:None,4:'LOGIC_GND',5:f'OPI_OK_{bank}',6:f'MOTOR_TX_GATE_{bank}',7:'MOTOR_IO_3V3',8:'MOTOR_IO_3V3'},'sticky bank interruption; exact physical gate clears latch',bank=bank)
    for ref,p in list(parts.items()):
        if p['kind'] in ('LVC2G17','LVC2G08','LVC2G74'):cap('MOTOR_IO_3V3','LOGIC_GND',100,'local logic bypass '+ref)
    power=['MOTOR_IO_3V3','LOGIC_GND','FIELD_GND','CHASSIS','MOTOR_5V_A','MOTOR_5V_B','AUX_5V_A','AUX_5V_B','AUX_24V_A','AUX_24V_B']
    inputs=[c[s] for c in channels for s in ('step_net','dir_net','enable_net')]+['TX_PERMIT_A_TO_MIA','TX_PERMIT_B_TO_MX4','MOTOR_POWER_OK_A_QUALIFIED','MOTOR_POWER_OK_B_QUALIFIED','OPI_REARM_A','OPI_REARM_B']
    outputs=[f'ALM{i}_FPGA' for i in range(12)]+['OPI_OK_A','OPI_OK_B','MOTOR_TX_GATE_A','MOTOR_TX_GATE_B']
    for ref,nets,role in [('B6001',power,'power boundary; rails not generated here'),('B6002',inputs[:21],'logic inputs'),('B6003',inputs[21:],'logic inputs'),('B6004',outputs,'logic outputs')]:
        parts[ref]={'kind':ref,'mpn':'','value':'INTERNAL LOGICAL BOUNDARY','footprint':'','physical':False,'pins':{str(i):n for i,n in enumerate(nets,1)},'role':role}
    terminal_map=[]
    for i in range(12):
        bank='A' if i<8 else 'B';nets=[f'STEP{i}_P',f'STEP{i}_N',f'DIR{i}_P',f'DIR{i}_N','LOGIC_GND','CHASSIS',None,f'EN{i}_NO',f'EN{i}_COM',f'EN{i}_NC',f'AUX_5V_{bank}',f'AUX_24V_{bank}','FIELD_GND',f'ALM{i}_FIELD']
        ref=f'BM{i+6000}';parts[ref]={'kind':'MotorBoundary','mpn':'','value':f'M{i} FIELD SIGNAL SET / CONNECTOR NOT SELECTED','footprint':'','physical':False,'pins':{str(i):n for i,n in enumerate(nets,1)},'role':'physical terminal requirement, not connector selection'}
        terminal_map.append({'motor':i,'boundary':ref,'positions':{str(k):v for k,v in enumerate(nets,1)},'connector_mpn':None,'connector_qualified':False})
    source_paths=['research/mc-motor-buffers/am26c31.pdf','research/mc-motor-buffers/sn74lvc07a.pdf','research/digital-inputs/iso1212.pdf','research/machine-permission/sn74lvc2g08.pdf','research/machine-permission/sn74lvc2g74.pdf']+[str(p.relative_to(ROOT)).replace('\\','/') for p in SOURCE.glob('*.pdf')]
    return {'schema_version':1,'revision':'motherboard-motors-r0.1','architecture':'one_custom_motherboard_all_12_fitted','manufacturing_ready':False,'physical_qualification':False,'components':parts,'channels':channels,'motor_count':12,'general_di_consumed':0,'general_do_consumed':0,'boundary_inputs':inputs,'boundary_outputs':outputs,'boundary_power':power,'terminal_map':terminal_map,'sources':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in source_paths},'operating_limits':{'motor_5v_v':[4.85,5.15],'motor_io_3v3_v':[3.2,3.4],'enable_contact_max_peak_v':30,'enable_contact_continuous_a':.05,'internal_ambient_c':[0,55]},'open_gates':['Parent must provide and independently supervise MOTOR_IO_3V3, both MOTOR_5V rails and bank AUX_5V/AUX_24V supplies; no power supply is fabricated by flags.','MOTOR_POWER_OK_*_QUALIFIED must combine actual local rail health and field/AUX health with qualified startup/timing, not a software constant.','820R/1.5nF Schmitt RC is a candidate; threshold-envelope guarantee across 3.2-3.4V, input-drive corners, repeated glitches and 100ns output pulse must be closed before claiming IS-1 qualification.','Source LED current screen uses 25C diode Vf limits at 10mA; cold/hot/ageing trigger/current/leak and QOD complete fault-to-inhibit timing remain physical gates.','TLP4176A candidate lands are package-envelope-derived; manufacturer assembly/stencil review remains open.','All 12 motor connector exact MPN/mate/orientation, isolation clearance, high current rails, shielding and transient return layout remain parent engineering.','TVS rated-pulse clamp below 60V at 25C is only component screening; temperature, surge source/energy, overshoot, dV/dt and board containment remain unqualified.','Unpowered/brownout ISO1212 output is invalid; FPGA/software must mask until independent receiving-rail qualification and freshness.','No receiver fail-safe claim for tri-stated STEP/DIR; drive profiles and independent STO/drive-power stop path remain required.','Native ERC/netlist checks do not establish pin allocation, routing, DRC, FPGA fit, target operation or manufacture readiness.']}


def relay_footprints(out):
    fpdir=out/'CNC_Motors.pretty';fpdir.mkdir(exist_ok=True)
    rec={}
    for name,px,py,sx,sy,bx,by,cy in [('TLP3640A_SO4_11-3C1',3.15,.635,1.2,.8,4.55,2.6,1.7),('TLP4176A_2.54SOP4_11-5H1S',3.15,1.27,1.8,.9,4.4,3.9,2.5)]:
        pads=[('1',-px,-py),('2',-px,py),('3',px,py),('4',px,-py)]
        cx=round(px+sx/2+.25,2)
        text=f'(footprint "{name}"(version 20250108)(generator "controller_hardware")(layer "F.Cu")(descr "Source-checked Toshiba pin/package candidate; see footprint-review.json")(attr smd)(property "Reference" "REF**"(at 0 {-cy-1} 0)(layer "F.SilkS")(effects(font(size 1 1)(thickness .15))))(property "Value" "{name}"(at 0 {cy+1} 0)(layer "F.Fab")(effects(font(size 1 1)(thickness .15))))(fp_rect(start {-bx/2} {-by/2})(end {bx/2} {by/2})(stroke(width .1)(type default))(fill none)(layer "F.Fab"))(fp_rect(start {-cx} {-cy})(end {cx} {cy})(stroke(width .05)(type default))(fill none)(layer "F.CrtYd"))(fp_circle(center {-bx/2+.4} {-by/2+.4})(end {-bx/2+.55} {-by/2+.4})(stroke(width .1)(type default))(fill none)(layer "F.Fab"))'
        text+=''.join(f'(pad "{n}" smd rect(at {x} {y})(size {sx} {sy})(layers "F.Cu" "F.Paste" "F.Mask"))' for n,x,y in pads)+')'
        (fpdir/(name+'.kicad_mod')).write_text(dump(parse(text))+'\n',encoding='utf-8')
        rec[name]={'pins':{'1':'anode','2':'cathode','3':'drain','4':'drain'},'pad_centres_mm':{n:[x,y] for n,x,y in pads},'pad_size_mm':[sx,sy],'geometry_basis':'Toshiba Fig14.1 reference lands, rotated into KiCad pin1 upper-left' if '3640' in name else 'Toshiba package11-5H1S maximum body/lead envelope; inferred candidate lands, no vendor land diagram','max_height_mm':2.2 if '3640' in name else 2.1,'courtyard_is_project_allowance':True,'stencil_approved':False,'three_d_model':None}
    (out/'footprint-review.json').write_text(json.dumps(rec,indent=2)+'\n',encoding='utf-8')
    (out/'fp-lib-table').write_text(dump(parse('(fp_lib_table(version 7)(lib(name "CNC_Motors")(type "KiCad")(uri "${KIPRJMOD}/CNC_Motors.pretty")(options "")(descr "Source checked motor photorelay candidates")))'))+'\n',encoding='utf-8')


def build(out=OUT):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);model=description();parts=model['components'];uid=lambda k:str(uuid.uuid5(NS,k));root=uid('root');functions=dict(PIN_FUNCTIONS)
    for p in parts.values():
        if not p['physical']:functions[p['kind']]={int(k):(k,'passive') for k in p['pins']}
    functions['PWR_FLAG']={1:('pwr','power_out')};layouts={};libs=[]
    for kind,table in functions.items():
        if kind in ('R','C','TVS'):layout=[(1,'',0,5.08,270,'passive'),(2,'',0,-5.08,90,'passive')];body='(rectangle(start -1.016 2.54)(end 1.016 -2.54)(stroke(width .254)(type default))(fill(type none)))'
        elif kind=='PWR_FLAG':layout=[(1,'pwr',0,0,90,'power_out')];body=''
        else:
            outs=[k for k,(_,t) in table.items() if t in ('output','tri_state','open_collector')];left=[k for k in table if k not in outs]
            if kind in ('TLP3640A','TLP4176A'):left=[1,2];outs=[3,4]
            layout=[]
            for sign,keys in [(-1,left),(1,outs)]:
                layout += [(k,table[k][0],sign*12.7,20.32-j*5.08,0 if sign<0 else 180,table[k][1]) for j,k in enumerate(keys)]
            low=min(p[3] for p in layout)-5.08;body=f'(rectangle(start -10.16 25.4)(end 10.16 {low})(stroke(width .254)(type default))(fill(type background)))'
        layouts[kind]=layout;libs.append(symbol(kind,layout,body,'B' if kind.startswith('B') or kind=='MotorBoundary' else kind if kind in ('R','C') else 'D' if kind=='TVS' else '#FLG' if kind=='PWR_FLAG' else 'U'))
    items=[];netmap={};ic_index=pass_index=boundary_index=0
    for ref,p in parts.items():
        if ref.startswith('U'):x=63.5+(ic_index%11)*101.6;y=83.82+(ic_index//11)*101.6;ic_index+=1
        elif p['physical']:x=40.64+(pass_index%17)*66.04;y=477.52+(pass_index//17)*25.4;pass_index+=1
        else:x=63.5+(boundary_index%8)*144.78;y=787.4+(boundary_index//8)*147.32;boundary_index+=1
        layout=layouts[p['kind']];physical=p['physical'];upper=max(pp[3] for pp in layout)
        small=p['kind'] in ('R','C','TVS');rx=x+3.81 if small else x;ry=y-2.54 if small else y-upper-10.16
        props=''.join(f'(property {quote(k)} {quote(v)}(at {rx} {ry+dy} 0){effects(.8,"hide") if hidden else effects(.8,"(justify left)" if small else "")})' for k,v,dy,hidden in [('Reference',ref,0,False),('Value',p['value'],2.54,False),('MPN',p['mpn'],0,True),('Footprint',p['footprint'],0,True)])
        items.append(f'(symbol(lib_id "CNC:{p["kind"]}")(at {x} {y} 0)(unit 1)(in_bom {"yes" if physical else "no"})(on_board {"yes" if physical else "no"})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "motherboard_motors"(path "/{root}"(reference {quote(ref)})(unit 1)))))')
        for n,_,px,py,_,_ in layout:
            sx,sy=round(x+px,4),round(y-py,4);net=p['pins'][str(n)]
            if net is None:items.append(f'(no_connect(at {sx} {sy})(uuid "{uid(ref+str(n)+"nc")}"))');continue
            dx=-5.08 if px<0 else 5.08 if px>0 else 0;dy=0 if px else (-5.08 if py>0 else 5.08);ex,ey=round(sx+dx,4),round(sy+dy,4)
            items.append(f'(wire(pts(xy {sx} {sy})(xy {ex} {ey}))(stroke(width 0)(type default))(uuid "{uid(ref+str(n)+"wire")}"))')
            items.append(f'(label {quote(net)}(at {ex} {ey} 0){effects(.65,"(justify right bottom)" if px<0 else "(justify left bottom)")}(uuid "{uid(ref+str(n)+"label")}"))')
            netmap.setdefault(net,[]).append([ref,str(n)])
    # Flags are explicit conditional supply declarations for standalone ERC;
    # they neither generate power nor survive into parent supply integration.
    for i,net in enumerate(('MOTOR_IO_3V3','MOTOR_5V_A','MOTOR_5V_B','LOGIC_GND')):
        ref=f'#FLG{i}';x=774.7+i*50.8;y=706.12
        items.append(f'(symbol(lib_id "CNC:PWR_FLAG")(at {x} {y} 0)(unit 1)(in_bom no)(on_board no)(dnp no)(uuid "{uid(ref)}")(property "Reference" "{ref}"(at {x} {y} 0){effects(1,"hide")})(property "Value" "CONDITIONAL SUPPLY BOUNDARY"(at {x} {y} 0){effects(1,"hide")})(instances(project "motherboard_motors"(path "/{root}"(reference "{ref}")(unit 1)))))(label "{net}"(at {x} {y} 0){effects(.8)}(uuid "{uid(ref+"label")}"))')
    note='TWELVE FITTED ON-MOTHERBOARD MOTOR INTERFACES: 24 DIFFERENTIAL SIGNALS / 12 NO+NC ENABLES / 12 SEPARATE ALARMS\nSource circuit candidate. Power/interface boundaries and qualified timing remain explicit parent obligations. Not fabrication data.'
    items.append(f'(text {quote(note)}(at 20.32 17.78 0){effects(1.4,"(justify left top)")}(uuid "{uid(note)}"))')
    raw=f'(kicad_sch(version 20250114)(generator "controller_hardware")(uuid "{root}")(paper "User" 1189 1050)(title_block(title "One-motherboard twelve motor interface source")(date "2026-09-30")(rev "r0.1"))(lib_symbols'+''.join(libs)+')'+''.join(items)+')'
    (out/'motherboard_motors.kicad_sch').write_text(dump(parse(raw))+'\n',encoding='utf-8')
    (out/'CNC.kicad_sym').write_text(dump(parse('(kicad_symbol_lib(version 20241209)(generator "controller_hardware")'+''.join(s.replace('(symbol "CNC:','(symbol "',1) for s in libs)+')'))+'\n',encoding='utf-8')
    (out/'sym-lib-table').write_text(dump(parse('(sym_lib_table(version 7)(lib(name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "Source-backed motherboard motor interface")))'))+'\n',encoding='utf-8')
    (out/'motherboard_motors.kicad_pro').write_text(json.dumps({'meta':{'filename':'motherboard_motors.kicad_pro','version':1},'erc':{'rule_severities':{'single_global_label':'warning','four_way_junction':'warning','simulation_model_issue':'warning','footprint_filter':'warning'}}},indent=2)+'\n',encoding='utf-8')
    (out/'design.json').write_text(json.dumps(model,indent=2)+'\n',encoding='utf-8');(out/'pin-map.json').write_text(json.dumps(netmap,indent=2)+'\n',encoding='utf-8')
    with (out/'bom.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['Reference','Value','MPN','Footprint','Status']);writer.writeheader();writer.writerows({'Reference':ref,'Value':p['value'],'MPN':p['mpn'],'Footprint':p['footprint'],'Status':'source_candidate_not_qualified'} for ref,p in parts.items() if p['physical'])
    relay_footprints(out)
    print(json.dumps({'physical_parts':sum(p['physical'] for p in parts.values()),'motor_count':12,'source':str(out/'motherboard_motors.kicad_sch'),'manufacturing_ready':False}))
    return model


if __name__=='__main__':build()
