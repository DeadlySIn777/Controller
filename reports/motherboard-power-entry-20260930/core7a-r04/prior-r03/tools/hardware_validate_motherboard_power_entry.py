"""Native connectivity, physical supply paths and independent inhibit contracts.

Arithmetic screens retain their exact datasheet test conditions. They are not
physical or full-temperature proof and never confer fabrication readiness.
"""
from collections import Counter
import hashlib
from itertools import product
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/motherboard_power_entry'
REPORT=ROOT/'reports/motherboard-power-entry-20260930'

# Independently transcribed primary pin-function records. Reviewed converter
# source libraries are retained and hash checked; new IC maps are checked here.
PRIMARY_FUNCTIONS={
 'MAIN':{1:'IN',2:'IN',3:'BGATE',4:'DRV',5:'IN_SYS',6:'UVLO',7:'OVP',8:'GND',9:'DVDT',10:'ILIM',11:'MODE',12:'SHDN',13:'IMON',14:'FLT_N',15:'PGTH',16:'PGOOD',17:'OUT',18:'OUT',19:'NC',20:'NC',21:'NC',22:'NC',23:'NC',24:'NC',25:'EP_GND'},
 'AUX24':{1:'IN',2:'UVLO',3:'OVP',4:'SHDN',5:'RTN',6:'GND',7:'ILIM',8:'DVDT',9:'FLT_N',10:'OUT',11:'EP_RTN'},
 'AUX5':{1:'IN',2:'GND',3:'EN',4:'FAULT_N',5:'ILIM',6:'OUT'},
 'FEED':{1:'CT',2:'NC',3:'VIN',4:'VBIAS',5:'ON',6:'GND',7:'PG',8:'OUT',9:'OUT',10:'OUT',11:'EP_VIN'},
 'FIELD_LDO':{1:'OUT',2:'DNC',3:'PG',4:'GND',5:'EN',6:'NC',7:'DELAY',8:'IN',9:'EP_GND'},
 'LVC2G04':{1:'1A',2:'GND',3:'2A',4:'2Y',5:'VCC',6:'1Y'},
 'LVC2G07':{1:'1A',2:'GND',3:'2A',4:'2Y',5:'VCC',6:'1Y'},
 'TLP3640A':{1:'A',2:'K',3:'D',4:'D'},
 'AHCT1G17':{1:'NC',2:'A',3:'GND',4:'Y',5:'VCC'},
 'LVC1G74':{1:'CLK',2:'D',3:'Q_N',4:'GND',5:'Q',6:'CLR_N',7:'PRE_N',8:'VCC'},
 'QREV':{1:'S1',2:'S2',3:'S3',4:'G',5:'D5_8_AND_LAND'},
 'Q':{1:'G',2:'S',3:'D'},
}

def rows(model,kind):
    return [(r,p) for r,p in model['components'].items() if p['kind']==kind and p['physical']]

def connected_resistors(model,a,b):
    return [(r,p) for r,p in rows(model,'R') if set(p['pins'].values())=={a,b}]

def resistor(model,a,b,value):
    return any(p.get('resistance_ohm')==value for _,p in connected_resistors(model,a,b))

def expected_pins(errors,ref,pins,wanted):
    if pins!={str(k):v for k,v in wanted.items()}:errors.append('Independent topology '+ref)

