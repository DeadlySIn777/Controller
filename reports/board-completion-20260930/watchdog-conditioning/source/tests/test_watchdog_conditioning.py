"""Independent pin/net/part mutation checks for the standalone timer frontends."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'hardware/is1_watchdogs/startup_conditioning_r0_2'
SPEC = importlib.util.spec_from_file_location('is1_watchdogs_validator', ROOT / 'tools/hardware_validate_watchdog_conditioning.py')
HW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HW)


class WatchdogConditioningTests(unittest.TestCase):
    def setUp(self):
        self.tree = ET.parse(OUT / 'netlist.xml')
        self.model = json.loads((OUT / 'design.json').read_text(encoding='utf-8'))
        self.fp = (OUT / 'CNC_IS1.pretty/TPS3851_DRB8.kicad_mod').read_text(encoding='utf-8')
        self.erc = json.loads((OUT / 'erc.json').read_text(encoding='utf-8'))

    def result(self):
        return HW.validate(self.tree, self.model, self.fp, self.erc)

    def reject(self, fragment):
        result = self.result()
        self.assertFalse(result['ok'], result)
        self.assertTrue(any(fragment in e for e in result['errors']), result)

    def node(self, ref, pin):
        nodes = self.tree.findall(f"nets/net/node[@ref='{ref}'][@pin='{pin}']")
        self.assertEqual(len(nodes), 1)
        return nodes[0]

    def net(self, name):
        return next((n for n in self.tree.findall('nets/net') if n.attrib['name'].removeprefix('/') == name), None)

    def move(self, ref, pin, target):
        node = self.node(ref, pin)
        source = next(n for n in self.tree.findall('nets/net') if node in list(n))
        destination = self.net(target)
        self.assertIsNotNone(destination)
        source.remove(node); destination.append(node)

    def component(self, ref):
        return self.tree.find(f"components/comp[@ref='{ref}']")

    def test_real_native_candidate_and_erc(self):
        result = self.result()
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['physical_components'], 29)
        self.assertFalse(result['manufacturing_ready'])
        self.assertFalse(result['complete_permission_chain'])

    def test_primary_physical_pin_fixtures_are_independent(self):
        # Reviewed TI Rev B p3, SCES519O p3 DBV5 and SCES381N p3 DBV6;
        # explicit fixtures are not imported from either builder or validator constants.
        functions = HW.primary_pin_functions()
        self.assertEqual(functions['TPS3851'], {'1': 'VDD', '2': 'CWD', '3': 'MR', '4': 'GND', '5': 'SET1',
                                               '6': 'WDI', '7': 'WDO', '8': 'RESET', '9': 'EP'})
        self.assertEqual(functions['LVC1G34'], {'1': 'NC', '2': 'A', '3': 'GND', '4': 'Y', '5': 'VCC'})
        self.assertEqual(functions['LVC2G17'], {'1': '1A', '2': 'GND', '3': '2A', '4': '2Y', '5': 'VCC', '6': '1Y'})
        self.assertEqual(functions['LVC1G08'], {'1': 'A', '2': 'B', '3': 'GND', '4': 'Y', '5': 'VCC'})

    def test_primary_extraction_refuses_incomplete_table(self):
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            for name in ('tps3851-revb.txt', 'sn74lvc1g34.txt', 'sn74lvc2g17.txt'):
                text = (HW.SOURCES / name).read_text(encoding='utf-8')
                if name == 'tps3851-revb.txt':
                    text = text.replace('MR 3 I', 'MR X I')
                (directory / name).write_text(text, encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'ambiguous or incomplete'):
                HW.primary_pin_functions(directory)

    def test_mirrored_old_tps3431_symbol_model_and_net_cannot_pass(self):
        # Reproduce the dangerous shared-map error: old EN3/ENOUT8 represented
        # consistently in symbol, model and net, but contradicted by primary TPS3851.
        self.tree.find("libparts/libpart[@part='TPS3851']/pins/pin[@num='3']").set('name', 'EN')
        self.tree.find("libparts/libpart[@part='TPS3851']/pins/pin[@num='8']").set('name', 'ENOUT')
        self.move('U1', '3', 'IO_3V3')
        self.node('U1', '3').set('pintype', 'input')
        self.model['components']['U1']['pins']['3'] = 'IO_3V3'
        self.model['components']['U1']['no_connect'] = []
        self.reject('Manufacturer physical pin functions differ: TPS3851')

    def test_swapped_buffer_input_ground_symbol_and_model_rejected(self):
        self.tree.find("libparts/libpart[@part='LVC1G34']/pins/pin[@num='2']").set('name', 'GND')
        self.tree.find("libparts/libpart[@part='LVC1G34']/pins/pin[@num='3']").set('name', 'A')
        self.move('U3', '2', 'LOGIC_GND'); self.move('U3', '3', 'FPGA_PROGRESS_M')
        self.model['components']['U3']['pins']['2'] = 'LOGIC_GND'
        self.model['components']['U3']['pins']['3'] = 'FPGA_PROGRESS_M'
        self.reject('Manufacturer physical pin functions differ: LVC1G34')

    def test_mr_has_explicit_no_connect_not_fpga_or_user_signal(self):
        for ref in ('U1', 'U2'):
            self.assertEqual(self.node(ref, '3').attrib['pintype'], 'input+no_connect')
            self.assertEqual(self.model['components'][ref]['no_connect'], ['3'])
        self.assertFalse(any('LOCAL_RESET' in n.attrib['name'] for n in self.tree.findall('nets/net')))

    def test_removed_mr_no_connect_marker_rejected(self):
        self.node('U1', '3').set('pintype', 'input')
        self.reject('missing no-connect marker')

    def test_mr_connected_to_motion_request_rejected(self):
        self.move('U1', '3', 'FPGA_MOTION_REQUEST')
        self.reject('Required MR/NC no-connect pins differ')

    def test_thermal_pad_must_be_ground(self):
        self.move('U1', '9', 'IO_3V3')
        self.reject('Native net mismatch')

    def test_cwd_nodes_cannot_be_shared(self):
        self.move('U2', '2', 'WD_M_CWD')
        self.reject('Native net mismatch: WD_M_CWD')

    def test_output_timer_cannot_use_motion_request(self):
        self.move('U2', '5', 'FPGA_MOTION_REQUEST')
        self.reject('Native net mismatch: FPGA_MOTION_REQUEST')

    def test_set1_cannot_be_permanently_high(self):
        self.move('U1', '5', 'IO_3V3')
        self.reject('Native net mismatch: IO_3V3')

    def test_progress_channels_cannot_be_crossed(self):
        self.move('U4', '2', 'FPGA_PROGRESS_M')
        self.reject('Native net mismatch: FPGA_PROGRESS_M')

    def test_wdi_cannot_bypass_rail_buffer(self):
        self.move('U1', '6', 'FPGA_PROGRESS_M')
        self.reject('Native net mismatch: FPGA_PROGRESS_M')

    def test_reset_must_qualify_health_not_only_wdo(self):
        self.move('U1', '8', 'WD_O_HEALTH_RAW')
        self.reject('Native net mismatch: WD_M_HEALTH_RAW')

    def test_separate_health_buffer_channels_cannot_be_crossed(self):
        self.move('U5', '3', 'WD_M_HEALTH_RAW')
        self.reject('Native net mismatch: WD_M_HEALTH_RAW')

    def test_raw_health_pullup_must_use_logic_rail(self):
        self.move('R1', '1', 'LOGIC_GND')
        self.reject('Native net mismatch: IO_3V3')

    def test_stronger_fpga_pulls_preserve_output_pulls(self):
        for ref in ('R3', 'R4', 'R5', 'R7', 'R13'):
            self.assertEqual(self.component(ref).findtext('value'), '4.7k 1%')
        for ref in ('R6', 'R8', 'R9', 'R10', 'R11', 'R12'):
            self.assertEqual(self.component(ref).findtext('value'), '100k 1%')
        self.assertFalse(self.model['startup_defaults_qualified'])

    def test_health_output_pull_cannot_be_pullup(self):
        self.move('R9', '2', 'IO_3V3')
        self.reject('Native net mismatch: LOGIC_GND')

    def test_missing_decoupler_rejected(self):
        self.tree.find('components').remove(self.component('C7'))
        self.reject('Native component set differs')

    def test_exact_timing_cap_part_rejects_4p7nf(self):
        self.component('C2').find('value').text = '4.7nF C0G 50V 5%'
        self.component('C2').find("fields/field[@name='MPN']").text = 'CL10C472JB8NNNC'
        self.model['components']['C2']['value'] = '4.7nF C0G 50V 5%'
        self.model['components']['C2']['mpn'] = 'CL10C472JB8NNNC'
        self.reject('Exact native part/value/footprint differs: C2')

    def test_exact_timer_variant_rejects_extended_timing(self):
        self.component('U1').find("fields/field[@name='MPN']").text = 'TPS3851G18EDRBT'
        self.reject('Exact native part/value/footprint differs: U1')

    def test_component_cannot_be_marked_dnp(self):
        ET.SubElement(self.component('U1'), 'property', {'name': 'dnp'})
        self.reject('Required physical part excluded: U1')

    def test_boundary_cannot_become_fitted_connector(self):
        marker = self.component('B1').find("property[@name='exclude_from_board']")
        self.component('B1').remove(marker)
        self.reject('Internal boundary must not be fitted or in BOM')

    def test_duplicate_conductor_rejected(self):
        net = self.net('IO_3V3')
        net.append(copy.deepcopy(self.node('U1', '1')))
        self.reject('Duplicate physical pin')

    def test_native_output_pin_cannot_be_open_drain(self):
        self.tree.find("libparts/libpart[@part='LVC2G17']/pins/pin[@num='6']").set('type', 'open_collector')
        self.reject('Native physical pin types differ: LVC2G17')

    def test_drb_thermal_pad_number_cannot_change(self):
        self.fp = self.fp.replace('(pad "9"', '(pad "10"')
        self.reject('DRB0008A physical copper pad map differs')

    def test_native_erc_violation_prevents_pass(self):
        self.erc['sheets'][0]['violations'].append({'type': 'pin_to_pin', 'severity': 'error'})
        self.reject('Native ERC violations: 1')

    def test_scope_cannot_claim_release_or_startup_qualification(self):
        for key in ('manufacturing_ready', 'assembly_integrated', 'physical_qualification', 'complete_permission_chain', 'startup_defaults_qualified'):
            with self.subTest(key=key):
                original = self.model[key]
                self.model[key] = True
                self.reject('Unqualified scope flag: ' + key)
                self.model[key] = original

    def test_legacy_toggle_cannot_be_marked_compatible(self):
        self.model['watchdog_contract']['legacy_toggle_compatible'] = True
        self.reject('Unreviewed watchdog contract: legacy_toggle_compatible')

    def test_required_conditioning_cannot_be_removed(self):
        self.model['watchdog_contract']['FPGA_conditioning_review_required'] = False
        self.reject('Unreviewed watchdog contract: FPGA_conditioning_review_required')

    def test_set1_cannot_bypass_reset_guard_driver(self):
        self.move('U1', '5', 'FPGA_MOTION_REQUEST')
        self.reject('Native net mismatch: FPGA_MOTION_REQUEST')

    def test_guard_input_cannot_be_tied_high(self):
        self.move('U7', '2', 'IO_3V3')
        self.reject('Native net mismatch: FPGA_USER_RESET_N')

    def test_gate_and_primary_pin_error_cannot_be_mirrored(self):
        self.tree.find("libparts/libpart[@part='LVC1G08']/pins/pin[@num='1']").set('name', 'Y')
        self.tree.find("libparts/libpart[@part='LVC1G08']/pins/pin[@num='4']").set('name', 'A')
        self.reject('Manufacturer physical pin functions differ: LVC1G08')

    def test_weak_pulls_cannot_be_reintroduced_in_native_and_model(self):
        self.component('R3').find('value').text = '100k 1%'
        self.component('R3').find("fields/field[@name='MPN']").text = 'CRCW0603100KFKEA'
        self.model['components']['R3']['value'] = '100k 1%'
        self.model['components']['R3']['mpn'] = 'CRCW0603100KFKEA'
        self.model['components']['R3']['resistance_ohm'] = 100000
        self.reject('Exact native part/value/footprint differs: R3')

    def test_reset_guard_cannot_reintroduce_weak_default_pull(self):
        self.component('R13').find('value').text = '100k 1%'
        self.reject('Exact native part/value/footprint differs: R13')

    def test_missing_guard_decoupler_rejected(self):
        self.tree.find('components').remove(self.component('C9'))
        self.reject('Native component set differs')

    def test_proposal_cannot_claim_frozen_spec_agreement(self):
        for key, value in (('interface_agreed', True), ('supersedes_is1', True),
                           ('interface_revision', 'IS-1'), ('status', 'qualified')):
            with self.subTest(key=key):
                original = self.model[key]
                self.model[key] = value
                self.reject('Proposed interface scope differs: '+key)
                self.model[key] = original

    def test_timer_leakage_cannot_be_claimed_as_datasheet_bound(self):
        self.model['watchdog_contract']['SET1_pin_leakage_datasheet_bound_available'] = True
        self.reject('Unreviewed watchdog contract: SET1_pin_leakage_datasheet_bound_available')


if __name__ == '__main__':
    unittest.main()
