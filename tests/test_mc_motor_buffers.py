"""Independent physical-path fault injection; no hardware measurements."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('mc_motor_buffer_validation',ROOT/'tools/hardware_validate_mc_motor_buffers.py')
HW=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(HW)
OUT=ROOT/'hardware/mc_motor_buffers'


class McMotorBufferTests(unittest.TestCase):
    def setUp(self):
        self.d=json.loads((OUT/'design.json').read_text(encoding='utf-8'))

    def reject(self,fragment):
        r=HW.validate(self.d,native=False)
        self.assertFalse(r['passed'],r)
        self.assertTrue(any(fragment in e for e in r['errors']),r)

    def resistor(self,net,ohms):
        return next(c for c in self.d['components'].values() if c.get('kind')=='R'
                    and c['resistance_ohm']==ohms and net in c['pins'].values())

    def native_mutation(self,mutate,fragment,erc=None):
        tree=ET.parse(OUT/'netlist.xml');mutate(tree)
        with tempfile.TemporaryDirectory() as td:
            directory=Path(td);tree.write(directory/'netlist.xml',encoding='utf-8')
            (directory/'erc.json').write_text(json.dumps(erc if erc is not None else
                json.loads((OUT/'erc.json').read_text())),encoding='utf-8')
            r=HW.validate(self.d,directory)
        self.assertFalse(r['passed'],r)
        self.assertTrue(any(fragment in e for e in r['errors']),r)

    def test_reviewed_native_candidate_and_no_completion_claim(self):
        r=HW.validate(self.d)
        self.assertTrue(r['passed'],r)
        self.assertEqual((r['motor_paths'],r['TX_paths'],r['bank_A_paths'],r['bank_B_paths']),(36,2,25,13))
        self.assertEqual(r['host_ideal_digital_checks'],342)
        self.assertFalse(r['complete_MC_isolation']);self.assertFalse(r['physical_measurement'])
        self.assertFalse(r['manufacturing_ready'])

    def test_primary_physical_pin_functions_and_oe_polarities(self):
        p=HW.primary_pins()
        self.assertEqual(len(p['LVC244A']),20);self.assertEqual(len(p['LVC2G126']),8)
        self.assertEqual({pin:p['LVC244A'][pin] for pin in ('1','2','18','19','20')},
                         {'1':'1OE_N','2':'1A1','18':'1Y1','19':'2OE_N','20':'VCC'})
        self.assertEqual(p['LVC2G126'],{'1':'1OE','2':'1A','3':'2Y','4':'GND',
                         '5':'2A','6':'1Y','7':'2OE','8':'VCC'})

    def test_primary_missing_table_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            directory=Path(td)
            for name in ('sn74lvc244a','sn74lvc2g126'):
                text=(ROOT/'research/mc-motor-buffers'/f'{name}-pin-source.txt').read_text(encoding='utf-8')
                if name=='sn74lvc244a':text=text.replace('Table 4-1. Pin Functions','missing table')
                (directory/f'{name}-pin-source.txt').write_text(text,encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'pin table absent'):HW.primary_pins(directory)

    def test_both_physical_bank_b_oe_pins_must_use_actual_qualified_copper(self):
        for pin in ('1','7'):
            with self.subTest(pin=pin):
                d=copy.deepcopy(self.d);d['components']['U5']['pins'][pin]='IO_3V3'
                r=HW.validate(d,native=False);self.assertFalse(r['passed'])
                self.assertTrue(any('physicalOE' in e for e in r['errors']),r)

    def test_bank_a_oe_may_not_be_conditionally_gated(self):
        self.d['components']['U1']['pins']['19']='BANK_B_BUFFER_ENABLE_QUALIFIED'
        self.reject('BankA OE')

    def test_244_supply_cannot_receive_5v(self):
        self.d['components']['U1']['pins']['20']='MOTION_5V';self.reject('Physical supply')

    def test_126_supply_ground_swap_rejected(self):
        p=self.d['components']['U5']['pins'];p['4'],p['8']=p['8'],p['4'];self.reject('Physical supply')

    def test_non_ioff_quad_126a_substitution_rejected(self):
        self.d['components']['U5']['mpn']='SN74LVC126APWR';self.reject('Exact MPN')

    def test_buffer_footprint_substitution_rejected(self):
        self.d['components']['U1']['footprint']='Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm'
        self.reject('Exact MPN')

    def test_channel_input_swap_rejected_without_using_path_metadata(self):
        p=self.d['components']['U1']['pins'];p['2'],p['4']=p['4'],p['2']
        self.reject('physical buffer+series path')

    def test_shared_raw_output_driver_rejected(self):
        self.d['components']['U1']['pins']['16']='STEP0_BUFFER_OUT'
        self.reject('physical buffer+series path')

    def test_series_shortcut_rejected(self):
        self.d['components']['U1']['pins']['18']='STEP0_TO_MIA';self.reject('physical buffer+series path')

    def test_expansion_series_output_cannot_land_on_standard_peer(self):
        self.resistor('STEP8_TO_MX4',33)['pins']['2']='STEP8_TO_MIA';self.reject('physical buffer+series path')

    def test_startup_step_pull_cannot_be_up(self):
        self.resistor('STEP0_FPGA',4700)['pins']['2']='IO_3V3';self.reject('startup pull')

    def test_startup_enable_pull_cannot_be_down(self):
        self.resistor('EN0_N_FPGA',4700)['pins']['2']='LOGIC_GND';self.reject('startup pull')

    def test_boe_pull_must_default_low(self):
        self.resistor('BANK_B_BUFFER_ENABLE_QUALIFIED',4700)['pins']['2']='IO_3V3'
        self.reject('BOE startup pull')

    def test_outgoing_enable_pull_to_mc_dead_rail_rejected(self):
        # Repurpose one fitted output PD to expose a dangerous partial-power fault.
        self.resistor('STEP0_TO_MIA',10000)['pins']={'1':'EN0_N_TO_MIA','2':'IO_3V3'}
        self.reject('Outgoing EN bias')

    def test_missing_decoupling_rejected(self):
        del self.d['components']['C1'];self.reject('decoupling count')

    def test_physical_component_cannot_be_dnp(self):
        self.d['components']['U5']['physical']=False;self.reject('fitted/boundary state')

    def test_unused_positive_oe_must_be_disabled(self):
        self.d['components']['U11']['pins']['7']='BANK_B_BUFFER_ENABLE_QUALIFIED'
        self.reject('Unused positiveOE')

    def test_unused_input_must_not_float(self):
        self.d['components']['U4']['pins']['4']=None;self.reject('Unused input')

    def test_shared_oe_observation_contract_cannot_be_different_net(self):
        self.d['boe_contract']['physical_net']='SOFTWARE_BOE_REQUEST';self.reject('observation contract')

    def test_source_identity_and_manufacturing_claim_are_gated(self):
        self.d['sources']['research/mc-motor-buffers/sn74lvc244a.pdf']='0'*64
        self.d['manufacturing_ready']=True;self.reject('source hash')
        self.assertTrue(any('Manufacturing-ready' in e for e in HW.validate(self.d,native=False)['errors']))

    def test_physical_model_uses_distinct_inputs_and_actual_gating(self):
        inputs={p[0]:0 for p in HW.requirements()}
        inputs.update({'STEP0_FPGA':1,'EN0_N_FPGA':1,'DIR8_FPGA':1,'EN8_N_FPGA':1,'TX_PERMIT':1})
        high=HW.physical_ideal_outputs(self.d,inputs,True,1)
        self.assertEqual([high[x] for x in ('STEP0_TO_MIA','DIR0_TO_MIA','EN0_N_TO_MIA',
                         'STEP8_TO_MX4','DIR8_TO_MX4','EN8_N_TO_MX4')],[1,0,1,0,1,1])
        disabled=HW.physical_ideal_outputs(self.d,inputs,True,0)
        self.assertEqual(disabled['STEP0_TO_MIA'],1);self.assertEqual(disabled['TX_PERMIT_A_TO_MIA'],1)
        self.assertIsNone(disabled['DIR8_TO_MX4']);self.assertIsNone(disabled['TX_PERMIT_B_TO_MX4'])
        self.assertTrue(all(x is None for x in HW.physical_ideal_outputs(self.d,inputs,False,1).values()))
        # A tied-low positiveOE really disables this physical channel in the model.
        self.d['components']['U5']['pins']['1']='LOGIC_GND'
        self.assertIsNone(HW.physical_ideal_outputs(self.d,inputs,True,1)['STEP8_TO_MX4'])

    def test_physical_model_does_not_trust_declared_path_metadata(self):
        self.d['paths']=[]
        inputs=HW.physical_startup_inputs(self.d)
        actual=HW.physical_ideal_outputs(self.d,inputs,True,1)
        self.assertEqual(len(actual),38)
        self.assertTrue(all(value==(1 if name.startswith('EN') else 0) for name,value in actual.items()))

    def test_receiver_high_default_is_conditional_and_not_fitted_on_mc(self):
        self.assertEqual(self.d['receiver_contract']['EN_N']['to'],'receiver_own_powered_3V3')
        self.assertFalse(self.d['receiver_contract']['receiving_circuits_drawn_here'])
        self.d['receiver_contract']['EN_N']['to']='IO_3V3';self.reject('receiver EN contract')

    def test_static_inactive_screen_is_not_loaded_or_transient_qualification(self):
        s=HW.static_bias_screen(self.d['components'])
        self.assertTrue(s['passed_static_inactive_threshold_screen'])
        self.assertLess(s['FPGA_tristate_STEP_DIR_worst_high_v'],.8)
        self.assertGreater(s['FPGA_tristate_EN_N_worst_low_v'],2)
        self.assertLess(s['qualified_BOE_floating_worst_high_v'],.8)
        self.assertGreater(s['MC_off_receiver_EN_N_A_worst_low_v'],2)
        self.assertGreater(s['MC_off_receiver_EN_N_B_worst_low_v'],2)
        self.assertLess(s['FPGA_single_pin_pull_plus_weak_pull_plus_buffer_leak_max_mA'],1)
        self.assertFalse(s['loaded_GPIO_drive_strength_over_temperature_qualified'])
        self.assertFalse(s['transient_power_sequence_qualified'])

    def test_native_mpns_detected_independent_of_zero_erc(self):
        self.native_mutation(lambda t:setattr(t.find("components/comp[@ref='U5']/fields/field[@name='MPN']"),'text','SN74LVC126A'),
                             'Native exact part')

    def test_native_function_label_swap_rejected(self):
        self.native_mutation(lambda t:t.find("libparts/libpart[@part='LVC2G126']/pins/pin[@num='1']").set('name','VCC'),
                             'manufacturer')

    def test_native_electrical_pin_type_rejected(self):
        self.native_mutation(lambda t:t.find("libparts/libpart[@part='LVC244A']/pins/pin[@num='18']").set('type','passive'),
                             'electrical types')

    def test_native_conductor_swap_rejected(self):
        self.native_mutation(lambda t:t.find("nets/net/node[@ref='U5'][@pin='1']").set('pin','8'),
                             'physical netlist')

    def test_native_dnp_rejected(self):
        def mutate(tree):ET.SubElement(tree.find("components/comp[@ref='U5']"),'property',{'name':'dnp','value':''})
        self.native_mutation(mutate,'fitted/boundary flags')

    def test_erc_electrical_suppression_rejected(self):
        erc=json.loads((OUT/'erc.json').read_text());erc['ignored_checks'].append({'key':'pin_to_pin'})
        self.native_mutation(lambda t:None,'ERC suppression',erc)

    def test_erc_warning_visibility_required(self):
        erc=json.loads((OUT/'erc.json').read_text());erc['included_severities']=['error']
        self.native_mutation(lambda t:None,'severities',erc)


if __name__=='__main__':unittest.main()
