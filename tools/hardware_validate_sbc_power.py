"""Independent SBC power connectivity and bounded arithmetic, no hardware access."""
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/sbc_power'

def num(d,k,lo=0,hi=1e6):
    x=d[k]
    if isinstance(x,bool) or not isinstance(x,(int,float)):raise ValueError(k+' must be numeric')
    try:x=float(x)
    except OverflowError as exc:raise ValueError(k+' outofrange') from exc
    if not math.isfinite(x) or not lo<=x<=hi:raise ValueError(k+' outofrange')
    return x

def interval(d,k,lo,hi):
    a=d[k]
    if not isinstance(a,list) or len(a)!=2:raise ValueError(k+' needs two corners')
    x,y=[num({'x':v},'x',lo,hi) for v in a]
    if x>y:raise ValueError(k+' reversed')
    return x,y

def analyze(d):
    if d['switch_mpn']!='TPS22990DMLR' or d['supervisor_mpn']!='TPS389001DSET':raise ValueError('Unsupported exact variants')
    b=d['bounds'];vmin,vmax=interval(b,'input_v',2.5,5.5)
    load=num(b,'sbc_running_current_a',0,10);cap=num(b,'sbc_charge_cap_max_f',1e-9,.1)
    ron=num(b,'switch_resistance_screening_ohm',1e-6,1);wire=num(b,'trace_contact_resistance_max_ohm',0,1)
    ctmin,ctmax=interval(b,'switch_ct_effective_f',1e-12,22e-6)
    fast=num(b,'switch_rise_time_typical_equation_screening_fast_factor',.01,1)
    rise=((.011*vmax+.002)*(ctmin*1e12)+4.7*vmax+7.8)*1e-6*fast
    charge=.8*vmax*cap/rise
    rt=num(b,'sense_top_ohm',1,1e7);rb=num(b,'sense_bottom_ohm',1,1e7)
    tol=num(b,'sense_resistor_total_fraction',0,.1);tt=num(b,'sense_threshold_fraction',0,.1)
    leak=num(b,'sense_leakage_a',0,1e-3)
    def thresholds(key):
        ref=num(b,key,.1,5)
        return [ref*(1-tt)*(1+rt*(1-tol)/(rb*(1+tol)))-leak*rt*(1-tol),ref*(1+tt)*(1+rt*(1+tol)/(rb*(1-tol)))+leak*rt*(1+tol)]
    fall=thresholds('sense_threshold_negative_v');rising=thresholds('sense_threshold_positive_v')
    tdmin,tdmax=interval(b,'supervisor_delay_cap_effective_f',1e-12,22e-6)
    icmin,icmax=interval(b,'supervisor_delay_current_a',1e-9,1e-3)
    vcmin,vcmax=interval(b,'supervisor_delay_threshold_v',.1,5)
    vi_min,vi_max=interval(b,'supervisor_delay_cap_initial_v_assumed',0,vcmax)
    delaymin=tdmin*max(0,vcmin-vi_max)/icmax;delaymax=tdmax*max(0,vcmax-vi_min)/icmin+25e-6
    qod=num(b,'qod_resistance_max_ohm',1,1e4);target=num(b,'fully_discharged_target_v',.01,vmax)
    remaining=vmax*math.exp(-delaymin/(qod*cap))
    out={'evidence':'conditional arithmetic; switchCTequation andexpandedRON are engineering assumptions, not guaranteed timing',
         'trip_falling_v':fall,'trip_rising_v':rising,'rising_max_below_regulated4p95v':rising[1]<4.95,
         'normal4p85v_above_falling_max':vmin>fall[1],
         'supervisor_delay_min_s':delaymin,'supervisor_delay_max_s':delaymax,
         'delay_requires_stated_initial_ct_voltage':True,'arbitrary_warm_reset_minimum_delay_proven':False,
         'qod_result_requires_powered_discharge_and_stated_ct_initial_voltage':True,
         'switch_10to90_rise_min_s_assumed':rise,'host_charge_current_a_assumed':charge,
         'host_running_plus_charge_a':load+charge,'switch_dc_drop_v':load*ron,'switch_dc_loss_w':load*load*ron,
         'host_min_v_with_contact_budget':vmin-load*(ron+wire),
         'host_min_v_ge4p75':vmin-load*(ron+wire)>=4.75,
         'output_after_min_reset_delay_v_if_qod_powered':remaining,'qod_discharge_pass_if_powered':remaining<target,
         'on_min_released_v_including350na_leak':vmin*.5-.00000035*165000,
         'pullup_current_at0p8v_a':.8/330000,
         'short_current_limit_implemented':False,'reverse_blocking_implemented':False,
         'pg_is_precision_voltage_monitor':False,'production_qualified':False}
    json.dumps(out,allow_nan=False);return out

