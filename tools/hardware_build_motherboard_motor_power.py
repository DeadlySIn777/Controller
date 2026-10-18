"""Actual voltage-window health circuitry for the one-board motor interface.

This block monitors real receiving rails after protection; it does not create
the supplies, invent power-good constants, or qualify assembled fault timing.
The frozen 6xxx motor circuit is not edited. New references occupy 9xxx.
"""
import csv
import hashlib
import json
from pathlib import Path
import shutil
import uuid

from hardware_build_assembly import parse, dump
from hardware_build_tx_schematic import effects, quote, symbol

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'hardware/motherboard_motor_power'
REPORT = ROOT / 'reports/motherboard-motor-power-20260930'
NS = uuid.UUID('bbfa81aa-78e7-4c78-9f7a-b654790389ac')
PINS = {
    'LTC2962': {1:('RDIS','input'),2:('MR','input'),3:('DVCC','power_in'),4:('VCC','power_in'),5:('REF','output'),6:('PG1','input'),7:('PG2','input'),8:('PG3','input'),9:('PG4','input'),10:('RT','input'),11:('GND','power_in'),12:('RST','open_collector'),13:('V4','input'),14:('V3','input'),15:('V2','input'),16:('V1','input'),17:('EP','power_in')},
    'ISO7720F': {1:('GND1','power_in'),2:('NC','no_connect'),3:('VCC1','power_in'),4:('INA','input'),5:('INB','input'),6:('NC','no_connect'),7:('GND1','power_in'),8:('NC','no_connect'),9:('GND2','power_in'),10:('NC','no_connect'),11:('NC','no_connect'),12:('OUTB','output'),13:('OUTA','output'),14:('VCC2','power_in'),15:('NC','no_connect'),16:('GND2','power_in')},
    'LVC1G17': {1:('NC','no_connect'),2:('A','input'),3:('GND','power_in'),4:('Y','output'),5:('VCC','power_in')},
    'LVC2G08': {1:('1A','input'),2:('1B','input'),3:('2Y','output'),4:('GND','power_in'),5:('2A','input'),6:('2B','input'),7:('1Y','output'),8:('VCC','power_in')},
    'R': {1:('','passive'),2:('','passive')},
    'C': {1:('','passive'),2:('','passive')},
}
MPNS = {
    'LTC2962': ('LTC2962HUD#PBF','CNC_MotorPower:LTC2962_UD16'),
    'ISO7720F': ('ISO7720FDWR','CNC_MotorPower:ISO7720_DW16_TI_HV'),
    'LVC1G17': ('SN74LVC1G17DBVR','Package_TO_SOT_SMD:SOT-23-5'),
    'LVC2G08': ('SN74LVC2G08DCUR','Package_SO:VSSOP-8_2.3x2mm_P0.5mm'),
}
BOUNDARY_POWER = ['CORE_5V','IO_3V3','LOGIC_GND','MOTOR_5V_A','MOTOR_5V_B','FIELD_5V','FIELD_GND','AUX_5V_A','AUX_5V_B','AUX_24V_A','AUX_24V_B']
BOUNDARY_OUTPUTS = ['MOTOR_POWER_OK_A_QUALIFIED','MOTOR_POWER_OK_B_QUALIFIED','MOTOR_LOGIC_HEALTH_A','MOTOR_LOGIC_HEALTH_B','MOTOR_FIELD_HEALTH_A_ISOLATED','MOTOR_FIELD_HEALTH_B_ISOLATED']
# Rail, UV top, OV top, bottom, requirement window, acceptance window.
# The 19–29 V AUX24 acceptance interval is a source-screen limitation, never
# a replacement for the inherited 18–30 V field requirement.
WINDOWS = [
    ('MOTOR_5V_A',87900,92100,10000,[4.85,5.15],[4.95,5.05]),
    ('IO_3V3',54500,57500,10000,[3.2,3.4],[3.25875,3.34125]),
    ('MOTOR_5V_B',87900,92100,10000,[4.85,5.15],[4.95,5.05]),
    ('IO_3V3',54500,57500,10000,[3.2,3.4],[3.25875,3.34125]),
    ('AUX_5V_A',86700,93100,10000,[4.8,5.25],[4.875,5.075]),
    ('AUX_24V_A',355000,580000,10000,[18,30],[19,29]),
    ('AUX_5V_B',86700,93100,10000,[4.8,5.25],[4.875,5.075]),
    ('AUX_24V_B',355000,580000,10000,[18,30],[19,29]),
]