def validate(model,tree):
    errors=[];parts=model['components'];actual={};nc=set();seen=set()
    for net in tree.findall('.//nets/net'):
        name=net.get('name').lstrip('/')
        for node in net.findall('node'):
            key=(node.get('ref'),node.get('pin'))
            if key in seen:errors.append('Duplicate native pin '+str(key))
            seen.add(key)
            if name.startswith('unconnected-'):nc.add(key)
            else:actual[key]=name
    wanted={};wanted_nc=set()
    for ref,p in parts.items():
        for pin,net in p['pins'].items():
            if net is None:wanted_nc.add((ref,pin))
            else:wanted[(ref,pin)]=net
    if actual!=wanted:errors.append('Native pin/net inventory differs from source (including aliases)')
    if nc!=wanted_nc:errors.append('Native NC inventory differs')
    comps={r.get('ref'):r for r in tree.findall('.//components/comp')}
    if set(comps)!=set(parts):errors.append('Native component population differs')
    for ref,p in parts.items():
        native=comps.get(ref)
        if native is None:continue
        for field,path in [('value','value'),('mpn',"fields/field[@name='MPN']"),('footprint','footprint')]:
            if (native.findtext(path) or '')!=p[field]:errors.append('Native component property '+ref+' '+field)
    for kind,pins in PRIMARY_FUNCTIONS.items():
        lib=tree.find(".//libpart[@part='"+kind+"']")
        if lib is None:errors.append('Missing native IC function record '+kind);continue
        actual_functions={int(x.get('num')):x.get('name') for x in lib.findall('pins/pin')}
        if actual_functions!=pins:errors.append('Independent manufacturer pin function '+kind)
    counts=Counter(p['kind'] for p in parts.values() if p['physical'])
    for ref,p in parts.items():
        if p['physical'] and (not p['mpn'] or not p['footprint'] or p.get('selection_required')):errors.append('Unselected purchasing component '+ref)
    required={'MAIN':3,'QREV':3,'Q':3,'F':3,'L':3,'CORE_LM70660RRXR':1,'MOTION_LM70660RRXR':1,'FIELD_LMR36506R5RPER':1,'FEED':3,'AUX5':2,'AUX24':2,'FIELD_LDO':2,'LVC2G04':2,'LVC2G07':2,'TLP3640A':8,'AHCT1G17':2,'LVC1G74':2}
    for kind,count in required.items():
        if counts[kind]!=count:errors.append('Required fitted supply/inhibit population '+kind)
    # Actual entry chain: connector->physical fuse->external reverse FET->eFuse.
    for prefix,inp,gnd,out in [('C','CORE_24V_INPUT','LOGIC_GND','CORE_24V_PROTECTED'),('FA','FIELD_A_24V_INPUT','FIELD_GND','FIELD_A_24V_PROTECTED'),('FB','FIELD_B_24V_INPUT','FIELD_B_0V','FIELD_B_24V_PROTECTED')]:
        ps=[(r,p) for r,p in rows(model,'MAIN') if p['pins'].get('5')==prefix+'_RAW']
        if len(ps)!=1:errors.append('Missing actual entry '+prefix);continue
        ref,p=ps[0]
        expected_pins(errors,ref,p['pins'],{1:prefix+'_IN',2:prefix+'_IN',3:prefix+'_BGATE',4:prefix+'_DRV',5:prefix+'_RAW',6:prefix+'_UV',7:prefix+'_OV',8:gnd,9:prefix+'_DVDT',10:prefix+'_ILIM',11:None,12:prefix+'_SHDN',13:prefix+'_IMON',14:prefix+'_FAULT_N',15:prefix+'_PGTH',16:prefix+'_PGOOD',17:out,18:out,25:gnd,**{i:None for i in range(19,25)}})
        if not any(x['pins']=={'1':inp,'2':prefix+'_RAW'} for _,x in rows(model,'F')):errors.append('No physical fuse '+prefix)
        if not any(x['pins']=={'1':prefix+'_RAW','2':prefix+'_RAW','3':prefix+'_RAW','4':prefix+'_BGATE','5':prefix+'_IN'} for _,x in rows(model,'QREV')):errors.append('Reverse FET source/drain swapped '+prefix)
        if not resistor(model,prefix+'_ILIM',gnd,4020 if prefix=='C' else 3000):errors.append('Entry current setting '+prefix)
    # A real inductor/shunt path supplies each buck output, not a flag.
    for domain,out in [('CORE','CORE_5V'),('MOTION','MOTION_5V_RAW')]:
        ref,p=rows(model,domain+'_LM70660RRXR')[0];pins=p['pins']
        if not all(pins[str(i)]=='CORE_24V_PROTECTED' for i in (1,2,3,27,28,29)):errors.append('Buck input '+domain)
        if pins['6']!=out or pins['12']!=out or pins['16']!=domain+'_CORE_FB_SELECT':errors.append('Fixed5V buck mode/sense '+domain)
        if not any(x['pins']=={'1':domain+'_CORE_SW','2':domain+'_CORE_ISNS'} for _,x in rows(model,'L')):errors.append('Missing buck inductor '+domain)
        if not resistor(model,domain+'_CORE_ISNS',out,.006):errors.append('Missing6mohm buck shunt '+domain)
        if not all(pins[str(i)]==domain+'_CORE_SW' for i in (20,21,22)):errors.append('CommonSW lands disagree '+domain)
        if not all(pins[str(i)]=='LOGIC_GND' for i in (17,23,24,25,26,30)):errors.append('Buck ground lands disagree '+domain)
    ref,p=rows(model,'FIELD_LMR36506R5RPER')[0]
    expected_pins(errors,ref,p['pins'],{1:'FIELD_FIELD_VCC',2:'FIELD_FIELD_5V_PGOOD',3:'FA_PGOOD',4:'FIELD_A_24V_PROTECTED',5:'FIELD_FIELD_SW',6:'FIELD_FIELD_BOOT',7:'FIELD_FIELD_VCC',8:'FIELD_5V',9:'FIELD_GND'})
    if not any(x['pins']=={'1':'FIELD_FIELD_SW','2':'FIELD_5V'} for _,x in rows(model,'L')):errors.append('No actual FIELD5 inductor')
    for bank,ohm in [('A',26700),('B',44200)]:
        ps=[(r,p) for r,p in rows(model,'AUX24') if p['pins'].get('10')=='AUX_24V_'+bank]
        if len(ps)!=1:errors.append('Missing actual AUX24 limiter '+bank);continue
        ref,p=ps[0];rtn='AUX24_'+bank+'_RTN'
        expected_pins(errors,ref,p['pins'],{1:'FIELD_A_24V_PROTECTED',2:'AUX24_'+bank+'_UVLO',3:rtn,4:None,5:rtn,6:'FIELD_GND',7:'AUX24_'+bank+'_ILIM',8:'AUX24_'+bank+'_DVDT',9:'AUX24_'+bank+'_FAULT_N',10:'AUX_24V_'+bank,11:rtn})
        if p['mpn']!='TPS26624DRCR':errors.append('AUX24 latch/reverse variant '+bank)
        if not resistor(model,p['pins']['7'],rtn,ohm):errors.append('Unpublished AUX24 current point '+bank)
        if not resistor(model,'FIELD_A_24V_PROTECTED',p['pins']['2'],1000000):errors.append('Missing UVLO pin-current limiter '+bank)
        if connected_resistors(model,rtn,'FIELD_GND'):errors.append('Forbidden RTN/GND bridge '+bank)
    for bank,gnd,inp,out in [('A','FIELD_GND','FIELD_A_24V_PROTECTED','DOA_FIELD_3V3'),('B','FIELD_B_0V','FIELD_B_24V_PROTECTED','DOB_FIELD_3V3')]:
        ref,p=next((r,p) for r,p in rows(model,'FIELD_LDO') if p['pins'].get('1')==out)
        expected_pins(errors,ref,p['pins'],{1:out,2:None,3:None,4:gnd,5:inp,6:None,7:None,8:inp,9:gnd})
        if p['mpn']!='TPS7A1633DGNR':errors.append('Wrong fixed fieldLDO '+bank)
    # Independently authored pin-level blanking and sticky-feed checks.
    for domain,rail,gnd,health in [('CORE','CORE_5V','LOGIC_GND',['MC_RAILS_OK_5V']*2),('FIELD','FIELD_5V','FIELD_GND',['MOTOR_FIELD_HEALTH_A_RAW','MOTOR_FIELD_HEALTH_B_RAW'])]:
        inv=next((r,p) for r,p in rows(model,'LVC2G04') if p['pins']['5']==rail)
        sink=next((r,p) for r,p in rows(model,'LVC2G07') if p['pins']['5']==rail)
        expected_pins(errors,inv[0],inv[1]['pins'],{1:health[0],2:gnd,3:health[1],4:domain+'_HEALTH_B_N',5:rail,6:domain+'_HEALTH_A_N'})
        expected_pins(errors,sink[0],sink[1]['pins'],{1:domain+'_HEALTH_A_N',2:gnd,3:domain+'_HEALTH_B_N',4:domain+'_HEALTH_B_LED_K',5:rail,6:domain+'_HEALTH_A_LED_K'})
        if inv[1]['mpn']!='74LVC2G04GW,125' or sink[1]['mpn']!='74LVC2G07GW,125':errors.append('Unreviewed LED driver substitution '+domain)
        for bank in ('A','B'):
            if not resistor(model,rail,domain+'_HEALTH_'+bank+'_LED_A',120):errors.append('NO series LED current resistance '+domain+bank)
            contacts=[p for _,p in rows(model,'TLP3640A') if p.get('bank')==bank and p['pins']['1'] in [domain+'_HEALTH_'+bank+'_LED_A',domain+'_HEALTH_'+bank+'_LED_MID']]
            if len(contacts)!=2:errors.append('Missing separate clear/directgate contacts '+domain+bank);continue
            if any(p['mpn']!='TLP3640A(TPL,E' for p in contacts):errors.append('NO contact variant changed '+domain+bank)
            expected_led={(domain+'_HEALTH_'+bank+'_LED_A',domain+'_HEALTH_'+bank+'_LED_MID'),(domain+'_HEALTH_'+bank+'_LED_MID',domain+'_HEALTH_'+bank+'_LED_K')}
            if {(p['pins']['1'],p['pins']['2']) for p in contacts}!=expected_led:errors.append('Photocontact LED chain polarity '+domain+bank)
            signal=[p for p in contacts if p['pins']['1'].endswith('_LED_MID')][0]
            expected_signal={3:'MOTOR_TX_GATE_SOURCE_'+bank if domain=='CORE' else 'MOTOR_TX_GATE_CONTACT_MID_'+bank,4:'MOTOR_TX_GATE_CONTACT_MID_'+bank if domain=='CORE' else 'MOTOR_TX_GATE_'+bank}
            if any(signal['pins'][str(k)]!=v for k,v in expected_signal.items()):errors.append('Direct gate bypass/isolation '+domain+bank)
    for bank in ('A','B'):
        ref,p=next((r,p) for r,p in rows(model,'LVC1G74') if p.get('bank')==bank)
        expected_pins(errors,ref,p['pins'],{1:'MOTOR_FEED_REARM_'+bank,2:'MOTION_5V_RAW',3:None,4:'LOGIC_GND',5:'MOTOR_FEED_ON_'+bank,6:'MOTOR_FEED_CLEAR_N_'+bank,7:'MOTION_5V_RAW',8:'MOTION_5V_RAW'})
        if not resistor(model,'MOTOR_FEED_CLEAR_N_'+bank,'LOGIC_GND',100000):errors.append('Missing activeLOW clear default '+bank)
        if not resistor(model,'MOTOR_TX_GATE_'+bank,'LOGIC_GND',1000):errors.append('Missing finalgate independent default '+bank)
        if not resistor(model,'MOTOR_FEED_ON_'+bank,'LOGIC_GND',10000):errors.append('Missing bank feed ON default '+bank)
        if not resistor(model,'MOTOR_5V_'+bank,'LOGIC_GND',330):errors.append('Missing receiving rail bleed '+bank)
        ref,p=next((r,p) for r,p in rows(model,'FEED') if p['pins']['8']=='MOTOR_5V_'+bank)
        expected_pins(errors,ref,p['pins'],{1:None,2:None,3:'MOTION_5V_RAW',4:'MOTION_5V_RAW',5:'MOTOR_FEED_ON_'+bank,6:'LOGIC_GND',7:'MOTOR_FEED_PG_'+bank,8:'MOTOR_5V_'+bank,9:'MOTOR_5V_'+bank,10:'MOTOR_5V_'+bank,11:'MOTION_5V_RAW'})
    if any(model.get(k) is not False for k in ('manufacturing_ready','physical_qualification')):errors.append('Readiness overstated')
    if model['inherited_requirements']['field24_requirement_v']!=[18,30]:errors.append('Frozen field envelope silently narrowed')
    if model['inherited_requirements']['new_fpga_regulators'] or model['inherited_requirements']['new_voltage_monitors']:errors.append('Unnecessary duplicated core power/supervision')
    for p,h in model['source_hashes'].items():
        if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h:errors.append('Reviewed reused source changed '+p)
    return errors

