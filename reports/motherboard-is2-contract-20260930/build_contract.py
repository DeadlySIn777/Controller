"""Record the authorized physical IS-2 delta without changing frozen IS-1 or CAD."""
from __future__ import annotations

import collections
import csv
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FROZEN = Path('C:/Users/Gluis/claude-worktrees/controller-interface-spec')
OUT = ROOT / 'hardware/motherboard/requirements.json'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name: str) -> dict:
    return json.loads((FROZEN / 'spec' / name).read_text(encoding='utf-8-sig'))


def main() -> None:
    if OUT.exists() or (HERE / 'inputs').exists():
        raise SystemExit('Refusing to overwrite an existing contract/source archive.')
    sources = [FROZEN / 'spec' / name for name in
               ['modules.json', 'terminals.json', 'allocations.json', 'protocol.json',
                'safety.json', 'service.json']]
    sources += [FROZEN / 'docs/CONTROLLER_INTERFACE_SPEC.md']
    sources += sorted((FROZEN / 'docs/interface-spec').glob('*.md'))
    before = {str(p.relative_to(FROZEN)).replace('\\', '/'): digest(p) for p in sources}
    for p in sources:
        dest = HERE / 'inputs' / p.relative_to(FROZEN)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dest)
        assert digest(p) == digest(dest)

    terminals = load('terminals.json')
    safety = load('safety.json')
    protocol = load('protocol.json')
    for name in ['modules.json', 'allocations.json', 'service.json']:
        assert load(name)['spec_revision'] == 'IS-1'
    assert terminals['spec_revision'] == safety['spec_revision'] == protocol['spec_revision'] == 'IS-1'

    regions = {
        'BASE': 'terminals_chassis', 'PSM': 'power_protection', 'CMC': 'compute_bay',
        'MC': 'fpga_supervision', 'MIA': 'motor_bank_a', 'MX4': 'motor_bank_b',
        'EIA': 'encoder_fast_inputs', 'DIC': 'digital_input_safety',
        'DOA': 'output_bank_a', 'DOB': 'output_bank_b', 'ACC': 'analog_process_comms',
        'ESC': 'esp_service_bay', 'SCART': 'settings_storage_bay',
        'EX8': 'optional_encoder_accessory', 'XTB': 'terminals_chassis', 'XS': 'optional_accessory',
    }

    rows = []
    for t in terminals['terminals']:
        optional = t['connector'].startswith('XE') and int(t['connector'][2:]) >= 4
        scope = 'optional_qualified_accessory_reference' if optional else 'motherboard_standard'
        res = t['resource']
        rows.append({
            'source_id': t['id'], 'source_pointer': f"spec/terminals.json#terminals/{len(rows)}",
            'logical_connector': t['connector'], 'logical_position': t['position'],
            'net': t['net'], 'function': t['function'], 'function_class': t['function_class'],
            'domain': t['domain'], 'inherited_owner': t['owner_card'],
            'motherboard_region_or_accessory': regions[t['owner_card']], 'scope': scope,
            'electrical_target': t['electrical_target'], 'protection': t['protection'],
            'power_up_state': t['power_up_state'], 'fault_state': t['fault_state'],
            'resource': res, 'cnc1_field': t['cnc1_field'], 'hal_pin': t['hal_pin'],
            'qualification_test_id': t['test_id'],
            'production_connector_mpn': None, 'production_footprint': None,
            'production_fpga_ball': None,
            'implementation_state': 'requirement_not_complete_controller_evidence',
            'mapping_note': ('Optional ENC4-11 functions remain reserved; this does not select a custom EX8/XTB card, socket, transport or accessory.'
                             if optional else
                             'Logical terminal/function retained; soldered circuit moves to the active motherboard. Legacy card/path/ball text is reference only, not production allocation.'),
        })

    connector_rows = []
    for c in terminals['connectors']:
        optional = c['id'].startswith('XE') and int(c['id'][2:]) >= 4
        connector_rows.append({
            'logical_id': c['id'], 'positions': c['positions'], 'function': c['purpose'],
            'scope': 'optional_qualified_accessory_reference' if optional else 'motherboard_standard',
            'source_owner': c['owner_card'], 'source_header_mpn': c['header_mpn'],
            'source_plug_mpn': c['plug_mpn'], 'source_keying': c['keying'],
            'source_status': c['mpn_status'], 'selected_header_mpn': None,
            'selected_plug_mpn': None, 'selected_footprint': None,
            'note': 'Retain logical pin order until a versioned electrical/terminal change; old rack location is superseded. Mating dimensions/current/clearance remain engineering work.',
        })

    def requirement(rid: str, function: str, counts: dict, connectors: list[str], note: str) -> dict:
        selected = [t for t in rows if t['logical_connector'] in connectors]
        return {'id': rid, 'function': function, 'counts': counts,
                'logical_connectors': connectors, 'terminal_source_ids': [t['source_id'] for t in selected],
                'terminal_nets': sorted({t['net'] for t in selected if t['net'] is not None}),
                'fpga_signals': sorted({t['resource']['signal'] for t in selected
                                        if t['resource'].get('kind') == 'fpga_pin'}),
                'note': note, 'implemented': False}

    functions = [
        requirement('MB-MOTOR-12', 'Differential STEP/DIR, individual enable and alarm',
                    {'motors_standard_fully_fitted': 12, 'step_pairs': 12, 'dir_pairs': 12,
                     'individual_no_com_nc_enable_sets': 12, 'individual_alarm_inputs': 12},
                    [f'XM{i}' for i in range(12)],
                    'M0-7 and M8-11 are motherboard banks A/B, not removable MIA/MX4. All twelve hardware paths are fitted; no paid unlock or motor-card purchase is introduced. Channels are not axes.'),
        requirement('MB-ENCODER-4', 'Four standard differential ABZ encoders',
                    {'standard_abz_ports': 4, 'receiver_channels': 12}, [f'XE{i}' for i in range(4)],
                    'Protected port supplies and validity/age retained. Commanded motor position is not measured encoder feedback.'),
        requirement('MB-ENCODER-GROWTH', 'Qualified optional encoder growth',
                    {'additional_abz_functions_reserved': 8}, [f'XE{i}' for i in range(4,12)],
                    'Preserve the ability to use twelve motor interfaces with encoder growth. No custom EX8/XTB family or guaranteed standard socket has been selected. Optional accessory must carry declared timing, isolation, identity and fault behavior.'),
        requirement('MB-DI-24', 'Twenty-four general digital inputs',
                    {'general_di': 24}, ['XDI0','XDI1','XDI2'],
                    'Do not consume general DI for dedicated drive alarms, safety interface or fast probes. NPN/PNP selectable hardware is FIO-P1, not an already fitted capability.'),
        requirement('MB-DO-16', 'Sixteen protected smart sourcing outputs',
                    {'general_do':16, 'quad_switches':4, 'continuous_a_per_channel':0.5,
                     'continuous_a_per_four_channel_group':2.0}, ['XDO0','XDO1'],
                    'TPS274C65ASRHAR remains the selected sourcing baseline. Keep current/fault/temperature/supply diagnostics and independent inhibition. Paired ILIM constraints require versioned configuration validation; 1/2 A, AUX12 and sinking options remain separate unqualified proposals.'),
        requirement('MB-FAST', 'Two fast probes, two differential frequency inputs, dedicated MPG and pendant',
                    {'probes':2, 'frequency_inputs':2, 'dedicated_mpg_ab':1, 'pendant_selector_inputs':10},
                    ['XPR','XF','XH1','XH2'],
                    'Retain coherent capture, typed supplies, accessory identity, debounce/staleness and marker/double-read rules where serial status registers are retained.'),
        requirement('MB-PROCESS', 'PWM and floating process contacts',
                    {'pwm':2,'floating_process_contacts':2}, ['XPW','XPC0','XPC1'],
                    'PWM inhibits low; PROC_PERMIT and output/path latches gate contacts in hardware. PROCESS_PERMIT does not become a generic spindle stop.'),
        requirement('MB-ANALOG', 'Isolated analog I/O',
                    {'independently_isolated_0_10v_ao':2,'isolated_group_ai':4}, ['XAO','XAI'],
                    'Retain AO safe-zero clamp, AI range/calibration/age and protected sensor supply. Exact ADC and total isolated power/cost remain open.'),
        requirement('MB-FIELDBUS', 'Isolated RS-485 and CAN',
                    {'rs485':1,'can':1}, ['XB1','XB2'],
                    'Ordinary replaceable third-party peripherals remain allowed. Profile rates/termination/error/age apply; fieldbus is never the only machine run-enable or a path into the servo thread.'),
        requirement('MB-SAFETY-INTERFACE', 'Hardwired machine permission and feedback interface',
                    {'external_permit':1,'process_permit':1,'safety_status':1,'reset_arm':1,
                     'contactor_feedback':1,'sto_feedback':1,'arm_lamp':1,'permission_contact':1}, ['XS1'],
                    'Independent receiver defaults and onboard safety-domain health replace DIC card presence. Motherboard is not a certified machine safety controller.'),
        requirement('MB-POWER', 'Separate protected entries and chassis/shield strategy',
                    {'protected_entries':3}, ['XP1','XP2','XP3','XPE1'],
                    'Physical entry/bank fuses plus coordinated electronic protection, measured flags/age and fail-closed defaults. Whole-assembly rail/current/thermal budgets must be rebuilt; old rack connector and slot-feed costs are not reused.'),
    ]

    transitions = [
        {'old':'BASE + thirteen card positions/cage/SCART bracket','new':'One active custom motherboard with labelled pluggable field terminals and commodity module sockets','disposition':'Physical rack, DIN/HB/H15 card connectors, guides/levers and redundant slot feeds removed from the new BOM; machine domain isolation/protection stays.'},
        {'old':'PSM / CMC / MC','new':'Soldered power, compute-bay interface, FPGA/clock/flash/supervision motherboard regions','disposition':'Only the purchased compute module is replaced independently; a soldered FPGA fault requires motherboard repair or replacement.'},
        {'old':'MIA + MX4 + XTB motor terminals','new':'Twelve fully fitted motor interface paths and all XM0-XM11 plugs on the motherboard','disposition':'Eight-plus-four removable motor-card topology and purchase dependency superseded.'},
        {'old':'EIA / DIC / DOA / DOB / ACC','new':'Soldered encoder/fast-input, DI/safety, two DO banks and analog/process/comms regions','disposition':'MCUs/Ioff/isolators/supervisors may remain where justified; physical card boundaries are removed, electrical isolation is not.'},
        {'old':'ESC custom service card','new':'Purchased replaceable ESP32 board/module in a reviewed motherboard socket/interface','disposition':'No custom ESP daughterboard required; exact purchased module, socket, pin map, power/reset/USB and antenna clearance remain to select.'},
        {'old':'SCART protected configuration/history cartridge','new':'Replaceable commodity storage/settings provision with protected, power-loss-tolerant configuration/history','disposition':'No silent equivalence between a generic SD/SSD and the old protected-memory guarantee; storage architecture/capacity/endurance/recovery still require qualification.'},
        {'old':'EX8 + encoder XTB, XS DIN slot','new':'Qualified optional accessory/standardized expansion interface','disposition':'Keep logical growth/capacity; do not create a new family of custom cards or advertise a connector before selection and qualification.'},
    ]

    changes = [
        {'id':'IS2-C01','subject':'Card presence, class and installed masks','required_change':'Define motherboard hardware revision and real onboard functional/rail qualification separately from removable-module presence. Do not tie missing MIA/MX4/DIC/etc presence pins true or emulate their MIR-1 identity. Installed motor mask follows all twelve actually fitted/qualified paths; armed/configured mask may use fewer.','affected':['CNS3.slot_status','STS.expansion.mx4','STS.installed_channels','CAP3/IDP3','hw.modules','module HAL pins'], 'status':'implementation_required'},
        {'id':'IS2-C02','subject':'Permission equations and bank-B OE','required_change':'Replace each obsolete card-present/tamper term with an explicitly reviewed onboard domain health/default/fault latch term. Keep rail/CDONE/endpoint/WD/EXT_PERMIT cuts, actual bank-B qualification and OPI_BOE interruption detection; do not remove it merely because the connector disappears.','affected':['DIC_OK','base_ok','out_base_ok','TX_PERMIT_A','TX_PERMIT_B','OUT_PERMIT_k','OPI_A/B/BOE/TX/OUT'], 'status':'schematic_and_RTL_revision_required'},
        {'id':'IS2-C03','subject':'Serial I/O controllers and identities','required_change':'Retain deterministic IOL1 L0-L3 behavior initially, if these local controllers remain fitted; use a versioned soldered-domain identity/port binding and real health/revision. Never fabricate removable slot straps or card EEPROM success. CRC, class/epoch/sequence/freshness, validate-before-commit, local watchdogs and hardwired enable gates remain mandatory.','affected':['IOL1','card/controller firmware','port expected class/slot','hardware health','diagnostics'], 'status':'protocol_firmware_service_revision_required'},
        {'id':'IS2-C04','subject':'DO shared current limits','required_change':'Represent or reject shared paired ILIM resources before apply. Selected AS chip cannot supply arbitrary independent per-channel trip settings or the 2 A proposed load tier. Preserve 0.5 A/channel and 2 A/four-channel group.','affected':['IOL1 DO8 config blob','public configuration schema','CLI/UI validation','DO register verification'], 'status':'electrical_constraint_fix_required'},
        {'id':'IS2-C05','subject':'Offline replacement and configuration','required_change':'Revise replaceable-unit list to motherboard, purchased compute/service/storage and qualified accessories. Preserve plug-by-plug harness retention, machine lineage/configuration, protected calibration, offline entitlement and deliberate recommissioning. Old five-minute per-card spare/service claims no longer apply to soldered regions.','affected':['hw.modules','service replacement checks','configuration restore','licensing','assembly/service instructions'], 'status':'service_implementation_required'},
        {'id':'IS2-C06','subject':'Module selector and bootstrap','required_change':'Implement qualified common-subset/default-off compute routing, stable cold-start selector, independent or safely bootstrapped identity cross-check and matching module OS. Wrong/reserved/ambiguous selection stays inhibited/service-only. Supported compute swap requires no FPGA/ESP reflash; new support still requires qualification.','affected':['compute carrier pin matrix','selector circuitry','boot/provisioning','capability manifest'], 'status':'circuit_and_host_image_required'},
        {'id':'IS2-C07','subject':'FPGA pin/bank allocation and timing','required_change':'Reconcile source schematic/native PCB/RTL wrapper/vendor pin file for all twelve motor paths, four base encoders, full IO and revised health/status. Optional encoder growth may reserve resource capacity but no old unproven ball allocation becomes approved. Native synthesis and vendor fit/timing plus physical transport/load measurements required.','affected':['T20F256 allocation','HDL wrapper','MC copper reuse','full board planes/returns','loaded timing budget'], 'status':'implementation_and_validation_required'},
        {'id':'IS2-C08','subject':'RGB and actual state observations','required_change':'Implement ordinary seven RGB indicators plus input/output/alarm and independent WDT indications, with powered hardware fault-red override. LED/UI healthy states follow measured/qualified observations with validity/age; no decorative status chain substitutes for protection.','affected':['status circuitry','pin/power budget','service diagnostics','panel labels'], 'status':'hardware_and_service_required'},
    ]

    data = {
        'schema_version':1, 'spec_revision':'IS-2', 'contract_id':'MOTHERBOARD-IS2-20260930',
        'date':'2026-09-30', 'status':'authorized_physical_topology_delta_implementation_incomplete',
        'manufacturing_ready':False, 'parent_revision':'IS-1',
        'scope':'Local physical/topology delta; not a complete revised wire ABI or a substitute for native schematic/PCB evidence.',
        'authorization':'Latest user directs one custom active motherboard, commodity replaceable modules and all twelve motor interfaces on that motherboard; this supersedes the IS-1 passive rack/card and removable motor9-12 physical arrangement.',
        'frozen_source_root':str(FROZEN).replace('\\','/'), 'frozen_input_hashes_sha256':before,
        'frozen_source_policy':'Read-only external IS-1; archived exact files under reports/motherboard-is2-contract-20260930/inputs. No external file changed.',
        'physical_architecture': {
            'custom_controller_pcbs':1, 'type':'active_motherboard',
            'custom_daughterboard_family_required':False, 'passive_backplane_required':False,
            'soldered_functions':['FPGA','clock/configuration flash','watchdogs/permission','all twelve motor interfaces','four base ABZ encoder ports','DI24','smart DO16','probe/frequency/MPG/pendant','PWM/process contacts','analog I/O','RS-485/CAN','power/protection','status LEDs','terminal blocks','module detection/provisioning interface'],
            'commodity_replaceable_modules':['electrically qualified CM4/CM5/BTT CB1/CB2 variants','ESP32 board/module with qualified socket','qualified storage/settings medium','qualified ordinary communications/accessories','future verified adapter'],
            'all_12_motor_paths_fitted':True, 'motor_9_12_custom_card_required':False,
            'software_license_unlock_of_base_motor_channels_promised':False,
            'compute_module_electrical_interchangeability_qualified':False,
            'native_board_dimensions_layers_finalized':False,
        },
        'boundary_transitions':transitions, 'functional_requirements':functions,
        'logical_contract_inheritance': {
            'fault_to_inhibit_max_ms':20.0,
            'inhibit_definition':safety['fault_timing']['definitions']['t_inhibit'],
            'fault_to_inhibit_is_machine_stop_time':False,
            'watchdog_progress':'Only accepted motion/full-I/O transactions produce the corresponding progress; external clock-independent watchdogs and separate motion/output latches retained.',
            'watchdog_components_reference':safety['watchdogs']['common'],
            'current_MC_watchdog_and_rail_circuit_is_physically_qualified':False,
            'host_link':protocol['host_link'],
            'host_link_note':'Inherit CNC3 dual-CS length/CRC/semantic discipline as the baseline. Removed rack fields require explicit versioned capability/diagnostics semantics; this file does not authorize ABI3 to misreport rack identities.',
            'servo_period_us':1000.0, 'completion_target_us':700.0,
            'timing_targets_are_measurements':False,
            'io_validate_before_commit':protocol['io_link']['validate_before_commit'],
            'io_watchdog_reference':protocol['io_link']['card_watchdogs'],
            'diagnostics':['real acquisition or qualified hardware flag','validity and data age on every displayed measurement','measured facts separate from AI diagnosis','unavailable/stale instead of plausible zero','no reported contact measurement where only command state is available'],
            'recovery':['no automatic motion or output restart','loss of position continuity unhomes affected joints','invalid/unconfigured/reset/unpowered/missing-module defaults inhibited','power-off replacement','offline setup/provisioning/configuration/entitlement','calibration and machine lineage retained and revalidated'],
            'public_service':['single CLI/configuration/UI service contract','structured discover/validation/preview/diff','reversible generation commit','electrical/motion limits remain deterministic','AI optional and cannot bypass protection'],
        },
        'field_output_baseline': {'mpn':'TPS274C65ASRHAR','polarity':'sourcing',
                                  'continuous_a_per_channel':0.5,'continuous_a_per_four_channel_group':2.0,
                                  'independent_2a_mode_qualified':False,'paired_ilim_validation_required':True,
                                  'FIO_P1_extension_applied':False},
        'implementation_conflicts':changes,
        'counts': {'source_field_terminal_rows':len(rows),
                   'motherboard_logical_terminal_positions':sum(t['scope']=='motherboard_standard' for t in rows),
                   'optional_encoder_reference_positions':sum(t['scope']=='optional_qualified_accessory_reference' for t in rows),
                   'source_connectors':len(connector_rows),
                   'motherboard_logical_field_connectors':sum(c['scope']=='motherboard_standard' for c in connector_rows),
                   'optional_encoder_reference_connectors':sum(c['scope']=='optional_qualified_accessory_reference' for c in connector_rows),
                   'base_direct_field_signal_names':77,'optional_encoder_direct_signal_names':24,
                   'base_IOL1_and_fast_status_signal_count_reference':19,
                   'complete_FPGA_pin_budget_qualified':False},
        'connector_function_mapping':connector_rows, 'terminal_function_mapping':rows,
        'evidence_boundary': {
            'existing_MC':'MC r0.4 / board-review revision 20260930-14 is reusable partial motion/supervision source/copper, not the complete motherboard.',
            'historical_six_joint_two_encoder_evidence_remains_historical':True,
            'source_inspection_this_contract':True,'native_ERC_this_contract':False,'native_DRC_this_contract':False,
            'host_tests_this_contract':False,'target_build_this_contract':False,'HDL_simulation_this_contract':False,
            'FPGA_vendor_fit_this_contract':False,'physical_measurements_this_contract':False,
        },
        'open_hardware_gates':['complete reconciled schematic','source-verified pinouts/footprints and module contacts','native FPGA bank/ball allocation and vendor fit','all required routing and planes','all conductive isolation/return/chassis boundaries','native full-controller ERC/DRC and uncapped connectivity','actual manufacturing rules and stackup','Gerbers/drills/CPL/BOM/assembly/test drawings','complete qty1/10/100 costing separate from purchased modules','physical timing/thermal/fault/EMC and machine qualification'],
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    fieldnames=['source_id','logical_connector','logical_position','net','function_class','domain',
                'inherited_owner','motherboard_region_or_accessory','scope','cnc1_field','hal_pin','qualification_test_id']
    with (HERE/'terminal-function-map.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=fieldnames,extrasaction='ignore')
        writer.writeheader();writer.writerows(rows)
    after={str(p.relative_to(FROZEN)).replace('\\','/'):digest(p) for p in sources}
    assert before==after
    ids=[r['source_id'] for r in rows]
    assert len(ids)==451 and len(set(ids))==451
    assert data['counts']['motherboard_logical_terminal_positions']==371
    assert data['counts']['optional_encoder_reference_positions']==80
    assert data['counts']['motherboard_logical_field_connectors']==37
    base_signals={r['resource']['signal'] for r in rows if r['scope']=='motherboard_standard' and r['resource'].get('kind')=='fpga_pin'}
    optional_signals={r['resource']['signal'] for r in rows if r['scope']=='optional_qualified_accessory_reference' and r['resource'].get('kind')=='fpga_pin'}
    assert len(base_signals)==77 and len(optional_signals)==24
    assigned=collections.Counter(r['source_id'] for fun in functions for r in rows if r['source_id'] in fun['terminal_source_ids'])
    assert set(assigned)==set(ids) and all(n==1 for n in assigned.values())
    receipt={'status':'document_and_data_consistency_pass','evidence_class':'source inspection and structural arithmetic only',
             'sources_unchanged':True,'archived_input_count':len(before), 'frozen_hashes_sha256':before,
             'requirements_sha256':digest(OUT),'terminal_function_map_sha256':digest(HERE/'terminal-function-map.csv'),
             'all_terminal_rows_mapped_exactly_once':True,'counts':data['counts'],
             'base_direct_field_signals':sorted(base_signals),'optional_encoder_direct_field_signals':sorted(optional_signals),
             'implementation_conflicts_named':len(changes),'manufacturing_ready':False}
    (HERE/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:receipt[k] for k in ['status','sources_unchanged','archived_input_count','all_terminal_rows_mapped_exactly_once','counts','implementation_conflicts_named']},indent=2))


if __name__=='__main__':
    main()
