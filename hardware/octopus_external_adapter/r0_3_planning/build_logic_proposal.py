"""Build the isolated r0.3 direct-sink interface proposal; no CAD release."""
from pathlib import Path
import copy
import json

ROOT = Path(__file__).resolve().parent
PREVIOUS = ROOT.parent / 'r0_2'
old = json.loads((PREVIOUS / 'logic_spec.json').read_text(encoding='utf-8'))
parts = {r: copy.deepcopy(old['parts'][r]) for r in ('J1', 'J2', 'J3', 'J4', 'SW1')}
parts['J2']['pins']['6'] = None
parts['J2']['pin_labels']['6'] = 'HOST_VIO_NC'
parts['J2']['notes'] = [
    'Underside seven-position header begins one 2.54 mm pitch beyond the absent VM location.',
    'No VM pin, pad, plated hole, copper or testpoint.',
    'Host VIO/VDD contact exists mechanically but its pad is electrically NC. No connection to a local supply or gate pull-up.',
    'Ground contacts are joined to external-supply negative; this interface is not galvanically isolated.'
]
parts['J1']['notes'].append('Top-view coordinates are defined in socket_contract; do not mirror the socket pinout when installing underside headers.')
parts['J3']['notes'] += [
    'Pin 1 is positive COM, NOT ground. The other three conductors are individual open-drain sinks.',
    'Host motor-output socket contacts remain NC; signals leave only through this adapter J3.'
]
parts['J4']['notes'].append('Final supported voltage range and input protection are owned by the r0.3 power specification; no host VM supply is used.')

for index, (signal, drain) in enumerate((('STEP', 'PUL_MINUS'), ('DIR', 'DIR_MINUS'), ('EN', 'ENA_MINUS')), 1):
    ref = f'Q{index}'
    parts[ref] = dict(reference=ref, value='NX6008NBK', mpn='NX6008NBKR', manufacturer='Nexperia',
        footprint='Package_TO_SOT_SMD:SOT-23',
        pins={'1': signal + '_GATE', '2': 'GND', '3': drain},
        pin_labels={'1': 'G', '2': 'S', '3': 'D'},
        pin_types={'1': 'input', '2': 'passive', '3': 'passive'}, kind='nmos',
        source='https://assets.nexperia.com/documents/data-sheet/NX6008NBK.pdf',
        ordering_source='https://www.nexperia.com/chemical-content/NX6008NBK.html',
        notes=['SOT-23 version, not the old SOT-323 NX6008NBKW.',
               'High host signal turns on the sink. Low or high-impedance host signal releases it after gate discharge.',
               '20 mA/channel is a proposed qualification load, not a measured rating.',
               'No direct connection between drain/COM supply and host VIO. Parasitic coupling and gate leakage are nonzero; this is not isolation.'])
    for rref, value, mpn, pins in [
        (f'R{index}', '1k 1%', 'RC0603FR-071KL', {'1': signal, '2': signal + '_GATE'}),
        (f'R{index+3}', '10k 1%', 'RC0603FR-0710KL', {'1': signal + '_GATE', '2': 'GND'})
    ]:
        parts[rref] = dict(reference=rref, value=value, mpn=mpn, manufacturer='Yageo',
            footprint='Resistor_SMD:R_0603_1608Metric', pins=pins,
            pin_labels={'1': '1', '2': '2'}, pin_types={'1': 'passive', '2': 'passive'},
            kind='resistor', source='https://www.yageo.com/en/ProductSearch/PartNumberSearch',
            notes=['Exact 1% resistor; 0603 metric 1608. No Amazon availability established.'])

socket_rows = []
logic_names = ['EN', 'MS1', 'MS2', 'MS3', 'RESET', 'SLEEP', 'STEP', 'DIR']
power_names = ['VMOT', 'GND_MOTOR', '2B', '2A', '1A', '1B', 'VDD', 'GND_LOGIC']
for i in range(8):
    socket_rows.append(dict(row_position=i+1, y_mm=round(1.27+i*2.54, 2),
        logic_row=dict(x_mm=1.27, original_a4988=logic_names[i], reference='J1', pad=str(i+1),
            net=parts['J1']['pins'][str(i+1)]),
        power_row=dict(x_mm=13.97, original_a4988=power_names[i],
            reference=None if i == 0 else 'J2', pad=None if i == 0 else str(i),
            net=None if i == 0 else parts['J2']['pins'][str(i)], physically_absent=i == 0)))

