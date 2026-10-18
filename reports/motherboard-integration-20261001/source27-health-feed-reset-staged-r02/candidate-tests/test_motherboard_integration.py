"""Native contract mutation checks for the additive motherboard integration."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(os.environ.get('CONTROLLER_PROJECT_ROOT',Path(__file__).resolve().parents[1]))
spec=importlib.util.spec_from_file_location('motherboard_validation',Path(os.environ.get('CONTROLLER_MOTHERBOARD_VALIDATOR',ROOT/'tools/hardware_validate_motherboard.py')))
validation=importlib.util.module_from_spec(spec);spec.loader.exec_module(validation)
# Report-local copied validators retain actual source/FPGA paths explicitly.
validation.ROOT=ROOT
validation.OUT=Path(os.environ.get('CONTROLLER_MOTHERBOARD_TEST_SOURCE',ROOT/'hardware/motherboard'))


class MotherboardIntegrationTests(unittest.TestCase):
    def setUp(self):
        folder=Path(os.environ.get('CONTROLLER_MOTHERBOARD_TEST_SOURCE',ROOT/'hardware/motherboard'))
        self.tree=ET.parse(folder/'netlist.xml')
        self.model=json.loads((folder/'design.json').read_text(encoding='utf-8'))
        self.mapping=json.loads((folder/'assembly-map.json').read_text(encoding='utf-8'))
    def run_check(self):return validation.validate(self.tree,self.model,self.mapping,check_hashes=False)
    def change_net(self,ref,pin,new_name):
        nets=self.tree.getroot().find('nets')
        for net in nets:
            for node in list(net):
                if node.attrib.get('ref')==ref and node.attrib.get('pin')==pin:
                    net.remove(node);new=ET.SubElement(nets,'net',{'code':'900000','name':new_name});new.append(node);return
        self.fail('Mutation source pin absent')
    def test_native_fitted_inventory_and_all_retained_pins(self):
        self.assertEqual([],self.run_check())
        self.assertEqual(1229,len(self.mapping['retained_native_pin_nets']))
        self.assertGreaterEqual(len(self.model['components']),537)
    def test_probe_threshold_cannot_feed_IN_before_SENSE(self):
        for threshold,incorrect in (('R14069','PRB0_IN_SENSE'),('R14072','PRB1_IN_SENSE')):
            with self.subTest(threshold=threshold):
                old=copy.deepcopy(self.tree)
                self.change_net(threshold,'2','/motherboard_operator/'+incorrect)
                self.assertTrue(any('RTHR must feed SENSE' in e for e in self.run_check()))
                self.tree=old
    def test_probe_sense_resistor_cannot_be_bypassed(self):
        self.change_net('R14070','1','/motherboard_operator/PRB0_SENSE')
        self.assertTrue(any('RTHR must feed SENSE' in e for e in self.run_check()))
    def test_field_pg_must_use_its_own_actual_return(self):
        if 'motherboard_diagnostics' not in self.mapping['blocks']:self.skipTest('Diagnostics not integrated')
        self.change_net('U22003','1','/motherboard_motors/FIELD_GND')
        self.assertTrue(any('separate field domain' in e for e in self.run_check()))
    def test_reset_bypass_cannot_use_predamping_regulator_net(self):
        if 'C18001' not in self.model['components']:self.skipTest('Dedicated reset bypass not integrated')
        self.change_net('C18001','1','/mc_local_power/IO_3V3_REG_LOCAL')
        self.assertTrue(any('Reset-buffer bypass must follow actual receiving' in e for e in self.run_check()))
    def test_reset_bypass_cannot_cross_field_return(self):
        if 'C18001' not in self.model['components']:self.skipTest('Dedicated reset bypass not integrated')
        self.change_net('C18001','2','/motherboard_do/FIELD_B_0V')
        self.assertTrue(any('Reset-buffer bypass must follow actual receiving' in e for e in self.run_check()))
    def test_field_pg_cannot_claim_an_orphan_mcu_pin(self):
        if 'motherboard_diagnostics' not in self.mapping['blocks']:self.skipTest('Diagnostics not integrated')
        self.change_net('U22002','13','/FAKE_ENTRY_PGOOD')
        self.mapping['blocks']['motherboard_diagnostics']['ports']['DOA_FIELD_POWER_GOOD']='FAKE_ENTRY_PGOOD'
        self.assertTrue(any('join actual hardware provider' in e for e in self.run_check()))
    def test_unused_status_ledger_cannot_remove_a_real_probe(self):
        if 'motherboard_diagnostics' not in self.mapping['blocks']:self.skipTest('Diagnostics not integrated')
        self.mapping['native_unused_functional_dispositions_allowed'][0]['pin']='G12'
        self.assertTrue(any('Unreviewed unused functional endpoint' in e for e in self.run_check()))
    def test_unused_compute_contact_must_be_explicit_native_nc(self):
        if 'motherboard_diagnostics' not in self.mapping['blocks']:self.skipTest('Diagnostics not integrated')
        self.change_net('J15002','2','/UNIMPLEMENTED_PCIE')
        self.assertTrue(any('New source pin/net mismatch J15002.2' in e for e in self.run_check()))
    def test_fault_testpad_must_be_actual_fpga_output(self):
        if 'motherboard_diagnostics' not in self.mapping['blocks']:self.skipTest('Diagnostics not integrated')
        self.change_net('TP22004','1','/UNIMPLEMENTED_TIMING_FAULT')
        self.assertTrue(any('join actual hardware provider' in e for e in self.run_check()))
    def test_iol1_clock_count_requires_actual_post_buffer_clock(self):
        self.change_net('R13057','1','/fpga_core/IOL1_L0_SCLK')
        self.assertTrue(any('clock counter must tap post-buffer' in e for e in self.run_check()))
    def test_acc_clock_count_requires_actual_tim3_pin(self):
        self.change_net('U14501','44','/FAKE_SOFTWARE_CLOCK_COUNT')
        self.assertTrue(any('clock counter must tap post-buffer' in e for e in self.run_check()))
    def test_status_trip_display_cannot_follow_normal_disarm(self):
        if 'motherboard_status' not in self.mapping['blocks']:self.skipTest('Status not integrated')
        self.change_net('U17013','1','/TX_PERMIT')
        self.mapping['blocks']['motherboard_status']['ports']['WD_M_TRIP_N']='TX_PERMIT'
        self.assertTrue(any('status observation must join hardware provider' in e for e in self.run_check()))
    def test_fpga_rail_readback_cannot_be_a_health_constant(self):
        if not self.mapping.get('native_reserved_health_reconciliation_allowed'):self.skipTest('Rail reconciliation not integrated')
        self.change_net('U1001','P4','/FALSE_ALWAYS_HEALTHY')
        self.mapping['native_reserved_health_reconciliation_allowed'][-1]['new_native_net']='/FALSE_ALWAYS_HEALTHY'
        self.assertTrue(any('Unreviewed reserved-health' in e or 'actual U2006.4' in e for e in self.run_check()))
    def test_reserved_expansion_ball_is_an_explicit_nc(self):
        if not self.mapping.get('native_reserved_health_reconciliation_allowed'):self.skipTest('Reservation reconciliation not integrated')
        self.change_net('U1001','K16','/UNIMPLEMENTED_XS_CARD_BUS')
        self.assertTrue(any('Retained MC fitted pin/net changed U1001.K16' in e for e in self.run_check()))
    def test_reserved_health_ledger_cannot_omit_the_last_ball(self):
        if not self.mapping.get('native_reserved_health_reconciliation_allowed'):self.skipTest('Reservation reconciliation not integrated')
        self.mapping['native_reserved_health_reconciliation_allowed'].pop()
        self.assertTrue(any('Exact nine reserved NC' in e for e in self.run_check()))
    def test_status_output_observation_requires_actual_terminal(self):
        if 'motherboard_status' not in self.mapping['blocks']:self.skipTest('Status not integrated')
        self.change_net('R17073','1','/motherboard_do/DO00_SW')
        self.assertTrue(any('Output LED must observe actual terminal voltage' in e for e in self.run_check()))
    def test_status_last_alarm_requires_actual_fpga_receive(self):
        if 'motherboard_status' not in self.mapping['blocks']:self.skipTest('Status not integrated')
        self.change_net('U17011','13','/FALSE_CACHED_ALARM12')
        self.assertTrue(any('status observation must join hardware provider' in e for e in self.run_check()))
    def test_identity_mux_cannot_hide_missing_acc_gpio(self):
        if 'motherboard_identity_io' not in self.mapping['blocks']:self.skipTest('Identity not integrated')
        self.change_net('U21001','6','/UNIMPLEMENTED_ID_GPIO')
        self.mapping['blocks']['motherboard_identity_io']['ports']['FREQ_1WIRE_DATA_HOST']='UNIMPLEMENTED_ID_GPIO'
        self.assertTrue(any('identity path must join existing frequency/ACC provider' in e for e in self.run_check()))
    def test_identity_requires_the_real_shared_xf_terminal(self):
        if 'motherboard_identity_io' not in self.mapping['blocks']:self.skipTest('Identity not integrated')
        self.change_net('R21003','1','/ORPHAN_ID_TERMINAL')
        self.assertTrue(any('identity path must join existing frequency/ACC provider' in e for e in self.run_check()))
    def test_ai_alias_cannot_hide_missing_actual_acquisition(self):
        if 'motherboard_analog_input' not in self.mapping['blocks']:self.skipTest('AI not integrated')
        self.change_net('U14707','2','/ISOLATED_AI_CLOCK')
        self.mapping['blocks']['motherboard_analog_input']['ports']['AI_SCLK_HOST']='ISOLATED_AI_CLOCK'
        self.assertTrue(any('must reach ACC provider' in e for e in self.run_check()))
    def test_safety_permission_requires_real_hardware_endpoint(self):
        if 'motherboard_safety_sensor' not in self.mapping['blocks']:self.skipTest('Safety not integrated')
        self.change_net('U19010','4','/FALSE_ALWAYS_HEALTHY')
        self.mapping['blocks']['motherboard_safety_sensor']['ports']['EXT_PERMIT_3V3']='FALSE_ALWAYS_HEALTHY'
        self.assertTrue(any('must physically join provider' in e for e in self.run_check()))
    def test_safety_preregulator_cannot_be_bypassed_by_source_override(self):
        if 'motherboard_safety_sensor' not in self.mapping['blocks']:self.skipTest('Safety not integrated')
        self.change_net('U11018','5','/motherboard_power_entry/FIELD_B_24V_PROTECTED')
        row=self.mapping['blocks']['motherboard_power_entry']['exact_source_pin_overrides'][0]
        row['new_native_net']='/motherboard_power_entry/FIELD_B_24V_PROTECTED'
        self.assertTrue(any('Unreviewed safety endpoint' in e or 'must physically join provider' in e for e in self.run_check()))
    def test_safety_adc_alias_cannot_hide_missing_actual_dic_gpio(self):
        if 'motherboard_safety_sensor' not in self.mapping['blocks']:self.skipTest('Safety not integrated')
        self.change_net('U19025','3','/ISOLATED_SENSOR_SCL')
        self.mapping['blocks']['motherboard_safety_sensor']['ports']['DIC_SENSOR_SCL']='ISOLATED_SENSOR_SCL'
        self.assertTrue(any('must physically join provider' in e for e in self.run_check()))
    def test_obsolete_home_deallocation_is_exactly_twelve_old_pins(self):
        ledger=self.mapping.get('native_home_nc_deallocations_allowed',[])
        if not ledger:self.skipTest('HOME delta not integrated')
        self.assertEqual(12,len(ledger))
        ledger[0]['pin']='G12'
        self.assertTrue(any('Unreviewed obsolete HOME' in e for e in self.run_check()))
    def test_home_cannot_be_reconnected_as_unrouted_required_signal(self):
        ledger=self.mapping.get('native_home_nc_deallocations_allowed',[])
        if not ledger:self.skipTest('HOME delta not integrated')
        self.change_net('U1001',ledger[0]['pin'],ledger[0]['old_native_net'])
        self.assertTrue(any('Retained MC' in e for e in self.run_check()))
    def test_terminal_enable_no_and_nc_cannot_be_swapped(self):
        if 'motherboard_terminals' not in self.mapping['blocks']:self.skipTest('Terminals not integrated')
        self.change_net('J19501','8','/motherboard_motors/EN0_NC')
        self.model['components']['J19501']['pins']['8']='EN0_NC'
        self.assertTrue(any('New source pin/net mismatch' in e for e in self.run_check()))
    def test_only_frozen_operator_source_replacement_is_allowed(self):
        if 'source_folder' not in self.mapping['blocks']['motherboard_operator']:self.skipTest('Derived operator not integrated')
        self.mapping['blocks']['motherboard_operator']['source_folder']='hardware/motherboard_process'
        self.assertTrue(any('Unreviewed source replacement' in e for e in self.run_check()))
    def test_communications_good_cannot_be_replaced_by_constant_healthy(self):
        if 'motherboard_comms' not in self.mapping['blocks']:self.skipTest('Comms not integrated')
        self.change_net('U14801','3','/FAKE_MODULE_GOOD')
        self.mapping['blocks']['motherboard_comms']['ports']['COMPUTE_3V3_GOOD']='FAKE_MODULE_GOOD'
        self.assertTrue(any('must join module/acquisition provider' in e for e in self.run_check()))
    def test_can_clock_alias_cannot_hide_a_disconnected_controller(self):
        if 'motherboard_comms' not in self.mapping['blocks']:self.skipTest('Comms not integrated')
        self.change_net('U14805','2','/UNCONNECTED_CAN_CLOCK')
        self.mapping['blocks']['motherboard_comms']['ports']['CAN_SPI_SCLK_HOST']='UNCONNECTED_CAN_CLOCK'
        self.assertTrue(any('must join module/acquisition provider' in e for e in self.run_check()))
    def test_rs485_return_uses_actual_powered_off_safe_compute_receiver(self):
        if 'motherboard_comms' not in self.mapping['blocks']:self.skipTest('Comms not integrated')
        self.change_net('U15038','2','/ISOLATED_UART_RETURN')
        self.mapping['blocks']['motherboard_compute']['ports']['RS485_UART_RX_HOST']='ISOLATED_UART_RETURN'
        self.assertTrue(any('must join module/acquisition provider' in e for e in self.run_check()))
    def test_swapped_step_and_direction_is_rejected(self):
        self.change_net('R5001','2','/mc_motor_buffers/DIR0_TO_MIA')
        self.assertTrue(any('Retained MC' in e for e in self.run_check()))
    def test_a_removed_retained_fitted_pin_is_rejected(self):
        self.change_net('U2006','4','/WRONG_RESET_BUFFER_INPUT')
        self.assertTrue(any('Retained MC' in e for e in self.run_check()))
    def test_actual_motor_receiving_pin_change_is_rejected(self):
        ref=next(r for r,c in self.model['components'].items() if c.get('source_block')=='motherboard_motors' and c.get('role')=='receiving STEP/DIR idle low')
        self.change_net(ref,'1','/UNCONNECTED_TEST_FIXTURE')
        self.assertTrue(any('New source pin/net mismatch' in e for e in self.run_check()))
    def test_exact_manufacturer_pin_footprint_binding_is_required(self):
        self.model['components']['U2006']['footprint']='Package_TO_SOT_SMD:WRONG_PIN_ORDER'
        self.assertTrue(any('Footprint mismatch U2006' in e for e in self.run_check()))
    def test_wrong_mpn_cannot_be_hidden_by_old_circuit_value(self):
        self.model['components']['U2003']['mpn']='LTC2962CUD#PBF'
        self.assertTrue(any('MPN mismatch U2003' in e for e in self.run_check()))
    def test_unqualified_integration_cannot_claim_manufacture(self):
        self.model['manufacturing_ready']=True
        self.assertTrue(any('cannot assert manufacture' in e for e in self.run_check()))
    def test_wildcard_retained_net_renaming_is_not_allowed(self):
        self.mapping['native_net_renames_allowed']=['*']
        self.assertTrue(any('retained native nets' in e for e in self.run_check()))
    def test_exact64_former_fpga_nc_promotions_are_bounded(self):
        additions={r['pin']:r['signal'] for r in self.mapping['native_net_renames_allowed'] if r['pin'] in ('M4','M6')}
        self.assertEqual({'M4':'FAST_PORTS_ENABLE','M6':'XF_POWER_ENABLE'} if 'motherboard_operator' in self.mapping['blocks'] else {},additions)
        self.assertEqual(64,len([r for r in self.mapping['native_net_renames_allowed'] if r['pin'] not in ('M4','M6')]))
        self.assertEqual({'U1001'},{r['reference'] for r in self.mapping['native_net_renames_allowed']})
        self.assertTrue(all(r['old_native_net'].startswith('unconnected-(U1001-') for r in self.mapping['native_net_renames_allowed']))
    def test_non_nc_pin_cannot_be_renamed_by_ledger(self):
        self.mapping['native_net_renames_allowed'][0]['pin']='H3'
        self.assertTrue(any('Unreviewed' in e for e in self.run_check()))
    def test_former_nc_cannot_be_promoted_to_a_wrong_field(self):
        self.mapping['native_net_renames_allowed'][0]['new_native_net']='/WRONG_WATCHDOG_STROBE'
        self.assertTrue(any('Unreviewed' in e for e in self.run_check()))
    def test_receiving_power_health_cannot_be_fabricated(self):
        self.change_net('U9008','7','/CONSTANT_HEALTHY')
        self.assertTrue(any('New source pin/net mismatch' in e for e in self.run_check()))
    def test_new_step_stage_logic_rail_joins_actual_monitored_rail(self):
        self.change_net('U6007','14','/UNMONITORED_MOTOR_3V3')
        self.assertTrue(any('New source pin/net mismatch' in e for e in self.run_check()))
    def test_clear_fanout_cannot_drive_retained_push_pull_output(self):
        self.change_net('R12003','2','/mc_permission/WD_M_TRIP_CLEAR_N')
        self.assertTrue(any('never push-pull output' in e for e in self.run_check()))
    def test_clear_request_default_high_is_rejected(self):
        self.change_net('R12006','2','/IO_3V3')
        self.assertTrue(any('default LOW' in e for e in self.run_check()))
    def test_digital_input_alias_cannot_hide_isolated_acquisition_stub(self):
        self.change_net('U13001','1','/ISOLATED_DI_STUB')
        self.mapping['blocks']['motherboard_io_control']['ports']['DI0_LOGIC']='ISOLATED_DI_STUB'
        self.assertTrue(any('must reach DIC acquisition' in e for e in self.run_check()))
    def test_actual_output_latch_is_observed(self):
        self.change_net('U13004','9','/COMMANDED_STATE_NOT_OBSERVED')
        self.assertTrue(any('control/readback must reach actual frontend' in e for e in self.run_check()))
    def test_actual_reset_buffer_reaches_output_permission(self):
        self.change_net('U13011','4','/MISSING_OUTPUT_RESET')
        self.assertTrue(any('MCU reset must reach DO permission' in e for e in self.run_check()))
    def test_no_duplicate_frontend_owned_defaults(self):
        self.model['components']['R13025']=copy.deepcopy(self.model['components']['R13024'])
        self.assertTrue(any('Duplicate DO frontend-owned' in e for e in self.run_check()))
    def test_matching_names_on_separate_native_nets_are_rejected(self):
        nets=self.tree.getroot().find('nets')
        original=next(n for n in nets if any(p.attrib.get('ref')=='U14031' and p.attrib.get('pin')=='4' for p in n))
        node=next(p for p in original if p.attrib.get('ref')=='U14031' and p.attrib.get('pin')=='4');original.remove(node)
        isolated=ET.SubElement(nets,'net',{'code':'987654','name':original.attrib['name']});isolated.append(node)
        self.assertTrue(any('Distinct native electrical nets' in e for e in self.run_check()))
    def test_final_motor_contact_cannot_be_bypassed(self):
        if 'motherboard_power_entry' not in self.mapping['blocks']:self.skipTest('Power contacts not integrated')
        self.change_net('U6001','4','/motherboard_motors/MOTOR_TX_GATE_SOURCE_A')
        self.assertTrue(any('bypasses hardware contacts' in e for e in self.run_check()))
    def test_process_reset_alias_cannot_hide_missing_actual_controller(self):
        if 'motherboard_acc_control' not in self.mapping['blocks']:self.skipTest('ACC not integrated')
        self.change_net('U14504','4','/ISOLATED_PROCESS_RESET')
        self.mapping['blocks']['motherboard_acc_control']['ports']['ACC_CONTROLLER_RESET_N']='ISOLATED_PROCESS_RESET'
        self.assertTrue(any('must join process frontend' in e for e in self.run_check()))
    def test_process_observation_cannot_be_replaced_by_command(self):
        if 'motherboard_acc_control' not in self.mapping['blocks']:self.skipTest('ACC not integrated')
        self.change_net('U14501','13','/motherboard_process/ACC_CARD_EN')
        self.assertTrue(any('must join process frontend' in e for e in self.run_check()))

    def test_distributed_logic_plane_cannot_bypass_real_damping(self):
        self.change_net('R18001','1','/IO_3V3')
        self.assertTrue(any('cannot bypass damping' in e for e in self.run_check()))

    def test_regulator_sense_must_remain_upstream_of_damping(self):
        self.change_net('U2002','3','/IO_3V3')
        self.assertTrue(any('Retained MC fitted pin/net changed U2002.3' in e for e in self.run_check()))

    def test_mode_resistor_cannot_select_automatic_voltage_mode(self):
        self.change_net('R2005','2','/LOGIC_GND')
        self.assertTrue(any('Retained MC fitted pin/net changed R2005.2' in e for e in self.run_check()))

    def test_wrong_regulator_cannot_hide_behind_matching_native_properties(self):
        self.model['components']['U2002']['mpn']='TPS62901RPJR'
        comp=next(c for c in self.tree.findall('.//components/comp') if c.attrib['ref']=='U2002')
        comp.find("./fields/field[@name='MPN']").text='TPS62901RPJR'
        self.assertTrue(any('Exact reviewed IO3 power part required U2002' in e for e in self.run_check()))

    def test_overvoltage_series_resistor_is_an_electrical_endpoint(self):
        self.change_net('R9007','1','/IO_3V3')
        self.assertTrue(any('New source pin/net mismatch R9007.1' in e for e in self.run_check()))

    def test_custom_unquoted_precision_value_cannot_replace_stock_window_part(self):
        self.model['components']['R18004']['mpn']='CUSTOM-58K3'
        self.assertTrue(any('Actual IO3 helper part required R18004' in e for e in self.run_check()))

    def test_analog_cs_alias_cannot_hide_disconnected_dac_control(self):
        self.change_net('U14605','4','/ISOLATED_AO0_CS')
        self.mapping['blocks']['motherboard_analog_output']['ports']['AO0_CS_N_HOST']='ISOLATED_AO0_CS'
        self.assertTrue(any('Actual AO isolated control/readback' in e for e in self.run_check()))

    def test_analog_readback_cannot_be_connected_to_output_command(self):
        self.change_net('U14609','4','/motherboard_acc_control/AI_SDI_HOST')
        self.assertTrue(any('Actual AO isolated control/readback' in e for e in self.run_check()))


if __name__=='__main__':unittest.main()
