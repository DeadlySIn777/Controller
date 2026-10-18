"""Independent physical-pin/net and bounded DC/startup review for MC power.

Host checks and ERC never establish dynamic/physical/manufacturing qualification.
Expected topology is authored here, not copied from the generated pin-map.
"""
from collections import defaultdict
import hashlib
from itertools import product
import json
import math
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.hardware_validate_power_sequence import threshold_bounds

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/mc_local_power'
RFP='Resistor_SMD:R_0603_1608Metric'
CFP='Capacitor_SMD:C_0603_1608Metric'


def expected_circuit():
    nets=defaultdict(set);parts={}
    def part(ref,value,mpn,fp,pins,physical=True):
        parts[ref]={'value':value,'mpn':mpn,'footprint':fp,'physical':physical}
        for pin,net in pins.items():nets[net].add((ref,str(pin)))
    def r(ref,value,mpn,a,b):part(ref,value,mpn,RFP,{1:a,2:b})
    def c(ref,value,mpn,a,fp=CFP):part(ref,value,mpn,fp,{1:a,2:'LOGIC_GND'})
    for i,rail in enumerate(('CORE_1V2','IO_3V3')):
        part(f'U{i+1}','TPS62901RPJR','TPS62901RPJR','CNC_MC_Power:TPS62901_RPJ9',
             {1:rail+'_PG_OD',2:rail+'_SW',3:rail,4:'LOGIC_GND',5:rail+'_EN',6:'CORE_5V',7:rail+'_MODE',8:rail+'_SS',9:'LOGIC_GND' if not i else rail+'_VSET'})
        part(f'L{i+1}','2.2uH' if not i else '1uH','XGL4020-222MEC' if not i else 'XGL4020-102MEC','CNC_MC_Power:XGL4020',{1:rail+'_SW',2:rail})
        r(f'R{i*4+1}','76.8k 1%' if not i else '32.4k 1%','CRCW060376K8FKEA' if not i else 'CRCW060332K4FKEA',rail+'_MODE','LOGIC_GND')
        r(f'R{i*4+2}','10k 1%','CRCW060310K0FKEA',rail+'_EN','LOGIC_GND')
        r(f'R{i*4+3}','100k 1%','CRCW0603100KFKEA',rail,'LOGIC_GND')
        if i:r('R8','301k 1%','CRCW0603301KFKEA',rail+'_VSET','LOGIC_GND')
        c(f'C{i*3+1}','10uF 25V X7R 10%','C3216X7R1E106K160AB','CORE_5V','Capacitor_SMD:C_1206_3216Metric')
        c(f'C{i*3+2}','22uF 10V X7S 20%','C2012X7S1A226M125AC',rail,'Capacitor_SMD:C_0805_2012Metric')
        c(f'C{i*3+3}','6.8nF 50V C0G 5%','GRM1885C1H682JA01D',rail+'_SS')
    ladders=(
        ((('R21','87.9k','8792'),),(('R29','92.1k','9212'),),('R27','R35','10k','1002')),
        ((('R41','1.07k','1071'),('R42','261','2610')),(('R49','1.15k','1151'),('R50','316','3160'),('R51','4.02',None)),('R47','R55','1k','1001')),
        ((('R61','54.5k','5452'),),(('R69','57.5k','5752'),),('R67','R75','10k','1002')))
    for i,rail in enumerate(('CORE_5V','CORE_1V2','IO_3V3')):
        rn=f'MC_SEQ_REF{i+1}'
        part(f'U{i+3}','LTC2962HUD#TRPBF','LTC2962HUD#TRPBF','CNC_MC_Power:LTC2962_UD16',
             {1:'CORE_5V',2:('CORE_5V','MC_SEQ_5V_OK','IO_3V3_EN')[i],3:'LOGIC_GND',4:'CORE_5V',5:rn,6:rn,7:'LOGIC_GND',8:rn,9:rn,10:'CORE_5V',11:'LOGIC_GND',12:('MC_SEQ_5V_OK','IO_3V3_EN','MC_RAILS_OK_5V')[i],13:'CORE_5V',14:'CORE_5V',15:rail+'_OV_SENSE',16:rail+'_UV_SENSE',17:'LOGIC_GND'})
        div=ladders[i]
        for index,chain in enumerate(div[:2]):
            prefix=('UV','OV')[index];sense=rail+'_'+prefix+'_SENSE'
            for j,(ref,value,code) in enumerate(chain):
                a=rail if not j else f'MC_SEQ_{prefix}{i+1}_{j}';b=sense if j==len(chain)-1 else f'MC_SEQ_{prefix}{i+1}_{j+1}'
                r(ref,value+(' 0.01% 5ppm' if code else ' 1% 100ppm'),'PLT0603Z'+code+'LST1' if code else 'CRCW06034R02FKEA',a,b)
            r(div[2][index],div[2][2]+' 0.01% 5ppm','PLT0603Z'+div[2][3]+'LST1',sense,'LOGIC_GND')
        c(f'C{i+7}','100nF 25V X7R 10%','GRM188R71E104KA01D','CORE_5V')
    for ref,value,code,a,b in (
        ('R101','3.3k','3K30','CORE_5V','MC_SEQ_5V_OK'),('R102','3.3k','3K30','MC_SEQ_5V_OK','CORE_1V2_EN'),('R103','10k','10K0','CORE_1V2_EN','LOGIC_GND'),
        ('R104','6.8k','6K80','CORE_5V','IO_3V3_EN'),('R105','10k','10K0','IO_3V3_EN','LOGIC_GND'),('R106','47k','47K0','CORE_5V','MC_RAILS_OK_5V'),
        ('R107','470k','470K','MC_RAILS_OK_5V','LOGIC_GND'),('R108','4.7k','4K70','FPGA_CRESET_N','LOGIC_GND')):
        r(ref,value+' 1%','CRCW0603'+code+'FKEA',a,b)
    part('U6','SN74LVC1G17DBVR','SN74LVC1G17DBVR','Package_TO_SOT_SMD:SOT-23-5',
         {1:'unconnected-(U6-NC-Pad1)',2:'MC_RAILS_OK_5V',3:'LOGIC_GND',4:'FPGA_CRESET_N',5:'IO_3V3'})
    c('C10','100nF 25V X7R 10%','GRM188R71E104KA01D','IO_3V3')
    boundary=['CORE_5V','LOGIC_GND','CORE_1V2','IO_3V3','FPGA_CRESET_N','MC_RAILS_OK_5V','CORE_1V2_PG_OD','IO_3V3_PG_OD','LOGIC_GND']
    part('B1','MC POWER REVIEW BOUNDARY','','',dict(enumerate(boundary,1)),False)
    return dict(nets),parts,boundary


