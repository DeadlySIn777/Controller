"""Read-only DC loading inventory from the native integrated MC netlist.

This records a bounded arithmetic screen, never electrical or manufacturing
qualification. It freezes the inspected input bytes before analysis.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/board-completion-20260930/motion-card-loading-r01'
VRAIL = 3.465
RTOL = .01
WEAK_UP = 27000
BOARD_LEAK = 5e-6  # Allocation only: no measured board contamination result.
GND = '/LOGIC_GND'
RAIL = '/IO_3V3'
FPGA_OUTPUTS = {'B3', 'C4', 'E4'}
FPGA_INPUTS = {'A2', 'D5', 'E6', 'P1'}
FPGA_FUTURE_OUTPUT_NETS = {
    '/FPGA_OUTPUT_REQUEST', '/watchdog_conditioning/FPGA_PROGRESS_O',
    '/mc_permission/OPI_REARM_TX', '/mc_permission/OPI_REARM_OUT',
    '/mc_permission/OPI_REARM_BOE', '/mc_permission/WD_REARM_M',
    '/mc_permission/WD_REARM_O', '/mc_permission/PERMIT_OUT_REQ',
}
SOURCE_PATHS = [
    'tmp/review_motion_card_loading.py',
    'hardware/motion_card/design.json', 'hardware/motion_card/netlist.xml',
    'hardware/motion_card/assembly-map.json', 'hardware/motion_card/erc.json',
    'tools/hardware_build_motion_card.py',
    'research/fpga-core/trion20-ds-v6.0.pdf',
    'research/fpga-core/trion20-ds-v6.0.txt',
    'research/fpga-core/sn74lvc1g08.pdf',
    'research/mc-local-power/sn74lvc1g17.pdf',
    'research/is1-watchdogs/sn74lvc1g34.pdf',
    'research/is1-watchdogs/sn74lvc2g17.pdf',
    'research/is1-watchdogs/tps3851-revb.pdf',
    'research/machine-permission/sn74lvc1g11.pdf',
    'research/machine-permission/sn74lvc2g08.pdf',
    'research/machine-permission/sn74lvc2g74.pdf',
    'research/machine-permission/sn74lvc2g04.pdf',
    'research/machine-permission/sn74lvc2g32.pdf',
]


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def resistance(c):
    if 'resistance_ohm' in c: return float(c['resistance_ohm'])
    match = re.match(r'(\d+(?:\.\d+)?)\s*([kKmMrR]?)', c['value'])
    if not match: raise ValueError(c['value'])
    scale = {'k': 1e3, 'K': 1e3, 'M': 1e6, 'm': 1e-3}.get(match[2], 1)
    return float(match[1]) * scale


def main():
    if OUT.exists(): raise SystemExit('Refusing to replace existing review evidence')
    source_hash = {s: sha(ROOT / s) for s in SOURCE_PATHS}
    for s in SOURCE_PATHS:
        dest = OUT / 'source' / s
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / s, dest)
    if any(sha(OUT / 'source' / s) != h for s, h in source_hash.items()):
        raise RuntimeError('Source changed while copied; review cannot complete')
    model = json.loads((OUT / 'source/hardware/motion_card/design.json').read_text())
    parts = model['components']
    netlist = ET.parse(OUT / 'source/hardware/motion_card/netlist.xml')
    mapping = json.loads((OUT / 'source/hardware/motion_card/assembly-map.json').read_text())
    resistor_nets = {}
    native = {}
    for net in netlist.findall('.//nets/net'):
        name = net.attrib['name']
        native[name] = [dict(n.attrib) for n in net.findall('node') if n.attrib['ref'] in parts]
        for node in native[name]:
            if node['ref'].startswith('R'):
                resistor_nets.setdefault(node['ref'], {})[node['pin']] = name
    rows = []
    for name, nodes in native.items():
        if name in {GND, RAIL, '/CORE_5V', '/CORE_1V2'}: continue
        if not any(parts[n['ref']].get('mpn', '').startswith('SN74LVC') for n in nodes): continue
        pulls_down, pulls_up, drivers, inputs, unknown = [], [], [], [], []
        fpga_output = False
        fpga_input = False
        for node in nodes:
            ref, pin, typ = node['ref'], node['pin'], node.get('pintype', '')
            c = parts[ref]
            mpn = c.get('mpn', '')
            if ref.startswith('R') and len(resistor_nets.get(ref, {})) == 2:
                other = next(n for p, n in resistor_nets[ref].items() if p != pin)
                row = {'reference': ref, 'ohm': resistance(c), 'tolerance_fraction': RTOL}
                if other == GND: pulls_down.append(row)
                elif other == RAIL: pulls_up.append(row)
            elif mpn.startswith('SN74LVC'):
                if typ == 'output': drivers.append({'reference': ref, 'pin': pin, 'mpn': mpn})
                elif typ == 'input':
                    # Full -40..125 C rows, at the actual datasheet II test conditions.
                    leakage = 2e-6 if mpn.startswith('SN74LVC1G34') else 5e-6
                    inputs.append({'reference': ref, 'pin': pin, 'mpn': mpn, 'ii_allowance_A': leakage})
            elif mpn.startswith('T20') and pin in FPGA_OUTPUTS:
                fpga_output = True
                drivers.append({'reference': ref, 'pin': pin, 'mpn': mpn, 'drive_qualified': False})
            elif mpn.startswith('T20') and pin in FPGA_INPUTS:
                fpga_input = True
                inputs.append({'reference': ref, 'pin': pin, 'mpn': mpn, 'ii_allowance_A': 10e-6})
            elif typ in {'input', 'bidirectional', 'output', 'open_collector', 'open_emitter'}:
                unknown.append({'reference': ref, 'pin': pin, 'mpn': mpn, 'pintype': typ})
        leakage = sum(i['ii_allowance_A'] for i in inputs)
        high_pull = sum(VRAIL / (r['ohm'] * (1-RTOL)) for r in pulls_down)
        low_pull = sum(VRAIL / (r['ohm'] * (1-RTOL)) for r in pulls_up)
        low_config = VRAIL / WEAK_UP if fpga_input else 0
        # Low inputs can source leakage into the output; grounded pulls need
        # no positive sink-current allocation. Pull-ups are conservatively
        # evaluated as if the actively driven output reached exactly zero.
        high = high_pull + leakage
        low = low_pull + low_config + leakage
        row = {'net': name, 'fitted_nodes': nodes, 'pulldowns': pulls_down,
               'pullups': pulls_up, 'drivers': drivers, 'receivers': inputs,
               'unknown_current_nodes': unknown, 'known_high_current_A': high,
               'known_low_current_A_with_configuration_pull_A': low,
               'fpga_configuration_pull_source_A': low_config,
               'unallocated_future_fpga_output': name in FPGA_FUTURE_OUTPUT_NETS,
               'high_light_load_100uA_screen': high <= 100e-6,
               'low_light_load_100uA_screen': low <= 100e-6,
               'physical_qualification': False}
        if drivers and not fpga_output:
            row['ordinary_3V_LVC_16mA_screen'] = high <= .016 and low <= .016
            row['conservative_ordinary_receiver_levels_V'] = {'VOH_min': 2.4, 'VOL_max': .4,
                                                            'VIH_min': 2.0, 'VIL_max': .8}
        if fpga_output or name in FPGA_FUTURE_OUTPUT_NETS:
            if pulls_down:
                # Configuration source allowance combines separate T20 tri-state
                # leakage, receiver II allowances and a declared board allowance.
                g = sum(1 / (r['ohm'] * (1+RTOL)) for r in pulls_down)
                source_leak = 10e-6 + leakage + BOARD_LEAK
                startup = (VRAIL/WEAK_UP + source_leak) / (1/WEAK_UP + g)
                row['startup_config_screen'] = {
                    'weak_up_min_ohm': WEAK_UP, 'source_leak_allowance_A': source_leak,
                    'voltage_max_V': startup, 'ordinary_VIL_max_V': .8,
                    'margin_V': .8-startup, 'future_pin_conditional': not fpga_output,
                    'board_allowance_measured': False,
                    'rail_corner_qualification': False,
                }
        if name in {'/WD_M_SET1_BUF', '/WD_O_SET1_BUF',
                    '/watchdog_conditioning/WD_M_WDI_BUF', '/watchdog_conditioning/WD_O_WDI_BUF'}:
            row['TPS3851_unknown_input_current'] = True
            row['assumed_timer_current_A'] = 50e-6
            row['high_with_assumed_timer_A'] = high + 50e-6
            row['low_with_assumed_timer_A'] = low + 50e-6
            row['timer_input_current_max_from_datasheet'] = None
            row['levels_require_timer_load_qualification'] = True
        rows.append(row)
    by_net = {r['net']: r for r in rows}
    reset = by_net['/FPGA_CRESET_N']
    # Source power block owns R2108; its published external budget explicitly
    # excludes that fitted local pulldown. Count every new fitted receiver.
    external_high = reset['known_high_current_A'] - VRAIL/(4700*(1-RTOL))
    external_low = reset['known_low_current_A_with_configuration_pull_A']
    external = {'net': '/FPGA_CRESET_N', 'local_pull_excluded': 'R2108',
                'external_high_A': external_high, 'external_high_limit_A': .001,
                'external_low_A': external_low, 'external_low_limit_A': .0001,
                'high_screen_pass': external_high <= .001,
                'low_screen_pass': external_low <= .0001,
                'includes_unknown_future_boundary_loads': False}
    required = {'/RAW_INHIBIT_N': {('U1001','A2'), ('U4003','7'), ('U4003','5'), ('U4007','6')},
                '/TX_PERMIT': {('U1001','E6'), ('U4007','4'), ('U4009','5'), ('U4010','1'), ('U4011','6')},
                '/WD_M_SET1_BUF': {('U3001','5'), ('U3006','4'), ('U4017','2')},
                '/WD_O_SET1_BUF': {('U3002','5'), ('U3007','4'), ('U4017','6')}}
    topology = {}
    for name, wanted in required.items():
        actual = {(n['ref'], n['pin']) for n in native[name]}
        topology[name] = {'required_fitted_nodes': [list(n) for n in sorted(wanted)],
                          'required_present': wanted <= actual}
        assert wanted <= actual, (name, wanted-actual)
    # Parts excluded from the production candidate are explicitly accounted,
    # not merely accidentally omitted by reference-prefix filtering.
    excluded, fitted_counts = {}, {}
    for name, block in mapping['blocks'].items():
        fitted = [r for r,c in parts.items() if c.get('source_block') == name]
        fitted_counts[name] = len(fitted)
        excluded[name] = {old:new for old,new in block['references'].items() if new not in parts}
    assert sum(fitted_counts.values()) == len(parts) == mapping['physical_parts'] == 203
    erc = json.loads((OUT/'source/hardware/motion_card/erc.json').read_text())
    violation_count = sum(len(s.get('violations', [])) for s in erc.get('sheets', []))
    result = {'schema_version': 1, 'captured_utc': datetime.now(timezone.utc).isoformat(),
              'scope': 'All fitted SN74LVC control-signal nets in the native integrated MC netlist; powered DC arithmetic only',
              'is_manufacturing_evidence': False, 'electrical_qualification': False,
              'fpga_vendor_fit_and_drive_qualified': False,
              'rail_max_screen_V': VRAIL, 'tolerance_fraction': RTOL,
              'source_sha256': source_hash,
              'copied_sha256': {s:sha(OUT/'source'/s) for s in SOURCE_PATHS},
              'logic_net_count': len(rows), 'physical_part_count': len(parts),
              'fitted_counts': fitted_counts, 'excluded_review_marker_references': excluded,
              'integrated_aliases': mapping['aliases'], 'topology_checks': topology,
              'native_erc_violation_count_observed': violation_count,
              'external_reset_budget': external, 'logic_nets': rows,
              'limitations': [
                  'Input II maxima are used at the exact datasheet test conditions, not assumed continuously guaranteed intermediate-voltage characteristics.',
                  'T20 drive-strength table is nominal-voltage, Tj=25 C data; it does not close loaded full-temperature output drive.',
                  'TPS3851 SET1 and WDI current maxima are unspecified; 50 uA is a qualification allocation, not a datasheet guarantee.',
                  'Board leakage allocation is not measured; partial-power/Ioff, output edge rates, CL and timing are not qualified.',
                  'Unknown external receivers/connectors and unallocated GPIO are not counted as zero-load implemented interfaces.',
                  'Analog reset supervisor/open-drain health threshold and rail-ramp proof remain separate unresolved qualifications.',
              ]}
    (OUT/'review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'review':str(OUT/'review.json'), 'logic_nets':len(rows),
                      'reset_external_high_uA':external_high*1e6,
                      'reset_external_low_uA':external_low*1e6,
                      'native_erc_violations_observed':violation_count}))


if __name__ == '__main__': main()
