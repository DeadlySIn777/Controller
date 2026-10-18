"""Independent native-netlist checks of the real IS-2 sixteen-path receiver."""
from __future__ import annotations
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/motherboard_fast_inputs'


def validate(tree,model):
    errors=[];actual={};seen=set()
    for net in tree.findall('./nets/net'):
        name=net.attrib['name'].removeprefix('/')
        nodes={(n.attrib['ref'],n.attrib['pin']) for n in net.findall('node')}
        if name in actual:errors.append('Duplicate net '+name)
        for node in nodes:
            if node in seen:errors.append('Pin occurs on multiple nets '+str(node))
            seen.add(node)
        actual[name]=nodes
    expected=defaultdict(set)
    def connect(net,ref,pin):expected[net].add((ref,str(pin)))
    # Pin groups transcribed independently from TI SLLS849E Table5-1/PW16.
    groups=((2,1,3),(6,7,5),(10,9,11),(14,15,13))
    names=[f'ENC{i}_{s}' for i in range(4) for s in 'ABZ']+['FREQ0','FREQ1','MPG_A','MPG_B']
    for i,name in enumerate(names):
        bank,local=divmod(i,4);positive,negative,output=groups[local];ref=f'U{bank+1}'
        connect(name+'_P',ref,positive);connect(name+'_N',ref,negative);connect(name+'_FPGA',ref,output)
        connect(name+'_P',f'R{i+1}',1);connect(name+'_N',f'R{i+1}',2)
        connect(name+'_FPGA','B8',i+3)
        if i<12:
            enc,sig=divmod(i,3);bref=f'B{enc+1}';p=3+sig*2
        elif i<14:bref='B5';p=3+(i-12)*2
        else:bref='B6';p=3+(i-14)*2
        connect(name+'_P',bref,p);connect(name+'_N',bref,p+1)
    for bank in range(4):
        ref=f'U{bank+1}'
        for pin in (4,12,16):connect('IO_3V3',ref,pin)
        connect('LOGIC_GND',ref,8)
    for i in range(1,9):connect('IO_3V3',f'C{i}',1);connect('LOGIC_GND',f'C{i}',2)
    connect('IO_3V3','B8',1);connect('LOGIC_GND','B8',2)
    for i in range(4):
        bref=f'B{i+1}';net=f'ENC{i}_5V_LIMITED'
        connect(net,bref,1);connect(net,'B7',i+1)
        for pin in (2,9):connect('LOGIC_GND',bref,pin)
        connect('CHASSIS',bref,10)
    for bref,net,powerpin in [('B5','FREQ_5V_LIMITED',5),('B6','MPG_5V_LIMITED',6)]:
        connect(net,bref,1);connect(net,'B7',powerpin)
        for pin in (2,9):connect('LOGIC_GND',bref,pin)
        connect('CHASSIS',bref,10)
    connect('MPG_VREF_2V5','B6',7);connect('MPG_VREF_2V5','B7',7)
    connect('LOGIC_GND','B7',8);connect('CHASSIS','B7',9)
    for net,ref,pin,outpin in [('FREQ_MOD_ID_TO_FRONTEND','B5',7,1),('FREQ_MOD_PRESENT_TO_FRONTEND','B5',8,2),('MPG_ENABLE_TO_STATUS','B6',8,3)]:
        connect(net,ref,pin);connect(net,'B9',outpin)
    for net in sorted(set(actual)|set(expected)):
        if actual.get(net,set())!=expected.get(net,set()):
            errors.append(f'{net}: missing={sorted(expected.get(net,set())-actual.get(net,set()))}; extra={sorted(actual.get(net,set())-expected.get(net,set()))}')
    components={c.attrib['ref']:c for c in tree.findall('./components/comp')}
    refs={*[f'U{i}' for i in range(1,5)],*[f'C{i}' for i in range(1,9)],*[f'R{i}' for i in range(1,17)],*[f'B{i}' for i in range(1,10)]}
    if set(components)!=refs:errors.append('Wrong receiver/component population')
    source_components=model.get('components',{})
    if not isinstance(source_components,dict) or set(source_components)!=refs:
        errors.append('Source component map is not keyed by the exact native references')
        source_components={}
    native_pin_nets={node:name for name,nodes in actual.items() for node in nodes}
    for ref,comp in components.items():
        value=comp.findtext('value');footprint=comp.findtext('footprint','');mpn=comp.findtext("./fields/field[@name='MPN']",'') or ''
        prop={p.attrib['name'] for p in comp.findall('property')}
        source=source_components.get(ref,{})
        source_pin_map=source.get('pins',{})
        native_pin_map={pin:name for (nref,pin),name in native_pin_nets.items() if nref==ref}
        if source_pin_map!=native_pin_map:
            errors.append('Source model pin map differs from native XML '+ref)
        if (source.get('value'),source.get('footprint'),source.get('mpn'),source.get('physical'),source.get('dnp')) != (value,footprint,mpn,not ref.startswith('B'),'dnp' in prop):
            errors.append('Source component part/fit/scope differs from native XML '+ref)
        if ref.startswith('U') and (value,footprint,mpn)!=('AM26LV32EIPWR','Package_SO:TSSOP-16_4.4x5mm_P0.65mm','AM26LV32EIPWR'):
            errors.append('Wrong receiver MPN/package '+ref)
        if ref.startswith('C'):
            odd=int(ref[1:])%2==1
            good=('100nF 100V X7R','Capacitor_SMD:C_0603_1608Metric','GRM188R72A104KA35D') if odd else ('1uF 16V X7R','Capacitor_SMD:C_0603_1608Metric','885012206052')
            if (value,footprint,mpn)!=good:errors.append('Wrong local bypass '+ref)
        if ref.startswith('R'):
            fit=int(ref[1:])<15
            good=('120R 1% 0.5W / '+('FIT' if fit else 'DNP'),'Resistor_SMD:R_1210_3225Metric','CRCW1210120RFKEA')
            if (value,footprint,mpn)!=good or ('dnp' in prop)==fit:errors.append('Wrong termination fit/rating '+ref)
        if ref.startswith('B'):
            if footprint or mpn or not {'exclude_from_bom','exclude_from_board'}.issubset(prop):
                errors.append('Nonphysical boundary became a fabricated connector '+ref)
        elif {'exclude_from_bom','exclude_from_board'} & prop:errors.append('Physical component excluded '+ref)
    if any(n.attrib.get('pintype','').endswith('no_connect') for n in tree.findall('./nets/net/node')):
        errors.append('Used receiver region contains undeclared NC')
    if [c.get('channel') for c in model.get('channels',[])]!=names:errors.append('Channel map capacity/order changed')
    for i,c in enumerate(model.get('channels',[])):
        if i>=len(names):break
        bank,local=divmod(i,4);p,n,o=groups[local]
        if (c.get('receiver'),c.get('positive_pin'),c.get('negative_pin'),c.get('output_pin'),c.get('logic_net'),c.get('termination_fitted')) != (f'U{bank+1}',p,n,o,names[i]+'_FPGA',i<14):
            errors.append('Channel source map differs from native normative mapping '+str(i))
    term=model.get('termination',{})
    for key,val in {'mpn':'CRCW1210120RFKEA','ohms':120,'tolerance':.01,'tcr_ppm_per_k':100,
                    'conservative_temperature_excursion_k':150,'maximum_applied_differential_v':5.5,
                    'rating_w_at70c':.5,'initial_local_ambient_max_c':70,'MPG_default':'DNP_open_only','physical_thermal_qualified':False}.items():
        if term.get(key)!=val:errors.append('Termination envelope changed '+key)
    minimum=120*.99*.985;power=5.5**2/minimum
    for key,value in [('minimum_ohms',minimum),('worst_w_per_fitted_channel',power),('worst_w_all_14_fitted',14*power),('worst_w_if_all16_fitted',16*power)]:
        actual_value=term.get(key)
        if type(actual_value) not in (float,int) or not math.isfinite(actual_value) or abs(actual_value-value)>1e-9:
            errors.append('Termination arithmetic changed '+key)
    if model.get('manufacturing_ready') is not False or model.get('unused_receiver_channels')!=[]:
        errors.append('Scope/readiness or used-channel declaration changed')
    return errors


