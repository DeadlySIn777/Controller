"""Independent primary-pin, physical-net and static-bias MC motor review.

No generator import. Host ideal-digital/high-Z exercise is not measured timing,
FPGA fit, power-ramp or complete receiver qualification.
"""
import argparse
from collections import Counter
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/mc_motor_buffers'
PARTS={'LVC244A':('SN74LVC244APWR','Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm'),
       'LVC2G126':('SN74LVC2G126DCUR','Package_SO:VSSOP-8_2.3x2mm_P0.5mm')}
PIN_TABLES={
 'LVC244A':{'1':'1OE_N','2':'1A1','3':'2Y4','4':'1A2','5':'2Y3','6':'1A3','7':'2Y2',
   '8':'1A4','9':'2Y1','10':'GND','11':'2A1','12':'1Y4','13':'2A2','14':'1Y3',
   '15':'2A3','16':'1Y2','17':'2A4','18':'1Y1','19':'2OE_N','20':'VCC'},
 'LVC2G126':{'1':'1OE','2':'1A','3':'2Y','4':'GND','5':'2A','6':'1Y','7':'2OE','8':'VCC'}}
CHANNELS={'LVC244A':[(2,18,1),(4,16,1),(6,14,1),(8,12,1),(11,9,19),(13,7,19),(15,5,19),(17,3,19)],
          'LVC2G126':[(2,6,1),(5,3,7)]}


def primary_pins(source_dir=ROOT/'research/mc-motor-buffers'):
    result={}
    for kind,name in [('LVC244A','sn74lvc244a'),('LVC2G126','sn74lvc2g126')]:
        text=(Path(source_dir)/(name+'-pin-source.txt')).read_text(encoding='utf-8')
        if name.upper() not in text:raise ValueError('Manufacturer identity absent: '+name)
        heading='Table 4-1. Pin Functions' if kind=='LVC244A' else 'Pin Functions'
        if heading not in text:raise ValueError('Manufacturer pin table absent: '+kind)
        table=text.split(heading,1)[1]
        pattern=r'\b(1A[1-4]|2A[1-4]|[12]\s*OE|[12]Y[1-4]|GND|VCC)\s+(\d+)\s+[A-E]\d\s+\d+\s+[IO—]\s+[^\n]+' if kind=='LVC244A' else r'\b([12]A|[12]OE|[12]Y|GND|VCC)\s+(\d+)\s+[A-D]\d\s+[IO—]\s+[^\n]+'
        parsed={}
        for match in re.finditer(pattern,table):
            function,pin=match.group(1,2);function=function.replace(' ','')
            if kind=='LVC244A' and function.endswith('OE'):function+='_N'
            if pin in parsed:raise ValueError('Duplicate physical manufacturer pin')
            parsed[pin]=function
        if parsed!=PIN_TABLES[kind]:raise ValueError('Manufacturer pin table differs/incomplete: '+kind)
        result[kind]=parsed
    return result


def requirements():
    required=[]
    for i in range(12):
        bank='A' if i<8 else 'B';peer='MIA' if i<8 else 'MX4'
        for prefix in ('STEP','DIR','EN'):
            base=f'EN{i}_N' if prefix=='EN' else f'{prefix}{i}'
            required.append((base+'_FPGA',base+'_TO_'+peer,bank,prefix))
    required += [('TX_PERMIT','TX_PERMIT_A_TO_MIA','A','TX'),('TX_PERMIT','TX_PERMIT_B_TO_MX4','B','TX')]
    return required


def physical_ideal_outputs(design, inputs, powered, qualified_boe):
    """Trace A/Y/OE/package-power/source-series nets; None means ideal high-Z.

    This deliberately ignores declared paths and bank metadata. It models no
    analog ramp, propagation delay, resistor divider or receiving-card state.
    """
    parts=design['components']
    def bit(net):
        if net=='LOGIC_GND':return 0
        if net=='IO_3V3':return 1 if powered else 0
        if net=='BANK_B_BUFFER_ENABLE_QUALIFIED':return qualified_boe
        return inputs.get(net)
    result={}
    for _,out,_,_ in requirements():
        edges=[n for c in parts.values() if c.get('kind')=='R' and c.get('resistance_ohm')==33
               for p,n0 in c['pins'].items() if n0==out
               for q,n in c['pins'].items() if p!=q]
        drivers=[]
        for c in parts.values():
            if c.get('kind') not in PARTS:continue
            p=c['pins'];vcc='20' if c['kind']=='LVC244A' else '8';gnd='10' if c['kind']=='LVC244A' else '4'
            for a,y,oe in CHANNELS[c['kind']]:
                if p.get(str(y)) not in edges:continue
                active=bit(p.get(str(oe)))==(0 if c['kind']=='LVC244A' else 1)
                live=powered and p.get(vcc)=='IO_3V3' and p.get(gnd)=='LOGIC_GND'
                drivers.append(bit(p.get(str(a))) if active and live else None)
        result[out]=drivers[0] if len(drivers)==1 else None
    return result


