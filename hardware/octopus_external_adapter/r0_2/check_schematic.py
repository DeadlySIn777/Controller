"""Compare actual Eeschema XML export with reviewed revision specifications."""
from pathlib import Path
import collections
import hashlib
import json
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
data = json.loads((OUT/'parts.json').read_text(encoding='utf-8'))
parts = data['parts']
native = ET.parse(OUT/'adapter.net.xml').getroot()
actual_parts = {e.attrib['ref']: e for e in native.findall('./components/comp')}
assert set(actual_parts) == set(parts), (set(actual_parts)-set(parts), set(parts)-set(actual_parts))
for ref, p in parts.items():
    comp = actual_parts[ref]
    assert comp.findtext('value') == p['value'], ref
    assert comp.findtext('footprint') == p['footprint'], ref
    stamp = comp.findtext('tstamps') or comp.findtext('tstamp')
    assert p['uuid'] in stamp, (ref, stamp, p['uuid'])
    fields = {f.attrib['name']: f.text for f in comp.findall('./fields/field')}
    assert fields['MPN'] == p['mpn'], ref
    assert fields['Manufacturer'] == p['manufacturer'], ref

actual = {}
net_members = collections.defaultdict(list)
for net in native.findall('./nets/net'):
    name = net.attrib['name']
    clean = name.removeprefix('/')
    for node in net.findall('node'):
        pair = (node.attrib['ref'], node.attrib['pin'])
        assert pair not in actual, pair
        actual[pair] = clean
        net_members[name].append(pair)
expected = {(ref, n): v for ref, p in parts.items() for n, v in p['pins'].items()}
assert set(actual) == set(expected), (set(actual)-set(expected), set(expected)-set(actual))
nc = 0
for pair, net in expected.items():
    value = actual[pair]
    if net is None:
        assert value.startswith('unconnected-'), (pair, value)
        assert sum(v == value for v in actual.values()) == 1, (pair, value)
        nc += 1
    else:
        assert value == net, (pair, net, value)
files = ['adapter.kicad_sch', 'Adapter.kicad_sym', 'sym-lib-table', 'adapter.net.xml', 'parts.json', 'power_spec.json', 'logic_spec.json', 'build_schematic.py']
receipt = {
    'status': 'PASS - NATIVE SCHEMATIC CONNECTIVITY ONLY',
    'native_export_tool': native.findtext('./design/tool'),
    'fitted_parts': len(parts), 'checked_pin_assignments': len(expected),
    'functional_nets': len(set(v for v in expected.values() if v)),
    'individually_unconnected_pins': nc,
    'part_footprints_values_MPNs_manufacturers_UUIDs': 'all match parts.json',
    'not_established': ['loaded timing', 'startup and enable behavior', 'supply/transient/thermal performance', 'actual host/driver compatibility', 'PCB connectivity/clearance', 'mechanical fit', 'physical operation', 'manufacturing release'],
    'sha256': {f: hashlib.sha256((OUT/f).read_bytes()).hexdigest() for f in files}
}
(OUT/'schematic-connectivity.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
print(json.dumps(receipt, indent=2))
