"""Reject stale/old-field/native parity fixtures; native inputs remain read-only."""
import copy
import json
import unittest
import run_corrected_api_parity_v2 as runner

class CorrectedGuard(unittest.TestCase):
    def setUp(self):
        self.report=json.loads((runner.OUT/"native-parity.json").read_text())
        self.host=json.loads((runner.OUT/"host-parity.json").read_text())
        self.board=runner.EXPECTED
        self.net=runner.sha(runner.NET)
    def gate(self):
        return runner.gate(self.report,self.host,self.board,self.net)
    def rejected(self):
        with self.assertRaises(ValueError):self.gate()
    def test_actual_pass(self):self.assertEqual(self.gate()["parity_defects"],0)
    def test_historical_cap_value(self):self.report["native_corrected_capacitor_fields"]["value"]="4.7uF 16V X7R";self.rejected()
    def test_historical_mpn(self):self.report["native_corrected_capacitor_fields"]["MPN"]="C2012X7R1C475K125AB";self.rejected()
    def test_wrong_export_hash(self):self.report["inputs"]["netlist"]["sha256"]="0"*64;self.rejected()
    def test_wrong_board_hash(self):self.report["inputs"]["board"]["sha256"]="0"*64;self.rejected()
    def test_duplicate_api_load(self):self.report["project_settings_binding"]["load_count"]=2;self.rejected()
    def test_unbound_project(self):self.report["project_settings_binding"]["explicit_board_set_project"]=False;self.rejected()
    def test_nodes_inventory(self):self.report["summary"]["netlist_nodes"]=9591;self.rejected()
    def test_no_net_copper_touch(self):self.report["summary"]["pads_no_net_touched_by_track_or_via"]=1;self.rejected()
    def test_node_conflict(self):self.report["pads"]["netlist_node_conflicts"]=[{"ref":"C11061","pin":"1"}];self.rejected()
    def test_scope_fill_requested(self):self.report["project_settings_binding"]["refill_requested"]=True;self.rejected()

if __name__=="__main__":unittest.main()