def inhibit_screen():
    # Primary bounds: ToshibaVF1.5..1.8 at10mA, NOIFTmax3mA,
    # NOIFCmin.1mA, IOFFmax1uA at25C. Nexperia07VOLmax.55V at
    # VCC4.5V/32mA and -40..85C; IOZ/IOFF2uA at exact tableconditions.
    # 1% initial +100ppm/K *30K maximum departure from25C within0..55C.
    r_corner=.01+100e-6*30
    led_min=(4.8-2*1.8-.55)/(120*(1+r_corner))
    led_max=(5.25-2*1.5)/(120*(1-r_corner))
    gate_off_v=2e-6*1000*(1+r_corner)
    clear_off_v=2e-6*100000*(1+r_corner)
    gate_high_v=2.4/(1+.6/(1000*(1-r_corner)))
    clear_decay_s=100000*(1+r_corner)*1e-9*1.05*math.log((5.05-clear_off_v)/(.3*4.95-clear_off_v))
    return {'evidence':'Conditional source arithmetic; source rails valid4.8..5.25V, internal ambient0..55C; optical parameters only25C testconditions, no temperature/time interpolation',
      'series_led_current_a':[led_min,led_max], 'led_current_bounds_use_monotonic_diode_inference':True,
      'ordinary_resistor_corner_including_initial_and_0_to55c_tcr':r_corner,
      'led_trigger_max_a_at25c':.003,'led_return_min_a_at25c':.0001,
      'powered_ioz_a_max_at_vcc5p5':2e-6,'vcc0_ioff_a_max':2e-6,
      'powered_leakage_at_every_4p8_to5p25v_guaranteed_by_testpoint':False,
      'nexperia_driver_vcc_recommended_v':[1.65,5.5],
      'below1p65_partial_led_driver_state':'unspecified; opto turnoff through every arbitrary source-supply ramp is not guaranteed',
      'gate_off_v_with_two_contact_leaks':gate_off_v,
      'clear_off_v_with_two_contact_leaks':clear_off_v,
      'final_gate_high_min_v_at_2p4v_source_testpoint':gate_high_v,
      'am26c31_vih_v':2,'logic_receiving_vih_v':2,
      'contacts_toff_max_s_at25c_if5ma_rl200_vdd20':.0002,
      'contacts_ton_max_s_at25c_if5ma_rl200_vdd20':.0005,
      'opening_at_actual5p36_to18p94ma_or_alltemperatures_guaranteed':False,
      'clear_decay_s_to_vil':clear_decay_s,
      'contact_plus_clear_rc_conditional_withdrawal_s':.0002+clear_decay_s,
      'direct_gate_path_opens_before_rail_removal_is_required':True,
      'default_low_iso_partial_region_independently_inhibited_at_valid_health_source_rails':True,
      'whole20ms_watchdog_physical_or_allcondition_proof':False,
      'field_ldo_per_bank_reservation_a':.020,
      'field_ldo_estimated_w_at30v_3p234v_20ma':(30-3.234)*.020,
      'field_ldo_estimated_tj_at55c_66p2kperw':55+(30-3.234)*.020*66.2,
      'field_ldo_100ma_at30v_continuous_allowed':False,
      'aux24_overload_testpoints_a':{'A':[.237,.257],'B':[.145,.159]},
      'aux24_hardshort_max_guaranteed_at_fittedR':False}

