"""Independent exported-net and bounded DC checks for the rail-reset candidate.

This deliberately cannot assert physical, lifetime, transient or manufacturing readiness.
No hardware access. No generator pin-map is trusted as the expected circuit.
"""
from collections import defaultdict
import hashlib
from itertools import product
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware/power_sequence"
RAILS = ("CORE_5V", "CORE_1V2", "IO_3V3", "ESP_3V3")
LIMITS = ((4.85, 5.15, 4.95, 5.05), (1.17, 1.23, 1.185, 1.215),
          (3.2, 3.4, 3.25875, 3.34125), (3.2, 3.4, 3.25875, 3.34125))
# Independent selected populations: ref, printed value, ohms, PLT resistance code.
DIVIDERS = (
    ((('R1','87.9k',87900,'8792'),), (('R9','92.1k',92100,'9212'),), ('R7','R15',10000,'1002')),
    ((('R21','1.10k',1100,'1101'),('R22','255',255,'2550')),
     (('R29','1.15k',1150,'1151'),('R30','294',294,'2940'),('R31','1',1,None)), ('R27','R35',1000,'1001')),
    ((('R41','54.5k',54500,'5452'),), (('R49','57.5k',57500,'5752'),), ('R47','R55',10000,'1002')),
    ((('R61','54.5k',54500,'5452'),), (('R69','57.5k',57500,'5752'),), ('R67','R75',10000,'1002')),
)


def threshold_bounds(chain, bottom, additional_precision_fraction=0):
    """Reference/tolerance/TCR/bias corners, not lifetime or dynamic qualification."""
    rt = []
    for sign in (-1, 1):
        rt.append(sum(ohm * (1 + sign * ((.0001 + 5e-6*100 + additional_precision_fraction)
                    if code else (.01 + 100e-6*100))) for _, _, ohm, code in chain))
    rb = [bottom * (1 + sign*(.0006 + additional_precision_fraction)) for sign in (-1, 1)]
    values = [ref*(1+top/bot) + bias*top for ref, top, bot, bias in
              product((.4975,.5025), rt, rb, (-15e-9,15e-9))]
    return [min(values), max(values)]


def windows(additional_precision_fraction=0):
    result=[]
    for rail, div, (lo, hi, reglo, reghi) in zip(RAILS, DIVIDERS, LIMITS):
        uv=threshold_bounds(div[0], div[2][2], additional_precision_fraction)
        ov=threshold_bounds(div[1], div[2][2], additional_precision_fraction)
        margins=[uv[0]-lo, reglo-uv[1], ov[0]-reghi, hi-ov[1]]
        result.append({'rail':rail,'uv_v':uv,'ov_v':ov,'static_margins_v':margins,
                       'static_acceptance_and_detection':min(margins)>0})
    return result


def enable_corners():
    """Coupled R101/R102/R104 network. Local 10k always fitted, carrier 10k optional.

    Ordinary resistor envelope 1% initial +100ppm/K*100K =2%. Each regulator EN
    has a conservative +/-1uA design allowance (datasheet300nA measured at12V;
    this allowance is a verification contract, not a new device guarantee).
    Powered, released supervisor weak currents: RST4..10uA + two MR4..16uA.
    """
    cases=[]
    for installed_a, installed_b in product((False,True), repeat=2):
        values=[]
        ranges=[(4.85,5.15)] + [(r*.98,r*1.02) for r in (3300,3300,3300,
                  5000 if installed_a else 10000,5000 if installed_b else 10000)]
        ranges += [(12e-6,42e-6),(-1e-6,1e-6),(-1e-6,1e-6)]
        for vs,r0,ra,rb,pa,pb,ix,ia,ib in product(*ranges):
            vx=(vs/r0+ix+ia*pa/(ra+pa)+ib*pb/(rb+pb))/(1/r0+1/(ra+pa)+1/(rb+pb))
            va=(vx/ra+ia)/(1/ra+1/pa)
            vb=(vx/rb+ib)/(1/rb+1/pb)
            values.append((vx,va,vb))
        cases.append({'core_carrier_pulldown':installed_a,'esp_carrier_pulldown':installed_b,
                      'seq5_v':[min(v[0] for v in values),max(v[0] for v in values)],
                      'core_en_v':[min(v[1] for v in values),max(v[1] for v in values)],
                      'esp_en_v':[min(v[2] for v in values),max(v[2] for v in values)]})
    io=[]
    for installed in (False,True):
        pd=5000 if installed else 10000
        vals=[(vs/rp+i)/(1/rp+1/rd) for vs,rp,rd,i in product((4.85,5.15),(6800*.98,6800*1.02),
                    (pd*.98,pd*1.02),(7e-6,27e-6))] # RST + MR +/-1uA EN allowance
        io.append({'carrier_pulldown':installed,'en_v':[min(vals),max(vals)]})
    return {'coupled_core_esp':cases,'io':io,'en_leakage_allowance_a':1e-6,
            'arbitrary_partial_power_proven':False}


