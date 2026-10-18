"""Independent netlist contract for the partial two-domain power-entry circuit."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'hardware/power_entry'


def validate(tree):
    errors, actual, expected = [], {}, defaultdict(set)
    unused = {(f'U{i}', str(pin)) for i in (1,2) for pin in (11,19,20,21,22,23,24)}
    disconnected, seen_pins = set(), set()
    for net in tree.findall('.//nets/net'):
        name = net.attrib['name'].lstrip('/')
        node_list = [(p.attrib['ref'],p.attrib['pin']) for p in net.findall('node') if not p.attrib['ref'].startswith('#')]
        nodes = set(node_list)
        if len(nodes) != len(node_list) or seen_pins.intersection(nodes):
            errors.append('Duplicate pin membership: '+name)
        seen_pins.update(nodes)
        if name.startswith('unconnected-'):
            disconnected.update(nodes)
            if len(nodes) != 1: errors.append('Unconnected net groups multiple pins: '+name)
        else:
            if name in actual:errors.append('Duplicate net name: '+name)
            actual[name] = nodes
    if disconnected != unused: errors.append('MODE/unused-pin explicit no-connect set changed')

    def add(net, ref, pin):expected[net].add((ref,str(pin)))
    values, mpns, footprints = {}, {}, {}
    for b,(prefix,ground,diag,out,ilim) in enumerate([
            ('C','LOGIC_GND','IO_3V3','CORE_24V_PROTECTED','7.50k 0.1%'),
            ('F','FIELD_GND','FIELD_5V','FIELD_24V_PROTECTED','3.65k 0.1%')]):
        def n(s):return prefix+'_'+s
        u,q1,q2 = f'U{b+1}',f'Q{b*2+1}',f'Q{b*2+2}'
        # Datasheet RGE24 contract, independent of generator/pin-map.json.
        pins={1:n('IN'),2:n('IN'),3:n('BG'),4:n('DRV'),5:n('RAW'),6:n('UV'),7:n('OV'),8:ground,
              9:n('DVDT'),10:n('ILIM'),12:n('SHDN'),13:n('IMON'),14:n('FAULT_N'),15:n('PGTH'),
              16:n('PGOOD'),17:out,18:out,25:ground}
        for pin,net in pins.items():add(net,u,pin)
        for pin,net in {1:n('RAW'),2:n('RAW'),3:n('RAW'),4:n('BG'),5:n('IN')}.items():add(net,q1,pin)
        for pin,net in {1:n('DRV'),2:n('RAW'),3:n('BG')}.items():add(net,q2,pin)
        mpns.update({u:'TPS26630RGER',q1:'CSD19537Q3',q2:'BSS138P,215',f'D{b*2+1}':'SMCJ30CA'})
        footprints[u]='Package_DFN_QFN:Texas_RGE0024H_VQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm'
        footprints[q1]='Package_SON:VSON-8_3.3x3.3mm_P0.65mm_NexFET'
        footprints[q2]='Package_TO_SOT_SMD:SOT-23'
        parts = [
            (f'F{b+1}','DC FUSE / RATING TBD',n('INPUT'),n('RAW')),
            (f'D{b*2+1}','SMCJ30CA / CANDIDATE',n('RAW'),ground),
            (f'D{b*2+2}','OUTPUT CLAMP / MPN TBD',out,ground),
            (f'C{b*4+1}','2.2uF 100V X7R / CANDIDATE',n('RAW'),ground),
            (f'C{b*4+2}','100nF 5% C0G / dVdT',n('DVDT'),ground),
            (f'C{b*4+3}','1uF 100V X7R',n('IN'),ground),
            (f'C{b*4+4}','1uF 100V X7R',out,ground)]
        resistors=[('887k 0.1%',n('RAW'),n('UV')),('29.4k 0.1%',n('UV'),n('OV')),
                   ('34.0k 0.1%',n('OV'),ground),(ilim,n('ILIM'),ground),
                   ('140k 0.1%',out,n('PGTH')),('10.0k 0.1%',n('PGTH'),ground),
                   ('10.0k 0.1%',n('IMON'),ground),('10k 1%',diag,n('FAULT_N'))]
        parts.extend((f'R{b*20+i}',value,a,z) for i,(value,a,z) in enumerate(resistors,1))
        for ref,value,a,z in parts:
            values[ref]=value;add(a,ref,1);add(z,ref,2)
        values[u]='TPS26630RGER';values[q1]='CSD19537Q3';values[q2]='BSS138P,215'
        for ref,label,nets in [(f'JIN{b+1}','DC INPUT BOUNDARY',[n('INPUT'),ground]),
                               (f'JOUT{b+1}','TO CONVERTER / LOADS',[out,ground]),
                               (f'JRESET{b+1}','DRY CONTACT: SHUTDOWN/CLEAR',[n('SHDN'),ground]),
                               (f'JSTAT{b+1}','LOCAL STATUS + EN CONTROL',[diag,ground,n('PGOOD'),n('FAULT_N'),n('IMON')])]:
            values[ref]=label
            for pin,net in enumerate(nets,1):add(net,ref,pin)
    for net in sorted(set(expected)|set(actual)):
        if expected.get(net,set()) != actual.get(net,set()):errors.append('Connectivity differs: '+net)
    comp_list=[c for c in tree.findall('.//components/comp') if not c.attrib['ref'].startswith('#')]
    comps={c.attrib['ref']:c for c in comp_list}
    if len(comps) != len(comp_list):errors.append('Duplicate component identity')
    if set(comps)!=set(values):errors.append('Component population changed')
    for ref,value in values.items():
        c=comps.get(ref)
        if c is None or c.findtext('value')!=value:errors.append('Value/default differs: '+ref)
        if c is not None and ref in mpns and c.findtext("./fields/field[@name='MPN']")!=mpns[ref]:errors.append('Device MPN differs: '+ref)
        if c is not None and ref in footprints and c.findtext('footprint')!=footprints[ref]:errors.append('Device footprint differs: '+ref)
        if c is not None and any(p.attrib.get('name','').lower() == 'dnp' for p in c.findall('property')):
            errors.append('Required component marked DNP: '+ref)
    # Preserve ERC semantics, including the two contacts of one shared OUT node.
    pin_types={1:'power_in',2:'power_in',3:'output',4:'output',5:'power_in',6:'input',7:'input',8:'power_in',
               9:'input',10:'input',11:'input',12:'input',13:'output',14:'open_collector',15:'input',
               16:'open_collector',17:'passive',18:'power_out',25:'power_in'}
    pin_types.update({n:'no_connect' for n in range(19,25)})
    pins=tree.findall(".//libpart[@part='TPS26630RGER']/pins/pin")
    actual_types={int(p.attrib['num']):p.attrib['type'] for p in pins}
    if len(pins)!=25 or actual_types!=pin_types:errors.append('eFuse pin electrical types changed')
    return errors


def main():
    errors=validate(ET.parse(OUT/'netlist.xml'))
    erc=json.loads((OUT/'erc.json').read_text(encoding='utf-8'))
    violations=[v for sheet in erc['sheets'] for v in sheet['violations']]
    if violations:errors.append(f'KiCad ERC has {len(violations)} violations')
    paths=[Path(__file__),ROOT/'tools/hardware_build_power_entry.py',ROOT/'tools/hardware_build_tx_schematic.py',
           ROOT/'tests/test_power_entry.py',ROOT/'tools/power_entry_analysis.py',
           ROOT/'tests/test_power_entry_analysis.py',ROOT/'reports/POWER_ENTRY.md',
           ROOT/'research/POWER_ENTRY_REVIEW.md',ROOT/'research/power-entry/analysis.json',
           ROOT/'hardware/electrical-design.json']
    paths += [p for p in OUT.iterdir() if p.is_file() and p.name!='validation.json']
    result={'schema_version':1,'scope':'Two-domain DC input circuit connectivity review','consistency_pass':not errors,
            'manufacturing_ready':False,'errors':errors,'efuse_count':2,'ground_domains':['LOGIC_GND','FIELD_GND'],
            'component_count':44,'connected_net_count':34,'explicit_no_connect_net_count':14,
            'erc_violations':len(violations),'kicad_version':erc['kicad_version'],'erc_ignored_checks':erc['ignored_checks'],
            'source_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            'limitations':['Fuse and output-clamp MPNs unresolved','19-30V draft does not meet unchanged 18-30V ledger envelope',
                           'PGOOD needs converter EN divider; full machine permission not implemented','No physical surge/current/thermal/isolation measurements or PCB layout']}
    (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f"Power entry: {'FAIL' if errors else 'PASS'}; {len(errors)} connectivity/ERC issues; manufacturing blocked")
    return bool(errors)


if __name__=='__main__':sys.exit(main())