def physical_startup_inputs(design):
    """External default-pull direction only; analog margin screened separately."""
    result={}
    for inp in {p[0] for p in requirements()}:
        rail=[]
        for c in design['components'].values():
            if c.get('kind')!='R' or c.get('resistance_ohm')!=4700:continue
            for p,n in c['pins'].items():
                if n==inp:rail.extend(v for q,v in c['pins'].items() if q!=p)
        result[inp]=0 if rail==['LOGIC_GND'] else 1 if rail==['IO_3V3'] else None
    return result


def static_bias_screen(parts):
    """Retained source limits, explicit divider/leakage assumptions and no fit claim."""
    vmax=D('3.465');vmin=D('3.14');rmax=D('4700')*D('1.01');rmin=D('4700')*D('.99')
    weak_up=D('27000');weak_down=D('30000')
    # TI244A full125C input leakage20uA plus T20 tristate10uA.
    leak=D('30e-6');par_up=weak_up*rmax/(weak_up+rmax);par_down=weak_down*rmax/(weak_down+rmax)
    idle_low=vmax*rmax/(weak_up+rmax)+leak*par_up
    idle_high=vmin*weak_down/(weak_down+rmax)-leak*par_down
    receiver_rmax=D('10100')
    # Worst case MC244A20uA Ioff and07A input5uA; receiver rail remains powered.
    en_high_A=vmin-D('25e-6')*receiver_rmax
    en_high_B=vmin-D('15e-6')*receiver_rmax
    step_low_A=D('21e-6')*receiver_rmax
    step_low_B=D('11e-6')*receiver_rmax
    boe_floating_low=(D('13')*D('5e-6')+D('5e-6')+D('10e-6'))*rmax
    input_load=vmax/rmin+D('20e-6')+vmax/weak_up
    tx_input_load=vmax/rmin+D('25e-6')+vmax/weak_up
    boe_driver_load=vmax/rmin+D('80e-6')
    fitted_pd_output_max=vmax/D('9900')
    with_required_receiver_output_max=vmax/D('4950')+D('1e-6')
    en_receiver_low_load_max=vmax/D('9900')+D('5e-6')
    result={'evidence':'static divider/leakage screening, not analog simulation/measurement',
        'assumptions':{'rail_bounds_v':[3.14,3.465],'strong_pull_ohm':4700,'strong_pull_tolerance':.01,
            'T20_weak_up_min_ohm':27000,'T20_weak_down_min_ohm':30000,'T20_tristate_abs_uA':10,
            'TI244A_input_Ioff_abs_uA_full125C':20,'TI2G126_input_abs_uA':5,'TI2G126_Ioff_abs_uA':10,
            'AM26C31I_input_abs_uA':1,'LVC07A_input_abs_uA':5,
            'receiver_pull_tolerance_assumed':.01,'powered_receiver_rail_bounds_required':[3.14,3.465]},
        'FPGA_tristate_STEP_DIR_worst_high_v':float(idle_low),
        'FPGA_tristate_EN_N_worst_low_v':float(idle_high),
        'qualified_BOE_floating_worst_high_v':float(boe_floating_low),
        'MC_off_receiver_EN_N_A_worst_low_v':float(en_high_A),
        'MC_off_receiver_EN_N_B_worst_low_v':float(en_high_B),
        'MC_off_receiver_STEP_DIR_A_worst_high_v':float(step_low_A),
        'MC_off_receiver_STEP_DIR_B_worst_high_v':float(step_low_B),
        'FPGA_single_pin_pull_plus_weak_pull_plus_buffer_leak_max_mA':float(input_load*1000),
        'FPGA_TX_fanout_two_buffers_pull_plus_weak_pull_plus_leak_max_mA':float(tx_input_load*1000),
        'qualified_BOE_driver_PD_plus_13OE_OPI_FPGA_input_leak_max_mA':float(boe_driver_load*1000),
        'buffer_output_fitted_PD_single_max_mA':float(fitted_pd_output_max*1000),
        'buffer_output_with_required_receiver_PD_max_mA':float(with_required_receiver_output_max*1000),
        'buffer_EN_N_active_low_receiver_bias_max_mA':float(en_receiver_low_load_max*1000),
        'all_36_FPGA_pulls_simultaneous_upper_load_mA':float(D('36')*input_load*1000),
        'buffer_quiescent_rail_input_conditions_only_max_mA':float((D('4')*D('40e-6')+D('7')*D('10e-6'))*1000),
        'buffer_incremental_supply_current_for_nonrail_inputs_or_switching_bounded':False,
        'loaded_GPIO_drive_strength_over_temperature_qualified':False,
        'transient_power_sequence_qualified':False,
        'passed_static_inactive_threshold_screen':idle_low<D('.8') and idle_high>D('2') and boe_floating_low<D('.8') and min(en_high_A,en_high_B)>D('2') and max(step_low_A,step_low_B)<D('.8')}
    return result