def local_windows(drift=0):
    rows=[]
    chains=(
        ('CORE_5V',(('R21','87.9k',87900,'8792'),),(('R29','92.1k',92100,'9212'),),10000,4.85,5.15,4.95,5.05),
        ('CORE_1V2',(('R41','1.07k',1070,'1071'),('R42','261',261,'2610')),(('R49','1.15k',1150,'1151'),('R50','316',316,'3160'),('R51','4.02',4.02,None)),1000,1.15,1.25,1.185,1.215),
        ('IO_3V3',(('R61','54.5k',54500,'5452'),),(('R69','57.5k',57500,'5752'),),10000,3.2,3.4,3.25875,3.34125))
    for rail,uchain,ochain,bottom,lo,hi,rlo,rhi in chains:
        uv=threshold_bounds(uchain,bottom,drift);ov=threshold_bounds(ochain,bottom,drift)
        margins=[uv[0]-lo,rlo-uv[1],ov[0]-rhi,hi-ov[1]]
        rows.append({'rail':rail,'uv_v':uv,'ov_v':ov,'static_margins_v':margins,'static_acceptance_and_detection':min(margins)>0})
    return rows


def analytical_screen(fpga):
    """Tolerance/current arithmetic from stated reservations, not measured maxima."""
    vrefmin=(.6*.9875-.008)/.75;vrefmax=(.6*1.0125+.008)/.75
    tmin=6800*.95*.9955/2.7*vrefmin-700;tmax=6800*1.05*1.0045/2.3*vrefmax+160
    rail_rows=[]
    for rail,load,voltage,extra,caplimit,l,freq in (('CORE_1V2',.8,1.215,2,50,2.2,1e6),('IO_3V3',.15,3.34125,10,100,1,2.5e6)):
        caps=[(ref,c) for ref,c in fpga['components'].items() if 'capacitance_f' in c and rail in c['pins'].values()]
        actual=sum(c['capacitance_f'] for _,c in caps)*1e6
        capmax=sum(c['capacitance_f']*(1+c['tolerance'])*(1+c['temperature_change']) for _,c in caps)*1e6
        # Additional parts allocation constrained to <=10% initial, <=15% temp.
        total=22*1.2*1.22+capmax+extra*1.1*1.15+(.1*1.1*1.15 if rail=='IO_3V3' else 0)
        cap_a=total*1e-6*voltage/(tmin*1e-6)
        inp=load*voltage/(4.85*.85)+.05
        ripple=voltage*(1-voltage/5.15)/(l*.8*.8*1e-6*freq)
        rail_rows.append({'rail':rail,'reservation_a':load,'fpga_cap_refs':[r for r,_ in caps],
                         'fpga_cap_nominal_uf':actual,'fpga_cap_upper_tolerance_temperature_uf':capmax,
                         'additional_nominal_budget_uf':extra,'total_output_upper_uf':total,'datasheet_total_effective_max_uf':caplimit,
                         'startup_charge_current_a_model':cap_a,'startup_output_total_a_model':load+cap_a,
                         'steady_input_a_with_85pct_efficiency_and_50ma_allowance':inp,
                         'nominal_frequency_ripple_a_model':ripple,'startup_peak_inductor_a_model':load+cap_a+ripple/2,
                         'frequency_lower_bound_guaranteed':False,'loaded_ramp_guaranteed':False,'min_effective_output_uf_requires_bias_review':6 if freq==1e6 else 10})
    core,io=rail_rows
    inputextra=.01
    steady=sum(r['steady_input_a_with_85pct_efficiency_and_50ma_allowance'] for r in rail_rows)+inputextra
    peak=steady+sum(r['startup_charge_current_a_model']*({'CORE_1V2':1.215,'IO_3V3':3.34125}[r['rail']])/(4.85*.85) for r in rail_rows)
    # Core EN has two fixed 10k pulls, not optional external loads.
    corecases=[]
    for vs,r0,ra,pd,iq,ie in product((4.85,5.15),(3300*.98,3300*1.02),(3300*.98,3300*1.02),(5000*.98,5000*1.02),(8e-6,26e-6),(-1e-6,1e-6)):
        vx=(vs/r0+iq+ie*pd/(ra+pd))/(1/r0+1/(ra+pd));va=(vx/ra+ie)/(1/ra+1/pd);corecases.append((vx,va))
    ios=[(vs/rp+iq)/(1/rp+1/pd) for vs,rp,pd,iq in product((4.85,5.15),(6800*.98,6800*1.02),(5000*.98,5000*1.02),(7e-6,27e-6))]
    reset=[(vs/rp+iq)/(1/rp+1/pd) for vs,rp,pd,iq in product((4.85,5.15),(47000*.98,47000*1.02),(470000*.98,470000*1.02),(-1e-6,15e-6))]
    return {'evidence_class':'bounded arithmetic / reservations; not physical guaranteed startup or fault timing',
            'soft_start_us_model':[tmin,tmax],'rails':rail_rows,'steady_slot_input_a_model':steady,'concurrent_startup_input_a_model':peak,
            'IS1_steady_slot_reservation_a':.45,'IS1_steady_slot_excess_a':max(steady-.45,0),'proposed_steady_slot_reservation_a':.5,
            'suggested_slot_startup_allowance_a':.8,'cold_input_cap_upper_uf':2*10*1.1*1.15+3*.1*1.1*1.15,
            'cold_input_cap_current_not_included':True,'slot_limiter_not_qualified':True,
            'core_seq_high_v':[min(v[0] for v in corecases),max(v[0] for v in corecases)],
            'core_en_high_v':[min(v[1] for v in corecases),max(v[1] for v in corecases)],
            'io_en_and_mr_high_v':[min(ios),max(ios)],'raw_reset_high_v':[min(reset),max(reset)],
            'powered_supervisor_low_v_at_datasheet_conditions':.15,
            'supervisor_release_delay_ms':[160,240],'three_sequential_release_delay_ms':[480,720],
            'static_windows':local_windows(),'aging_400ppm_sensitivity':local_windows(.0004),
            'reset_buffer_high_min_v_at_vcc_ge_3_and_load_le_16ma':2.4,
            'buffer_reset_high_load_a_with_external_1ma':3.4/(4700*.98)+.001,
            'buffer_reset_low_max_v_with_external_sink_load_le_100ua':.1,
            'existing_reset_and_input_VIH_VIL_v':[2,.8],
            'reset_high_low_interface_margins_v':[2.4-2,.8-.1],
            'powered_supervisor_asserted_sink_load_a':{'MC_SEQ_5V_OK':5.15/(3300*.98)+26e-6,'IO_3V3_EN':5.15/(6800*.98)+26e-6,'MC_RAILS_OK_5V':5.15/(47000*.98)+15e-6},
            'reset_zero_io_supply_ioff_pd_upper_v':10e-6*4700*1.02,
            'physical_or_arbitrary_partial_power':False}


