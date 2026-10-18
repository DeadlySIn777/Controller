"""Host controls; no KiCad process is launched by these tests."""
import copy
import json
from pathlib import Path
import unittest

from host_parity import load_parser, compare
from run_native_parity import gate_report, verify_frozen
from project_clone import verify_clone
from fresh_export import canonical

HERE = Path(__file__).resolve().parent
FROZEN = HERE / "root106"


class PortableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = load_parser(FROZEN / "tools/netlist_parity.py")
        cls.nl = cls.parser["read_netlist"](FROZEN / "source/sch.net")
        cls.board = json.loads((FROZEN / "host-board-table.json").read_text())

    def test_authentic_frozen_candidate_matches_all_physical_pads(self):
        result = compare(self.nl, self.board, self.parser)
        self.assertEqual(result["verdict"], "PASS")
        self.assertEqual((result["netlist_nodes"], result["physical_pads_matched"], result["board_pads"]), (9590, 9609, 9950))
        self.assertEqual(result["native_api_confirmation"], "PENDING")

    def test_wrong_net_on_repeated_numbered_physical_pad_rejected(self):
        b = copy.deepcopy(self.board)
        duplicate = next((p for p in b["pads"] if sum(q["ref"] == p["ref"] and q["number"] == p["number"] for q in b["pads"]) > 1 and p["net"]), None)
        self.assertIsNotNone(duplicate)
        duplicate["net"] = "/WRONG_NET"
        result = compare(self.nl, b, self.parser)
        self.assertEqual(result["verdict"], "FAIL")
        self.assertEqual(result["counts"]["pad_net_mismatch"], 1)

    def test_component_identity_and_node_mutations_rejected(self):
        for field in ["fpid", "value"]:
            with self.subTest(field=field):
                b = copy.deepcopy(self.board)
                next(iter(b["footprints"].values()))[field] = "changed"
                self.assertEqual(compare(self.nl, b, self.parser)["verdict"], "FAIL")
        b = copy.deepcopy(self.board)
        removed = next(p for p in b["pads"] if p["net"])
        b["pads"] = [p for p in b["pads"] if (p["ref"], p["number"]) != (removed["ref"], removed["number"])]
        self.assertGreater(compare(self.nl, b, self.parser)["counts"]["node_without_pad"], 0)

    def test_net_collisions_and_duplicate_refs_rejected(self):
        b = copy.deepcopy(self.board)
        p = next(p for p in b["pads"] if "{slash}" in p["net"])
        q = copy.deepcopy(p); q["net"] = p["net"].replace("{slash}", "/"); b["pads"].append(q)
        self.assertGreater(compare(self.nl, b, self.parser)["counts"]["normalisation_collisions"], 0)
        b = copy.deepcopy(self.board); b["duplicate_refs"].append("R4013")
        self.assertEqual(compare(self.nl, b, self.parser)["verdict"], "FAIL")

    def test_no_netlist_node_cannot_acquire_net(self):
        b = copy.deepcopy(self.board)
        p = next(p for p in b["pads"] if not p["number"])
        p["net"] = "/LOGIC_GND"
        self.assertEqual(compare(self.nl, b, self.parser)["counts"]["netted_pad_without_node"], 1)

    def test_source_identity_records_nonphysical_exclusions(self):
        result = json.loads((FROZEN / "source-identity.json").read_text())
        self.assertEqual(result["verdict"], "PASS")
        self.assertEqual((len(result["reachable_files"]), result["placed_component_refs"], len(result["explicitly_not_on_board"])), (27, 2717, 357))
        self.assertTrue(all(p["on_board"] == "no" for p in result["explicitly_not_on_board"]))


class NativeReceiptControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = json.loads((FROZEN / "inputs.json").read_text())
        cls.host = json.loads((FROZEN / "host-parity.json").read_text())
        # Authentic historical API schema is used solely as a synthetic host fixture.
        cls.report = json.loads(Path("Z:/pcb-runs/claude-finish/agent-work/netlist-parity/parity-noconn.json").read_text())
        cls.report["inputs"]["board"]["sha256"] = cls.inputs["board_sha256"]
        cls.report["inputs"]["netlist"]["sha256"] = cls.inputs["netlist_sha256"]

    def test_zero_exit_does_not_authorize_mismatch_report(self):
        for field, value in [("parity_defects", 1), ("pad_net_mismatch", 1), ("status", "mismatches"),
                             ("parity_defects", False), ("pads_no_net_touched_by_track_or_via", 1)]:
            with self.subTest(field=field, value=value):
                r = copy.deepcopy(self.report); r["summary"][field] = value
                with self.assertRaises(ValueError):
                    gate_report(r, self.inputs, self.host)

    def test_stale_report_and_inventory_rejected(self):
        for part in ["board", "netlist"]:
            with self.subTest(part=part):
                r = copy.deepcopy(self.report); r["inputs"][part]["sha256"] = "0" * 64
                with self.assertRaisesRegex(ValueError, "hash differs"):
                    gate_report(r, self.inputs, self.host)
        r = copy.deepcopy(self.report); r["summary"]["pads_matched"] -= 1
        with self.assertRaisesRegex(ValueError, "inventory counts"):
            gate_report(r, self.inputs, self.host)

    def test_contradictory_node_assignment_rejected_even_if_defect_total_zero(self):
        r = copy.deepcopy(self.report); r["pads"]["netlist_node_conflicts"] = [{"ref": "U1", "pin": "1"}]
        with self.assertRaisesRegex(ValueError, "contradictory"):
            gate_report(r, self.inputs, self.host)

    def test_missing_report_field_rejects(self):
        r = copy.deepcopy(self.report); del r["summary"]["board_pads"]
        with self.assertRaises(ValueError):
            gate_report(r, self.inputs, self.host)

    def test_valid_schema_does_not_claim_cli_or_drc(self):
        result = gate_report(self.report, self.inputs, self.host)
        self.assertEqual(result["verdict"], "PASS")
        self.assertIn("NOT ESTABLISHED", result["cli_schematic_parity"])
        self.assertFalse(result["adopted"])

    def test_frozen_snapshot_and_requested_candidate_hashes(self):
        result = verify_frozen(FROZEN, FROZEN / "board.kicad_pcb")
        self.assertEqual(result["board_sha256"], "53838149db4378929875b9862681b790a3a7ed975ee5530c4af975abbeb7df64")

    def test_actual_saved_native_results_and_context_clones(self):
        for name in ["root106", "c03"]:
            with self.subTest(name=name):
                directory = HERE / name
                inputs = json.loads((directory / "inputs.json").read_text())
                host = json.loads((directory / "host-parity.json").read_text())
                report = json.loads((directory / "native-parity.json").read_text())
                self.assertEqual(gate_report(report, inputs, host)["verdict"], "PASS")
                binding = report["project_settings_binding"]
                self.assertTrue(binding["explicit_settings_manager_load"])
                self.assertTrue(binding["explicit_board_set_project"])
                self.assertFalse(binding["settings_save_requested"])
                self.assertTrue(verify_clone(directory, json.loads((directory / "project-clone.json").read_text())))


class ExportControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = load_parser(FROZEN / "tools/netlist_parity.py")
        cls.old = cls.parser["read_netlist"](FROZEN / "source/sch.net")
        cls.fresh = cls.parser["read_netlist"](FROZEN / "source-export/fresh.net")

    def test_actual_fresh_export_semantically_matches(self):
        self.assertEqual(canonical(self.old), canonical(self.fresh))

    def test_export_dates_paths_and_node_order_do_not_define_identity(self):
        a = copy.deepcopy(self.old)
        a["info"] = {"source": "different path", "date": "different date"}
        for net in a["nets"].values():
            net["nodes"].reverse()
        self.assertEqual(canonical(self.old), canonical(a))

    def test_changed_component_node_and_contradictory_exports_rejected(self):
        for section in ["component", "node", "conflict"]:
            with self.subTest(section=section):
                a = copy.deepcopy(self.old)
                if section == "component":
                    next(iter(a["components"].values()))["footprint"] = "wrong"
                elif section == "node":
                    a["node_net"][next(iter(a["node_net"]))] = "wrong"
                else:
                    a["node_conflicts"] = [{"ref": "U1", "pin": "1"}]
                if section == "conflict":
                    with self.assertRaises(ValueError): canonical(a)
                else:
                    self.assertNotEqual(canonical(self.old), canonical(a))


if __name__ == "__main__":
    unittest.main(verbosity=2)