def validate(design=None,directory=OUT,native=True):
    directory=Path(directory);d=design if design is not None else json.loads((directory/'design.json').read_text())
    parts=d.get('components',{});errors=[];checks=0
    def check(test,message):
        nonlocal checks
        checks+=1
        if not test:errors.append(message)
    try:manufacturer=primary_pins()
    except (ValueError,FileNotFoundError) as exc:manufacturer={};errors.append(str(exc))
    check(d.get('manufacturing_ready') is False,'Manufacturing-ready claim forbidden')
    check(d.get('revision')=='mc-motor-buffers-r0.1','Revision differs')
    check(d.get('operating_supply_v')==[3.14,3.465] and d.get('logic_interface_nominal_v')==3.3,'Only specified3.3Vlogic domain allowed')
    expected_sources={f'research/mc-motor-buffers/{name}{suffix}' for name in ('sn74lvc244a','sn74lvc2g126','sn74lvc07a','am26c31') for suffix in ('.pdf','.txt')}
    expected_sources|={f'research/mc-motor-buffers/{name}-pin-source.txt' for name in ('sn74lvc244a','sn74lvc2g126')}
    expected_sources.add('research/fpga-core/trion20-ds-v6.0.pdf')
    check(set(d.get('sources',{}))==expected_sources,'Primary source set differs')
    for path,digest in d.get('sources',{}).items():check((ROOT/path).is_file() and hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,'Primary source hash changed: '+path)
    buffers={r:c for r,c in parts.items() if c.get('kind') in PARTS}
    check(Counter(c['kind'] for c in buffers.values())==Counter({'LVC244A':4,'LVC2G126':7}),'Required Ioff buffer count/functions differ')
    check(len(parts)==128 and sum(c.get('physical',False) for c in parts.values())==124,'Fitted/logical component count differs')
    expected_refs={f'U{i}' for i in range(1,12)}|{f'C{i}' for i in range(1,12)}|{f'R{i}' for i in range(1,103)}|{'B1','B2','B3','B4'}
    check(set(parts)==expected_refs,'Exact component reference set differs')
    resistors={r:c for r,c in parts.items() if c.get('kind')=='R'}
    check(Counter(c.get('resistance_ohm') for c in resistors.values())==Counter({33:38,4700:38,10000:26}),'Required source/default resistor count differs')
    caps={r:c for r,c in parts.items() if c.get('kind')=='C'}
    check(len(caps)==11,'Per-buffer decoupling count differs')
    for ref,c in parts.items():
        check(c.get('physical') is (ref not in ('B1','B2','B3','B4')),'Required fitted/boundary state differs: '+ref)
        if c.get('kind') in PARTS:
            kind=c['kind'];p=c.get('pins',{});functions=PIN_TABLES[kind]
            check((c.get('mpn'),c.get('footprint'),c.get('value'))==(*PARTS[kind],PARTS[kind][0]),'Exact MPN/footprint differs: '+ref)
            check(set(p)==set(functions),'Physical package pin set differs: '+ref)
            for pin,name in functions.items():
                if name in ('VCC','GND'):check(p.get(pin)==('IO_3V3' if name=='VCC' else 'LOGIC_GND'),'Physical supply/ground differs: '+ref+'/'+pin)
            for a,y,oe in CHANNELS[kind]:
                if p.get(str(y)) is None:
                    check(p.get(str(a))=='LOGIC_GND','Unused input floats/drives: '+ref+'/'+str(a))
                    if kind=='LVC2G126':check(p.get(str(oe))=='LOGIC_GND','Unused positiveOE notdisabled')
                elif kind=='LVC244A':check(p.get(str(oe))=='LOGIC_GND','BankA OE must be tiedactive')
                else:check(p.get(str(oe))=='BANK_B_BUFFER_ENABLE_QUALIFIED','BankB physicalOE bypass/polarity mismatch')
        elif c.get('kind')=='R':
            check(set(c.get('pins',{}))=={'1','2'},'Physical resistor pin set differs: '+ref)
            ohms=c.get('resistance_ohm');mpn={33:'CRCW060333R0FKEA',4700:'CRCW06034K70FKEA',10000:'CRCW060310K0FKEA'}.get(ohms)
            check((c.get('value'),c.get('mpn'),c.get('footprint'),c.get('tolerance'))==(str(ohms)+'R 1%',mpn,'Resistor_SMD:R_0603_1608Metric',.01),'Selected resistor/value differs: '+ref)
        elif c.get('kind')=='C':check((c.get('value'),c.get('mpn'),c.get('footprint'),c.get('pins'))==('100nF X7R 25V 10%','GRM188R71E104KA01D','Capacitor_SMD:C_0603_1608Metric',{'1':'IO_3V3','2':'LOGIC_GND'}),'Decoupling differs: '+ref)
        elif ref not in ('B1','B2','B3','B4'):check(False,'Unexpected physical function: '+ref)
    def resistor_edges(net,ohms=None):
        return [(r,next(n for pin,n in c['pins'].items() if pin!=p)) for r,c in resistors.items() for p,n in c['pins'].items() if n==net and (ohms is None or c.get('resistance_ohm')==ohms)]
    def pull(net,to,ohms):return len([edge for edge in resistor_edges(net,ohms) if edge[1]==to])==1
    required=requirements();found=[];used=set();physical_outputs=[];declared_input=set(d.get('boundary_inputs',[]));declared_output=set(d.get('boundary_outputs',[]))
    check(declared_output=={p[1] for p in required},'Exact required output boundary differs')
    check(declared_input=={p[0] for p in required}|{'IO_3V3','LOGIC_GND','BANK_B_BUFFER_ENABLE_QUALIFIED'},'Exact required input boundary differs')
    check(pull('BANK_B_BUFFER_ENABLE_QUALIFIED','LOGIC_GND',4700) and len(resistor_edges('BANK_B_BUFFER_ENABLE_QUALIFIED'))==1,'Qualified physical BOE startup pull differs')
    for inp,out,bank,signal in required:
        candidates=[]
        for ref,c in buffers.items():
            for a,y,oe in CHANNELS[c['kind']]:
                if c['pins'].get(str(a))==inp and c['pins'].get(str(y)) is not None:
                    raw=c['pins'][str(y)]
                    if (raw in [edge[1] for edge in resistor_edges(out,33)]):candidates.append((ref,a,y,oe,raw,c['kind']))
        check(len(candidates)==1,'Missing/duplicate physical buffer+series path: '+out)
        if len(candidates)!=1:continue
        ref,a,y,oe,raw,kind=candidates[0];used.add((ref,y));physical_outputs.append(raw)
        check(kind==('LVC244A' if bank=='A' else 'LVC2G126'),'Wrong Ioff/OE function for bank: '+out)
        check(raw not in declared_output and raw not in declared_input,'Boundary bypasses source resistor: '+out)
        check(len(resistor_edges(out,33))==1 and len(resistor_edges(raw,33))==1,'Series path shorts/multidrops: '+out)
        check(pull(inp,'IO_3V3' if signal=='EN' else 'LOGIC_GND',4700),'FPGA/gate startup pull differs: '+inp)
        check(len(resistor_edges(inp))==1,'Input has extra pull/series conductor: '+inp)
        if signal=='EN':
            check(len(resistor_edges(out))==1,'Outgoing EN bias must not attach toMCdeadrail: '+out)
        else:check(pull(out,'LOGIC_GND',10000),'Outgoing idle-low pull absent/wrong: '+out)
        found.append((inp,out,bank,ref,a,y,oe))
    for ref,c in buffers.items():
        for _,y,_ in CHANNELS[c['kind']]:check(c['pins'].get(str(y)) is None or (ref,y) in used,'Unexpected/unvalidated driven channel')
    check(len(physical_outputs)==len(set(physical_outputs)),'Output drivers short together')
    check(d.get('boe_contract',{}).get('physical_net')=='BANK_B_BUFFER_ENABLE_QUALIFIED' and d.get('boe_contract',{}).get('same_net_required_for_OPI_BOE_CLR_N') is True,'ActualOE observation contract changed')
    check(d.get('receiver_contract',{}).get('EN_N')=={'pull_ohm':10000,'to':'receiver_own_powered_3V3','receiver':'SN74LVC07APWR','pull_fitted_on_MC_output':False},'Powered-receiver EN contract differs')
    check(d.get('receiver_contract',{}).get('receiving_circuits_drawn_here') is False,'Receiver completion overclaimed')
    if native:
        xml=ET.parse(directory/'netlist.xml').getroot();actual={};native_nc=set()
        for net in xml.findall('./nets/net'):
            for node in net.findall('node'):
                key=(node.attrib['ref'],node.attrib['pin']);name=net.attrib['name'].lstrip('/')
                check(key not in actual,'Duplicate native pin conductor')
                if name.startswith('unconnected-') and parts.get(key[0],{}).get('pins',{}).get(key[1],'MISSING') is None:native_nc.add(key);continue
                actual[key]=name
        expected={(r,p):n for r,c in parts.items() for p,n in c.get('pins',{}).items() if n is not None}
        check(actual==expected,'Native physical netlist does not match source graph')
        check(native_nc=={(r,p) for r,c in parts.items() for p,n in c.get('pins',{}).items() if n is None},'Native no-connect set differs')
        native_components=xml.findall('./components/comp');check({c.attrib['ref'] for c in native_components}==set(parts),'Native component set differs')
        for c in native_components:
            ref=c.attrib['ref'];declared=parts.get(ref,{})
            fields={f.attrib['name']:f.text or '' for f in c.findall('./fields/field')}
            check((c.findtext('value',''),fields.get('MPN',''),c.findtext('footprint',''))==(declared.get('value'),declared.get('mpn'),declared.get('footprint')),'Native exact part/value/footprint differs: '+ref)
            props={p.attrib['name'] for p in c.findall('property')}
            check(({'exclude_from_bom','exclude_from_board'}<=props) if ref in ('B1','B2','B3','B4') else not props&{'exclude_from_bom','exclude_from_board','dnp'},'Native fitted/boundary flags differ: '+ref)
            kind=declared.get('kind')
            if kind not in PARTS:continue
            lib=c.find('libsource');item=next(p for p in xml.findall('./libparts/libpart') if p.attrib['part']==lib.attrib['part'])
            check({p.attrib['num']:p.attrib['name'] for p in item.findall('./pins/pin')}==manufacturer.get(kind),'Native package functions disagree with manufacturer: '+ref)
            expected_types={p:'power_in' if n in ('VCC','GND') else 'tri_state' if 'Y' in n else 'input' for p,n in PIN_TABLES[kind].items()}
            check({p.attrib['num']:p.attrib['type'] for p in item.findall('./pins/pin')}==expected_types,'Native package pin electrical types differ: '+ref)
        erc=json.loads((directory/'erc.json').read_text());check(not [v for s in erc.get('sheets',[]) for v in s.get('violations',[])],'Native ERC has violations')
        allowed_ignored={'single_global_label','four_way_junction','simulation_model_issue','footprint_filter'}
        check({i.get('key') for i in erc.get('ignored_checks',[])}<=allowed_ignored,'Native electrical ERC suppression forbidden')
        check(set(erc.get('included_severities',[]))=={'error','warning'},'Native ERC severities suppressed')
    ideal_checks=0
    if not errors:
        # Derive levels from actual A/Y/OE/power/source-series conductor paths.
        for powered in (False,True):
            for enable in (0,1):
                for bit in (0,1):
                    actual=physical_ideal_outputs(d,{p[0]:bit for p in required},powered,enable)
                    for inp,out,bank,ref,a,y,oe in found:
                        wanted=bit if powered and (bank=='A' or enable==1) else None
                        check(actual[out]==wanted,'Ideal physical channel/high-Z policy differs: '+out);ideal_checks+=1
        idle_inputs=physical_startup_inputs(d)
        idle_outputs=physical_ideal_outputs(d,idle_inputs,True,1)
        for inp,out,bank,ref,a,y,oe in found:
            check(idle_outputs[out]==(1 if out.startswith('EN') else 0),'Startup idle meaning differs');ideal_checks+=1
    numerical=static_bias_screen(parts);check(numerical['passed_static_inactive_threshold_screen'],'Staticbiasthresholdscreenfailed')
    return {'passed':not errors,'errors':errors,'checks':checks,'host_ideal_digital_checks':ideal_checks,
        'motor_paths':36,'TX_paths':2,'bank_A_paths':25,'bank_B_paths':13,'physical_parts':124,
        'evidence_class':'primary source + native netlist/ERC + host ideal digital + static numerical screening',
        'static_bias_screen':numerical,'physical_measurement':False,'complete_MC_isolation':False,
        'manufacturing_ready':False,'open_gates':d.get('open_gates',[])}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);args=parser.parse_args()
    report=validate()
    if args.output:args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2));raise SystemExit(0 if report['passed'] else 1)
