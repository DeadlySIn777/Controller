"""Independent purchasing exclusions and unknown-cost controls on a frozen BOM."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('motherboard_cost',ROOT/'tools/motherboard_cost_audit.py')
cost=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(cost)
OUT=ROOT/'reports/motherboard-cost-20260930/source-r26-2688-complete-cost-v11'

class MotherboardCostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obs=json.loads((OUT/'CATALOGUE_OBSERVATIONS.json').read_text(encoding='utf-8'))
        cls.result=cost.calculate(OUT,cls.obs)

    def test_copper_test_pads_are_not_purchased_or_placed(self):
        rows=[r for r in self.result['lines'] if r['mpn']=='PCB_COPPER_TEST_PAD_D1.0']
        self.assertEqual(3,len(rows))
        for row in rows:
            self.assertEqual('bare_PCB_geometry_no_purchase',row['status'])
            self.assertEqual(0,row['required_pieces'])
            self.assertIsNone(row['buy_pieces'])
            self.assertEqual(36,row['physical_footprints_per_board'])

    def test_external_offer_cannot_turn_geometry_into_purchased_parts(self):
        obs=copy.deepcopy(self.obs)
        obs['offers'].append(dict(mpn='PCB_COPPER_TEST_PAD_D1.0',currency='USD',minimum=1000,multiple=1000,
            packaging='Reel',price_breaks=[dict(minimum=1000,unit_usd='100.00')]))
        result=cost.calculate(OUT,obs)
        self.assertEqual(self.result['summaries'],result['summaries'])

    def test_physical_and_purchase_totals_do_not_confuse_DNP_and_bare_copper(self):
        for row in self.result['summaries']:
            n=row['build_boards']
            self.assertEqual(2688*n,row['physical_footprint_pieces'])
            self.assertEqual(2642*n,row['purchased_fitted_component_pieces'])
            self.assertEqual(37*n,row['bare_PCB_copper_testpad_pieces'])
            self.assertEqual(n,row['bare_PCB_chassis_pad_pieces'])
            self.assertEqual(6*n,row['bare_PCB_NPTH_mount_pieces'])
            self.assertEqual(44*n,row['bare_PCB_geometry_pieces'])
            self.assertEqual(2*n,row['dnp_footprint_pieces'])

    def test_missing_parts_and_turnkey_quote_remain_unknown(self):
        for row in self.result['summaries']:
            self.assertEqual(185,row['unpriced_mpn_count'])
            self.assertEqual(720*row['build_boards'],row['unpriced_fitted_component_pieces'])
            for key in ('full_component_purchase_total_usd','stock_qualified_purchase_total_usd',
                        'complete_manufactured_custom_board_total_usd','complete_controller_kit_total_usd'):
                self.assertIsNone(row[key])

    def test_complete_exact_fixture_keeps_module_and_accessory_sources_separate(self):
        frozen=cost.check_frozen(OUT)
        for source in ('hardware/motherboard_esp_socket/design.json',
                       'hardware/motherboard_terminals/design.json',
                       'hardware/motherboard_power_entry/fitted-accessories-bom.csv'):
            self.assertIn(source,frozen['files_sha256'])
            self.assertTrue((OUT/'inputs'/source).is_file())
        module=self.result['unselected_off_board_modules'][1]
        fitted=json.loads((OUT/'inputs/hardware/motherboard_esp_socket/design.json').read_text())['purchased_module']
        self.assertEqual(fitted['mpn'],module['selected_mpn'])
        self.assertEqual(1,module['quantity'])
        self.assertFalse(module['revision_in_stock_qualified'])

if __name__=='__main__':unittest.main()