def reset_bounds():
    """Loaded reset interface contracts, with device test-condition limits preserved."""
    high=[(v/rp+i)/(1/rp+1/rd) for v,rp,rd,i in product((4.85,5.15),(47000*.98,47000*1.02),
             (470000*.98,470000*1.02),(-5e-6+4e-6,5e-6+10e-6))]
    # External ESP load allowance is powered-only; no energised external injection
    # is permitted in the zero-supply calculation. Intermediate supplies are open.
    return {'qualifier_high_v':[min(high),max(high)],
        'qualifier_low_v_at_vcc_ge_2v25_and_sink_le_3ma':.150,
        'qualifier_zero_core5_v_with_5u1a_leak':5.1e-6/(1/(47000*1.02)+1/(470000*1.02)),
        'fpga_reset_high_min_v_at_vcc_ge_3v_load_le_16ma':2.4,
        'fpga_reset_high_load_a':3.4/(4700*.98),
        'esp_reset_high_load_a_including_20ua_allowance':3.4/(47000*.98)+20e-6,
        'esp_reset_voh_min_relative_to_vcc_v':-.1,
        'esp_reset_min_high_margin_v':3.2-.1-.75*3.2,
        'zero_destination_vcc_buffer_ioff_pd_v':{'FPGA_CRESET_N':10e-6*4700*1.02,'ESP_CHIP_PU':10e-6*47000*1.02},
        'partial_power_or_external_injection_qualified':False}