def validate(tree,model,fpga,footprints=None):
    errors=[];expected,wanted,boundary=expected_circuit()
    actual={};seen=set()
    for row in tree.findall('.//nets/net'):
        n=re.sub(r'^(unconnected-\([^)]*\))-.*$',r'\1',row.attrib['name'].lstrip('/'))
        if n in actual:errors.append('Duplicate net '+n)
        actual[n]=set()
        for node in row.findall('node'):
            pair=(node.attrib['ref'],node.attrib['pin'])
            if pair in seen:errors.append('Repeated pin '+str(pair))
            seen.add(pair);actual[n].add(pair)
    for net in sorted(set(actual)|set(expected)):
        if actual.get(net,set())!=expected.get(net,set()):errors.append('Net mismatch '+net)
    comps=tree.findall('.//components/comp')
    if len(comps)!=len(wanted) or {c.attrib['ref'] for c in comps}!=set(wanted):errors.append('Component population differs')
    for c in comps:
        ref=c.attrib['ref'];a={'value':c.findtext('value'),'mpn':c.findtext("./fields/field[@name='MPN']") or '','footprint':c.findtext('footprint') or ''}
        if a!={k:wanted.get(ref,{}).get(k) for k in a}:errors.append('Value/MPN/package mismatch '+ref)
        if any(p.attrib.get('name','').lower()=='dnp' for p in c.findall('property')):errors.append('Required component DNP '+ref)
    physical_pins={
        'TPS62901RPJR':{'1':('PG','open_collector'),'2':('SW','power_out'),'3':('VOS','input'),'4':('GND','power_in'),'5':('EN','input'),'6':('VIN','power_in'),'7':('MODE/S-CONF','input'),'8':('SS/TR','input'),'9':('FB/VSET','input')},
        'LTC2962HUD':{str(k):(v,'power_in' if k in (3,4,11,17) else 'open_collector' if k==12 else 'output' if k==5 else 'input') for k,v in {1:'RDIS',2:'MR',3:'DVCC',4:'VCC',5:'REF',6:'PG1',7:'PG2',8:'PG3',9:'PG4',10:'RT',11:'GND',12:'RST',13:'V4',14:'V3',15:'V2',16:'V1',17:'EP'}.items()},
        'LVC1G17':{'1':('NC','no_connect'),'2':('A','input'),'3':('GND','power_in'),'4':('Y','output'),'5':('VCC','power_in')}}
    for name,pins in physical_pins.items():
        rows=tree.findall(f".//libpart[@part='{name}']/pins/pin")
        if len(rows)!=len(pins) or {p.attrib['num']:(p.attrib['name'],p.attrib['type']) for p in rows}!=pins:errors.append('Physical IC pin map '+name)
    if model.get('manufacturing_ready') is not False or model.get('physical_qualification') is not False:errors.append('Readiness overstated')
    if model.get('boundary')!={'B1':boundary}:errors.append('Boundary changed')
    if model.get('component_deviation')!={'IS-1':'TPS386000','proposed':'LTC2962HUD#TRPBF x3','reason':'Preserve narrow guaranteed rail windows; TPS386000 full corners do not close them.'}:errors.append('Unversioned supervisor deviation')
    if model.get('rail_limits_v')!={'CORE_5V':[4.85,5.15],'CORE_1V2':[1.15,1.25],'IO_3V3':[3.2,3.4]}:errors.append('Actual rail windows changed')
    if model.get('threshold_deviation')!={'historical_tight_ledger_core_v':[1.17,1.23],'actual_T20_core_v':[1.15,1.25],'core_UV_top_ohm':1331,'core_OV_top_ohm':1470.02,'bottom_ohm':1000,'additional_drift_fraction':.0004,'reason':'Inset thresholds within actual Efinix operating limits while avoiding historical sub-mV false-trip and aging margins.'}:errors.append('Unrecorded actual core-limit threshold change')
    if model.get('regulation_only_v')!={'CORE_5V':[4.95,5.05],'CORE_1V2':[1.185,1.215],'IO_3V3':[3.25875,3.34125]}:errors.append('Regulation assumptions changed')
    if model.get('load_reservations_a')!={'CORE_1V2':.8,'IO_3V3':.15,'CORE_5V_steady_slot':.5,'IS1_steady_slot':.45,'additional_supervision_input':.01}:errors.append('Load reservations changed')
    if model.get('slot_power_deviation')!={'IS-1_steady_a':.45,'IS-2_proposed_steady_a':.5,'IS-2_proposed_startup_allowance_a':.8,'reason':'Count both converter reservations, overhead and complete decoupling; input-cap charging separately.'}:errors.append('Unversioned slot power deviation')
    if model.get('rail_capacitor_limits')!={'CORE_1V2':{'effective_max_uf':50,'additional_nominal_load_budget_uf':2},'IO_3V3':{'effective_max_uf':100,'additional_nominal_load_budget_uf':10}}:errors.append('Capacitance allocations changed')
    if model.get('release_delay_ms')!=[160,240]:errors.append('Supervisor delay changed')
    if model.get('reset_boundary_contract')!={'destination':'3.3 V logic inputs; existing FPGA core reset-AND input','external_high_load_max_a':.001,'external_low_load_max_a':.0001,'external_pushpull_driver_allowed':False,'raw_5v_qualifier_may_drive_FPGA':False}:errors.append('Reset electrical loading/drive contract changed')
    # The design manifest must describe the same circuit, excluding the NC pin.
    for ref,w in wanted.items():
        c=model.get('components',{}).get(ref,{})
        if any(c.get(k)!=v for k,v in w.items()):errors.append('Source manifest part '+ref)
        target={p:n for n,nodes in expected.items() for r,p in nodes if r==ref and not n.startswith('unconnected-')}
        if c.get('pins')!=target:errors.append('Source manifest pins '+ref)
    if set(model.get('components',{}))!=set(wanted):errors.append('Source manifest population')
    if footprints is not None:
        pads={'TPS62901_RPJ9':{'1':(-.625,-.25,.65,.2),'2':(-.625,.25,.65,.2),'3':(-.625,.75,.65,.2),'4':(.45,.75,1,.2),'5':(.625,.25,.65,.2),'6':(.45,-.25,1,.2),'7':(.5,-.925,.25,.55),'8':(0,-.925,.25,.55),'9':(-.5,-.925,.25,.55)},
              'XGL4020':{'1':(-1.185,0,.98,3.4),'2':(1.185,0,.98,3.4)}}
        ud={str(i+1):(-1.4,-.75+i*.5,.7,.25) for i in range(4)}
        ud.update({str(i+5):(-.75+i*.5,1.4,.25,.7) for i in range(4)});ud.update({str(i+9):(1.4,.75-i*.5,.7,.25) for i in range(4)});ud.update({str(i+13):(.75-i*.5,-1.4,.25,.7) for i in range(4)});ud['17']=(0,0,1.45,1.45);pads['LTC2962_UD16']=ud
        for name,target in pads.items():
            rows=re.findall(r'\(pad "(\d+)" smd roundrect \(at ([^ ]+) ([^)]+)\) \(size ([^ ]+) ([^)]+)\)',footprints.get(name,''))
            try:a={p[0]:tuple(float(v) for v in p[1:]) for p in rows}
            except ValueError:a={}
            if len(rows)!=len(target) or a!=target:errors.append('Manufacturer copper pad map '+name)
    try:screen=analytical_screen(fpga)
    except (KeyError,TypeError,ValueError):errors.append('External FPGA cap model invalid');return errors
    if screen['steady_slot_input_a_model']>=.5:errors.append('Proposed steady slot reservation exceeded')
    if screen['concurrent_startup_input_a_model']>=.8:errors.append('Proposed startup slot allocation exceeded')
    for r in screen['rails']:
        if not math.isfinite(r['total_output_upper_uf']) or r['total_output_upper_uf']>r['datasheet_total_effective_max_uf']:errors.append('Effective maximum output capacitance exceeded '+r['rail'])
        if r['startup_output_total_a_model']>=1:errors.append('Startup output current reservation exceeded '+r['rail'])
    if screen['core_seq_high_v'][0]<1.6 or screen['core_en_high_v'][0]<1.03 or screen['core_en_high_v'][1]>3.6:errors.append('Core enable/MR DC interface')
    if screen['io_en_and_mr_high_v'][0]<1.6 or screen['io_en_and_mr_high_v'][1]>3.6:errors.append('IO enable/MR DC interface')
    if screen['raw_reset_high_v'][0]<3.33:errors.append('Reset Schmitt high interface')
    if screen['raw_reset_high_v'][1]>5.5:errors.append('Reset Schmitt input exceeds5.5V operating limit')
    if screen['buffer_reset_high_load_a_with_external_1ma']>.016:errors.append('Reset high load exceedsVOHguarantee')
    if max(screen['powered_supervisor_asserted_sink_load_a'].values())>.003:errors.append('Supervisor sink exceedslow-levelguarantee')
    if not all(r['static_acceptance_and_detection'] for r in screen['static_windows']):errors.append('Fresh static window corner failed')
    if not all(r['static_acceptance_and_detection'] for r in screen['aging_400ppm_sensitivity']):errors.append('400ppm drift threshold corner failed')
    return errors


