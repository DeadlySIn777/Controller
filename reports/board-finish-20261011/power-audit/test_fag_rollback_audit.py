"""Host rejection tests for exact donor ownership; no native file modifications."""
import unittest
from audit_fag_rollback import NET, validate_rollback


def segment(uuid, net=NET, width="0.3", x="1"):
    return (f'\t(segment\n\t\t(start {x} 2)\n\t\t(end 3 4)\n\t\t(width {width})\n'
            f'\t\t(locked yes)\n\t\t(layer "In3.Cu")\n\t\t(net "{net}")\n\t\t(uuid "{uuid}")\n\t)\n').encode()


def via(uuid):
    return (f'\t(via\n\t\t(at 3 4)\n\t\t(size 0.6)\n\t\t(drill 0.3)\n'
            f'\t\t(locked yes)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "{NET}")\n\t\t(uuid "{uuid}")\n\t)\n').encode()


def board(*chunks):
    return b"(kicad_pcb\n" + b"".join(chunks) + b")\n"


class RollbackAuditTests(unittest.TestCase):
    def setUp(self):
        self.old = segment("old", "/LOGIC_GND", "0.2")
        self.foreign = segment("recovered", "/motherboard_operator/FREQ_POWER_FAULT_N", "0.2")
        self.owned = segment("owned")
        self.via = via("owned-via")
        self.base = board(self.old)
        self.donor = board(self.old, self.owned, self.via)
        self.source = board(self.old, self.foreign, self.owned, self.via)
        self.candidate = board(self.old, self.foreign)

    def validate(self, candidate=None, donor=None, source=None):
        return validate_rollback(self.base, donor or self.donor, source or self.source,
                                 candidate or self.candidate, expected_count=2)

    def test_exact_whole_owned_delta(self):
        self.assertEqual(self.validate()["removed_items"], 2)

    def test_protected_foreign_removed(self):
        with self.assertRaises(ValueError):
            self.validate(candidate=board(self.old))

    def test_via_retained(self):
        with self.assertRaises(ValueError):
            self.validate(candidate=board(self.old, self.foreign, self.via))

    def test_foreign_item_added(self):
        with self.assertRaises(ValueError):
            self.validate(candidate=board(self.old, self.foreign, segment("hidden", "/LOGIC_GND")))

    def test_donor_changes_older_copper(self):
        with self.assertRaises(ValueError):
            self.validate(donor=board(segment("old", "/LOGIC_GND", x="9"), self.owned, self.via))

    def test_owned_item_identity_reused_with_other_geometry(self):
        with self.assertRaises(ValueError):
            self.validate(source=board(self.old, self.foreign, segment("owned", x="9"), self.via))

    def test_foreign_net_mislabelled_owned(self):
        changed = segment("owned", "/LOGIC_GND")
        with self.assertRaises(ValueError):
            self.validate(donor=board(self.old, changed, self.via), source=board(self.old, self.foreign, changed, self.via))

    def test_retained_bytes_changed(self):
        with self.assertRaises(ValueError):
            self.validate(candidate=board(self.old, segment("recovered", "/motherboard_operator/FREQ_POWER_FAULT_N", x="9")))


if __name__ == "__main__":
    unittest.main()