def validate(tree, design, model, footprint_text=None):
    errors=[]; expected=defaultdict(set); wanted={}
    def wire(net,*nodes):expected[net].update((ref,str(pin)) for ref,pin in nodes)
    def part(ref,val,mpn,foot):wanted[ref]={'value':val,'mpn':mpn,'footprint':foot}
    def resistor(ref,val,mpn,top,bottom):
        part(ref,val,mpn,'Resistor_SMD:R_0603_1608Metric');wire(top,(ref,1));wire(bottom,(ref,2))
    pin_names={'1':'RDIS','2':'MR','3':'DVCC','4':'VCC','5':'REF','6':'PG1','7':'PG2','8':'PG3',
               '9':'PG4','10':'RT','11':'GND','12':'RST','13':'V4','14':'V3','15':'V2','16':'V1','17':'EP'}
    mr=('CORE_5V','SEQ_5V_OK','IO_3V3_EN','SEQ_5V_OK')
    rst=('SEQ_5V_OK','IO_3V3_EN','SEQ_FPGA_RESET_GOOD','SEQ_ESP_RESET_GOOD')
    window_models=[]
    for i,(rail,div) in enumerate(zip(RAILS,DIVIDERS)):
        u=f'U{i+1}';refnet=f'SEQ_REF{i+1}'
        part(u,'LTC2962HUD#TRPBF','LTC2962HUD#TRPBF','CNC_Power:LTC2962_UD16')
        for p in (1,4,10,13,14):wire('CORE_5V',(u,p))
        for p in (3,7,11,17):wire('LOGIC_GND',(u,p))
        for p in (5,6,8,9):wire(refnet,(u,p))
        wire(mr[i],(u,2));wire(rst[i],(u,12));wire(rail+'_UV_SENSE',(u,16));wire(rail+'_OV_SENSE',(u,15))
        data={'rail':rail,'uv_top_ohm':sum(t[2] for t in div[0]),'ov_top_ohm':sum(t[2] for t in div[1]),
              'bottom_ohm':div[2][2],'uv_series':[],'ov_series':[]}
        for n,(prefix,chain) in enumerate(zip(('UV','OV'),div[:2])):
            sense=rail+'_'+prefix+'_SENSE'
            for j,(ref,val,ohm,code) in enumerate(chain):
                top=rail if not j else f'SEQ_{prefix}{i+1}_{j}'
                bottom=sense if j==len(chain)-1 else f'SEQ_{prefix}{i+1}_{j+1}'
                resistor(ref,val+(' 0.01% 5ppm' if code else ' 1% 100ppm'),
                         'PLT0603Z'+code+'LST1' if code else 'CRCW06031R00FKEA',top,bottom)
                data[prefix.lower()+'_series'].append({'reference':ref,'ohm':ohm,
                    'initial_fraction':.0001 if code else .01,'tcr_ppm':5 if code else 100})
            resistor(div[2][n],f'{div[2][2]/1000:g}k 0.01% 5ppm',
                     'PLT0603Z'+div[2][3]+'LST1',sense,'LOGIC_GND')
        window_models.append(data)
    rrows=((101,'3.3k','3K30','CORE_5V','SEQ_5V_OK'),
           (102,'3.3k','3K30','SEQ_5V_OK','CORE_1V2_EN'),(103,'10k','10K0','CORE_1V2_EN','LOGIC_GND'),
           (104,'3.3k','3K30','SEQ_5V_OK','ESP_3V3_EN'),(105,'10k','10K0','ESP_3V3_EN','LOGIC_GND'),
           (106,'6.8k','6K80','CORE_5V','IO_3V3_EN'),(107,'10k','10K0','IO_3V3_EN','LOGIC_GND'),
           (108,'47k','47K0','CORE_5V','SEQ_FPGA_RESET_GOOD'),(109,'470k','470K','SEQ_FPGA_RESET_GOOD','LOGIC_GND'),
           (110,'4.7k','4K70','FPGA_CRESET_N','LOGIC_GND'),(111,'47k','47K0','CORE_5V','SEQ_ESP_RESET_GOOD'),
           (112,'470k','470K','SEQ_ESP_RESET_GOOD','LOGIC_GND'),(113,'47k','47K0','ESP_CHIP_PU','LOGIC_GND'))
    for n,val,code,top,bot in rrows:resistor(f'R{n}',val+' 1%','CRCW0603'+code+'FKEA',top,bot)
    for i,(rail,qual,out) in enumerate((('IO_3V3','SEQ_FPGA_RESET_GOOD','FPGA_CRESET_N'),
                                      ('ESP_3V3','SEQ_ESP_RESET_GOOD','ESP_CHIP_PU'))):
        u=f'U{i+5}';part(u,'SN74LVC1G17DBVR','SN74LVC1G17DBVR','Package_TO_SOT_SMD:SOT-23-5')
        wire(rail,(u,5));wire(qual,(u,2));wire(out,(u,4));wire('LOGIC_GND',(u,3))
        # KiCad records explicitly unconnected pins as distinct singleton nets.
        wire(f'unconnected-({u}-NC-Pad1)',(u,1))
    for i,rail in enumerate(('CORE_5V',)*4+('IO_3V3','ESP_3V3'),1):
        c=f'C{i}';part(c,'100nF 25V X7R 20%','','Capacitor_SMD:C_0603_1608Metric')
        wire(rail,(c,1));wire('LOGIC_GND',(c,2))
    boundary={'JRAIL1':[*RAILS,'LOGIC_GND'],
              'JCTRL1':['CORE_1V2_EN','IO_3V3_EN','ESP_3V3_EN','FPGA_CRESET_N','ESP_CHIP_PU','SEQ_5V_OK','LOGIC_GND']}
    for ref,nets in boundary.items():
        part(ref,'INTEGRATION BOUNDARY','','')
        for pin,net in enumerate(nets,1):wire(net,(ref,pin))
    actual={};seen=set()
    for net in tree.findall('.//nets/net'):
        name=net.attrib['name'].lstrip('/')
        # The exporter appends a UUID to no-connect net names; retain the semantic name.
        name=re.sub(r'^(unconnected-\([^)]*\))-.*$',r'\1',name)
        if name in actual:errors.append('Duplicate net: '+name)
        actual[name]=set()
        for node in net.findall('node'):
            pair=(node.attrib['ref'],node.attrib['pin'])
            if pair in seen:errors.append('Pin repeated: '+str(pair))
            seen.add(pair);actual[name].add(pair)
    for name in sorted(set(expected)|set(actual)):
        if expected.get(name,set())!=actual.get(name,set()):errors.append('Net mismatch: '+name)
    comps=tree.findall('.//components/comp')
    if len(comps)!=len(wanted) or {c.attrib['ref'] for c in comps}!=set(wanted):errors.append('Fitted component set changed')
    for comp in comps:
        data={'value':comp.findtext('value'),'mpn':comp.findtext("./fields/field[@name='MPN']") or '',
              'footprint':comp.findtext('footprint') or ''}
        if data!=wanted.get(comp.attrib['ref']):errors.append('Value/MPN/footprint mismatch: '+comp.attrib['ref'])
        if any(p.attrib.get('name','').lower()=='dnp' for p in comp.findall('property')):errors.append('Required part marked DNP')
    expected_pins={p:(name,'power_in' if p in ('3','4','11','17') else 'open_collector' if p=='12'
                        else 'output' if p=='5' else 'input') for p,name in pin_names.items()}
    bp={'1':('NC','no_connect'),'2':('A','input'),'3':('GND','power_in'),'4':('Y','output'),'5':('VCC','power_in')}
    for name,pins in (('LTC2962HUD',expected_pins),('LVC1G17',bp)):
        rows=tree.findall(f".//libpart[@part='{name}']/pins/pin")
        if len(rows)!=len(pins) or {p.attrib['num']:(p.attrib['name'],p.attrib['type']) for p in rows}!=pins:
            errors.append('Physical pin function/type mismatch: '+name)
    expected_model={'schema_version':1,'manufacturing_ready':False,'candidate_not_production_selection':True,
        'parts':wanted,'pin_map':pin_names,'boundary':boundary,'windows':window_models,
        'monitor_reference_v':[.4975,.5025],'monitor_input_bias_a':15e-9,'resistor_temperature_excursion_c':100,
        'fixed_delay_ms':[160,240],'additional_core5_reservation_a':.010,'additional_core5_cap_max_uf':.552,
        'unproven':['aging_and_assembly_stress','ripple_and_load_transients','brownout_slew_and_filter_delay',
            'arbitrary_partial_power','shutdown_order','FPGA_package_supply_mapping','machine_permission',
            'physical_qualification','production_cost']}
    for key,value in expected_model.items():
        if model.get(key)!=value:errors.append('Unreviewed model: '+key)
    for rail,limits in zip(RAILS,LIMITS):
        row=[r for r in design['rails'] if r['id']==rail]
        if len(row)!=1 or (row[0]['min_v'],row[0]['max_v'])!=limits[:2]:errors.append('Frozen rail limits changed: '+rail)
    if not all(r['static_acceptance_and_detection'] for r in windows()):errors.append('Fresh static threshold envelope failed')
    if all(r['static_acceptance_and_detection'] for r in windows(.0004)):
        errors.append('Aging sensitivity unexpectedly accepted; recheck corner model')
    ens=enable_corners()
    for case in ens['coupled_core_esp']:
        if case['seq5_v'][0]<1.6:errors.append('Coupled MR high insufficient')
        for key in ('core_en_v','esp_en_v'):
            if case[key][0]<1.03 or case[key][1]>3.6:errors.append('Coupled EN out of allowed window')
    for case in ens['io']:
        if case['en_v'][0]<1.6 or case['en_v'][1]>3.6:errors.append('IO EN/MR out of allowed window')
    resets=reset_bounds()
    if resets['qualifier_high_v'][0]<3.33:errors.append('Reset Schmitt high margin insufficient')
    if resets['esp_reset_high_load_a_including_20ua_allowance']>100e-6:errors.append('ESP VOH proof exceeds100uA test load')
    if resets['qualifier_zero_core5_v_with_5u1a_leak']>=.89:errors.append('Zero CORE5 qualifier can remain high')
    if footprint_text is not None:
        pads=re.findall(r'\(pad "(\d+)" smd roundrect \(at ([^ ]+) ([^)]+)\) \(size ([^ ]+) ([^)]+)\)',footprint_text)
        expected_pad={str(i+1):(-1.4,-.75+i*.5,.7,.25) for i in range(4)}
        expected_pad.update({str(i+5):(-.75+i*.5,1.4,.25,.7) for i in range(4)})
        expected_pad.update({str(i+9):(1.4,.75-i*.5,.7,.25) for i in range(4)})
        expected_pad.update({str(i+13):(.75-i*.5,-1.4,.25,.7) for i in range(4)})
        expected_pad['17']=(0,0,1.45,1.45)
        try:actual_pads={p[0]:tuple(float(v) for v in p[1:]) for p in pads}
        except ValueError:actual_pads={}
        if len(pads)!=17 or actual_pads!=expected_pad:errors.append('UD16 manufacturer pad map differs')
    return errors


