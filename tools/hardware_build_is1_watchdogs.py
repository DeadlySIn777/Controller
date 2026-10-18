"""Standalone IS-1 timer frontends; not a permission circuit or manufacturing release."""
import csv
import hashlib
import json
from pathlib import Path
import uuid

from hardware_build_tx_schematic import effects, quote, symbol
from hardware_build_logic_power import footprint

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'hardware/is1_watchdogs'
NS = uuid.UUID('c7ddf508-1a10-4d43-b860-49dc722d3ff9')
SPEC = Path('C:/Users/Gluis/claude-worktrees/controller-interface-spec/docs/interface-spec/04-safety-power-timing.md')


def uid(name):
    return str(uuid.uuid5(NS, name))


def build(out=OUT):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    root = uid('root')
    two = [(1, '', 0, 5.08, 270, 'passive'), (2, '', 0, -5.08, 90, 'passive')]
    pins = {
        'TPS3851': [(1, 'VDD', 0, 25.4, 270, 'power_in'), (2, 'CWD', -20.32, 15.24, 0, 'input'),
                    (3, 'MR_N', -20.32, 7.62, 0, 'input'), (4, 'GND', -5.08, -25.4, 90, 'power_in'),
                    (5, 'SET1', -20.32, -2.54, 0, 'input'), (6, 'WDI', -20.32, -12.7, 0, 'input'),
                    (7, 'WDO_N', 20.32, 7.62, 180, 'open_collector'),
                    (8, 'RESET_N', 20.32, -7.62, 180, 'open_collector'),
                    (9, 'EP', 5.08, -25.4, 90, 'power_in')],
        'LVC1G34': [(1, 'NC', -15.24, -7.62, 0, 'no_connect'), (2, 'A', -15.24, 7.62, 0, 'input'),
                    (3, 'GND', 0, -20.32, 90, 'power_in'), (4, 'Y', 15.24, 0, 180, 'output'),
                    (5, 'VCC', 0, 20.32, 270, 'power_in')],
        'LVC2G17': [(1, '1A', -15.24, 7.62, 0, 'input'), (2, 'GND', 0, -20.32, 90, 'power_in'),
                    (3, '2A', -15.24, -7.62, 0, 'input'), (4, '2Y', 15.24, -7.62, 180, 'output'),
                    (5, 'VCC', 0, 20.32, 270, 'power_in'), (6, '1Y', 15.24, 7.62, 180, 'output')],
        'R': two, 'C': two,
        'INTERNAL_REVIEW_BOUNDARY': [(i, str(i), -5.08, -(i - 1) * 5.08, 0, 'passive') for i in range(1, 9)],
        'PWR_FLAG': [(1, 'pwr', 0, 0, 90, 'power_out')],
    }
    rect = '(rectangle(start -17.78 22.86)(end 17.78 -22.86)(stroke(width .254)(type default))(fill(type background)))'
    small = '(rectangle(start -12.7 17.78)(end 12.7 -17.78)(stroke(width .254)(type default))(fill(type background)))'
    cap = '(polyline(pts(xy -2.54 .762)(xy 2.54 .762))(stroke(width .3)(type default))(fill(type none))) (polyline(pts(xy -2.54 -.762)(xy 2.54 -.762))(stroke(width .3)(type default))(fill(type none))) (polyline(pts(xy 0 2.54)(xy 0 .762))(stroke(width .254)(type default))(fill(type none))) (polyline(pts(xy 0 -.762)(xy 0 -2.54))(stroke(width .254)(type default))(fill(type none)))'
    shapes = {'TPS3851': rect, 'LVC1G34': small, 'LVC2G17': small,
              'R': '(rectangle(start -1.016 2.54)(end 1.016 -2.54)(stroke(width .254)(type default))(fill(type none)))',
              'C': cap, 'INTERNAL_REVIEW_BOUNDARY': '(rectangle(start -2.54 2.54)(end 2.54 -40.64)(stroke(width .254)(type default))(fill(type background)))',
              'PWR_FLAG': ''}
    library = [symbol(n, p, shapes[n], 'R' if n == 'R' else 'C' if n == 'C' else 'B' if n == 'INTERNAL_REVIEW_BOUNDARY' else '#FLG' if n == 'PWR_FLAG' else 'U') for n, p in pins.items()]
    items, positions, components, nets = [], {}, {}, {}

    def place(name, ref, value, x, y, mpn='', fp='', physical=True, **extra):
        positions[ref] = {str(n): (round(x + px, 4), round(y - py, 4)) for n, _, px, py, _, _ in pins[name]}
        passive = name in ('R', 'C')
        rx, ry, vy = (x + 3.81, y - 2.54, y + 1.27) if passive else (x, y - 34.29, y - 30.48)
        style = effects(.95, '(justify left)') if passive else effects(1.15)
        if ref.startswith('#'):
            style = effects(1.15, 'hide')
        props = f'(property "Reference" {quote(ref)}(at {rx} {ry} 0){style})(property "Value" {quote(value)}(at {rx} {vy} 0){style})'
        props += f'(property "MPN" {quote(mpn)}(at {x} {y} 0){effects(extra="hide")})(property "Footprint" {quote(fp)}(at {x} {y} 0){effects(extra="hide")})'
        items.append(f'(symbol(lib_id "CNC:{name}")(at {x} {y} 0)(unit 1)(in_bom {"yes" if physical else "no"})(on_board {"yes" if physical else "no"})(dnp no)(uuid "{uid(ref)}"){props}(instances(project "is1_watchdogs"(path "/{root}"(reference {quote(ref)})(unit 1)))))')
        if not ref.startswith('#'):
            components[ref] = {'value': value, 'mpn': mpn, 'footprint': fp, 'physical': physical, 'pins': {}, 'no_connect': [], **extra}

    def label(ref, pin, net, dx=0, dy=0):
        x, y = positions[ref][str(pin)]
        xx, yy = round(x + dx, 4), round(y + dy, 4)
        if dx or dy:
            items.append(f'(wire(pts(xy {x} {y})(xy {xx} {yy}))(stroke(width 0)(type default))(uuid "{uid(ref+str(pin)+"wire")}"))')
        items.append(f'(label {quote(net)}(at {xx} {yy} 0){effects(.95,"(justify left bottom)")}(uuid "{uid(ref+str(pin)+"label")}"))')
        if ref in components:
            components[ref]['pins'][str(pin)] = net
            nets.setdefault(net, []).append([ref, str(pin)])

    def nc(ref, pin):
        x, y = positions[ref][str(pin)]
        items.append(f'(no_connect(at {x} {y})(uuid "{uid(ref+str(pin)+"NC")}"))')
        components[ref]['no_connect'].append(str(pin))

    def note(x, y, text, size=1.2):
        items.append(f'(text {quote(text)}(at {x} {y} 0){effects(size,"(justify left top)")}(uuid "{uid(text)}"))')

    for index, tag in enumerate(('M', 'O')):
        ref, wdi_ref = f'U{index+1}', f'U{index+3}'
        y = 99.06 + index * 154.94
        request = 'FPGA_MOTION_REQUEST' if tag == 'M' else 'FPGA_OUTPUT_REQUEST'
        place('TPS3851', ref, 'TPS3851G18SDRBT', 170.18, y, 'TPS3851G18SDRBT', 'CNC_IS1:TPS3851_DRB8', role=f'{tag}_independent_timer')
        mapping = {1: 'IO_3V3', 2: f'WD_{tag}_CWD', 4: 'LOGIC_GND', 5: request, 6: f'WD_{tag}_WDI_BUF',
                   7: f'WD_{tag}_HEALTH_RAW', 8: f'WD_{tag}_HEALTH_RAW', 9: 'LOGIC_GND'}
        for pin, net in mapping.items():
            label(ref, pin, net, dx=-60.96 if pin in (2, 5, 6) else 10.16 if pin in (7, 8) else 0,
                  dy=-5.08 if pin == 1 else 5.08 if pin in (4, 9) else 0)
        nc(ref, 3)
        place('LVC1G34', wdi_ref, 'SN74LVC1G34DBVR', 398.78, y, 'SN74LVC1G34DBVR', 'Package_TO_SOT_SMD:SOT-23-5', role=f'{tag}_WDI_rail_buffer')
        for pin, net in {2: f'FPGA_PROGRESS_{tag}', 3: 'LOGIC_GND', 4: f'WD_{tag}_WDI_BUF', 5: 'IO_3V3'}.items():
            label(wdi_ref, pin, net, dx=-63.5 if pin == 2 else 7.62 if pin == 4 else 0,
                  dy=-5.08 if pin == 5 else 5.08 if pin == 3 else 0)
        nc(wdi_ref, 1)

    place('LVC2G17', 'U5', 'SN74LVC2G17DBVR', 497.84, 172.72, 'SN74LVC2G17DBVR', 'Package_TO_SOT_SMD:SOT-23-6', role='separate_health_Schmitt_channels')
    for pin, net in {1: 'WD_M_HEALTH_RAW', 2: 'LOGIC_GND', 3: 'WD_O_HEALTH_RAW', 4: 'WD_O_OK', 5: 'IO_3V3', 6: 'WD_M_OK'}.items():
        label('U5', pin, net, dx=-63.5 if pin in (1, 3) else 7.62 if pin in (4, 6) else 0,
              dy=-5.08 if pin == 5 else 5.08 if pin == 2 else 0)

    def passive(kind, ref, value, top, bottom, x, y, mpn, **details):
        fp = ('Resistor_SMD:R_' if kind == 'R' else 'Capacitor_SMD:C_') + '0603_1608Metric'
        place(kind, ref, value, x, y, mpn, fp, **details)
        label(ref, 1, top, dy=-5.08)
        label(ref, 2, bottom, dy=5.08)

    for index, tag in enumerate(('M', 'O')):
        y = 149.86 + index * 154.94
        passive('C', f'C{index+1}', '3.3nF C0G 50V 5%', f'WD_{tag}_CWD', 'LOGIC_GND', 86.36, y,
                'CL10C332JB8NNNC', capacitance_f=3.3e-9, tolerance=.05, dielectric='C0G', voltage_v=50)
    for index in range(5):
        passive('C', f'C{index+3}', '100nF X7R 25V 10%', 'IO_3V3', 'LOGIC_GND', 68.58 + index * 86.36, 365.76,
                'GRM188R71E104KA01D', capacitance_f=1e-7, tolerance=.10, dielectric='X7R', voltage_v=25, decouples=f'U{index+1}')
    rows = [
        ('R1', 'IO_3V3', 'WD_M_HEALTH_RAW', 10000, 238.76, 99.06),
        ('R2', 'IO_3V3', 'WD_O_HEALTH_RAW', 10000, 238.76, 254.0),
        ('R3', 'FPGA_MOTION_REQUEST', 'LOGIC_GND', 100000, 55.88, 124.46),
        ('R4', 'FPGA_OUTPUT_REQUEST', 'LOGIC_GND', 100000, 55.88, 279.4),
        ('R5', 'FPGA_PROGRESS_M', 'LOGIC_GND', 100000, 292.1, 139.7),
        ('R6', 'WD_M_WDI_BUF', 'LOGIC_GND', 100000, 393.7, 139.7),
        ('R7', 'FPGA_PROGRESS_O', 'LOGIC_GND', 100000, 292.1, 294.64),
        ('R8', 'WD_O_WDI_BUF', 'LOGIC_GND', 100000, 393.7, 294.64),
        ('R9', 'WD_M_OK', 'LOGIC_GND', 100000, 472.44, 226.06),
        ('R10', 'WD_O_OK', 'LOGIC_GND', 100000, 548.64, 226.06),
    ]
    for ref, top, bottom, value, x, y in rows:
        passive('R', ref, '10k 1%' if value == 10000 else '100k 1%', top, bottom, x, y,
                'CRCW060310K0FKEA' if value == 10000 else 'CRCW0603100KFKEA', resistance_ohm=value, tolerance=.01)

    boundary = ['IO_3V3', 'LOGIC_GND', 'FPGA_MOTION_REQUEST', 'FPGA_OUTPUT_REQUEST', 'FPGA_PROGRESS_M', 'FPGA_PROGRESS_O', 'WD_M_OK', 'WD_O_OK']
    place('INTERNAL_REVIEW_BOUNDARY', 'B1', 'INTERNAL REVIEW BOUNDARY', 548.64, 317.5, physical=False, role='diagram_boundary_only_no_fitted_connector')
    for pin, net in enumerate(boundary, 1):
        label('B1', pin, net, dx=-71.12)
    for i, net in enumerate(('IO_3V3', 'LOGIC_GND'), 1):
        ref = f'#FLG{i}'
        place('PWR_FLAG', ref, 'EXTERNAL REVIEW SUPPLY', 358.14 + (i - 1) * 25.4, 330.2, physical=False)
        label(ref, 1, net, dy=5.08)
    note(15.24, 17.78, 'IS-1 DUAL WATCHDOG TIMER FRONTENDS - STANDALONE REVIEW CANDIDATE', 2.1)
    note(15.24, 30.48, 'NOT CONNECTED TO THE ASSEMBLY. No complete permission chain, latches, field outputs, PCB or physical qualification.', 1.25)
    note(15.24, 40.64, 'Separate timers / shared IO_3V3 and LOGIC_GND / G18 threshold is not a 3.3V power-good qualification / all inputs INTERNAL logic.', 1.15)
    note(15.24, 51.0, 'WD_M: motion ARM / UPDATE progress; WD_O: full-I/O progress. SET1=0 disables its timer. MR open per frozen IS-1.', 1.2)
    note(292.1, 53.34, 'WDI: one 1us high pulse, idle LOW. FALLING edges feed timer.\nOld toggle-per-UPDATE gateware is INCOMPATIBLE.\n3.3nF C0G: calculated timing, never a measured20ms proof.', 1.15)
    note(432.0, 121.0, 'Each RESET + WDO wired-AND with\n10k pull-up. WD_M_OK / WD_O_OK\nhave100k pulls; partial power UNQUALIFIED.\nNo sticky permission latch in this block.', 1.15)
    note(432.0, 277.0, 'T20 reset GPIO weak pull-ups defeat100k\nrequest/progress pulls (about2.73V worst\ncase). Startup LOW is NOT qualified.\nNeeds reviewed interface conditioning;\nfuture permission gates are not drawn.', 1.1)
    note(15.24, 397.51, 'DRB copper-pad candidate only: paste/stencil, thermal vias, CWD guarding/cleanliness/leakage, routing, partial power and brownout remain unqualified.', 1.05)
    schematic = f'(kicad_sch(version 20250114)(generator "eeschema")(uuid "{root}")(paper "A2")(title_block(title "IS-1 dual watchdogs - review only")(date "2026-09-30")(rev "r0.1"))(lib_symbols {"".join(library)})' + ''.join(items) + ')\n'
    (out / 'is1_watchdogs.kicad_sch').write_text(schematic, encoding='utf-8')
    (out / 'CNC.kicad_sym').write_text('(kicad_symbol_lib(version 20241209)(generator "kicad_symbol_editor")' + ''.join(s.replace('(symbol "CNC:', '(symbol "', 1) for s in library) + ')\n', encoding='utf-8')
    (out / 'is1_watchdogs.kicad_pro').write_text('{"meta":{"filename":"is1_watchdogs.kicad_pro","version":1}}\n', encoding='utf-8')
    (out / 'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "CNC") (type "KiCad") (uri "${KIPRJMOD}/CNC.kicad_sym") (options "") (descr "IS-1 standalone timer frontend review")))\n', encoding='utf-8')
    pretty = out / 'CNC_IS1.pretty'
    pretty.mkdir(exist_ok=True)
    pads = [(i + 1, -1.4, -.975 + i * .65, .6, .31) for i in range(4)]
    pads += [(i + 5, 1.4, .975 - i * .65, .6, .31) for i in range(4)]
    pads += [(9, 0, 0, 1.5, 1.75)]
    (pretty / 'TPS3851_DRB8.kicad_mod').write_text(footprint('TPS3851_DRB8', (3, 3), pads), encoding='utf-8')
    (out / 'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "CNC_IS1") (type "KiCad") (uri "${KIPRJMOD}/CNC_IS1.pretty") (options "") (descr "DRB0008A copper candidate; stencil/thermal/routing UNQUALIFIED")))\n', encoding='utf-8')
    data = {
        'schema_version': 1, 'revision': 'is1-watchdogs-r0.1', 'status': 'standalone_review_candidate_not_qualified',
        'manufacturing_ready': False, 'assembly_integrated': False, 'physical_qualification': False,
        'complete_permission_chain': False, 'startup_defaults_qualified': False,
        'boundary': {'kind': 'internal_review_only', 'fitted_connector': False, 'nets': boundary},
        'rails': {'IO_3V3': {'nominal_v': 3.3, 'review_range_v': [3.14, 3.465]}, 'ground': 'LOGIC_GND'},
        'components': components,
        'watchdog_contract': {'timer_count': 2, 'independent_timing_capacitors': True, 'shared_supply_and_ground': True,
            'mpn': 'TPS3851G18SDRBT', 'timing_cap_mpn': 'CL10C332JB8NNNC', 'timing_cap_f': 3.3e-9,
            'timing_cap_tolerance': .05, 'standard_timing': True, 'set1_low_disables_timer': True,
            'wdi_falling_edge_only': True, 'required_pulse_high_us': 1, 'legacy_toggle_compatible': False,
            'mr': 'unconnected_internal_pullup_per_frozen_IS1', 'health': 'RESET_WDO_wired_AND_then_separate_Schmitt',
            'timing_analysis_owner': 'tools/is1_watchdog_analysis.py', 'physical_20ms_proof': False,
            'FPGA_startup_LOW_qualified': False, 'FPGA_conditioning_review_required': True,
            'SET1_driven_LOW_logic_standard_qualified': False},
        'primary_pin_sources': [
            {'url': 'https://www.ti.com/lit/ds/symlink/tps3851.pdf', 'revision': 'SBVS300B June 2025', 'pages': '3 physical pins; DRB0008A mechanical/land pattern'},
            {'url': 'https://www.ti.com/lit/ds/symlink/sn74lvc1g34.pdf', 'revision': 'SCES519O October 2025', 'pages': '3 DBV physical pins'},
            {'url': 'https://www.ti.com/lit/ds/symlink/sn74lvc2g17.pdf', 'revision': 'SCES381N January 2015', 'pages': '3 DBV physical pins'},
        ],
        'frozen_spec': {'revision': 'IS-1', 'path': str(SPEC), 'sha256': hashlib.sha256(SPEC.read_bytes()).hexdigest() if SPEC.exists() else None},
        'primary_source_sha256': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sorted((ROOT / 'research/is1-watchdogs').glob('*')) if p.is_file()},
        'footprint_scope': 'TI_DRB0008A_copper_only_stencil_thermal_routing_unqualified',
        'unqualified': ['complete_permission_chain', 'sticky_fault_latches', 'FPGA_progress_pulse_implementation',
            'T20_GPIO_configuration_pullup_vs_100k_request_progress_pulldown', 'SET1_driven_LOW_logic_standard_margin',
            'loaded_CWD_leakage_at_temperature_humidity', 'brownout_slew', 'partial_power', 'pin_input_thresholds_with_actual_driver',
            'external_loads_and_health_propagation', 'physical_20ms_fault_to_inhibit', 'machine_stop_response',
            'PCB_stencil_thermal_guarding_routing', 'production_cost_and_release'],
    }
    (out / 'design.json').write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    (out / 'pin-map.json').write_text(json.dumps({n: sorted(v) for n, v in sorted(nets.items())}, indent=2) + '\n', encoding='utf-8')
    with (out / 'bom.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Reference', 'Value', 'MPN', 'Footprint', 'Status'])
        for ref, p in components.items():
            if p['physical']:
                writer.writerow([ref, p['value'], p['mpn'], p['footprint'], 'candidate_not_qualified'])
    print(out / 'is1_watchdogs.kicad_sch')
    return data


if __name__ == '__main__':
    build()