def main():
    model=json.loads((OUT/'design.json').read_text());tree=ET.parse(OUT/'netlist.xml')
    errors=validate(tree,model)
    erc=json.loads((OUT/'erc.json').read_text());violations=[v for sheet in erc['sheets'] for v in sheet['violations']]
    if violations:errors.append(f'ERC has {len(violations)} violations')
    if erc.get('ignored_checks'):errors.append('Native ERC has ignored checks')
    files=[ROOT/'tools/hardware_build_motherboard_fast_inputs.py',ROOT/'tools/hardware_validate_motherboard_fast_inputs.py',ROOT/'tests/test_motherboard_fast_inputs.py']
    files += [p for p in OUT.iterdir() if p.is_file() and p.name not in ['validation.json','motherboard_fast_inputs.kicad_prl']]
    result={'schema_version':1,'revision':'MB-FAST-r0.1','consistency_pass':not errors,'manufacturing_ready':False,
            'errors':errors,'native_ERC_violations':len(violations),'ERC_ignored_checks':erc.get('ignored_checks'),
            'native_KiCad_version':erc['kicad_version'],'receiver_ics':4,'used_receiver_channels':16,'unused_receiver_channels':0,
            'schematic_components_including_boundaries':len(tree.findall('./components/comp')),'physical_footprints':28,'fitted_physical_parts':26,'DNP_parts':2,
            'native_nets':len(tree.findall('./nets/net')),'independent_physical_pin_map_matches':not errors,
            'termination':model['termination'],'open_gates':model['open_gates'],
            'source_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.exists()},
            'evidence_boundary':'Native circuit ERC/XML and source/arithmetic only; no parent integration, PCB DRC/routing, target or physical qualification.'}
    (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['consistency_pass','errors','native_ERC_violations','ERC_ignored_checks','receiver_ics','used_receiver_channels','native_nets','fitted_physical_parts','DNP_parts']},indent=2))
    return bool(errors)


if __name__=='__main__':sys.exit(main())
