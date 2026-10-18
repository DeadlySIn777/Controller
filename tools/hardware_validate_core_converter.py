"""Independent connection contract for the drawn LM70660 core converter."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/core_converter'


def validate(tree):
    errors=[];expected=defaultdict(set);actual={};seen=set()
    def add(net,ref,pin):expected[net].add((ref,str(pin)))
    pins={1:'CORE_24V_PROTECTED',2:'CORE_24V_PROTECTED',3:'CORE_24V_PROTECTED',4:'CORE_BOOT',5:'CORE_SW_BOOT',
          6:'CORE_5V',7:'CORE_5V_PG',8:'CORE_VDDA',9:'C_PGOOD',11:'CORE_ISNS',12:'CORE_5V',13:'CORE_CONFIG',
          14:'CORE_RT',15:'CORE_COMP',16:'CORE_FB_SELECT',17:'LOGIC_GND',18:'CORE_VDDA',19:'CORE_VCC',
          20:'CORE_SW',21:'CORE_SW',22:'CORE_SW',23:'LOGIC_GND',24:'LOGIC_GND',25:'LOGIC_GND',26:'LOGIC_GND',
          27:'CORE_24V_PROTECTED',28:'CORE_24V_PROTECTED',29:'CORE_24V_PROTECTED',30:'LOGIC_GND'}
    for pin,net in pins.items():add(net,'U1',pin)
    parts={
        'L1':('4.7uH 20%','CORE_SW','CORE_ISNS'), 'RS1':('6mOhm 1% 1.5W','CORE_ISNS','CORE_5V'),
        'CBST1':('47nF25V X7R','CORE_BOOT','CORE_SW_BOOT'), 'CVCC1':('4.7uF16V X7R','CORE_VCC','LOGIC_GND'),
        'CVDDA1':('100nF16V X7R','CORE_VDDA','LOGIC_GND'), 'RFBSEL1':('24.9k1%','CORE_FB_SELECT','CORE_VDDA'),
        'RRT1':('49.9k0.1%','CORE_RT','LOGIC_GND'), 'RCFG1':('29.4k1%','CORE_CONFIG','LOGIC_GND'),
        'RCOMP1':('9.53k1%','CORE_COMP','CORE_COMP_ZERO'), 'CCOMP1':('22nF5% C0G','CORE_COMP_ZERO','LOGIC_GND'),
        'CHF1':('330pF5% C0G','CORE_COMP','LOGIC_GND'), 'RENHI1':('100k0.1%','CORE_24V_PROTECTED','C_PGOOD'),
        'RENLO1':('10k0.1%','C_PGOOD','LOGIC_GND'), 'RPG1':('100k1%','CORE_5V_PG','IO_3V3')}
    for i in range(1,5):
        parts[f'CIN{i}']=('4.7uF100V X7S 10% 1210','CORE_24V_PROTECTED','LOGIC_GND')
    for i in range(1,4):
        parts[f'COUT{i}']=('47uF10V X7S 20% 1210','CORE_5V','LOGIC_GND')
    for i in (1,2,3):parts[f'CBULK{i}']=('330uF16V 20% polymer','CORE_5V','LOGIC_GND')
    for i in (1,2):parts[f'CINHF{i}']=('10nF100V X7R','CORE_24V_PROTECTED','LOGIC_GND')
    for ref,(_,a,b) in parts.items():add(a,ref,1);add(b,ref,2)
    bounds={'JIN1':['CORE_24V_PROTECTED','LOGIC_GND'],'JOUT1':['CORE_5V','LOGIC_GND'],
            'JCTRL1':['C_PGOOD','LOGIC_GND','CORE_5V_PG'],'JDIAG1':['IO_3V3','LOGIC_GND']}
    for ref,nets in bounds.items():
        for i,net in enumerate(nets,1):add(net,ref,i)
    nc=set()
    for net in tree.findall('.//nets/net'):
        name=net.attrib['name'].lstrip('/')
        nodes=[(n.attrib['ref'],n.attrib['pin']) for n in net.findall('node') if not n.attrib['ref'].startswith('#')]
        if len(nodes)!=len(set(nodes)) or seen.intersection(nodes):errors.append('Duplicate pin membership')
        seen.update(nodes)
        if name.startswith('unconnected-'):
            if len(nodes)!=1:errors.append('Grouped no-connect')
            nc.update(nodes)
        else:
            if name in actual:errors.append('Duplicate net name')
            actual[name]=set(nodes)
    if nc!={('U1','10')}:errors.append('NC pin changed')
    for name in set(actual)|set(expected):
        if actual.get(name,set())!=expected.get(name,set()):errors.append('Connectivity differs: '+name)
    cs=tree.findall('.//components/comp');comps={c.attrib['ref']:c for c in cs}
    if len(cs)!=len(comps) or set(comps)!=set(parts)|set(bounds)|{'U1'}:errors.append('Population differs')
    for ref,(v,_,_) in parts.items():
        if ref not in comps or comps[ref].findtext('value')!=v:errors.append('Value differs: '+ref)
    mpns={'U1':'LM70660RRXR','L1':'XAL7070-472MEC','RS1':'KRL3216D-C-R006-F-T1'}
    mpns.update({f'CIN{i}':'CGA6M3X7S2A475K200AE' for i in range(1,5)})
    mpns.update({f'COUT{i}':'CGA6P1X7S1A476M250AC' for i in range(1,4)})
    mpns.update({f'CBULK{i}':'16SVPG330M' for i in (1,2,3)})
    for ref,mpn in mpns.items():
        if ref not in comps or comps[ref].findtext("./fields/field[@name='MPN']")!=mpn:errors.append('MPN differs: '+ref)
    for ref,c in comps.items():
        if any(p.attrib.get('name','').lower()=='dnp' for p in c.findall('property')):errors.append('Unreviewed DNP: '+ref)
    for ref in ('U1','RS1','CBULK1','CBULK2','CBULK3'):
        if comps.get(ref) is not None and comps[ref].findtext('footprint') not in ('',None):errors.append('Unreviewed special footprint: '+ref)
    pg=tree.find(".//libpart[@part='LM70660RRXR']/pins/pin[@num='7']")
    if pg is None or pg.attrib.get('type')!='open_collector':errors.append('PG type changed')
    return errors


def main():
    errors=validate(ET.parse(OUT/'netlist.xml'))
    erc=json.loads((OUT/'erc.json').read_text())
    count=sum(len(s['violations']) for s in erc['sheets'])
    if count:errors.append(f'ERC has {count} violations')
    files=[p for p in OUT.rglob('*') if p.is_file() and p.name!='validation.json' and '__pycache__' not in p.parts]
    files += [Path(__file__),ROOT/'tools/hardware_build_core_converter.py',ROOT/'tools/hardware_build_assembly.py',
              ROOT/'tools/hardware_build_tx_schematic.py',ROOT/'tests/test_core_converter.py']
    result={'schema_version':1,'manufacturing_ready':False,'consistency_pass':not errors,'errors':errors,
            'kicad_version':erc['kicad_version'],'erc_violations':count,'source_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
            'scope':'Actual circuit connections and bounded part selection; no load-step, stability, startup, thermal or physical qualification'}
    (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Core converter:', 'PASS' if not errors else errors)
    return bool(errors)


if __name__=='__main__':raise SystemExit(main())
