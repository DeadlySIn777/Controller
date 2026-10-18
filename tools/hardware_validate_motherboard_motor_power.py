"""Independent native-net and bounded voltage-window review.

Expected component topology and bounds are authored independently of the
generator. Native ERC, host tests, static corners and physical timing differ.
"""
from collections import defaultdict
import hashlib
from itertools import product
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'hardware/motherboard_motor_power'
RFP = 'Resistor_SMD:R_0603_1608Metric'
CFP = 'Capacitor_SMD:C_0603_1608Metric'
RAIL_ROWS = [
    ('MOTOR_5V_A',87900,92100,4.85,5.15,4.95,5.05),
    ('IO_3V3',54500,57500,3.2,3.4,3.25875,3.34125),
    ('MOTOR_5V_B',87900,92100,4.85,5.15,4.95,5.05),
    ('IO_3V3',54500,57500,3.2,3.4,3.25875,3.34125),
    ('AUX_5V_A',86700,93100,4.8,5.25,4.875,5.075),
    ('AUX_24V_A',355000,580000,18,30,19,29),
    ('AUX_5V_B',86700,93100,4.8,5.25,4.875,5.075),
    ('AUX_24V_B',355000,580000,18,30,19,29),
]


def expected_circuit():
    nets=defaultdict(set);parts={};r=9000;c=9000
    def part(ref,value,mpn,fp,pins,physical=True):
        parts[ref]={'value':value,'mpn':mpn,'footprint':fp,'physical':physical,'pins':{str(k):v for k,v in pins.items()}}
        for k,v in pins.items():
            net=v if v is not None else f'unconnected-({ref}-'+('NC' if ref!='U9008' else 'unused')+f'-Pad{k})'
            nets[net].add((ref,str(k)))
    def resistor(a,b,ohms,precision=False):
        nonlocal r
        r+=1;ref=f'R{r}'
        codes={87900:'8792',92100:'9212',54500:'5452',57500:'5752',86700:'8672',93100:'9312',355000:'3553',580000:'5803',10000:'1002'}
        mpn='PLT0603Z'+codes[ohms]+'LST1' if precision else {1000:'CRCW06031K00FKEA',10000:'CRCW060310K0FKEA',100000:'CRCW0603100KFKEA'}[ohms]
        part(ref,f'{ohms}R '+('0.01% 5ppm' if precision else '1% 100ppm'),mpn,RFP,{1:a,2:b})
    def capacitor(a,b):
        nonlocal c
        c+=1;part(f'C{c}','100nF 100V X7R 10%','GRM188R72A104KA35D',CFP,{1:a,2:b})
    for i,(domain,bank,supply,ground) in enumerate((('LOGIC','A','CORE_5V','LOGIC_GND'),('LOGIC','B','CORE_5V','LOGIC_GND'),('FIELD','A','FIELD_5V','FIELD_GND'),('FIELD','B','FIELD_5V','FIELD_GND'))):
        ref=f'U{9001+i}';vref=f'MOTOR_PWR_REF_{domain}_{bank}';raw=f'MOTOR_{domain}_HEALTH_{bank}_RAW'
        pins={1:supply,2:supply,3:ground,4:supply,5:vref,6:vref,7:ground,8:vref,9:ground,10:supply,11:ground,12:raw,17:ground}
        for j,(rail,uv,ov,*_) in enumerate(RAIL_ROWS[i*2:i*2+2]):
            uvnet=f'MOTOR_PWR_{domain}_{bank}_{j}_UV';ovnet=f'MOTOR_PWR_{domain}_{bank}_{j}_OV'
            pins[16-j*2]=uvnet;pins[15-j*2]=ovnet
            resistor(rail,uvnet,uv,True);resistor(uvnet,ground,10000,True)
            resistor(rail,ovnet,ov,True);resistor(ovnet,ground,10000,True)
        part(ref,'LTC2962HUD#PBF','LTC2962HUD#PBF','CNC_MotorPower:LTC2962_UD16',pins)
        resistor(supply,raw,10000);resistor(raw,ground,100000);capacitor(supply,ground)
    for i,bank in enumerate(('A','B')):
        part(f'U{9005+i}','SN74LVC1G17DBVR','SN74LVC1G17DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:None,2:f'MOTOR_LOGIC_HEALTH_{bank}_RAW',3:'LOGIC_GND',4:f'MOTOR_LOGIC_HEALTH_{bank}',5:'IO_3V3'})
        resistor(f'MOTOR_LOGIC_HEALTH_{bank}','LOGIC_GND',10000);capacitor('IO_3V3','LOGIC_GND')
    part('U9007','ISO7720FDWR','ISO7720FDWR','CNC_MotorPower:ISO7720_DW16_TI_HV',{1:'FIELD_GND',2:None,3:'FIELD_5V',4:'MOTOR_FIELD_HEALTH_A_RAW',5:'MOTOR_FIELD_HEALTH_B_RAW',6:None,7:'FIELD_GND',8:None,9:'LOGIC_GND',10:None,11:None,12:'MOTOR_FIELD_HEALTH_B_ISOLATED',13:'MOTOR_FIELD_HEALTH_A_ISOLATED',14:'IO_3V3',15:None,16:'LOGIC_GND'})
    capacitor('FIELD_5V','FIELD_GND');capacitor('IO_3V3','LOGIC_GND')
    for bank in ('A','B'):resistor(f'MOTOR_FIELD_HEALTH_{bank}_ISOLATED','LOGIC_GND',10000)
    part('U9008','SN74LVC2G08DCUR','SN74LVC2G08DCUR','Package_SO:VSSOP-8_2.3x2mm_P0.5mm',{1:'MOTOR_LOGIC_HEALTH_A',2:'MOTOR_FIELD_HEALTH_A_ISOLATED',3:'MOTOR_POWER_OK_B_QUALIFIED',4:'LOGIC_GND',5:'MOTOR_LOGIC_HEALTH_B',6:'MOTOR_FIELD_HEALTH_B_ISOLATED',7:'MOTOR_POWER_OK_A_QUALIFIED',8:'IO_3V3'})
    capacitor('IO_3V3','LOGIC_GND')
    for bank in ('A','B'):resistor(f'MOTOR_POWER_OK_{bank}_QUALIFIED','LOGIC_GND',1000)
    power=['CORE_5V','IO_3V3','LOGIC_GND','MOTOR_5V_A','MOTOR_5V_B','FIELD_5V','FIELD_GND','AUX_5V_A','AUX_5V_B','AUX_24V_A','AUX_24V_B']
    outputs=['MOTOR_POWER_OK_A_QUALIFIED','MOTOR_POWER_OK_B_QUALIFIED','MOTOR_LOGIC_HEALTH_A','MOTOR_LOGIC_HEALTH_B','MOTOR_FIELD_HEALTH_A_ISOLATED','MOTOR_FIELD_HEALTH_B_ISOLATED']
    for ref,rows in [('B9001',power),('B9002',outputs)]:part(ref,'INTERNAL REVIEW BOUNDARY','','',dict(enumerate(rows,1)),False)
    return dict(nets),parts,power,outputs


def analytical_screen(model=None):
    # Full H-grade resistor temperature excursion ±100 K is conservative for
    # the product0–55°C ambient.400ppm lifetime drift is a sensitivity allowance.
    tolerance=.0001+5e-6*100+.0004
    thresholds=[]
    for rail,uv,ov,lo,hi,reglo,reghi in RAIL_ROWS:
        limits=[]
        for top in (uv,ov):
            corners=[ref*(1+rt/rb)+ib*rt for ref,rt,rb,ib in product((.4975,.5025),(top*(1-tolerance),top*(1+tolerance)),(10000*(1-tolerance),10000*(1+tolerance)),(-15e-9,15e-9))]
            limits.append([min(corners),max(corners)])
        u,o=limits;margins=[u[0]-lo,reglo-u[1],o[0]-reghi,hi-o[1]]
        thresholds.append({'rail':rail,'uv_v':u,'ov_v':o,'static_margin_v':margins,'acceptance_v':[reglo,reghi],'requirement_v':[lo,hi],'static_bounds_pass':min(margins)>0})
    raw={}
    for domain,power_min,power_max,input_current in [('LOGIC',4.85,5.15,5e-6),('FIELD',4.925,5.075,10e-6)]:
        vals=[(vp/rp+ipu-ii)/(1/rp+1/rd) for vp,rp,rd,ipu,ii in product((power_min,power_max),(10000*.98,10000*1.02),(100000*.98,100000*1.02),(4e-6,10e-6),(-input_current,input_current))]
        raw[domain]={'released_v':[min(vals),max(vals)],'rst_sink_current_a_max':power_max/(10000*.98)+input_current,'rst_low_max_v_at_valid_vcc':.15,'input_leakage_spec_conditions_retained':True}
    # Frozen motor receivers fit a10k qualifier pull-down in parallel with this
    # block's1k. Each receiving AND input contributes≤5uA at table conditions.
    qload=3.4/(1000*.98)+3.4/(10000*.98)+5e-6
    return {'evidence_class':'bounded static corner and conditional logic arithmetic; no physical qualification','windows':thresholds,'precision_r_corner_fraction_including_drift':tolerance,'raw_health':raw,'logic_high_schmitt_outer_table_max_v':3.33,'schmitt_threshold_screen_basis':'Largest published VT+ maximum at listed1.65/2.3/3/4.5/5.5V test points; no interpolated3.3V threshold or timing bound','field_high_input_requirement_v':.7*5.075,'qualified_output_load_a_max':qload,'qualified_output_voh_min_v_at_3v_8ma':2.4,'qualified_receiving_vih_max_v':2,'qualified_high_margin_v':.4,'zero_core5_raw_logic_bias_v_with_powered_buffer_leak_allowance':(100e-9+5e-6)/(1/(10000*1.02)+1/(100000*1.02)),'zero_qualified_output_bias_v_with_10ua_ioff_and_5ua_receiving_allowance':15e-6/(1/(1000*1.02)+1/(10000*1.02)),'supervisor_fault_us_max_only_at_10pct_overdrive':40,'release_ms':[160,240],'iso7720_default_low_input_le1p7_output_ge2p25':True,'iso7720_supply_1p7_to2p25_undetermined':True,'arbitrary_partial_power_proven':False,'full_18_to30v_aux24_acceptance_proven':False,'supplies_or_limiters_fitted':False}


def native_net_inventory(tree):
    nets={}; seen=set(); errors=[]
    for row in tree.findall('.//nets/net'):
        name=re.sub(r'^(unconnected-\([^)]*\))-.*$',r'\1',row.attrib['name'].lstrip('/'))
        if name in nets:errors.append('Duplicate net '+name)
        nets[name]=set()
        for node in row.findall('node'):
            key=(node.attrib['ref'],node.attrib['pin'])
            if key in seen:errors.append('Repeated native pin '+str(key))
            seen.add(key);nets[name].add(key)
    return nets,seen,errors


def validate(tree,model,footprints=None):
    errors=[];expected,parts,power,outputs=expected_circuit();actual,seen,issues=native_net_inventory(tree);errors+=issues
    for net in sorted(set(actual)|set(expected)):
        if actual.get(net,set())!=expected.get(net,set()):errors.append('Net mismatch '+net)
    comps={c.attrib['ref']:c for c in tree.findall('.//components/comp')}
    if set(comps)!=set(parts):errors.append('Native component inventory changed')
    for ref,p in parts.items():
        c=comps.get(ref)
        if c is None:continue
        got={'value':c.findtext('value'),'mpn':c.findtext("./fields/field[@name='MPN']") or '', 'footprint':c.findtext('footprint') or ''}
        if got!={k:p[k] for k in got}:errors.append('Native value/MPN/package mismatch '+ref)
        source=model.get('components',{}).get(ref,{})
        if any(source.get(k)!=p[k] for k in ('value','mpn','footprint','physical','pins')):errors.append('Source component/pin mismatch '+ref)
        if source.get('kind')=='R':
            precision='PLT' in p['mpn'];tol=.0001 if precision else .01;tcr=5 if precision else 100
            if source.get('initial_tolerance')!=tol or source.get('tcr_ppm')!=tcr:errors.append('Resistor guarantee changed '+ref)
    if set(model.get('components',{}))!=set(parts):errors.append('Manifest component population changed')
    maps={
      'LTC2962':{1:('RDIS','input'),2:('MR','input'),3:('DVCC','power_in'),4:('VCC','power_in'),5:('REF','output'),6:('PG1','input'),7:('PG2','input'),8:('PG3','input'),9:('PG4','input'),10:('RT','input'),11:('GND','power_in'),12:('RST','open_collector'),13:('V4','input'),14:('V3','input'),15:('V2','input'),16:('V1','input'),17:('EP','power_in')},
      'ISO7720F':{1:('GND1','power_in'),2:('NC','no_connect'),3:('VCC1','power_in'),4:('INA','input'),5:('INB','input'),6:('NC','no_connect'),7:('GND1','power_in'),8:('NC','no_connect'),9:('GND2','power_in'),10:('NC','no_connect'),11:('NC','no_connect'),12:('OUTB','output'),13:('OUTA','output'),14:('VCC2','power_in'),15:('NC','no_connect'),16:('GND2','power_in')},
      'LVC1G17':{1:('NC','no_connect'),2:('A','input'),3:('GND','power_in'),4:('Y','output'),5:('VCC','power_in')},
      'LVC2G08':{1:('1A','input'),2:('1B','input'),3:('2Y','output'),4:('GND','power_in'),5:('2A','input'),6:('2B','input'),7:('1Y','output'),8:('VCC','power_in')}}
    for name,want in maps.items():
        got={int(p.attrib['num']):(p.attrib['name'],p.attrib['type']) for p in tree.findall(f".//libpart[@part='{name}']/pins/pin")}
        if got!=want:errors.append('Independent manufacturer pin function '+name)
    contract={'supervisor':'LTC2962 H-grade, VCC2.25–5.5V, DVCC grounded for open-drain','pg_modes':['+ADJ','-ADJ','+ADJ','-ADJ'],'release_ms':[160,240],'sense_v_threshold':[.4975,.5025],'sense_bias_max_a':15e-9,'precision_r_initial':.0001,'precision_r_tcr_ppm':5,'precision_r_temperature_excursion_c':100,'additional_precision_drift_fraction':.0004,'aux5_min_falling_trip_v':4.8,'aux24_inherited_requirement_v':[18,30],'aux24_static_acceptance_limit_v':[19,29],'field_logic_returns_joined':False,'gate_truth':'MOTOR_POWER_OK_bank = LOGIC_HEALTH_bank AND FIELD_HEALTH_bank_ISOLATED','core5_input_v':[4.85,5.15],'receiving_io3_input_v':[3.2,3.4],'io3_extra_bypass_nominal_uf':.5,'supervisor_tuv_max_us_at_10pct_overdrive':40,'isolator_default':'LOW with F suffix; input ≤1.7V/output ≥2.25V; 1.7–2.25V is undetermined','brownout_slew_or_fault_guaranteed':False}
    if model.get('contract')!=contract:errors.append('Unreviewed health contract change')
    if model.get('boundary_power')!=power or model.get('boundary_outputs')!=outputs or model.get('boundary_inputs')!=[]:errors.append('Boundary changed')
    if any(model.get(k) is not False for k in ('manufacturing_ready','physical_qualification','arbitrary_partial_power_qualified')):errors.append('Readiness or partial-power proof overstated')
    windows=model.get('windows',[])
    if len(windows)!=8:errors.append('Missing actual voltage window')
    else:
        for i,(row,(rail,uv,ov,lo,hi,reglow,reghigh)) in enumerate(zip(windows,RAIL_ROWS)):
            if row.get('rail')!=rail or row.get('requirement_limits_v')!=[lo,hi] or row.get('static_acceptance_v')!=[reglow,reghigh]:errors.append('Actual rail limits/acceptance changed '+str(i))
            if [(d.get('top_ohm'),d.get('bottom_ohm')) for d in row.get('dividers',[])]!=[(uv,10000),(ov,10000)]:errors.append('Window model disagrees with physical divider '+str(i))
    if footprints is not None:
        rows=re.findall(r'\(pad "(\d+)" smd roundrect \(at ([^ ]+) ([^)]+)\) \(size ([^ ]+) ([^)]+)\)',footprints.get('ISO7720_DW16_TI_HV',''))
        got={int(n):(float(x),float(y),float(sx),float(sy)) for n,x,y,sx,sy in rows}
        want={i+1:(-4.875,round(-4.445+i*1.27,4),1.65,.6) for i in range(8)}
        want.update({i+9:(4.875,round(4.445-i*1.27,4),1.65,.6) for i in range(8)})
        if got!=want or len(rows)!=16:errors.append('TI HV land-pattern copper changed')
        retained=(ROOT/'hardware/motion_card/CNC_MC_Power.pretty/LTC2962_UD16.kicad_mod').read_text(encoding='utf-8')
        if footprints.get('LTC2962_UD16')!=retained:errors.append('Retained LTC SMD/thermal copper or geometry changed')
    screen=analytical_screen()
    if not all(w['static_bounds_pass'] for w in screen['windows']):errors.append('Static threshold acceptance/detection margin failed')
    if screen['qualified_output_load_a_max']>.008:errors.append('Qualified AND output load exceeds guaranteed8mA condition')
    if screen['raw_health']['LOGIC']['released_v'][0]<3.33:errors.append('Logic health high fails outer published Schmitt threshold envelope')
    if screen['raw_health']['FIELD']['released_v'][0]<.7*5.075:errors.append('Field health high threshold not met')
    if max(v['rst_sink_current_a_max'] for v in screen['raw_health'].values())>.003:errors.append('Supervisor sink exceeds guaranteed3mA condition')
    return errors


def evaluate_actual_health(model,states):
    """Evaluate fitted gate graph at valid supplies only, not power transitions."""
    values={};component=model['components'];states=dict(states)
    for i,(domain,bank) in enumerate((('LOGIC','A'),('LOGIC','B'),('FIELD','A'),('FIELD','B'))):
        p=component[f'U{9001+i}']['pins']
        good=all(states[w['rail']] for w in model['windows'] if w['supervisor']==f'U{9001+i}')
        values[p['12']]=good
    for ref in ('U9005','U9006'):
        p=component[ref]['pins'];values[p['4']]=values[p['2']]
    iso=component['U9007']['pins']
    values[iso['13']]=values[iso['4']] and states['FIELD_5V'];values[iso['12']]=values[iso['5']] and states['FIELD_5V']
    gate=component['U9008']['pins']
    values[gate['7']]=values[gate['1']] and values[gate['2']]
    values[gate['3']]=values[gate['5']] and values[gate['6']]
    return {f'MOTOR_POWER_OK_{b}_QUALIFIED':values[f'MOTOR_POWER_OK_{b}_QUALIFIED'] for b in ('A','B')}


def main():
    model=json.loads((OUT/'design.json').read_text(encoding='utf-8'));tree=ET.parse(OUT/'netlist.xml')
    fps={p.stem:p.read_text(encoding='utf-8') for p in (OUT/'CNC_MotorPower.pretty').glob('*.kicad_mod')}
    errors=validate(tree,model,fps)
    for p,want in model['source_sha256'].items():
        if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=want:errors.append('Reviewed source changed '+p)
    erc=json.loads((OUT/'erc.json').read_text(encoding='utf-8'));violations=[v for s in erc['sheets'] for v in s['violations']]
    if violations:errors.append('Native ERC violations '+str(len(violations)))
    if erc.get('ignored_checks')!=[]:errors.append('ERC ignored-check list is not empty')
    _,seen,issues=native_net_inventory(tree)
    result={'schema_version':1,'consistency_pass':not errors,'errors':errors,'physical_parts':sum(p['physical'] for p in model['components'].values()),'native_pin_assignments':len(seen),'declared_nc_pins':sum(v is None for p in model['components'].values() for v in p['pins'].values()),'native_erc_violations':len(violations),'erc_ignored_checks':erc['ignored_checks'],'kicad_version':erc['kicad_version'],'analytical_screen':analytical_screen(),'manufacturing_ready':False,'physical_qualification':False,'scope':'Actual voltage-window health circuit; source/netlist/ERC only; no converter/limiter or full power-transition qualification','open_gates':model['open_gates']}
    (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2));raise SystemExit(bool(errors))


if __name__=='__main__':main()