def evaluate_graph(model,core_health,field_a,field_b,gate_a,gate_b):
    values={'MC_RAILS_OK_5V':core_health,'MOTOR_FIELD_HEALTH_A_RAW':field_a,'MOTOR_FIELD_HEALTH_B_RAW':field_b,'MOTOR_TX_GATE_SOURCE_A':gate_a,'MOTOR_TX_GATE_SOURCE_B':gate_b}
    for _,p in rows(model,'LVC2G04'):
        for ip,op in [('1','6'),('3','4')]:values[p['pins'][op]]=not values[p['pins'][ip]]
    led_active={}
    for _,p in rows(model,'LVC2G07'):
        for ip,op in [('1','6'),('3','4')]:led_active[p['pins'][op]]=not values[p['pins'][ip]]
    for domain in ('CORE','FIELD'):
        for bank in ('A','B'):values[domain+'_HEALTH_'+bank+'_LED_MID']=led_active[domain+'_HEALTH_'+bank+'_LED_K']
    for domain in ('CORE','FIELD'):
        for _,p in rows(model,'TLP3640A'):
            if p['pins']['1']!=domain+'_HEALTH_'+p['bank']+'_LED_MID':continue
            values[p['pins']['4']]=values[p['pins']['3']] and values[p['pins']['1']]
    return {f'MOTOR_TX_GATE_{b}':values[f'MOTOR_TX_GATE_{b}'] for b in ('A','B')}