ratio_min = 9900 / (9900 + 1010)
ratio_max = 10100 / (10100 + 990)
rth = 1010 * 10100 / (1010 + 10100)
data = dict(schema_version=1, revision='r0.3-planning',
    status='PROPOSED DIRECT-SINK INTERFACE ONLY - NOT CAD OR MANUFACTURING RELEASE',
    shared_nets=['EXT_RAW', 'V_EXT_PROT', 'V5_REG', 'V5_SELECT', 'COM_PLUS', 'GND'],
    host_input_nominal_v=[3.3, 5.0], input_abs_operating_max_v=5.5,
    proposed_output_channel_max_ma=20, proposed_output_aggregate_max_ma=60,
    logic_supply_v=None,
    power_ownership={'owner':'power specification', 'refs':'U20+, Q20+, R20+, C20+, D20+, L20+, F20+',
        'reverse_block':'Power owner must provide V5_REG -> reverse block -> V5_SELECT.',
        'indicator_rail':'V_IND_3V3 is independent of all host command gates.'},
    selectors=copy.deepcopy(old['selectors']),
    socket_contract=dict(view='TOP/component-side view; +Y from EN/VM end toward DIR/GND end',
        board_width_mm=15.24, header_row_spacing_mm=12.70, pin_pitch_mm=2.54,
        vm_absent_xy_mm=[13.97,1.27], original_body_length_mm=20.32,
        final_board_length_mm=None, rows=socket_rows,
        source='https://www.pololu.com/product/1182',
        warning='This is the A4988-compatible footprint contract, not evidence that every BTT/SKR socket matches.'),
    input_contract=dict(
        target_voh_min_v=2.1, target_vol_max_v=0.2,
        qualifications='Targets at adapter header referenced to adapter GND; exact host output specification and loaded waveform must be checked.',
        resistor_tolerance_percent=1,
        minimum_divider_ratio=ratio_min, maximum_divider_ratio=ratio_max,
        nominal_high_input_current_ma={'3.3V':3.3/11, '5V':5/11},
        max_resistive_static_input_current_ma_at_5p5v=5.5/(0.99+9.9),
        illustrative_total_static_input_current_ma_at_5p5v=5.5/(0.99+9.9)+0.010,
        max_initial_charge_current_ma_at_5p5v=5.5/0.99,
        illustrative_gate_leakage_budget_ua=10,
        leakage_budget_limit='Conservative calculation using the 25 C +/-8 V gate-leakage stress point; not a full-temperature leakage guarantee.',
        minimum_gate_high_v_at_2p1v=2.1*ratio_min-10e-6*rth,
        maximum_gate_low_v_at_0p2v=0.2*ratio_max+10e-6*rth,
        fet_resistance_anchor='3.9 ohm maximum at VGS=1.8 V, ID=50 mA, Tj=25 C; not a full-temperature 3.3 V interface guarantee.',
        proposed_sink_drop_at_20ma_25c_v=0.02*3.9,
        qualified_min_pulse_width_us=None, qualified_max_step_frequency_hz=None),
    signal_truth_table=[
        dict(host='HIGH within contract', gate='ON', drain='sinks toward GND', driver_input_current='flows from COM+ through a compatible driver input'),
        dict(host='LOW within contract', gate='OFF target', drain='high impedance except leakage', driver_input_current='off target; must verify loaded and temperature behavior'),
        dict(host='high impedance / unpowered', gate='10k pull-down discharges gate', drain='released after discharge', driver_input_current='off target; driver may still be enabled when ENA input current is off')
    ],
    startup_contract=[
        'No powered buffer or supervisor gates STEP/DIR/EN in this proposal.',
        'Pulldowns prevent a deliberately floating command from holding a MOSFET gate high; they do not guarantee zero spurious edges during power transitions.',
        'External drivers that enable with ENA open can be enabled during host reset, power loss, unplugging, or firmware startup. Do not call this fail-safe or drive-disabled startup.',
        'Host firmware must initialize STEP low and establish DIR/EN before motion is allowed; select input polarity from the actual driver manual and verify on the bench.',
        'Motor power and external-driver configuration control real enable semantics. This adapter is not an E-stop or STO circuit.',
        'Power off before changing SW1 or attaching/removing board, signal cable, or power wiring.'
    ],
    harness_contract=dict(board_socket='JST B4B-XH-A(LF)(SN)', cable_housing='JST XHP-4',
        crimp_contact='JST SXH-001T-P0.6', pitch_mm=2.5,
        pin1='COM_PLUS splits to PUL+, DIR+, ENA+ at the driver',
        pin2='PUL_MINUS to driver PUL-', pin3='DIR_MINUS to driver DIR-', pin4='ENA_MINUS to driver ENA-',
        ground_return='J4 pin2/GND joins host grounds through J2. J3 has no dedicated GND wire.',
        applies_to='Drivers with compatible common-positive optoisolated/current-input STEP/DIR/ENA interface and selected COM voltage.',
        excludes='Not differential signaling; not common-cathode-only inputs; not a universal interface; drive input resistors/selector/current must be verified.',
        mapping_check='Check numbered cavities from JST drawing and continuity fixture; do not infer from wire colors or apparent front/back orientation.'),
    fabrication_target=dict(copper_layers=2, min_track_mm=0.1524, min_copper_gap_mm=0.1524,
        min_drill_mm=0.3, min_via_diameter_mm=0.6, smt_side='TOP ONLY',
        note='Candidate footprint pad geometry checked separately; completed PCB routing and mask review still required.'),
    footprint_resolution=dict(custom_library_relative='../r0_2/Adapter.pretty',
        standard_libraries='Installed KiCad 10 footprints; native geometry verified by check_logic_proposal.py.',
        release_requirement='Copy qualified custom footprints and attribution into final r0.3 project before release; planning references do not constitute a package.'),
    parts=parts,
    evidence_boundaries=['Source inspection, calculations and isolated native footprint checks only.',
        'No final schematic/ERC, PCB/DRC, host fit, cable continuity, loaded waveform, thermal or startup evidence.',
        'No Amazon exact-part availability, retail target achievement, or manufacturing readiness claimed.'])
(ROOT / 'logic_spec.json').write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
print(f'Wrote proposal: {len(parts)} parts')
