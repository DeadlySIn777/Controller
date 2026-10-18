"""Independent frozen-terminal semantics, native pins, domains and vendor lands."""
import argparse, hashlib, json, re, xml.etree.ElementTree as ET
from pathlib import Path
from hardware_build_assembly import parse, child, children, point, value
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'hardware/motherboard_terminals'
LIB=Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')
PRIMARY={2:('1844210','1840366',8.4),3:('1844223','1840379',11.9),
    6:('1844252','1840405',22.4),10:('1844294','1840447',36.4),
    12:('1844317','1840463',43.4),14:('1844333','1840489',50.4)}


def expected_terminal(row):
    """Interpret the frozen logical function, independently of generated aliases."""
    name=row['logical_connector'];pos=row['logical_position']
    if name.startswith('XM'):
        i=int(name[2:]);bank='A' if i<8 else 'B'
        return [f'STEP{i}_P',f'STEP{i}_N',f'DIR{i}_P',f'DIR{i}_N','LOGIC_GND','CHASSIS',
            None,f'EN{i}_NO',f'EN{i}_COM',f'EN{i}_NC',f'AUX_5V_{bank}',f'AUX_24V_{bank}',
            'FIELD_GND',f'ALM{i}_FIELD'][pos-1]
    if name.startswith('XE'):
        i=int(name[2:]);return [f'ENC{i}_5V_LIMITED','LOGIC_GND',f'ENC{i}_A_P',f'ENC{i}_A_N',
            f'ENC{i}_B_P',f'ENC{i}_B_N',f'ENC{i}_Z_P',f'ENC{i}_Z_N','LOGIC_GND','CHASSIS'][pos-1]
    if name.startswith('XDI'):
        i=int(name[3:]);return ([f'DI{k}_FIELD' for k in range(8*i,8*i+8)]+
            [f'SENS24_G{i}']*2+['FIELD_B_0V']*2)[pos-1]
    if name.startswith('XDO'):
        i=int(name[3:]);return ([f'DO{k:02d}' for k in range(8*i,8*i+8)]+
            [f'FIELD_{"A" if i==0 else "B"}_0V']*4)[pos-1]
    table={'XPE1':['CHASSIS'],'XH1':['MPG_5V_LIMITED','LOGIC_GND','MPG_A_P','MPG_A_N',
        'MPG_B_P','MPG_B_N','MPG_VREF_2V5','MPG_ENABLE','LOGIC_GND','CHASSIS'],
        'XH2':[f'MPG_SEL_{a}' for a in 'XYZABC']+['MPG_MUL_X1','MPG_MUL_X10','MPG_MUL_X100','MPG_PEND_AUX','LOGIC_GND','CHASSIS'],
        'XPR':['PRB0_IN','PRB0_24V','FIELD_GND','PRB1_IN','PRB1_24V','FIELD_GND'],
        'XF':['FREQ_5V_LIMITED','LOGIC_GND','FREQ0_P','FREQ0_N','FREQ1_P','FREQ1_N','FREQ_MOD_ID_TO_FRONTEND','FREQ_MOD_PRESENT_TO_FRONTEND','LOGIC_GND','CHASSIS'],
        'XPW':['PWM0','LOGIC_GND','PWM1','LOGIC_GND','PWM_5V_AUX','CHASSIS'],
        'XPC0':['PEN0_1','PEN0_2'],'XPC1':['PEN1_1','PEN1_2'],
        'XAO':['AO0_OUT','AO0_COM','CHASSIS','AO1_OUT','AO1_COM','CHASSIS'],
        'XAI':[f'AI{i}_{s}' for i in range(4) for s in ('P','N')]+['AI_REF_10V','AI_SENS_24V','AI_AGND','CHASSIS'],
        'XB1':['RS485_B','RS485_A','RS485_COM','RS485_TERM','CHASSIS','RS485_COM'],
        'XB2':['CAN_H','CAN_L','CAN_GND','CAN_TERM','CHASSIS','CAN_GND'],
        'XS1':['SAFE_24V','EXT_PERMIT_IN','PROCESS_PERMIT_IN','SAFETY_STATUS_IN','RESET_ARM_IN',
            'ARM_LAMP','CONTACTOR_FB_IN','STO_FB_IN','FIELD_B_0V','PERMIT_OUT_1','PERMIT_OUT_2','CHASSIS']}
    return table[name][pos-1]


