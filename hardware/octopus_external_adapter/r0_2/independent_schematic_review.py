"""Record a second source-level review separate from JSON-to-netlist parity.

Pin tables below were independently read from the linked manufacturer PDFs.
The resulting report is not a physical qualification or fabrication release.
"""
from pathlib import Path
import hashlib
import json

OUT = Path(__file__).resolve().parent
parts = json.loads((OUT/'parts.json').read_text(encoding='utf-8'))['parts']
pin_maps = {
    'U1': {'1': '1OE', '2': '1A', '3': '2Y', '4': 'GND', '5': '2A', '6': '1Y', '7': '2OE', '8': 'VCC'},
    'U2': {'1': 'OE', '2': 'A', '3': 'GND', '4': 'Y', '5': 'VCC'},
    'U3': {'1': 'GND', '2': 'RESET_N', '3': 'VDD'},
    'Q1': {'1': 'G', '2': 'S', '3': 'D'},
    'Q2': {'1': 'G', '2': 'S', '3': 'D'},
    'Q3': {'1': 'G', '2': 'S', '3': 'D'},
    'Q20': {'1': 'G', '2': 'S', '3': 'D'},
    'U20': {'1': 'PGOOD', '2': 'EN', '3': 'VIN', '4': 'VOUT', '5': 'SW', '6': 'SW', '7': 'BOOT', '8': 'VCC', '9': 'BIAS', '10': 'GND', '11': 'MODE/SYNC'},
    'U21': {'1': 'IN', '2': 'GND', '3': 'NC', '4': 'ADJ', '5': 'OUT'},
    'D1': {'1': 'K', '2': 'A'},
    'D21': {'1': 'K', '2': 'A'},
    'D22': {'1': 'K', '2': 'A'},
}
for ref, expected in pin_maps.items():
    actual = parts[ref]['pin_labels']
    assert actual == expected, (ref, expected, actual)
assert parts['U21']['mpn'].startswith('LT3014B'), 'Reverse-sensitive rejected LDO must not remain fitted.'
assert parts['U1']['pins'] == {'1': 'LOGIC_READY', '2': 'STEP_IN', '3': 'DIR_BUF', '4': 'GND', '5': 'DIR_IN', '6': 'STEP_BUF', '7': 'LOGIC_READY', '8': 'V_LOGIC'}
assert parts['U2']['pins'] == {'1': 'LOGIC_READY', '2': 'EN_IN', '3': 'GND', '4': 'EN_BUF', '5': 'V_LOGIC'}
assert parts['Q20']['pins'] == {'1': 'REV_GATE', '2': 'V_EXT_PROT', '3': 'V_EXT_FUSED'}
assert parts['D21']['pins'] == {'1': 'V_EXT_PROT', '2': 'REV_GATE'}
assert parts['U20']['pins']['9'] == 'V5_REG'
assert all(parts['U20']['pins'][n] is None for n in ['1', '5', '6', '7'])
assert parts['U20']['pins']['11'] == 'GND'
assert parts['U20']['pins']['3'] == 'BUCK_VIN'
assert parts['D22']['pins'] == {'1': 'BUCK_VIN', '2': 'V_EXT_PROT'}
assert parts['R21']['pins']['1'] == 'BUCK_VIN'
assert all(parts[ref]['pins']['1'] == 'BUCK_VIN' for ref in ['C20', 'C21'])
assert parts['D1']['pins'] == {'1': 'V5_SELECT', '2': 'V5_REG'}
assert parts['SW1']['pins'] == {'1': 'V5_SELECT', '2': 'COM_PLUS', '3': 'V_EXT_PROT'}
assert parts['J2']['pins']['6'] == 'HOST_VIO'
assert all(net not in {'V_EXT_PROT', 'V5_REG', 'V_LOGIC', 'COM_PLUS'} for net in parts['J2']['pins'].values())
assert parts['U21']['pins'] == {'1': 'V_EXT_PROT', '2': 'GND', '3': None, '4': 'LDO_ADJ', '5': 'V_LOGIC'}
assert parts['R23']['pins'] == {'1': 'V_LOGIC', '2': 'LDO_ADJ'}
assert parts['R24']['pins'] == {'1': 'LDO_ADJ', '2': 'GND'}
assert parts['R25']['pins'] == {'1': 'V_LOGIC', '2': 'GND'}
assert parts['R23']['mpn'] == 'RT0603BRD07174KL'
assert parts['R24']['mpn'] == 'RT0603BRD07100KL'
assert parts['R25']['mpn'] == 'RC0603FR-0722KL'
v_nominal = 1.22*(1+174000/100000)
v_min = 1.18*(1+(174000*.999)/(100000*1.001))
v_max = 1.26*(1+(174000*1.001)/(100000*.999)) + 100e-9*(174000*1.001)
assert 3.126+.031 < v_min < v_max < 3.6
assert v_min/(22000*1.01) > 100e-6