def parent_interposition_rules():
    motor=json.loads((ROOT/'hardware/motherboard_motors/design.json').read_text())
    final={}
    for bank,pin in [('A','7'),('B','3')]:
        net='MOTOR_TX_GATE_'+bank
        consumers=sorted([r,k] for r,p in motor['components'].items() if p['physical'] for k,n in p['pins'].items() if n==net and (r,k)!=('U6042',pin))
        final[bank]={'old_driver':['U6042',pin],'old_driver_mpn':'SN74LVC2G08DCUR','new_driver_net':'MOTOR_TX_GATE_SOURCE_'+bank,'final_consumers_must_remain_exact':consumers,'frozen_motor_source_sha256':hashlib.sha256((ROOT/'hardware/motherboard_motors/design.json').read_bytes()).hexdigest()}
    return {'exactly_two_output_pin_changes_permitted':final,'no_wildcard_net_rename':True,'final_gate_inputs_and_source_gate_outputs_must_not_be_directly_joined':True,'raw_field_health_promotions':{'A':['U9003','12'],'B':['U9004','12']},'IO3_to_motorIO3_mapping':'Explicit whole-board power map only; no ground-domain aliases inferred.'}

def main():
    model=json.loads((OUT/'design.json').read_text());tree=ET.parse(OUT/'netlist.xml')
    errors=validate(model,tree);screen=inhibit_screen(); REPORT.mkdir(exist_ok=True)
    result={'passed':not errors,'errors':errors,'fitted_parts':sum(p['physical'] for p in model['components'].values()),'native_pins':sum(len(p['pins']) for p in model['components'].values()),'native_nc_pins':sum(n is None for p in model['components'].values() for n in p['pins'].values()),'source_engineering_gates':model['engineering_gates'],'conditional_screen':screen,'parent_interposition_rules':parent_interposition_rules(),'manufacturing_ready':False}
    (REPORT/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['passed','errors','fitted_parts','native_pins','native_nc_pins']}));return bool(errors)

if __name__=='__main__':raise SystemExit(main())
