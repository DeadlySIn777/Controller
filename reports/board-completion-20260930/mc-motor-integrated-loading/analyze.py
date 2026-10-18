"""Independent, report-only native-net load/capacitance inventory of the 327-part MC.

Reads an immutable local snapshot, imports no hardware generator or validator,
and never changes schematic/PCB/design source or a prior engineering receipt.
Numerical screens use expressly named allocations, not physical guarantees.
"""
from __future__ import annotations
import hashlib
import json
import math
import re
import shutil
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SNAP = HERE / 'inputs'
FILES = [
    'hardware/motion_card/design.json', 'hardware/motion_card/netlist.xml',
    'hardware/motion_card/assembly-map.json', 'hardware/motion_card/validation.json',
    'hardware/motion_card/erc.json', 'hardware/motion_card/motion_card.kicad_sch',
    'hardware/motion_card/fpga_core.kicad_sch', 'hardware/motion_card/mc_local_power.kicad_sch',
    'hardware/motion_card/watchdog_conditioning.kicad_sch', 'hardware/motion_card/mc_permission.kicad_sch',
    'hardware/motion_card/mc_motor_buffers.kicad_sch', 'hardware/motion_card/motion_card.kicad_pro',
    'hardware/mc_motor_buffers/design.json', 'hardware/mc_motor_buffers/validation.json',
    'hardware/mc_motor_buffers/README.md', 'hardware/mc_motor_buffers/review.json',
    'hardware/mc_local_power/design.json', 'hardware/mc_local_power/validation.json',
    'hardware/mc_local_power/README.md', 'tools/hardware_validate_mc_local_power.py',
    'hardware/fpga_core/design.json',
    'research/mc-motor-buffers/sn74lvc244a.pdf', 'research/mc-motor-buffers/sn74lvc244a.txt',
    'research/mc-motor-buffers/sn74lvc2g126.pdf', 'research/mc-motor-buffers/sn74lvc2g126.txt',
    'research/mc-motor-buffers/sn74lvc07a.pdf', 'research/mc-motor-buffers/sn74lvc07a.txt',
    'research/mc-motor-buffers/am26c31.pdf', 'research/mc-motor-buffers/am26c31.txt',
    'research/fpga-core/trion20-ds-v6.0.pdf', 'research/fpga-core/trion20-ds-v6.0.txt',
    'reports/next-implementation-20260930/watchdog-numerical-screen-reviewed.json',
    'reports/board-completion-20260930/watchdog-conditioning/conditioning-analysis.json',
    'PROJECT_MEMORY.md', 'docs/BUILD_PLAN.md', 'docs/PLATFORM_ROADMAP.md',
    'reports/ENGINEERING_STATUS.md',
]
EXTERNAL = Path('C:/Users/Gluis/claude-worktrees/controller-interface-spec/docs/interface-spec/04-safety-power-timing.md')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def prepare():
    manifest = HERE / 'input-manifest.json'
    if manifest.exists():
        saved = json.loads(manifest.read_text(encoding='utf-8'))
        for key, row in saved.items():
            assert sha(SNAP / key) == row['sha256'], 'Modified immutable input: ' + key
    else:
        saved = {}
    for key in FILES + ['frozen-is1/04-safety-power-timing.md']:
        if key in saved:
            continue
        src = EXTERNAL if key.startswith('frozen-is1/') else ROOT / key
        dst = SNAP / key
        dst.parent.mkdir(parents=True, exist_ok=True)
        before = sha(src)
        shutil.copy2(src, dst)
        assert sha(src) == sha(dst) == before
        saved[key] = {'source': str(src), 'sha256': before, 'bytes': src.stat().st_size}
    manifest.write_text(json.dumps(saved, indent=2) + '\n', encoding='utf-8')
    return saved


def load(key):
    return json.loads((SNAP / key).read_text(encoding='utf-8'))


def canon(s):
    return s.rsplit('/', 1)[-1]