def main():
    frozen=OUT/'input-electrical-design.json';design=json.loads(frozen.read_text(encoding='utf-8'))
    model=json.loads((OUT/'design-envelope.json').read_text(encoding='utf-8'));tree=ET.parse(OUT/'netlist.xml')
    fp=(OUT/'CNC_Power.pretty/LTC2962_UD16.kicad_mod').read_text(encoding='utf-8')
    errors=validate(tree,design,model,fp)
    if model['source_ledger_sha256']!=hashlib.sha256(frozen.read_bytes()).hexdigest():errors.append('Frozen ledger hash differs')
    erc=json.loads((OUT/'erc.json').read_text());violations=[v for s in erc['sheets'] for v in s['violations']]
    if violations:errors.append(f'ERC violations: {len(violations)}')
    paths=[ROOT/p for p in ('tools/hardware_build_power_sequence.py','tools/hardware_validate_power_sequence.py',
        'tools/hardware_build_tx_schematic.py','tools/hardware_build_logic_power.py','tests/test_power_sequence.py','reports/POWER_SEQUENCE.md')]
    paths += [p for p in OUT.rglob('*') if p.is_file() and p.name!='validation.json' and p.suffix!='.kicad_prl']
    paths += [p for p in (ROOT/'research/power-sequence').rglob('*') if p.is_file()]
    result={'schema_version':1,'scope':'autonomous power window and reset engineering candidate',
        'consistency_pass':not errors,'manufacturing_ready':False,'errors':errors,
        'component_count':len(tree.findall('.//components/comp')),'net_count':len(tree.findall('.//nets/net')),
        'threshold_static_corners':windows(),'threshold_aging_sensitivity_400ppm':windows(.0004),
        'enable_corners':enable_corners(),'reset_bounds':reset_bounds(),
        'additional_core5_reservation_a':.010,'additional_core5_cap_max_uf':.552,
        'kicad_version':erc['kicad_version'],'erc_violations':len(violations),'erc_ignored_checks':erc['ignored_checks'],
        'source_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths) if p.exists()},
        'boundary':'Exact export and fresh static corners only; lifetime, transient, partial-power, reset configuration and physical evidence remain open'}
    (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f"Power sequence: {'PASS' if not errors else 'FAIL'}; {len(errors)} issues; manufacturing blocked")
    for error in errors:print(error)
    return bool(errors)


if __name__=='__main__':sys.exit(main())