def validate(tree, model, geometry=True):
    errors=[];actual={};codes={};parts=model['components']
    for net in tree.findall('.//nets/net'):
        codes.setdefault(net.attrib['name'],set()).add(net.attrib['code'])
        for p in net.findall('node'):
            key=p.attrib['ref'],p.attrib['pin']
            if key in actual:errors.append('Repeated native pin '+repr(key))
            actual[key]=(net.attrib['name'],net.attrib['code'])
    native={p.attrib['ref']:p for p in tree.findall('.//components/comp') if p.attrib['ref'] in parts}
    if set(parts)!=set(native):errors.append('Exact physical inventory mismatch')
    for ref,p in parts.items():
        if ref not in native:continue
        for key,v in [('value',p['value']),('footprint',p['footprint'])]:
            if native[ref].findtext(key)!=v:errors.append('Native '+key+' mismatch '+ref)
        if native[ref].findtext("./fields/field[@name='MPN']",'')!=p['mpn']:errors.append('Native MPN mismatch '+ref)
        if {pin for r,pin in actual if r==ref}!=set(p['pins']):errors.append('Exact pad inventory mismatch '+ref)
        for pin,net in p['pins'].items():
            observed=actual.get((ref,pin),('MISSING',''))[0]
            if net is None:
                if not observed.startswith('unconnected-'):errors.append('Deliberate motor NC must be disconnected '+ref+'.'+pin)
            elif observed!='/'+net:errors.append('Native pin/net mismatch '+ref+'.'+pin)
    requirements=json.loads((ROOT/'hardware/motherboard/requirements.json').read_text(encoding='utf8'))
    required={r['source_id']:r for r in requirements['terminal_function_mapping'] if r['scope']=='motherboard_standard'}
    ledger=model['terminal_ledger'];byid={r['source_id']:r for r in ledger}
    if len(byid)!=len(ledger) or set(byid)!=set(required):errors.append('Exactly371 frozen terminal functions required')
    for sid,row in byid.items():
        if sid not in required:continue
        spec=required[sid]
        if spec['logical_connector'] in ('XP1','XP2','XP3'):
            i=int(spec['logical_connector'][-1])-1;pos=spec['logical_position']
            expected=(f'J{11001+2*i+(pos-1)//2}',str(1+(pos-1)%2))
            if (row['reference'],row['pin'])!=expected or not row.get('reused_existing_power_entry'):
                errors.append('Existing power header must be reused '+sid)
            continue
        wanted=expected_terminal(spec);key=row['reference'],row['pin']
        if wanted is None:
            if not row.get('NC_reason') or not actual.get(key,('',''))[0].startswith('unconnected-'):
                errors.append('Documented motor isolation NC required '+sid)
        elif row.get('source_net')!=wanted or actual.get(key,('',''))[0]!='/'+wanted:
            errors.append('Actual terminal must implement frozen function '+sid)
    domains=['LOGIC_GND','FIELD_GND','FIELD_B_0V','AO0_COM','AO1_COM','AI_AGND','RS485_COM','CAN_GND','CHASSIS']
    if any(len(codes.get('/'+n,set()))!=1 for n in domains):errors.append('Each domain needs one distinct native electrical net')
    if len({next(iter(codes.get('/'+n,{'MISSING'}))) for n in domains})!=len(domains):errors.append('Isolated return/chassis domains must never be DC joined')
    couplings=[p for r,p in parts.items() if r.startswith('C')]
    if len(couplings)!=9 or sorted(p['pins']['1'] for p in couplings)!=sorted(domains[:-1]+['LOGIC_GND']):errors.append('Exact nine AC-only chassis couplings required')
    for p in couplings:
        if p['mpn']!='VY2472M49Y5US63V7' or p['pins']['2']!='CHASSIS':errors.append('Exact Vishay HF coupling part/domain required')
    if geometry:
        for ref,p in parts.items():
            lib,name=p['footprint'].split(':',1);file=LIB/(lib+'.pretty')/(name+'.kicad_mod')
            if not file.exists():errors.append('Footprint unavailable '+ref);continue
            fp=parse(file.read_text(encoding='utf8'));pads={value(x[1]):x for x in children(fp,'pad') if value(x[1])}
            if set(pads)!=set(p['pins']):errors.append('Native footprint numbered inventory mismatch '+ref)
            if p['kind'].startswith('Header'):
                n=int(p['kind'][6:]);mpn,plug,width=PRIMARY[n]
                if p['mpn']!=mpn or p['mating_plug_mpn']!=plug:errors.append('Manufacturer mating pair mismatch '+ref)
                fab=[r for r in children(fp,'fp_rect') if value(child(r,'layer')[1])=='F.Fab']
                if len(fab)!=1 or point(child(fab[0],'start'))!=(-2.45,-1.2) or point(child(fab[0],'end'))!=(round(width-2.45,6),8.):errors.append('Manufacturer body/insertion orientation mismatch '+ref)
                for number,pad in pads.items():
                    if point(child(pad,'at'))!=(3.5*(int(number)-1),0.) or float(child(pad,'drill')[1])!=1.2 or point(child(pad,'size'))!=(1.8,3.6):errors.append('Manufacturer header pitch/drill/land mismatch '+ref+'.'+number)
            elif p['kind']=='C':
                if point(child(pads['1'],'at'))!=(0.,0.) or point(child(pads['2'],'at'))!=(7.5,0.):errors.append('Vishay lead pitch mismatch '+ref)
                if any(float(child(q,'drill')[1])!=1. for q in pads.values()):errors.append('Vishay lead clearance drill mismatch '+ref)
            elif p['kind']=='MOUNT':
                pad=pads['1']
                if float(child(pad,'drill')[1])!=4.3 or point(child(pad,'size'))!=(8.6,8.6):errors.append('Actual plated M4 bond geometry required')
                if p.get('purchased') is not False or not p.get('exclude_from_position'):errors.append('Bare M4 pad must not become purchased assembly part')
    return errors


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',type=Path,default=SOURCE);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    model=json.loads((a.source/'design.json').read_text(encoding='utf8'));tree=ET.parse(a.source/'netlist.xml');errors=validate(tree,model)
    report=dict(ok=not errors,errors=errors,physical_parts=len(model['components']),terminal_functions=len(model['terminal_ledger']),
        exact_header_families=6,native_checks=True,manufacturer_dimension_checks=True,manufacturing_ready=False,
        remaining=['Native PCB edge orientation/mated envelopes/tool access','Parent fitted-provider integration and zero copper joins',
            'Measured chassis bond/EMC/leakage; separate enclosure protective-earth fault path'])
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(report));raise SystemExit(bool(errors))


if __name__=='__main__':main()