def main():
    manifest = prepare()
    design = load('hardware/motion_card/design.json')
    comps = design['components']
    assert len(comps) == 327
    xml = ET.parse(SNAP / 'hardware/motion_card/netlist.xml').getroot()
    fresh = ET.parse(HERE / 'fresh-netlist.xml').getroot()
    def conductors(tree):
        return sorted((canon(n.get('name')), p.get('ref'), p.get('pin'), p.get('pinfunction'), p.get('pintype'))
                      for n in tree.find('nets') for p in n)
    assert conductors(xml) == conductors(fresh), 'Fresh native schematic conductor export differs'
    native, pin_net = {}, {}
    for node in xml.find('nets'):
        key = canon(node.get('name'))
        assert key not in native
        native[key] = [dict(p.attrib) for p in node if p.get('ref') in comps]
        for pin in native[key]:
            assert (pin['ref'], pin['pin']) not in pin_net
            pin_net[pin['ref'], pin['pin']] = key
    checks = 0
    for ref, comp in comps.items():
        for pin, net in comp['pins'].items():
            if net is not None:
                assert pin_net.get((ref, str(pin))) == canon(net), (ref, pin, net)
                checks += 1

    def inventory(net):
        return [{'ref': p['ref'], 'pin': p['pin'], 'function': p.get('pinfunction'),
                 'type': p.get('pintype'), 'mpn': comps[p['ref']].get('mpn'),
                 'value': comps[p['ref']]['value'], 'source_block': comps[p['ref']]['source_block']}
                for p in native[net]]

    def pulls(net):
        result = []
        for p in native[net]:
            r = p['ref']
            if r.startswith('R'):
                comp = comps[r]
                other = next((n for pin, n in comp['pins'].items() if str(pin) != p['pin']), None)
                value = comp.get('resistance_ohm')
                if value is None:
                    m = re.match(r'([0-9.]+)([kM]?)(?:\s|R)', comp['value'])
                    assert m, (r, comp['value'])
                    value = float(m.group(1)) * {'': 1, 'k': 1000, 'M': 1000000}[m.group(2)]
                result.append({'ref': r, 'ohm': value, 'other_net': other})
        return result

    inputs = {}
    for i in range(12):
        for signal in ('STEP', 'DIR', 'EN'):
            net = f'EN{i}_N_FPGA' if signal == 'EN' else f'{signal}{i}_FPGA'
            bias = pulls(net)
            assert len(bias) == 1 and bias[0]['ohm'] == 4700
            assert bias[0]['other_net'] == ('IO_3V3' if signal == 'EN' else 'LOGIC_GND')
            assert len(native[net]) == 3
            assert len([p for p in native[net] if p['ref'] == 'U1001']) == 1
            inputs[net] = {'nodes': inventory(net), 'pulls': bias}
    assert len(inputs) == 36
    for net in ('TX_PERMIT', 'BANK_B_BUFFER_ENABLE_QUALIFIED'):
        bias = pulls(net)
        assert sorted(r['ohm'] for r in bias) == [4700, 10000]
        assert all(r['other_net'] == 'LOGIC_GND' for r in bias)
    boe = native['BANK_B_BUFFER_ENABLE_QUALIFIED']
    assert len([p for p in boe if p['ref'].startswith('U50') and p['pintype'] == 'input']) == 13
    assert not any(p['pintype'] in ('output', 'bidirectional') for p in boe)
    assert ('U4013', '6') in {(p['ref'], p['pin']) for p in boe}

    # Count manufacturer-defined A and OE pins independently of declared path ledger.
    a_pins, a_grounded, b_data, b_oe, path_counts = [], [], [], [], Counter()
    for ref, comp in comps.items():
        if comp.get('mpn') == 'SN74LVC244APWR':
            for pin in ('2', '4', '6', '8', '11', '13', '15', '17'):
                net = pin_net[ref, pin]
                (a_grounded if net == 'LOGIC_GND' else a_pins).append([ref, pin, net])
            for pin in ('1', '19'):
                assert pin_net[ref, pin] == 'LOGIC_GND'
            path_counts['A_chips'] += 1
        elif comp.get('mpn') == 'SN74LVC2G126DCUR':
            for pin in ('2', '5'):
                if pin_net[ref, pin] != 'LOGIC_GND':
                    b_data.append([ref, pin, pin_net[ref, pin]])
            for pin in ('1', '7'):
                if pin_net[ref, pin] != 'LOGIC_GND':
                    b_oe.append([ref, pin, pin_net[ref, pin]])
            path_counts['B_chips'] += 1
    assert (len(a_pins), len(a_grounded), len(b_data), len(b_oe)) == (25, 7, 13, 13)
    assert path_counts == {'A_chips': 4, 'B_chips': 7}
    outputs = {}
    for i in range(12):
        card = 'MIA' if i < 8 else 'MX4'
        for sig in ('STEP', 'DIR', 'EN'):
            net = f'EN{i}_N_TO_{card}' if sig == 'EN' else f'{sig}{i}_TO_{card}'
            bias = pulls(net)
            assert len(bias) == (1 if sig == 'EN' else 2)
            assert any(p['ohm'] == 33 for p in bias)
            assert not any(p['other_net'] == 'IO_3V3' for p in bias)
            if sig != 'EN':
                assert any(p['ohm'] == 10000 and p['other_net'] == 'LOGIC_GND' for p in bias)
            outputs[net] = {'nodes': inventory(net), 'resistors': bias}
    for net in ('TX_PERMIT_A_TO_MIA', 'TX_PERMIT_B_TO_MX4'):
        outputs[net] = {'nodes': inventory(net), 'resistors': pulls(net)}
    assert len(outputs) == 38

    cap_groups = defaultdict(list)
    for ref, comp in comps.items():
        if ref.startswith('C') and {pin_net.get((ref, '1')), pin_net.get((ref, '2'))} == {'IO_3V3', 'LOGIC_GND'}:
            m = re.match(r'([0-9.]+)([un])F', comp['value'])
            assert m
            uf = float(m.group(1)) * (1 if m.group(2) == 'u' else .001)
            tol, temp = (.20, .22) if ref == 'C2005' else (.10, .15)
            cap_groups[comp['source_block']].append({'ref': ref, 'nominal_uf': uf,
                                                    'upper_uf': uf * (1+tol) * (1+temp)})
    cap_sums = {group: {'refs': rows, 'nominal_uf': sum(r['nominal_uf'] for r in rows),
                        'upper_uf': sum(r['upper_uf'] for r in rows)} for group, rows in cap_groups.items()}
    assert len(cap_groups['mc_motor_buffers']) == 11
    assert math.isclose(cap_sums['mc_motor_buffers']['nominal_uf'], 1.1)
    populated_extra = sum(cap_sums[g]['nominal_uf'] for g in ('watchdog_conditioning', 'mc_permission', 'mc_motor_buffers'))
    assert math.isclose(populated_extra, 3.7)

    vmax, vmin = 3.465, 3.14
    pdmin, pdmax = 4700*.99, 4700*1.01
    ten_min, ten_max = 10000*.99, 10000*1.01
    parallel_max = 1 / (1/pdmax + 1/ten_max)
    pullload = vmax/pdmin
    weakload = vmax/27000
    step_start = lambda leak: (vmax/27000+leak)/(1/27000+1/pdmax)
    en_start = lambda leak: (vmin/pdmax-leak)/(1/pdmax+1/30000)
    motor_current = 36*(pullload+weakload)+24*20e-6+12*5e-6
    # Conditional allocations: receiver circuitry is required but absent, not qualified.
    own_pd = 26*vmax/ten_min
    future_receiver_pd = 26*vmax/ten_min
    future_am_leak = 24*1e-6
    increment_tx_boe = 2*pullload + 25e-6 + 65e-6
    icc = 4*40e-6+7*10e-6
    conditional_dicc = len(a_pins)*.005 + (len(b_data)+len(b_oe))*.0005
    loadallocation = motor_current + own_pd + future_receiver_pd + future_am_leak + increment_tx_boe + icc
    power = load('hardware/mc_local_power/validation.json')['analytical_screen']
    factor = 3.34125/(4.85*.85)
    screens = {
        'evidence_class': 'native inventory + arithmetic with declared leakage/receiver/power allocations; no physical measurement',
        'STEP_DIR_configuration_weak_PU_upper_A_v': step_start(30e-6),
        'STEP_DIR_configuration_weak_PU_upper_B_v': step_start(15e-6),
        'EN_N_with_user_weak_PD_lower_A_v': en_start(30e-6),
        'EN_N_with_user_weak_PD_lower_B_v': en_start(15e-6),
        'motor36_input_allocation_native_bank_leakage_a': motor_current,
        'standalone_all_A_leakage_36_allocation_a': 36*(pullload+weakload+20e-6),
        'TX_PERMIT_fitted_receiver_leakage_a': 50e-6,
        'TX_PERMIT_high_pulls_plus_receiver_leakage_a': pullload+vmax/ten_min+50e-6,
        'TX_PERMIT_low_configuration_weak_PU_plus_receiver_leakage_a': weakload+50e-6,
        'BOE_fitted_receiver_leakage_a': 70e-6,
        'BOE_high_pulls_plus_receiver_leakage_a': pullload+vmax/ten_min+70e-6,
        'BOE_no_driver_floating_low_allocation_v': parallel_max*70e-6,
        'FPGA_CRESET_N_external_high_a': vmax/ten_min+20e-6,
        'FPGA_CRESET_N_external_low_a': 20e-6,
        'FPGA_CRESET_N_total_high_at_power_block_3v4_screen_a': 3.4/(4700*.98)+3.4/ten_min+20e-6,
        'STEP_DIR_high_load_with_receiving_PD_a': 2*vmax/ten_min+1e-6,
        'EN_N_low_load_from_receiver_rail_a': vmax/ten_min+5e-6,
        'A_STEP_DIR_receiver_low_at_100ua_row_v': .3 + 33*1.01*1e-6,
        'A_STEP_DIR_receiver_high_at_3v_12ma_row_v': 2.25 - 33*1.01*(2*vmax/ten_min+1e-6),
        'A_EN_N_receiver_low_using_3v_24ma_125C_row_v': .8+33*1.01*(vmax/ten_min+5e-6),
        'A_EN_N_receiver_low_using_3v_24ma_85C_row_v': .55+33*1.01*(vmax/ten_min+5e-6),
        'B_EN_N_receiver_low_using_3v_16ma_row_v': .4+33*1.01*(vmax/ten_min+5e-6),
        'MC_zero_supply_EN_N_A_receiver_lower_allocated_v': vmin-25e-6*ten_max-20e-6*33*1.01,
        'MC_zero_supply_EN_N_B_receiver_lower_allocated_v': vmin-15e-6*ten_max-10e-6*33*1.01,
        'MC_zero_supply_STEP_DIR_A_receiver_upper_allocated_v': 21e-6*ten_max+20e-6*33*1.01,
        'MC_zero_supply_STEP_DIR_B_receiver_upper_allocated_v': 11e-6*ten_max+10e-6*33*1.01,
        'buffer_ICC_rail_input_IO_zero_only_a': icc,
        'conditional_additive_DICC_125C_test_point_a': conditional_dicc,
        'conditional_additive_DICC_85C_test_point_a': len(a_pins)*.0005+(len(b_data)+len(b_oe))*.0005,
        'new_buffer_stage_rail_reservation_proposal_without_DICC_a': loadallocation,
        'new_buffer_stage_rail_reservation_proposal_with_conditional125C_DICC_a': loadallocation+conditional_dicc,
        'fitted26_output_PD_high_allocation_a': own_pd,
        'required_future26_receiver_PD_high_allocation_a': future_receiver_pd,
        'new_TX_BOE_PD_and_receiver_increment_a': increment_tx_boe,
        'slot_conversion_IO3V3_to_5V_with_85pct_efficiency_factor': factor,
        'preserved_baseline_slot_steady_a_model': power['steady_slot_input_a_model'],
        'preserved_baseline_slot_concurrent_startup_a_model': power['concurrent_startup_input_a_model'],
        'additive_slot_reservation_without_DICC_a_model': power['steady_slot_input_a_model']+loadallocation*factor,
        'additive_slot_reservation_with_conditional125C_DICC_a_model': power['steady_slot_input_a_model']+(loadallocation+conditional_dicc)*factor,
        'additive_concurrent_startup_with_conditional125C_DICC_a_model': power['concurrent_startup_input_a_model']+(loadallocation+conditional_dicc)*factor,
        'populated_additional_nominal_IO3V3_uf': populated_extra,
        'nominal_IO3V3_additional_reservation_uf': 10,
        'actual_fitted_direct_IO3V3_upper_uf': sum(s['upper_uf'] for s in cap_sums.values()),
        'power_block_IO3V3_cap_model_with_full_reserved_extra_upper_uf': 89.90465,
        'full_delta_ICC_arbitrary_nonrail_bound_proved': False,
        'full_operating_rail_power_bound_proved': False,
        'configured_FPGA_GPIO_drive_full_temperature_qualified': False,
        'intermediate_rail_or_opposite_partial_power_qualified': False,
    }
    assert screens['FPGA_CRESET_N_external_high_a'] < .001
    assert screens['FPGA_CRESET_N_external_low_a'] < .0001
    assert screens['A_EN_N_receiver_low_using_3v_24ma_125C_row_v'] > .8
    assert screens['A_EN_N_receiver_low_using_3v_24ma_85C_row_v'] < .8
    assert screens['B_EN_N_receiver_low_using_3v_16ma_row_v'] < .8
    assert math.isclose(screens['actual_fitted_direct_IO3V3_upper_uf'], 81.93515)
    assert screens['additive_slot_reservation_without_DICC_a_model'] > .5
    assert screens['additive_concurrent_startup_with_conditional125C_DICC_a_model'] > .8
    erc = load('hardware/motion_card/erc.json')
    violations = [v for s in erc['sheets'] for v in s['violations']]
    assert not violations
    timer = load('reports/next-implementation-20260930/watchdog-numerical-screen-reviewed.json')['selected_3n3']
    results = {
        'revision': 'mc-motor-integrated-loading-r01', 'physical_components': 327,
        'native_declared_connected_pin_checks': checks, 'native_erc_violations_observed': len(violations),
        'fresh_native_netlist_conductor_export_matches_copied_source': True,
        'manufacturing_ready': False, 'physical_measurement': False,
        'motor_gpio_inputs': inputs, '38_outgoing_paths': outputs,
        'TX_PERMIT': {'nodes': inventory('TX_PERMIT'), 'pulls': pulls('TX_PERMIT')},
        'BANK_B_BUFFER_ENABLE_QUALIFIED': {'nodes': inventory('BANK_B_BUFFER_ENABLE_QUALIFIED'),
                                         'pulls': pulls('BANK_B_BUFFER_ENABLE_QUALIFIED'),
                                         'fitted_driver_present': False},
        'FPGA_CRESET_N': {'nodes': inventory('FPGA_CRESET_N'), 'pulls': pulls('FPGA_CRESET_N')},
        'buffer_counts': {'A_used_data': a_pins, 'A_grounded_data': a_grounded,
                          'B_used_data': b_data, 'B_used_positive_OE': b_oe, **path_counts},
        'IO3V3_direct_capacitance_by_source': cap_sums, 'screens': screens,
        'watchdog_selected_3n3_existing_allocation': timer,
        'source_unchanged_during_review': all(sha(Path(r['source'])) == r['sha256'] for r in manifest.values()),
        'input_sha256': {key: row['sha256'] for key, row in manifest.items()},
    }
    assert results['source_unchanged_during_review']
    (HERE/'analysis.json').write_text(json.dumps(results, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'components': len(comps), 'native_connected_pin_checks': checks,
                      'source_inputs_unchanged': results['source_unchanged_during_review'],
                      'screens': screens}, indent=2))


if __name__ == '__main__':
    main()