def description():
    parts = {}; u = r = c = 9000; window_rows = []
    def ic(kind,pins,role):
        nonlocal u
        u += 1; ref = 'U'+str(u); mpn,fp = MPNS[kind]
        parts[ref] = {'kind':kind,'mpn':mpn,'value':mpn,'footprint':fp,'physical':True,'pins':{str(k):v for k,v in pins.items()},'role':role}
        return ref
    def resistor(a,b,ohms,role,precision=False):
        nonlocal r
        r += 1; ref = 'R'+str(r)
        if precision:
            # Four-character EIA resistance code; exact production availability
            # is a procurement gate, not silently substituted by a 1% resistor.
            exp = 0; base = ohms
            while base >= 1000: base /= 10; exp += 1
            code = f'{int(base):03d}{exp}'
            mpn = 'PLT0603Z'+code+'LST1'; tol = .0001; tcr = 5
        else:
            mpn = {1000:'CRCW06031K00FKEA',10000:'CRCW060310K0FKEA',100000:'CRCW0603100KFKEA'}[ohms]; tol = .01; tcr = 100
        parts[ref] = {'kind':'R','mpn':mpn,'value':f'{ohms}R '+('0.01% 5ppm' if precision else '1% 100ppm'),'footprint':'Resistor_SMD:R_0603_1608Metric','physical':True,'pins':{'1':a,'2':b},'resistance_ohm':ohms,'initial_tolerance':tol,'tcr_ppm':tcr,'role':role}
        return ref
    def capacitor(a,b,role):
        nonlocal c
        c += 1; ref = 'C'+str(c)
        parts[ref] = {'kind':'C','mpn':'GRM188R72A104KA35D','value':'100nF 100V X7R 10%','footprint':'Capacitor_SMD:C_0603_1608Metric','physical':True,'pins':{'1':a,'2':b},'capacitance_f':100e-9,'initial_tolerance':.1,'role':role}
        return ref
    for index,bank in enumerate(('A','B','A','B')):
        field = index >= 2; domain = 'FIELD' if field else 'LOGIC'
        power = 'FIELD_5V' if field else 'CORE_5V'; gnd = 'FIELD_GND' if field else 'LOGIC_GND'
        output = f'MOTOR_{domain}_HEALTH_{bank}_RAW'; reference = f'MOTOR_PWR_REF_{domain}_{bank}'
        pins = {1:power,2:power,3:gnd,4:power,5:reference,6:reference,7:gnd,8:reference,9:gnd,10:power,11:gnd,12:output,17:gnd}
        subset = WINDOWS[index*2:index*2+2]
        for j,(rail,uv,ov,bottom,limits,accept) in enumerate(subset):
            uvnet = f'MOTOR_PWR_{domain}_{bank}_{j}_UV'; ovnet = f'MOTOR_PWR_{domain}_{bank}_{j}_OV'
            pins[16-j*2] = uvnet; pins[15-j*2] = ovnet
            references = []
            for kind,top,net in [('UV',uv,uvnet),('OV',ov,ovnet)]:
                tr = resistor(rail,net,top,'actual post-protection rail '+kind,True)
                br = resistor(net,gnd,bottom,'Kelvin supervisor sense return '+kind,True)
                references.append({'kind':kind,'top_ref':tr,'bottom_ref':br,'top_ohm':top,'bottom_ohm':bottom})
            window_rows.append({'supervisor':'U'+str(9001+index),'rail':rail,'domain':domain,'bank':bank,'uv_pin':16-j*2,'ov_pin':15-j*2,'requirement_limits_v':limits,'static_acceptance_v':accept,'dividers':references})
        ic('LTC2962',pins,f'{domain} bank {bank}: two actual voltage windows, RST released only when all four comparators valid')
        resistor(power,output,10000,'released health pull-up belongs to supervisor source rail')
        resistor(output,gnd,100000,'health raw power-loss bias, not intermediate-voltage guarantee')
        capacitor(power,gnd,'window supervisor bypass')
    for bank in ('A','B'):
        ic('LVC1G17',{1:None,2:f'MOTOR_LOGIC_HEALTH_{bank}_RAW',3:'LOGIC_GND',4:f'MOTOR_LOGIC_HEALTH_{bank}',5:'IO_3V3'},f'bank {bank} slow-edge Schmitt translation to actual receiving 3.3 V')
        resistor(f'MOTOR_LOGIC_HEALTH_{bank}','LOGIC_GND',10000,'zero-VCC Ioff output bias')
        capacitor('IO_3V3','LOGIC_GND','health translation bypass')
    ic('ISO7720F',{1:'FIELD_GND',2:None,3:'FIELD_5V',4:'MOTOR_FIELD_HEALTH_A_RAW',5:'MOTOR_FIELD_HEALTH_B_RAW',6:None,7:'FIELD_GND',8:None,9:'LOGIC_GND',10:None,11:None,12:'MOTOR_FIELD_HEALTH_B_ISOLATED',13:'MOTOR_FIELD_HEALTH_A_ISOLATED',14:'IO_3V3',15:None,16:'LOGIC_GND'},'default-LOW isolated actual field health, F suffix required')
    capacitor('FIELD_5V','FIELD_GND','isolator field bypass')
    capacitor('IO_3V3','LOGIC_GND','isolator logic bypass')
    for bank in ('A','B'):resistor(f'MOTOR_FIELD_HEALTH_{bank}_ISOLATED','LOGIC_GND',10000,'receiving isolated health output bias; VCCO partial state remains unqualified')
    ic('LVC2G08',{1:'MOTOR_LOGIC_HEALTH_A',2:'MOTOR_FIELD_HEALTH_A_ISOLATED',3:'MOTOR_POWER_OK_B_QUALIFIED',4:'LOGIC_GND',5:'MOTOR_LOGIC_HEALTH_B',6:'MOTOR_FIELD_HEALTH_B_ISOLATED',7:'MOTOR_POWER_OK_A_QUALIFIED',8:'IO_3V3'},'hardware AND actual receiving logic and isolated field health; no software authority')
    capacitor('IO_3V3','LOGIC_GND','hardware health gate bypass')
    for bank in ('A','B'):resistor(f'MOTOR_POWER_OK_{bank}_QUALIFIED','LOGIC_GND',1000,'qualified health zero-supply default; counts frozen motor 10k in parallel')
    for ref,nets in [('B9001',BOUNDARY_POWER),('B9002',BOUNDARY_OUTPUTS)]:
        parts[ref] = {'kind':ref,'mpn':'','value':'INTERNAL REVIEW BOUNDARY','footprint':'','physical':False,'pins':{str(i):n for i,n in enumerate(nets,1)},'role':'logical interface, not fitted connector or supply'}
    sources = ['reports/motherboard-motor-power-20260930/sources/iso7720.pdf','reports/motherboard-motor-power-20260930/sources/ltc2962-primary-review.json','research/mc-local-power/sn74lvc1g17.pdf','research/machine-permission/sn74lvc2g08.pdf','research/power-sequence/vishay-plt.pdf','hardware/mc_local_power/design.json','hardware/motherboard_motors/design.json','hardware/motion_card/CNC_MC_Power.pretty/LTC2962_UD16.kicad_mod']
    return {'schema_version':1,'revision':'motherboard-motor-power-r0.1','architecture':'one_custom_motherboard','manufacturing_ready':False,'physical_qualification':False,'arbitrary_partial_power_qualified':False,'components':parts,'windows':window_rows,'boundary_inputs':[],'boundary_outputs':BOUNDARY_OUTPUTS,'boundary_power':BOUNDARY_POWER,'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},'contract':{'supervisor':'LTC2962 H-grade, VCC2.25–5.5V, DVCC grounded for open-drain','pg_modes':['+ADJ','-ADJ','+ADJ','-ADJ'],'release_ms':[160,240],'sense_v_threshold':[.4975,.5025],'sense_bias_max_a':15e-9,'precision_r_initial':.0001,'precision_r_tcr_ppm':5,'precision_r_temperature_excursion_c':100,'additional_precision_drift_fraction':.0004,'aux5_min_falling_trip_v':4.8,'aux24_inherited_requirement_v':[18,30],'aux24_static_acceptance_limit_v':[19,29],'field_logic_returns_joined':False,'gate_truth':'MOTOR_POWER_OK_bank = LOGIC_HEALTH_bank AND FIELD_HEALTH_bank_ISOLATED','core5_input_v':[4.85,5.15],'receiving_io3_input_v':[3.2,3.4],'io3_extra_bypass_nominal_uf':.5,'supervisor_tuv_max_us_at_10pct_overdrive':40,'isolator_default':'LOW with F suffix; input ≤1.7V/output ≥2.25V; 1.7–2.25V is undetermined','brownout_slew_or_fault_guaranteed':False},'open_gates':['Actual MOTOR_5V_A/B supplies, protection and source current budget are absent; CORE_5V4.85V lower bound has no guaranteed downstream loss headroom.','FIELD_5V generation and actual AUX_5V/AUX_24V independent bank limiters, current limits, output drop/distribution and sustained-short survival must be implemented.','AUX24 inherited18–30V requirement is preserved;19–29V is only the guaranteed static acceptance screen for these thresholds, not equivalent full-range qualification.','LTC2962 comparator40us maximum is specified at10% overdrive; no maximum for arbitrarily shallow faults or all brownout slopes.','LTC2962 power-down reset state is guaranteed only down to VCC1V; exact0V leakage and powered valid operation are separate from intermediate rails.','ISO7720F output is undetermined with receiving power absent or supply1.7–2.25V; defaultLOW is not a proof of all intermediate-power transitions.','No hard power cut independent of partially powered3.3V logic is fitted by this monitoring-only block; parent power sequencing/withdrawal slope and LED rail transitions require physical validation.','Supply overvoltage monitoring is delayed fault signalling, not a surge clamp.','Precision resistor exact orderability, lifetime drift, soldering stress and source impedance/noise require sourcing and qualification.','Board layout must preserve FIELD_GND/LOGIC_GND isolation and Kelvin sense references, with actual contact/copper/drop and domain-entry assignment verified.']}


def footprints(out):
    pretty = out/'CNC_MotorPower.pretty'; pretty.mkdir(exist_ok=True)
    source = ROOT/'hardware/motion_card/CNC_MC_Power.pretty/LTC2962_UD16.kicad_mod'
    shutil.copyfile(source,pretty/source.name)
    pads = [(str(i+1),-4.875,round(-4.445+i*1.27,4)) for i in range(8)]
    pads += [(str(i+9),4.875,round(4.445-i*1.27,4)) for i in range(8)]
    raw = '(footprint "ISO7720_DW16_TI_HV"(version 20250108)(generator "pcbnew")(layer "F.Cu")(attr smd)(descr "TI SLLSEP3G DW0016B4221009/B HV example lands; not assembled qualification")(property "Reference" "REF**"(at 0 -6.7 0)(layer "F.SilkS")(effects(font(size 1 1)(thickness .15))))(property "Value" "ISO7720FDWR"(at 0 6.7 0)(layer "F.Fab")(effects(font(size 1 1)(thickness .15))))(fp_rect(start -3.8 -5.25)(end 3.8 5.25)(stroke(width .1)(type default))(fill none)(layer "F.Fab"))(fp_rect(start -5.95 -5.7)(end 5.95 5.7)(stroke(width .05)(type default))(fill none)(layer "F.CrtYd"))(fp_circle(center -3.1 -4.6)(end -2.9 -4.6)(stroke(width .1)(type default))(fill none)(layer "F.Fab"))'
    raw += ''.join(f'(pad "{n}" smd roundrect(at {x} {y})(size 1.65 .6)(layers "F.Cu" "F.Paste" "F.Mask")(roundrect_rratio .08333333))' for n,x,y in pads)+')'
    (pretty/'ISO7720_DW16_TI_HV.kicad_mod').write_text(dump(parse(raw))+'\n',encoding='utf-8')
    review = {'LTC2962_UD16':{'source':str(source.relative_to(ROOT)).replace('\\','/'),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'copper_unchanged':True,'thermal_pad_type':'smd','thermal_pad_net':'same local domain GND','three_d_model':None},'ISO7720_DW16_TI_HV':{'primary_pdf':'sources/iso7720.pdf','drawing':'DW0016B4221009/B07/2016','reference':'HV/isolation example, not IPC nominal example','pad_size_mm':[1.65,.6],'pad_centres_mm':{n:[x,y] for n,x,y in pads},'copper_gap_mm':8.1,'body_max_mm':[7.6,10.5],'courtyard_allowance_includes_flash':True,'three_d_model':None,'stencil_or_isolation_qualified':False}}
    (out/'footprint-review.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')


def build(out=OUT):
    out = Path(out); out.mkdir(parents=True,exist_ok=True)
    model = description(); parts = model['components']; uid = lambda name:str(uuid.uuid5(NS,name)); root = uid('root')
    funcs = dict(PINS)
    for p in parts.values():
        if not p['physical']:funcs[p['kind']] = {int(k):(k,'passive') for k in p['pins']}
    funcs['PWR_FLAG'] = {1:('pwr','power_out')}
    library = []; geometry = {}
    for kind,pinmap in funcs.items():
        if kind in ('R','C'):
            coords = [(1,'',0,5.08,270,'passive'),(2,'',0,-5.08,90,'passive')]
            shape = '(rectangle(start -1.016 2.54)(end 1.016 -2.54)(stroke(width .254)(type default))(fill(type none)))' if kind=='R' else '(polyline(pts(xy -2.54 .762)(xy 2.54 .762))(stroke(width .3)(type default))(fill(type none)))(polyline(pts(xy -2.54 -.762)(xy 2.54 -.762))(stroke(width .3)(type default))(fill(type none)))(polyline(pts(xy 0 2.54)(xy 0 .762))(stroke(width .254)(type default))(fill(type none)))(polyline(pts(xy 0 -.762)(xy 0 -2.54))(stroke(width .254)(type default))(fill(type none)))'
        elif kind=='PWR_FLAG':coords=[(1,'pwr',0,0,90,'power_out')];shape=''
        else:
            keys=list(pinmap);left=keys[:(len(keys)+1)//2];right=keys[len(left):];half=max(len(left),len(right))*5.08
            coords=[]
            for side,keys in ((-1,left),(1,right)):
                for i,n in enumerate(keys):coords.append((n,pinmap[n][0],side*20.32,half-i*10.16,0 if side<0 else 180,pinmap[n][1]))
            shape=f'(rectangle(start -17.78 {half+5.08})(end 17.78 {-half+5.08})(stroke(width .254)(type default))(fill(type background)))'
        geometry[kind]=coords
        library.append(symbol(kind,coords,shape,'R' if kind=='R' else 'C' if kind=='C' else '#FLG' if kind=='PWR_FLAG' else 'B' if kind.startswith('B') else 'U'))
    items=[];nets={};ic_count=passive_count=boundary_count=0
    for ref,p in parts.items():
        kind=p['kind']; passive=kind in ('R','C')
        if passive:x=50.8+(passive_count%10)*101.6;y=441.96+(passive_count//10)*38.1;passive_count+=1
        elif p['physical']:x=177.8+(ic_count%4)*266.7;y=114.3+(ic_count//4)*167.64;ic_count+=1
        else:x=177.8+boundary_count*508;y=756.92;boundary_count+=1
        py=y-10.16 if passive else y-max(abs(row[3]) for row in geometry[kind])-15.24
        props=f'(property "Reference" {quote(ref)}(at {x+5.08 if passive else x} {py} 0){effects(.95)})(property "Value" {quote(p["value"])}(at {x+7.62 if passive else x} {py+5.08} 0){effects(.8)})'
        props+=f'(property "MPN" {quote(p["mpn"])}(at {x} {y} 0){effects(extra="hide")})(property "Footprint" {quote(p["footprint"])}(at {x} {y} 0){effects(extra="hide")})'
        items.append(f'(symbol(lib_id "CNC:{kind}")(at {x} {y} 0)(unit 1)(in_bom {"yes" if p["physical"] else "no"})(on_board {"yes" if p["physical"] else "no"})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "motherboard_motor_power"(path "/{root}"(reference {quote(ref)})(unit 1)))))')
        for n,_,px,py,_,_ in geometry[kind]:
            xx,yy=round(x+px,4),round(y-py,4);net=p['pins'][str(n)]
            if net is None:items.append(f'(no_connect(at {xx} {yy})(uuid "{uid(ref+str(n)+"nc")}"))');continue
            ex=xx if passive else round(xx+(-30.48 if px<0 else 10.16),4);ey=round(yy+(-5.08 if n==1 else 5.08),4) if passive else yy
            if (ex,ey)!=(xx,yy):items.append(f'(wire(pts(xy {xx} {yy})(xy {ex} {ey}))(stroke(width 0)(type default))(uuid "{uid(ref+str(n)+"w")}"))')
            items.append(f'(label {quote(net)}(at {ex} {ey} 0){effects(.7,"(justify left bottom)")}(uuid "{uid(ref+str(n)+"l")}"))')
            nets.setdefault(net,[]).append([ref,str(n)])
    for i,net in enumerate(BOUNDARY_POWER):
        x,y=50.8+i*88.9,899.16;ref='#FLG'+str(9001+i)
        items.append(f'(symbol(lib_id "CNC:PWR_FLAG")(at {x} {y} 0)(unit 1)(in_bom no)(on_board no)(dnp no)(uuid "{uid(ref)}")(property "Reference" {quote(ref)}(at {x} {y-5.08} 0){effects(extra="hide")})(property "Value" "ACTUAL PARENT RAIL REQUIRED"(at {x} {y-2.54} 0){effects(extra="hide")})(instances(project "motherboard_motor_power"(path "/{root}"(reference {quote(ref)})(unit 1)))))(label {quote(net)}(at {x} {y} 0){effects(.7,"(justify left bottom)")}(uuid "{uid(ref+"l")}"))')
    for i,line in enumerate(['MOTOR POWER HEALTH / ONE MOTHERBOARD / SOURCE CANDIDATE r0.1','Four actual voltage-window monitors; FIELD/LOGIC remain isolated; no supply or limiter created here.','Health = receiving 5V and 3.3V valid AND isolated AUX5/AUX24 valid; no FPGA/software bypass.','LTC fault40us bound requires10% overdrive. ISO power1.7–2.25V undetermined. Physical brownout qualification remains open.','AUX24 inherited18–30V requirement retained; current guaranteed static arming screen only19–29V.']):
        items.append(f'(text {quote(line)}(at 25.4 {20.32+i*7.62} 0){effects(1.2,"(justify left top)")}(uuid "{uid("note"+str(i))}"))')
    raw=f'(kicad_sch(version 20250114)(generator "eeschema")(uuid "{root}")(paper "User" 1189 950)(title_block(title "Motor receiving and field power health")(date "2026-09-30")(rev "r0.1 / source candidate"))(lib_symbols {"".join(library)})'+''.join(items)+')'
    (out/'motherboard_motor_power.kicad_sch').write_text(dump(parse(raw))+'\n',encoding='utf-8')
    lib='(kicad_symbol_lib(version 20241209)(generator "kicad_symbol_editor")'+''.join(s.replace('(symbol "CNC:','(symbol "',1) for s in library)+')'
    (out/'CNC.kicad_sym').write_text(dump(parse(lib))+'\n',encoding='utf-8')
    (out/'sym-lib-table').write_text(dump(parse('(sym_lib_table(version 7)(lib(name "CNC")(type "KiCad")(uri "${KIPRJMOD}/CNC.kicad_sym")(options "")(descr "Actual motor health source candidate")))'))+'\n',encoding='utf-8')
    (out/'fp-lib-table').write_text(dump(parse('(fp_lib_table(version 7)(lib(name "CNC_MotorPower")(type "KiCad")(uri "${KIPRJMOD}/CNC_MotorPower.pretty")(options "")(descr "Source-backed power monitor lands")))'))+'\n',encoding='utf-8')
    (out/'motherboard_motor_power.kicad_pro').write_text(json.dumps({'meta':{'filename':'motherboard_motor_power.kicad_pro','version':1},'erc':{'rule_severities':{k:'warning' for k in ('single_global_label','four_way_junction','simulation_model_issue','footprint_filter')}}},indent=2)+'\n',encoding='utf-8')
    model['nets']={n:sorted(v) for n,v in sorted(nets.items())}
    (out/'design.json').write_text(json.dumps(model,indent=2)+'\n',encoding='utf-8')
    (out/'pin-map.json').write_text(json.dumps(model['nets'],indent=2)+'\n',encoding='utf-8')
    with (out/'bom.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f);writer.writerow(['Reference','Value','MPN','Footprint','Status'])
        for ref,p in parts.items():
            if p['physical']:writer.writerow([ref,p['value'],p['mpn'],p['footprint'],'source candidate / not qualified'])
    footprints(out)
    print(out/'motherboard_motor_power.kicad_sch')


if __name__=='__main__':build()