review = {
    'status': 'PASS - INDEPENDENT SOURCE/PIN/CONNECTION REVIEW, NOT PHYSICAL QUALIFICATION',
    'review_date': '2026-10-06',
    'reviewed_parts_pin_functions': list(pin_maps),
    'reviewed_pin_function_count': sum(map(len, pin_maps.values())),
    'logic_rail_component_screen': {
        'nominal_V': v_nominal,
        'minimum_V': v_min,
        'maximum_V_including_100nA_ADJ_allowance': v_max,
        'minimum_bleed_current_uA': v_min/(22000*1.01)*1e6,
        'screen_scope': 'Reference, initial resistor tolerance and stated ADJ allowance only; no temperature-coefficient, ripple or transient qualification. Supervisor hysteresis is typical, so first-article startup measurement remains required.'
    },
    'correction_identified': 'TPS7A16A-Q1 limits OUT-to-IN to +0.3 V; the old output reservoir could exceed this on input collapse. Replaced with LT3014B, whose reverse-current protection and differential rating cover that condition without relying on an unspecified diode drop.',
    'D21_lifecycle_check': 'Diodes PCN 2780 discontinues BZT52C12-7-F-79; it explicitly recommends the selected BZT52C12-7-F as an active replacement. The family-page EOL link does not make this selected order code obsolete.',
    'checks': [
        'TI DCU/DCK buffer pinouts and TPS3839 DBZ pinout match package drawings.',
        'The two logic buffers accept 5.5 V inputs while powered in the reviewed 3.0-3.6 V band; active-high OE is connected to active-low-reset supervisor output.',
        'Nexperia N- and P-MOSFET pin functions match G1/S2/D3; Q20 body-diode orientation allows positive-input startup while blocking reversed DC input.',
        'Fixed-5V module BIAS is connected to VOUT, MODE/SYNC is grounded, SW/BOOT have no external wiring, VCC has its dedicated bypass, and external load is not placed on VCC.',
        'D22 isolates the buck input reservoir from sudden external-rail collapse; U20 VIN, UVLO divider and input bypass all connect on the protected side of that diode.',
        'Selected 5 V leg has correctly oriented reverse-blocking diode; non-shorting switch selects COM only and never switches ground or logic supply.',
        'Host VIO supplies only the EN bias reference and is not wired to an adapter power rail; VM contact remains physically omitted.'
    ],
    'limits': [
        'Exact host board/socket fit remains to be qualified; there is no universal BTT/SKR claim.',
        'Supervisor delay does not prove no spurious pulse: STEP already high on output-enable release can create an active edge. Firmware idle state and driver disable/startup sequence must be verified.',
        'CL57T-type ENA behavior is not a safety function and may enable a drive when its enable input is unpowered. Each exact driver profile requires verification.',
        'TVS/fuse/FET component ratings do not establish surge immunity or short-circuit behavior of the assembled board.',
        'Loaded 5 V common voltage after selector-diode, cable and sink losses, and 24 V input currents, require exact driver profile and measurements.',
        'Power sequencing, loaded edges, temperature, EMI and mechanical clearance need physical first-article measurements.'
    ],
    'primary_sources': {
        'U1': 'https://www.ti.com/lit/ds/symlink/sn74lvc2g126.pdf',
        'U2': 'https://www.ti.com/lit/ds/symlink/sn74lvc1g126.pdf',
        'U3': 'https://www.ti.com/lit/ds/symlink/tps3839.pdf',
        'Q1_Q2_Q3': 'https://assets.nexperia.com/documents/data-sheet/NX6008NBKW.pdf',
        'Q20': 'https://assets.nexperia.com/documents/data-sheet/PMV100EPA.pdf',
        'U20': 'https://www.ti.com/lit/ds/symlink/tpsm365r6.pdf',
        'U21': 'https://www.analog.com/media/en/technical-documentation/data-sheets/3014bfb.pdf',
        'D1_D22': 'https://assets.nexperia.com/documents/data-sheet/PMEG6010CEH.pdf',
        'D21': 'https://www.diodes.com/datasheet/download/BZT52Cxx.pdf',
        'D21_lifecycle': 'https://www.diodes.com/assets/PCN-Files/Diodes_PCN_2780_EOL.pdf',
        'rejected_LDO': 'https://www.ti.com/lit/ds/symlink/tps7a16a-q1.pdf'
    },
    'sha256': {name: hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ['parts.json', 'power_spec.json', 'logic_spec.json', 'adapter.kicad_sch', 'adapter.net.xml']},
    'manufacturing_ready': False,
}
(OUT/'independent-schematic-review.json').write_text(json.dumps(review, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'status': review['status'], 'reviewed_pin_functions': review['reviewed_pin_function_count']}))
