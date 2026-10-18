"""Independent physical-pin/net checks for the proposed IS-2 conditioning candidate."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'hardware/is1_watchdogs/startup_conditioning_r0_2'
SOURCES = ROOT / 'research/is1-watchdogs'

# Independently reviewed TI physical package functions, not imported from the builder.
PIN_TYPES = {
    'TPS3851': {'1': 'power_in', '2': 'input', '3': 'input', '4': 'power_in', '5': 'input', '6': 'input',
                '7': 'open_collector', '8': 'open_collector', '9': 'power_in'},
    'LVC1G08': {'1': 'input', '2': 'input', '3': 'power_in', '4': 'output', '5': 'power_in'},
    'LVC1G34': {'1': 'no_connect', '2': 'input', '3': 'power_in', '4': 'output', '5': 'power_in'},
    'LVC2G17': {'1': 'input', '2': 'power_in', '3': 'input', '4': 'output', '5': 'power_in', '6': 'output'},
}
CHIP_NETS = {
    'U6': {'1': 'FPGA_MOTION_REQUEST', '2': 'FPGA_USER_RESET_N', '3': 'LOGIC_GND', '4': 'WD_M_SET1_BUF', '5': 'IO_3V3'},
    'U7': {'1': 'FPGA_OUTPUT_REQUEST', '2': 'FPGA_USER_RESET_N', '3': 'LOGIC_GND', '4': 'WD_O_SET1_BUF', '5': 'IO_3V3'},
    'U1': {'1': 'IO_3V3', '2': 'WD_M_CWD', '4': 'LOGIC_GND', '5': 'WD_M_SET1_BUF',
           '6': 'WD_M_WDI_BUF', '7': 'WD_M_HEALTH_RAW', '8': 'WD_M_HEALTH_RAW', '9': 'LOGIC_GND'},
    'U2': {'1': 'IO_3V3', '2': 'WD_O_CWD', '4': 'LOGIC_GND', '5': 'WD_O_SET1_BUF',
           '6': 'WD_O_WDI_BUF', '7': 'WD_O_HEALTH_RAW', '8': 'WD_O_HEALTH_RAW', '9': 'LOGIC_GND'},
    'U3': {'2': 'FPGA_PROGRESS_M', '3': 'LOGIC_GND', '4': 'WD_M_WDI_BUF', '5': 'IO_3V3'},
    'U4': {'2': 'FPGA_PROGRESS_O', '3': 'LOGIC_GND', '4': 'WD_O_WDI_BUF', '5': 'IO_3V3'},
    'U5': {'1': 'WD_M_HEALTH_RAW', '2': 'LOGIC_GND', '3': 'WD_O_HEALTH_RAW', '4': 'WD_O_OK',
           '5': 'IO_3V3', '6': 'WD_M_OK'},
}
PARTS = {
    'U6': ('SN74LVC1G08DCKR', 'Package_TO_SOT_SMD:SOT-353_SC-70-5'),
    'U7': ('SN74LVC1G08DCKR', 'Package_TO_SOT_SMD:SOT-353_SC-70-5'),
    'U1': ('TPS3851G18SDRBT', 'CNC_IS1:TPS3851_DRB8'),
    'U2': ('TPS3851G18SDRBT', 'CNC_IS1:TPS3851_DRB8'),
    'U3': ('SN74LVC1G34DBVR', 'Package_TO_SOT_SMD:SOT-23-5'),
    'U4': ('SN74LVC1G34DBVR', 'Package_TO_SOT_SMD:SOT-23-5'),
    'U5': ('SN74LVC2G17DBVR', 'Package_TO_SOT_SMD:SOT-23-6'),
}
RESISTORS = {
    'R11': ('WD_M_SET1_BUF', 'LOGIC_GND', 100000),
    'R12': ('WD_O_SET1_BUF', 'LOGIC_GND', 100000),
    'R13': ('FPGA_USER_RESET_N', 'LOGIC_GND', 4700),
    'R1': ('IO_3V3', 'WD_M_HEALTH_RAW', 10000), 'R2': ('IO_3V3', 'WD_O_HEALTH_RAW', 10000),
    'R3': ('FPGA_MOTION_REQUEST', 'LOGIC_GND', 4700), 'R4': ('FPGA_OUTPUT_REQUEST', 'LOGIC_GND', 4700),
    'R5': ('FPGA_PROGRESS_M', 'LOGIC_GND', 4700), 'R6': ('WD_M_WDI_BUF', 'LOGIC_GND', 100000),
    'R7': ('FPGA_PROGRESS_O', 'LOGIC_GND', 4700), 'R8': ('WD_O_WDI_BUF', 'LOGIC_GND', 100000),
    'R9': ('WD_M_OK', 'LOGIC_GND', 100000), 'R10': ('WD_O_OK', 'LOGIC_GND', 100000),
}
BOUNDARY = ['IO_3V3', 'LOGIC_GND', 'FPGA_MOTION_REQUEST', 'FPGA_OUTPUT_REQUEST',
            'FPGA_PROGRESS_M', 'FPGA_PROGRESS_O', 'WD_M_OK', 'WD_O_OK', 'FPGA_USER_RESET_N']
UNC = {('U1', '3'): 'input+no_connect', ('U2', '3'): 'input+no_connect',
       ('U3', '1'): 'no_connect', ('U4', '1'): 'no_connect'}


def primary_pin_functions(source_dir=SOURCES):
    """Derive manufacturer functions directly from retained primary text tables."""
    source_dir = Path(source_dir)
    timer = (source_dir / 'tps3851-revb.txt').read_text(encoding='utf-8')
    if 'REVISED JUNE 2025' not in timer or 'DRB0008A' not in timer:
        raise ValueError('TPS3851 Rev B / DRB0008A primary identity missing')
    table = timer.split('Table 4-1. Pin Functions', 1)[1].split('PAGE 4', 1)[0]
    rows = re.findall(r'^(CWD|GND|MR|RESET|SET1|VDD|WDI|WDO)\s+([1-8])\s+[IO—](?:\s|$)', table, re.MULTILINE)
    if len(rows) != 8 or len({p for _, p in rows}) != 8:
        raise ValueError('TPS3851 primary table ambiguous or incomplete')
    if 'thermal pad is internally connected to GND' not in table:
        raise ValueError('TPS3851 grounded thermal-pad source missing')
    result = {'TPS3851': {pin: name for name, pin in rows}}
    result['TPS3851']['9'] = 'EP'
    single = (source_dir / 'sn74lvc1g34.txt').read_text(encoding='utf-8')
    if 'SCES519O' not in single or 'DBV' not in single:
        raise ValueError('LVC1G34 DBV primary identity missing')
    st = single.split('Table 4-1. Pin Functions', 1)[1].split('PAGE 4', 1)[0]
    sr = re.findall(r'^(NC|A|GND|Y|VCC)\s+(\d+)\s+', st, re.MULTILINE)
    if len(sr) != 5 or len({p for _, p in sr}) != 5:
        raise ValueError('LVC1G34 primary table ambiguous or incomplete')
    result['LVC1G34'] = {pin: name for name, pin in sr}
    dual = (source_dir / 'sn74lvc2g17.txt').read_text(encoding='utf-8')
    if 'SCES381N' not in dual or 'DBV PACKAGE' not in dual:
        raise ValueError('LVC2G17 DBV primary identity missing')
    dt = dual.split('PinFunctions', 1)[1].split('PAGE 4', 1)[0]
    dr = re.findall(r'^(1A|1Y|2A|2Y|GND|VCC)\s+(\d+)\s+[IO—]', dt, re.MULTILINE)
    if len(dr) != 6 or len({p for _, p in dr}) != 6:
        raise ValueError('LVC2G17 primary table ambiguous or incomplete')
    result['LVC2G17'] = {pin: name for name, pin in dr}
    gate = (ROOT/'research/fpga-core/sn74lvc1g08.txt').read_text(encoding='utf-8')
    if 'SCES217AA' not in gate or 'DBV, DCK' not in gate:
        raise ValueError('LVC1G08 DCK primary identity missing')
    gt = gate.split('Pin Functions', 1)[1].split('www.ti.com', 1)[0]
    gr = re.findall(r'^(A|B|GND|VCC|Y)\s+(\d+)\s+\d+\s+\d+\s+(?:Input|Ground|Power pin|Output)', gt, re.MULTILINE)
    if len(gr) != 5 or len({p for _, p in gr}) != 5:
        raise ValueError('LVC1G08 primary physical table incomplete')
    result['LVC1G08'] = {pin: name for name, pin in gr}
    return result


def expected():
    parts = {r: {'value': mpn, 'mpn': mpn, 'footprint': fp} for r, (mpn, fp) in PARTS.items()}
    nets = defaultdict(set)
    for ref, mapping in CHIP_NETS.items():
        for pin, net in mapping.items():
            nets[net].add((ref, pin))
    for ref, (a, b, resistance) in RESISTORS.items():
        parts[ref] = {'value': '4.7k 1%' if resistance == 4700 else '10k 1%' if resistance == 10000 else '100k 1%',
                      'mpn': 'CRCW06034K70FKEA' if resistance == 4700 else 'CRCW060310K0FKEA' if resistance == 10000 else 'CRCW0603100KFKEA',
                      'footprint': 'Resistor_SMD:R_0603_1608Metric'}
        nets[a].add((ref, '1')); nets[b].add((ref, '2'))
    for index in range(1, 10):
        ref = f'C{index}'
        parts[ref] = {'value': '3.3nF C0G 50V 5%' if index <= 2 else '100nF X7R 25V 10%',
                      'mpn': 'CL10C332JB8NNNC' if index <= 2 else 'GRM188R71E104KA01D',
                      'footprint': 'Capacitor_SMD:C_0603_1608Metric'}
        nets['WD_M_CWD' if index == 1 else 'WD_O_CWD' if index == 2 else 'IO_3V3'].add((ref, '1'))
        nets['LOGIC_GND'].add((ref, '2'))
    parts['B1'] = {'value': 'INTERNAL REVIEW BOUNDARY', 'mpn': '', 'footprint': ''}
    for pin, net in enumerate(BOUNDARY, 1):
        nets[net].add(('B1', str(pin)))
    return parts, dict(nets)


def validate(tree, model, footprint_text=None, erc=None, source_dir=SOURCES):
    tree = tree.getroot() if isinstance(tree, ET.ElementTree) else tree
    errors = []
    wanted_parts, wanted_nets = expected()
    # A mirrored builder/model pin error cannot override these independently extracted tables.
    try:
        functions = primary_pin_functions(source_dir)
    except (ValueError, IndexError, OSError, re.error) as exc:
        functions = {}
        errors.append('Primary physical pin extraction: ' + str(exc))
    aliases = {'MR_N': 'MR', 'WDO_N': 'WDO', 'RESET_N': 'RESET'}
    for name, types in PIN_TYPES.items():
        libparts = tree.findall(f"libparts/libpart[@part='{name}']")
        if len(libparts) != 1:
            errors.append('Native symbol missing/ambiguous: ' + name)
            continue
        rows = libparts[0].findall('pins/pin')
        native = {p.attrib['num']: aliases.get(p.attrib['name'], p.attrib['name']) for p in rows}
        if len(rows) != len(native) or native != functions.get(name):
            errors.append('Manufacturer physical pin functions differ: ' + name)
        if {p.attrib['num']: p.attrib['type'] for p in rows} != types:
            errors.append('Native physical pin types differ: ' + name)

    components = [c for c in tree.findall('components/comp') if not c.attrib['ref'].startswith('#')]
    if len(components) != len(wanted_parts) or {c.attrib['ref'] for c in components} != set(wanted_parts):
        errors.append('Native component set differs')
    for c in components:
        ref = c.attrib['ref']
        fields = {p.attrib['name']: p.text or '' for p in c.findall('fields/field')}
        actual = {'value': c.findtext('value', ''), 'mpn': fields.get('MPN', ''), 'footprint': c.findtext('footprint', '')}
        if actual != wanted_parts.get(ref):
            errors.append('Exact native part/value/footprint differs: ' + ref)
        props = {p.attrib['name'] for p in c.findall('property')}
        if ref == 'B1':
            if not {'exclude_from_bom', 'exclude_from_board'} <= props:
                errors.append('Internal boundary must not be fitted or in BOM')
        elif props & {'dnp', 'exclude_from_bom', 'exclude_from_board'}:
            errors.append('Required physical part excluded: ' + ref)

    actual_nets, seen, unc_seen = {}, set(), set()
    for n in tree.findall('nets/net'):
        name = n.attrib['name'].removeprefix('/')
        connected = set()
        for node in n.findall('node'):
            ref, pin = node.attrib['ref'], node.attrib['pin']
            if ref.startswith('#'):
                continue
            pair = (ref, pin)
            if pair in seen:
                errors.append('Duplicate physical pin in native nets: ' + str(pair))
            seen.add(pair); connected.add(pair)
            if name.startswith('unconnected-'):
                if pair not in UNC or node.attrib.get('pintype') != UNC.get(pair):
                    errors.append('Unreviewed or missing no-connect marker: ' + str(pair))
                unc_seen.add(pair)
        if name.startswith('unconnected-'):
            if len(connected) != 1:
                errors.append('No-connect pin has another conductor: ' + name)
            continue
        if name in actual_nets:
            errors.append('Duplicate native net: ' + name)
        actual_nets[name] = connected
    if unc_seen != set(UNC):
        errors.append('Required MR/NC no-connect pins differ')
    for name in set(wanted_nets) | set(actual_nets):
        if wanted_nets.get(name, set()) != actual_nets.get(name, set()):
            errors.append('Native net mismatch: ' + name)

    for key in ('manufacturing_ready', 'assembly_integrated', 'physical_qualification', 'complete_permission_chain', 'startup_defaults_qualified'):
        if model.get(key) is not False:
            errors.append('Unqualified scope flag: ' + key)
    for key, value in {'revision': 'watchdog-conditioning-r0.2-proposed-IS2',
                       'status': 'proposed_IS2_not_agreed_or_integrated',
                       'interface_revision': 'IS-2-PROPOSED', 'interface_agreed': False,
                       'supersedes_is1': False, 'frozen_IS1_unchanged': True}.items():
        if model.get(key) != value:
            errors.append('Proposed interface scope differs: ' + key)
    if model.get('boundary') != {'kind': 'internal_review_only', 'fitted_connector': False, 'nets': BOUNDARY}:
        errors.append('Internal boundary scope differs')
    mparts = model.get('components', {})
    if set(mparts) != set(wanted_parts):
        errors.append('Model component set differs')
    for ref, p in wanted_parts.items():
        got = mparts.get(ref, {})
        if {key: got.get(key) for key in p} != p:
            errors.append('Exact model part/value/footprint differs: ' + ref)
        target = {pin: net for net, members in wanted_nets.items() for member, pin in members if member == ref}
        if got.get('pins') != target:
            errors.append('Model physical pin nets differ: ' + ref)
        if got.get('no_connect') != [pin for rr, pin in UNC if rr == ref]:
            errors.append('Model no-connect pins differ: ' + ref)
        if got.get('physical') is not (ref != 'B1'):
            errors.append('Model fitted status differs: ' + ref)
    for ref in ('C1', 'C2'):
        p = mparts.get(ref, {})
        for key, value in {'capacitance_f': 3.3e-9, 'tolerance': .05, 'dielectric': 'C0G', 'voltage_v': 50}.items():
            if p.get(key) != value:
                errors.append('Exact timing capacitor model differs: ' + ref + '/' + key)
    for i in range(3, 10):
        p = mparts.get(f'C{i}', {})
        if p.get('capacitance_f') != 1e-7 or p.get('decouples') != f'U{i-2}':
            errors.append('Per-IC decoupling model differs: C' + str(i))
    for ref, (_, _, value) in RESISTORS.items():
        if mparts.get(ref, {}).get('resistance_ohm') != value or mparts.get(ref, {}).get('tolerance') != .01:
            errors.append('Exact resistor model differs: ' + ref)
    contract = model.get('watchdog_contract', {})
    for key, value in {'timer_count': 2, 'mpn': 'TPS3851G18SDRBT', 'timing_cap_mpn': 'CL10C332JB8NNNC',
                       'timing_cap_f': 3.3e-9, 'timing_cap_tolerance': .05, 'standard_timing': True,
                       'set1_low_disables_timer': True, 'wdi_falling_edge_only': True, 'required_pulse_high_us': 1,
                       'legacy_toggle_compatible': False, 'physical_20ms_proof': False,
                       'FPGA_startup_LOW_qualified': False, 'FPGA_conditioning_review_required': True,
                       'SET1_driven_LOW_logic_standard_qualified': False,
                       'SET1_reset_guard': 'FPGA_USER_RESET_N', 'SET1_driver': 'SN74LVC1G08DCKR',
                       'FPGA_facing_pulldown_ohm': 4700, 'reset_input_pull_ohm': 4700, 'SET1_output_pull_ohm': 100000,
                       'SET1_pin_load_budget_ua': 50, 'SET1_pin_leakage_datasheet_bound_available': False,
                       'mr': 'unconnected_internal_pullup_per_frozen_IS1',
                       'health': 'RESET_WDO_wired_AND_then_separate_Schmitt'}.items():
        if contract.get(key) != value:
            errors.append('Unreviewed watchdog contract: ' + key)

    if footprint_text is not None:
        rows = re.findall(r'\(pad "(\d+)" smd roundrect \(at ([^ ]+) ([^)]+)\) \(size ([^ ]+) ([^)]+)\)', footprint_text)
        target = {str(i + 1): (-1.4, -.975 + i * .65, .6, .31) for i in range(4)}
        target.update({str(i + 5): (1.4, .975 - i * .65, .6, .31) for i in range(4)})
        target['9'] = (0, 0, 1.5, 1.75)
        got = {p: tuple(float(v) for v in (x, y, w, h)) for p, x, y, w, h in rows}
        if len(rows) != 9 or got != target:
            errors.append('DRB0008A physical copper pad map differs')
        if model.get('footprint_scope') != 'TI_DRB0008A_copper_only_stencil_thermal_routing_unqualified':
            errors.append('DRB stencil/thermal/routing scope overstated')
    if erc is not None:
        violations = [v for sheet in erc['sheets'] for v in sheet['violations']]
        if violations:
            errors.append('Native ERC violations: ' + str(len(violations)))
    return {'ok': not errors, 'errors': sorted(set(errors)), 'manufacturing_ready': False,
            'physical_qualification': False, 'complete_permission_chain': False,
            'physical_components': 29, 'diagram_boundary_components': 1,
            'evidence_class': 'manufacturer_source_extraction_and_native_net_part_pin_consistency'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true', help='read-only validation; do not rewrite a receipt')
    args = ap.parse_args()
    tree = ET.parse(OUT / 'netlist.xml')
    model = json.loads((OUT / 'design.json').read_text(encoding='utf-8'))
    erc = json.loads((OUT / 'erc.json').read_text(encoding='utf-8'))
    result = validate(tree, model, (OUT / 'CNC_IS1.pretty/TPS3851_DRB8.kicad_mod').read_text(encoding='utf-8'), erc)
    for entry in json.loads((SOURCES / 'sources.json').read_text(encoding='utf-8')):
        for pk, hk in (('path', 'sha256'), ('text_path', 'text_sha256')):
            if pk in entry and hashlib.sha256((SOURCES / entry[pk]).read_bytes()).hexdigest() != entry[hk]:
                result['errors'].append('Retained primary source hash differs: ' + entry[pk])
    for rel, expected_hash in model.get('primary_source_sha256', {}).items():
        if hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != expected_hash:
            result['errors'].append('Model primary source hash differs: ' + rel)
    paths = [ROOT / 'tools/hardware_build_watchdog_conditioning.py', Path(__file__), ROOT / 'tests/test_watchdog_conditioning.py',
             ROOT / 'tools/hardware_build_tx_schematic.py', ROOT / 'tools/hardware_build_logic_power.py']
    paths += [p for p in OUT.rglob('*') if p.is_file() and p.name != 'validation.json' and p.suffix not in ('.pdf', '.kicad_prl')]
    paths += [p for p in SOURCES.glob('*') if p.is_file()]
    result['ok'] = not result['errors']
    result['kicad_version'] = erc['kicad_version']
    result['erc_violations'] = sum(len(s['violations']) for s in erc['sheets'])
    result['erc_ignored_checks'] = erc['ignored_checks']
    result['source_sha256'] = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths) if p.exists()}
    if not args.check:
        (OUT / 'validation.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('ok', 'errors', 'manufacturing_ready', 'erc_violations')}, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
