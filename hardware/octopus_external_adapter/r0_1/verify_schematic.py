"""Compare KiCad's exported netlist with the independent reviewed candidate contract.

This checks source connectivity only, not equipment identity, voltages, timing or fit.
Run after native netlist export. Only writes schematic-connectivity.json locally.
"""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
EXPECTED={
    'J1':{1:'EN',2:None,3:None,4:None,5:None,6:None,7:'STEP',8:'DIR'},
    'J2':{1:'GND',2:None,3:None,4:None,5:None,6:'+5V',7:'GND'},
    'J3':{1:'+5V',2:'PUL_MINUS',3:'DIR_MINUS',4:'ENA_MINUS'},
    'U1':{1:'STEP_G',2:'ENA_MINUS',3:'DIR_G',4:'GND',5:'DIR_MINUS',6:'EN_G',7:'PUL_MINUS',8:'+5V'},
    'R1':{1:'STEP',2:'STEP_G'},'R2':{1:'DIR',2:'DIR_G'},'R3':{1:'EN',2:'EN_G'},
    'R4':{1:'STEP_G',2:'GND'},'R5':{1:'DIR_G',2:'GND'},'R6':{1:'EN_G',2:'+5V'},
    'C1':{1:'+5V',2:'GND'},'C2':{1:'+5V',2:'GND'},
}

def main():
    xml=ET.parse(ROOT/'adapter.net.xml').getroot()
    found={}; nc_groups=[]
    for net in xml.find('nets'):
        name=net.attrib['name']
        nodes=list(net)
        for node in nodes:
            key=(node.attrib['ref'],int(node.attrib['pin']))
            assert key not in found, f'Duplicate pin {key}'
            if name.startswith('unconnected-'):
                assert len(nodes)==1, f'NC shares a net: {name}'
                found[key]=None
            else:
                found[key]=name.removeprefix('/')
        if name.startswith('unconnected-'): nc_groups.append(name)
    expected={(ref,pin):net for ref,pins in EXPECTED.items() for pin,net in pins.items()}
    assert found==expected, f'Connectivity mismatch: {set(found.items()) ^ set(expected.items())}'
    components={c.attrib['ref']:c for c in xml.find('components')}
    assert set(components)==set(EXPECTED), 'Unexpected or missing fitted part'
    ulib=next(p for p in xml.find('libparts') if p.attrib['part']=='SN74LVC3G06DCUR')
    pin_types={int(p.attrib['num']):p.attrib['type'] for p in ulib.find('pins')}
    assert pin_types=={1:'input',2:'open_collector',3:'input',4:'power_in',5:'open_collector',6:'input',7:'open_collector',8:'power_in'},pin_types
    manifest=json.loads((ROOT/'parts.json').read_text())
    for ref,component in components.items():
        p=manifest['parts'][ref]
        assert component.findtext('footprint')==p['footprint'],ref
        assert component.findtext('tstamps')==p['uuid'],ref
        assert component.findtext('value')==p['value'],ref
    checks=dict(native_export_tool=xml.findtext('design/tool'),
        fitted_parts=len(components), checked_pin_assignments=len(found),
        functional_nets=len({n for n in found.values() if n}), individually_unconnected_pins=len(nc_groups),
        u1_electrical_pin_types='verified: three inputs, three open-collector/open-drain outputs, two power inputs',
        part_footprints_values_uuids='all match parts.json',
        status='PASS - NATIVE SCHEMATIC CONNECTIVITY ONLY',
        not_established=['actual host identity','host rail/load capability','enable default and timing',
            'cable polarity/assembly','PCB connectivity/clearance','mechanical fit','physical operation','manufacturing release'],
        sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in [
            'adapter.kicad_sch','Adapter.kicad_sym','sym-lib-table','adapter.net.xml','parts.json','build_schematic.py']})
    (ROOT/'schematic-connectivity.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in checks.items() if k not in ['sha256','not_established']},indent=2))

if __name__=='__main__':main()