def validate(tree,d):
    errors=[];expected=defaultdict(set);actual={};seen=set()
    def add(net,ref,pin):expected[net].add((ref,str(pin)))
    switches={1:'SBC_SLEW_CT',3:'CORE_5V',4:'CORE_5V',5:'SBC_ENABLE',6:'LOGIC_GND',7:'SBC_SWITCH_PG',8:'SBC_5V',9:'SBC_5V',10:'SBC_5V',11:'CORE_5V'}
    supervisor={1:'SBC_SENSE',2:'LOGIC_GND',3:'SBC_RESET_N',4:'CORE_5V',5:'SBC_DELAY_CT',6:'SBC_ENABLE'}
    for ref,pins in [('U1',switches),('U2',supervisor)]:
        for n,net in pins.items():add(net,ref,n)
    parts={'RHI1':('31.6k0.1%10ppm','CORE_5V','SBC_SENSE'),'RLO1':('10k0.1%10ppm','SBC_SENSE','LOGIC_GND'),
           'REN1':('330k1%','CORE_5V','SBC_ENABLE'),'RPD1':('330k1%','SBC_ENABLE','LOGIC_GND'),
           'RMR1':('100k1%','CORE_5V','SBC_RESET_N'),'RPG1':('100k1%','SBC_5V','SBC_SWITCH_PG'),
           'CIN1':('2.2uF16V X7R','CORE_5V','LOGIC_GND'),'CBIAS1':('100nF16V X7R','CORE_5V','LOGIC_GND'),
           'CSUP1':('100nF16V X7R','CORE_5V','LOGIC_GND'),'COUT1':('1uF16V X7R','SBC_5V','LOGIC_GND'),
           'CTSW1':('1uF50V X7R','SBC_SLEW_CT','LOGIC_GND'),'CTSUP1':('2.2uF16V X7R','SBC_DELAY_CT','LOGIC_GND')}
    for ref,(_,a,b) in parts.items():add(a,ref,1);add(b,ref,2)
    bounds={'JIN1':['CORE_5V','LOGIC_GND'],'JOUT1':['SBC_5V','LOGIC_GND'],'JSTATUS1':['SBC_ENABLE','SBC_SWITCH_PG','LOGIC_GND'],'JMR1':['SBC_RESET_N','LOGIC_GND']}
    for ref,nets in bounds.items():
        for i,net in enumerate(nets,1):add(net,ref,i)
    nc=set()
    for net in tree.findall('.//nets/net'):
        name=net.attrib['name'].lstrip('/');nodes=[(n.attrib['ref'],n.attrib['pin']) for n in net.findall('node') if not n.attrib['ref'].startswith('#')]
        if len(nodes)!=len(set(nodes)) or seen.intersection(nodes):errors.append('Duplicate pin')
        seen.update(nodes)
        if name.startswith('unconnected-'):
            if len(nodes)!=1:errors.append('Grouped NC')
            nc.update(nodes)
        else:
            if name in actual:errors.append('Duplicate netname')
            actual[name]=set(nodes)
    if nc!={('U1','2')}:errors.append('NC changed')
    for name in set(actual)|set(expected):
        if actual.get(name,set())!=expected.get(name,set()):errors.append('Connectivity differs:'+name)
    cs=tree.findall('.//components/comp');comps={c.attrib['ref']:c for c in cs}
    if len(cs)!=len(comps) or set(comps)!=set(parts)|set(bounds)|{'U1','U2'}:errors.append('Population differs')
    for ref,(value,_,_) in parts.items():
        if ref not in comps or comps[ref].findtext('value')!=value:errors.append('Value differs:'+ref)
    for ref,mpn in [('U1','TPS22990DMLR'),('U2','TPS389001DSET')]:
        if ref not in comps or comps[ref].findtext("./fields/field[@name='MPN']")!=mpn:errors.append('MPN differs:'+ref)
        if ref in comps and comps[ref].findtext('footprint') not in ('',None):errors.append('Unqualified footprint:'+ref)
    for ref,c in comps.items():
        if any(p.attrib.get('name','').lower()=='dnp' for p in c.findall('property')):errors.append('Unreviewed DNP:'+ref)
    for part,pin in [('TPS22990DMLR','7'),('TPS389001DSET','6')]:
        p=tree.find(f".//libpart[@part='{part}']/pins/pin[@num='{pin}']")
        if p is None or p.attrib.get('type')!='open_collector':errors.append('Outputtype changed:'+part)
    try:analyze(d)
    except (ValueError,KeyError,TypeError,OverflowError) as exc:errors.append('Invaliddesignbounds:'+str(exc))
    return errors

def main():
    d=json.loads((OUT/'design-envelope.json').read_text());tree=ET.parse(OUT/'netlist.xml');errors=validate(tree,d)
    erc=json.loads((OUT/'erc.json').read_text());count=sum(len(s['violations']) for s in erc['sheets'])
    if count:errors.append(f'ERCviolations:{count}')
    result=analyze(d)
    (ROOT/'research/sbc-power/analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    paths=[p for p in OUT.iterdir() if p.is_file() and p.name!='validation.json']+[Path(__file__),ROOT/'tools/hardware_build_sbc_power.py',ROOT/'tools/hardware_build_tx_schematic.py',ROOT/'tools/hardware_build_assembly.py',ROOT/'tests/test_sbc_power.py',ROOT/'reports/SBC_POWER.md']
    paths += [p for p in (ROOT/'research/sbc-power').iterdir() if p.is_file()]
    out={'schema_version':1,'manufacturing_ready':False,'consistency_pass':not errors,'errors':errors,'erc_violations':count,'kicad_version':erc['kicad_version'],'component_count':len(tree.findall('.//components/comp')),'net_count':len(tree.findall('.//nets/net')),'source_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'scope':'CircuitERC/connectivity andbounded calculations; noPCB,SPICEorphysicalqualification'}
    (OUT/'validation.json').write_text(json.dumps(out,indent=2)+'\n');print('SBCpower:', 'PASS' if not errors else errors)
    return bool(errors)

if __name__=='__main__':raise SystemExit(main())
