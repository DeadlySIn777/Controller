"""Cross-check source package assignments against vendor CSV, XML and template.

The initial unexecuted-output reviewer wrongly expected unsuffixed CSV signal names
and nonblank voltage cells on bottom special pads. Retain that script unchanged.
"""
import ast
import collections
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

H = Path(__file__).resolve().parent
RUN = H/'efinity-native-pincheck-r1'
OUT = H/'efinity-native-pincheck-review-r2'
ISF = H/'release-review/vendor-constraints-r1/R299-T20F256-physical-pin-voltage.isf'


def sha(p):
    with Path(p).open('rb') as s:
        return hashlib.file_digest(s, 'sha256').hexdigest()


def main():
    assert not OUT.exists()
    expected, modes = {}, {}
    for node in ast.walk(ast.parse(ISF.read_text())):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        name = node.func.attr
        if name == 'assign_pkg_pin':
            expected[ast.literal_eval(node.args[0])] = ast.literal_eval(node.args[1])
        if name in ('create_input_gpio', 'create_output_gpio', 'create_input_clock_gpio'):
            modes[ast.literal_eval(node.args[0])] = 'output' if name == 'create_output_gpio' else 'input'
    assert set(expected) == set(modes) and len(expected) == 135
    csvfile = RUN/'generated/controller_is2_R299_pincheck.pinout.csv'
    rows = list(csv.DictReader(io.StringIO('\n'.join(x for x in csvfile.read_text().splitlines() if x.strip() and not x.startswith('#')))))
    assert len(rows) == 256 and len({x['Pin Number'] for x in rows}) == 256
    by_ball = {x['Pin Number']: x for x in rows}
    ns = {'p': 'http://www.efinixinc.com/peri_design_db'}
    root = ET.parse(RUN/'controller_is2_R299_pincheck.peri.xml').getroot()
    assert root.attrib['device_def'] == 'T20F256'
    gpio = {g.attrib['name']: g for g in root.findall('p:gpio_info/p:gpio', ns)}
    banks = {b.attrib['name']: b.attrib['iostd'] for b in root.findall('p:device_info/p:iobank_info/p:iobank', ns)}
    assert set(gpio) == set(expected)
    special = []
    for name, ball in expected.items():
        row, g = by_ball[ball], gpio[name]
        # CSV includes alternate-function annotations after the XML GPIO identity.
        assert row['Pin Name'] == g.attrib['gpio_def'] or row['Pin Name'].startswith(g.attrib['gpio_def']+'_')
        assert row['Direction'].lower() == modes[name] == g.attrib['mode']
        assert row['I/O Standard'] == g.attrib['io_standard'] == banks[row['Bank']] == '3.3 V LVTTL / LVCMOS'
        if g.attrib['is_lvds_gpio'] == 'true':
            # Native bottom special GPIOs use per-pad CSV suffixes even in single-ended mode.
            match = re.fullmatch(r'GPIOB_(?:CLK([PN])\d+|([RT]X[PN])\d+(?:_EXTFB\d+)?)', row['Pin Name'])
            assert match
            suffix = ('RX'+match[1]) if match[1] else match[2]
            assert row['Signal Name'] == name+'.'+suffix and row['I/O Bank Voltage'] == ''
            assert row['Bank'] in ('4A', '4B')
            special.append({'source': name, 'ball': ball, 'native_csv_signal': row['Signal Name'], 'voltage_authority': 'XML iobank iostd and native API readback; CSV voltage cell blank'})
        else:
            assert row['Signal Name'] == name and row['I/O Bank Voltage'] == '3.3 V'
    assert len(special) == 32 and len({by_ball[b]['Bank'] for b in expected.values()}) == 7
    assert expected['FPGA_CLK_50M'] == 'H3'
    assert gpio['FPGA_CLK_50M'].find('p:input_config', ns).attrib['conn_type'] == 'gclk'
    vendor = json.loads((RUN/'receipt.json').read_bytes())
    assert vendor['interface_imported'] and vendor['vendor_design_check_passed'] and not vendor['bank_voltage_errors'] and not vendor['package_pin_errors']
    record = {'status': 'NATIVE_PACKAGE_CSV_XML_SOURCE_CROSSCHECK_PASS_PACKAGE_SCOPE_ONLY',
        'assigned_pins': 135, 'directions': dict(collections.Counter(modes.values())),
        'native_unique_package_balls': 256, 'source_banks_3V3': 7,
        'native_special_single_ended_pad_report_rows': special,
        'initial_reviewer_failure': 'CSV matching assumption; first script retained unchanged, no native rerun',
        'full_physical_RTL_fit_timing_and_IO_defaults': 'OPEN', 'bitstream_generated': False,
        'input_SHA256': {str(p): sha(p) for p in [Path(__file__), H/'review_efinity_pin_artifacts.py', ISF, RUN/'receipt.json', csvfile, RUN/'controller_is2_R299_pincheck.peri.xml']},
        'adopted': False, 'manufacturing_ready': False}
    OUT.mkdir()
    (OUT/'receipt.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps({k: record[k] for k in ('status', 'assigned_pins', 'directions', 'source_banks_3V3')}))


if __name__ == '__main__':
    main()
