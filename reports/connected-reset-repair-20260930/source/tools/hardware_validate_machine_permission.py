"""Independent net contract and event model. No physical or safety qualification."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/machine_permission'
PARTS={
 'U1':('TPS3431SDRBR','CNC_Permit:TPS3431_DRB8'),
 'U2':('SN74LVC2G17DBVR','Package_TO_SOT_SMD:SOT-23-6'),
 'U3':('SN74LVC1G34DBVR','Package_TO_SOT_SMD:SOT-23-5'),
 'U4':('SN74LVC1G11DBVR','Package_TO_SOT_SMD:SOT-23-6'),
 'U5':('SN74LVC2G08DCUR','Package_SO:VSSOP-8_2.3x2mm_P0.5mm'),
 'U6':('SN74LVC2G74DCUR','Package_SO:VSSOP-8_2.3x2mm_P0.5mm'),
 'U7':('SN74LVC1G11DBVR','Package_TO_SOT_SMD:SOT-23-6')}
PINS={
 'TPS3431':{'1':('VDD','power_in'),'2':('CWD','input'),'3':('EN','input'),'4':('GND','power_in'),
            '5':('SET1','input'),'6':('WDI','input'),'7':('WDO_N','open_collector'),'8':('ENOUT','open_collector'),'9':('EP','power_in')},
 'LVC2G17':{'1':('1A','input'),'2':('GND','power_in'),'3':('2A','input'),'4':('2Y','output'),'5':('VCC','power_in'),'6':('1Y','output')},
 'LVC1G34':{'1':('NC','no_connect'),'2':('A','input'),'3':('GND','power_in'),'4':('Y','output'),'5':('VCC','power_in')},
 'LVC1G11':{'1':('A','input'),'2':('GND','power_in'),'3':('B','input'),'4':('Y','output'),'5':('VCC','power_in'),'6':('C','input')},
 'LVC2G08':{'1':('1A','input'),'2':('1B','input'),'3':('2Y','output'),'4':('GND','power_in'),'5':('2A','input'),'6':('2B','input'),'7':('1Y','output'),'8':('VCC','power_in')},
 'LVC2G74':{'1':('CLK','input'),'2':('D','input'),'3':('Q_N','output'),'4':('GND','power_in'),'5':('Q','output'),'6':('CLR_N','input'),'7':('PRE_N','input'),'8':('VCC','power_in')}}
CHIPNETS={
 'U1':('IO_3V3','WD_CWD','IO_3V3','LOGIC_GND','IO_3V3','WD_INPUT_BUF','WD_HEALTH_RAW_N','WD_HEALTH_RAW_N','LOGIC_GND'),
 'U2':('WD_HEALTH_RAW_N','LOGIC_GND','FPGA_CDONE','CDONE_BUF','IO_3V3','WD_HEALTH_BUF'),
 'U3':('unconnected-(U3-NC-Pad1)','FPGA_PROGRESS_WDI','LOGIC_GND','WD_INPUT_BUF','IO_3V3'),
 'U4':('FPGA_LOCAL_RESET_N','LOGIC_GND','CDONE_BUF','BASE_INTERLOCK_OK','IO_3V3','EXT_PERMIT_3V3'),
 'U5':('BASE_INTERLOCK_OK','WD_HEALTH_BUF','LATCH_CLEAR_N','LOGIC_GND','HW_WATCHDOG_OK_N','FPGA_ENDPOINT_READY','HW_WATCHDOG_OK_N','IO_3V3'),
 'U6':('FPGA_MOTION_REQUEST','IO_3V3','unconnected-(U6-Q_N-Pad3)','LOGIC_GND','HW_PERMISSION_LATCHED','LATCH_CLEAR_N','IO_3V3','IO_3V3'),
 'U7':('HW_PERMISSION_LATCHED','LOGIC_GND','FPGA_MOTION_REQUEST','TX_PERMIT','IO_3V3','HW_WATCHDOG_OK_N')}
BOUNDARY={'JCTRL1':['IO_3V3','LOGIC_GND','FPGA_LOCAL_RESET_N','FPGA_CDONE','EXT_PERMIT_3V3','FPGA_ENDPOINT_READY','FPGA_MOTION_REQUEST','FPGA_PROGRESS_WDI'],
          'JOUT1':['TX_PERMIT','HW_WATCHDOG_OK_N','HW_PERMISSION_LATCHED','WD_HEALTH_RAW_N','LOGIC_GND']}
RESISTORS={
 'R1':('10k','10K0','IO_3V3','WD_HEALTH_RAW_N'),
 'R2':('100k','100K','WD_INPUT_BUF','LOGIC_GND'),
 'R3':('10k','10K0','FPGA_PROGRESS_WDI','LOGIC_GND'),
 'R4':('10k','10K0','FPGA_LOCAL_RESET_N','LOGIC_GND'),
 'R5':('10k','10K0','EXT_PERMIT_3V3','LOGIC_GND'),
 'R6':('10k','10K0','FPGA_ENDPOINT_READY','LOGIC_GND'),
 'R7':('10k','10K0','FPGA_MOTION_REQUEST','LOGIC_GND'),
 'R8':('10k','10K0','LATCH_CLEAR_N','LOGIC_GND'),
 'R9':('10k','10K0','HW_PERMISSION_LATCHED','LOGIC_GND'),
 'R10':('10k','10K0','TX_PERMIT','LOGIC_GND'),
 'R11':('10k','10K0','HW_WATCHDOG_OK_N','LOGIC_GND')}
WATCHDOG={'mpn':'TPS3431SDRBR','capacitor_pf':120,'cap_initial_tolerance':.05,'cap_temperature_allowance':.006,
 'cap_parasitic_allowance_pf':10,'timer_relative_error':.095,'reset_pulse_ms':[170,230],
 'falling_edge_only':True,'enabled_permanently':True,'nominal_timeout_ms':64.288}


def electrical_bounds():
    cmin=120*.95*.994;cmax=120*1.05*1.006
    return {'timing_cap_min_pf':cmin,'timing_cap_max_pf':cmax,
        'timeout_nominal_ms':77.4*.120+55,
        'timeout_fresh_ms':[(77.4*cmin/1000+55)*.905,(77.4*cmax/1000+55)*1.095],
        'timeout_with_10pf_parasitic_max_ms':(77.4*(cmax+10)/1000+55)*1.095,
        'parasitic_and_leakage_physically_verified':False,
        'tx_load_a_at3v4_seven_10k_min_and_six_1ua_inputs':7*3.4/(10000*.98)+6e-6,
        'tx_voh_bound_v_at_vcc_ge3v_load_le16ma':2.4,'tx_receiver_vih_v':2.0,
        'tx_off_v_with_10ua_ioff_six_1ua_inputs_and_all_pulldowns':16e-6*(10000*1.02/7),
        'wdi_load_a_100k_pd_and_20ua_allowance':3.4/(100000*.98)+20e-6,
        'wdi_voh_min_v_at100ua':3.2-.1,'wdi_required_high_max_v':.8*3.4,
        'additional_io3_reservation_a':.010,'io3_cap_max_uf':7*.1*1.2*1.15+(cmax+10)*1e-6}


class PermissionModel:
    """Event model of intended digital behavior; not SPICE or timed gate simulation.

    init_ms=.381 uses TI's typical CWD-evaluation value, NOT a maximum guarantee.
    Actual power transitions/metastability are expressly outside this model.
    """
    def __init__(self,timeout_ms=None,reset_ms=200,init_ms=.381):
        self.timeout=64.288 if timeout_ms is None else timeout_ms
        self.reset_ms=reset_ms;self.now=0;self.event=init_ms;self.state='initializing'
        self.inputs={'reset':False,'cdone':False,'external':False,'ready':False,'request':False,'wdi':False}
        self.previous_request=False;self.q=False;self.raw=False;self.tx=False;self.trace=[]
        self._evaluate('initial')

    def _evaluate(self,reason):
        s=self.inputs
        self.raw=self.state=='watching' and s['reset'] and s['cdone'] and s['external']
        clear=self.raw and s['ready']
        if not clear:self.q=False
        elif s['request'] and not self.previous_request:self.q=True
        self.previous_request=s['request']
        self.tx=self.q and s['request'] and self.raw
        self.trace.append({'ms':round(self.now,9),'reason':reason,'watchdog':self.state,
            'raw_inhibit_n':self.raw,'latch_q':self.q,'tx_permit':self.tx,'inputs':dict(s)})

    def advance(self,when):
        if when<self.now:raise ValueError('time cannot move backwards')
        while self.event<=when:
            self.now=self.event
            if self.state=='watching':self.state='reset_pulse';self.event=self.now+self.reset_ms
            else:self.state='watching';self.event=self.now+self.timeout
            self._evaluate('watchdog transition')
        self.now=when

    def set(self,when,**inputs):
        if set(inputs)-set(self.inputs):raise ValueError('unknown signal')
        if any(type(v) is not bool for v in inputs.values()):raise ValueError('digital values required')
        self.advance(when);old=self.inputs['wdi'];self.inputs.update(inputs)
        if old and not self.inputs['wdi'] and self.state=='watching':self.event=self.now+self.timeout
        self._evaluate('input change')


def demonstration_trace():
    m=PermissionModel();m.set(1,reset=True,cdone=True,external=True)
    m.set(2,ready=True);m.set(3,request=True)
    m.set(4,wdi=True);m.set(5,wdi=False)
    m.advance(70);m.set(71,ready=False,request=False)
    m.set(100,wdi=True);m.set(101,wdi=False) # ignored during fixed reset pulse
    m.advance(270);m.set(271,wdi=True);m.set(272,wdi=False)
    m.set(273,ready=True);m.set(274,request=True)
    m.set(275,external=False);m.set(276,external=True)
    # Clock/request still high: cleared latch cannot resume itself.
    m.set(277,wdi=True);m.set(278,wdi=False)
    m.set(279,request=False);m.set(280,request=True)
    return m.trace


def validate(tree,model,footprint_text=None):
    errors=[];expected=defaultdict(set);wanted={}
    def wire(net,ref,pin):expected[net].add((ref,str(pin)))
    for ref,nets in CHIPNETS.items():
        for pin,net in enumerate(nets,1):wire(net,ref,pin)
        mpn,fp=PARTS[ref];wanted[ref]={'value':mpn,'mpn':mpn,'footprint':fp}
    for ref,(value,code,top,bottom) in RESISTORS.items():
        wire(top,ref,1);wire(bottom,ref,2)
        wanted[ref]={'value':value+' 1%','mpn':'CRCW0603'+code+'FKEA','footprint':'Resistor_SMD:R_0603_1608Metric'}
    for i in range(1,9):
        ref=f'C{i}';wire('WD_CWD' if i==1 else 'IO_3V3',ref,1);wire('LOGIC_GND',ref,2)
        wanted[ref]={'value':'120pF C0G 50V 5%' if i==1 else '100nF X7R 25V 20%',
                    'mpn':'GRM1885C1H121JA01D' if i==1 else '',
                    'footprint':'Capacitor_SMD:C_0603_1608Metric'}
    for ref,nets in BOUNDARY.items():
        for pin,net in enumerate(nets,1):wire(net,ref,pin)
        wanted[ref]={'value':'INTERNAL BOUNDARY','mpn':'','footprint':''}
    actual={};seen=set()
    for net in tree.findall('.//nets/net'):
        name=re.sub(r'^(unconnected-\([^)]*\))-.*$',r'\1',net.attrib['name'].lstrip('/'))
        if name in actual:errors.append('Duplicate net: '+name)
        actual[name]=set()
        for node in net.findall('node'):
            pair=(node.attrib['ref'],node.attrib['pin'])
            if pair in seen:errors.append('Repeated pin: '+str(pair))
            seen.add(pair);actual[name].add(pair)
    for name in set(expected)|set(actual):
        if expected.get(name,set())!=actual.get(name,set()):errors.append('Net mismatch: '+name)
    comps=tree.findall('.//components/comp')
    if len(comps)!=len(wanted) or {c.attrib['ref'] for c in comps}!=set(wanted):errors.append('Component set mismatch')
    for comp in comps:
        data={'value':comp.findtext('value'),'mpn':comp.findtext("./fields/field[@name='MPN']") or '',
              'footprint':comp.findtext('footprint') or ''}
        if data!=wanted.get(comp.attrib['ref']):errors.append('Part value/package mismatch: '+comp.attrib['ref'])
        if any(p.attrib.get('name','').lower()=='dnp' for p in comp.findall('property')):errors.append('Required part DNP')
    for name,pins in PINS.items():
        rows=tree.findall(f".//libpart[@part='{name}']/pins/pin")
        if len(rows)!=len(pins) or {p.attrib['num']:(p.attrib['name'],p.attrib['type']) for p in rows}!=pins:
            errors.append('Pin functions differ: '+name)
    checks={'schema_version':1,'manufacturing_ready':False,'minimum_motor_requirement':8,'expansion_motor_requirement':12,
        'historical_ledger_used_only_for_rail_reference':True,'boundary':BOUNDARY,'parts':wanted,'watchdog':WATCHDOG,
        'unproven':['physical_edge_timing','power_transition_behavior','watchdog_pin_leakage','actual_cap_parasitic_and_leakage',
          'full_temperature_schmitt_interpolation','async_clear_recovery_metastability','external_permit_frontend',
          'single_component_fault_coverage','machine_stop_response','production_cost']}
    for key,value in checks.items():
        if model.get(key)!=value:errors.append('Unreviewed model: '+key)
    if footprint_text is not None:
        padrows=re.findall(r'\(pad "(\d+)" smd roundrect \(at ([^ ]+) ([^)]+)\) \(size ([^ ]+) ([^)]+)\)',footprint_text)
        target={str(i+1):(-1.4,-.975+i*.65,.6,.31) for i in range(4)}
        target.update({str(i+5):(1.4,.975-i*.65,.6,.31) for i in range(4)});target['9']=(0,0,1.5,1.75)
        got={p[0]:tuple(float(x) for x in p[1:]) for p in padrows}
        if len(padrows)!=9 or got!=target:errors.append('DRB contact pad map differs')
    bounds=electrical_bounds()
    if bounds['timing_cap_min_pf']<100:errors.append('Timing capacitor outside tested lower bound')
    if bounds['tx_load_a_at3v4_seven_10k_min_and_six_1ua_inputs']>.016:errors.append('TX output too heavily loaded')
    if bounds['wdi_load_a_100k_pd_and_20ua_allowance']>100e-6:errors.append('WDI VOH light-load proof invalid')
    return sorted(errors)


def main():
    tree=ET.parse(OUT/'netlist.xml');model=json.loads((OUT/'design-envelope.json').read_text())
    fp=(OUT/'CNC_Permit.pretty/TPS3431_DRB8.kicad_mod').read_text();errors=validate(tree,model,fp)
    if model['source_ledger_sha256']!=hashlib.sha256((OUT/'input-electrical-design.json').read_bytes()).hexdigest():errors.append('Frozen ledger hash differs')
    erc=json.loads((OUT/'erc.json').read_text());violations=[v for s in erc['sheets'] for v in s['violations']]
    if violations:errors.append(f'ERC violations: {len(violations)}')
    (OUT/'behavior-trace.json').write_text(json.dumps({'scope':'Boolean/event study; no transistor timing or RTL execution','trace':demonstration_trace()},indent=2)+'\n')
    paths=[ROOT/p for p in ('tools/hardware_build_machine_permission.py','tools/hardware_validate_machine_permission.py',
        'tools/hardware_build_tx_schematic.py','tools/hardware_build_logic_power.py','tests/test_machine_permission.py','reports/MACHINE_PERMISSION.md')]
    paths += [p for p in OUT.rglob('*') if p.is_file() and p.name!='validation.json' and p.suffix!='.kicad_prl']
    paths += [p for p in (ROOT/'research/machine-permission').rglob('*') if p.is_file()]
    result={'schema_version':1,'consistency_pass':not errors,'manufacturing_ready':False,'errors':errors,
      'component_count':len(tree.findall('.//components/comp')),'net_count':len(tree.findall('.//nets/net')),
      'electrical_bounds':electrical_bounds(),'kicad_version':erc['kicad_version'],'erc_violations':len(violations),
      'erc_ignored_checks':erc['ignored_checks'],
      'source_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths) if p.exists()}}
    (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f"Machine permission: {'PASS' if not errors else 'FAIL'}; {len(errors)} issues; manufacture blocked")
    for e in errors:print(e)
    return bool(errors)


if __name__=='__main__':sys.exit(main())