def main():
    model=json.loads((OUT/'design.json').read_text(encoding='utf-8'));fpga=json.loads((ROOT/'hardware/fpga_core/design.json').read_text(encoding='utf-8'))
    fps={p.stem:p.read_text(encoding='utf-8') for p in (OUT/'CNC_MC_Power.pretty').glob('*.kicad_mod')}
    tree=ET.parse(OUT/'netlist.xml');errors=validate(tree,model,fpga,fps)
    for p,want in model['source_sha256'].items():
        if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=want:errors.append('Source changed '+p)
    erc=json.loads((OUT/'erc.json').read_text(encoding='utf-8'));v=[v for s in erc['sheets'] for v in s['violations']]
    if v:errors.append(f'Native ERC has {len(v)} violations')
    if {x['key'] for x in erc['ignored_checks']}!={'single_global_label','four_way_junction','simulation_model_issue','footprint_filter'}:errors.append('Native ERC default ignored-check set changed')
    result={'schema_version':1,'consistency_pass':not errors,'manufacturing_ready':False,'scope':'MC two local regulators plus three independent precision-window supervisors',
            'errors':errors,'physical_parts':sum(c['physical'] for c in model['components'].values()),'boundary_parts':1,'native_erc_violations':len(v),
            'kicad_version':erc['kicad_version'],'erc_ignored_checks':erc['ignored_checks'],'analytical_screen':analytical_screen(fpga),
            'source_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),ROOT/'tools/hardware_build_mc_local_power.py',ROOT/'tests/test_mc_local_power.py']+[p for p in OUT.rglob('*') if p.is_file() and p.name!='validation.json']}}
    (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'pass':not errors,'physical_parts':result['physical_parts'],'errors':errors}))
    return bool(errors)


if __name__=='__main__':sys.exit(main())
