"""Cheap independent composite ownership and attribution rejection fixtures."""
import copy
import unittest
from audit_c05_rollback import E1_NETS, validate_composite, validate_attribution
from test_fag_rollback_audit import board, segment, via


class CompositeTests(unittest.TestCase):
    def setUp(self):
        self.old, self.foreign = segment("old", "/LOGIC_GND"), segment("recovered", "/LOGIC_GND")
        self.fag = [segment("fag"), via("fag-via")]
        self.e1 = [segment("e1-" + str(index), net) for index, net in enumerate(sorted(E1_NETS))]
        self.base = board(self.old)
        self.donor = board(self.old, *self.fag)
        self.subset = board(self.old, *self.e1)
        self.source = board(self.old, self.foreign, *self.fag, *self.e1)
        self.candidate = board(self.old, self.foreign)

    def check(self, candidate=None, subset=None):
        return validate_composite(self.base, self.donor, subset or self.subset, self.source,
                                  candidate or self.candidate, fag_count=2, e1_count=4)

    def test_complete_groups(self):
        self.assertEqual(self.check()["removed_total"], 6)

    def test_partial_e1_group(self):
        with self.assertRaises(ValueError):
            self.check(candidate=board(self.old, self.foreign, self.e1[0]))

    def test_foreign_copper_removed(self):
        with self.assertRaises(ValueError):
            self.check(candidate=board(self.old))

    def test_fake_e1_group(self):
        with self.assertRaises(ValueError):
            self.check(subset=board(self.old, *self.e1[:3], segment("hidden", "/LOGIC_GND")))

    def test_protected_source_changed(self):
        with self.assertRaises(ValueError):
            self.check(candidate=board(self.old, segment("recovered", "/LOGIC_GND", x="9")))

    def test_hidden_addition(self):
        with self.assertRaises(ValueError):
            self.check(candidate=board(self.old, self.foreign, segment("new", "/LOGIC_GND")))


class AttributionTests(unittest.TestCase):
    def setUp(self):
        self.drc = {"violations": [{"severity": "error", "type": "clearance", "description": "fixture",
                                     "items": [{"uuid": "fag"}, {"uuid": "retained"}]}]}
        self.owners = {"fag": "FAG"}
        self.source = {"fag", "retained"}
        self.receipt = {"verdict": "PASS_EXACT_ERROR_ATTRIBUTION", "all_errors_have_exact_single_donor_owner": True,
                        "counts_by_new_donor_group": {"FAG": 1}, "errors": 1,
                        "records": [{"owner": "FAG", "type": "clearance", "description": "fixture", "item_uuids": ["fag", "retained"]}]}

    def check(self, receipt=None, drc=None):
        return validate_attribution(receipt or self.receipt, drc or self.drc, self.owners, self.source, {"FAG": 1})

    def test_actual_attribution(self):
        self.assertEqual(self.check()["raw_drc_errors"], 1)

    def test_stale_raw_record(self):
        changed = copy.deepcopy(self.receipt)
        changed["records"][0]["item_uuids"] = ["other", "retained"]
        with self.assertRaises(ValueError):
            self.check(receipt=changed)

    def test_unattributed_raw_error(self):
        changed = copy.deepcopy(self.drc)
        changed["violations"][0]["items"] = [{"uuid": "retained"}]
        with self.assertRaises(ValueError):
            self.check(drc=changed)

    def test_error_outside_source(self):
        changed = copy.deepcopy(self.drc)
        changed["violations"][0]["items"][1]["uuid"] = "unknown"
        with self.assertRaises(ValueError):
            self.check(drc=changed)


if __name__ == "__main__":
    unittest.main()
