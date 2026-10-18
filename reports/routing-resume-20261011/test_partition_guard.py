import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from partition_guard import check_board, compare


def receipt(nets, api=None):
    missing = sum(len(groups) - 1 for groups in nets.values())
    return {"refilled": True, "sha256": "a" * 64, "nets": nets,
            "pad_island_joins": missing, "api_unconnected_count": missing if api is None else api}


class GuardTests(unittest.TestCase):
    def test_net_gain_cannot_hide_loss(self):
        b = receipt({"lost": [["a", "b"]], "gained": [["c"], ["d"], ["e"]]})
        a = receipt({"lost": [["a"], ["b"]], "gained": [["c", "d", "e"]]})
        r = compare(b, a)
        self.assertEqual((r["verdict"], r["completed"], r["lost"]), ("FAIL", 2, 1))

    def test_clean_gain_passes(self):
        r = compare(receipt({"n": [["a"], ["b"]]}), receipt({"n": [["a", "b"]]}))
        self.assertEqual((r["verdict"], r["completed"], r["lost"]), ("PASS", 1, 0))

    def test_partial_split_detected(self):
        r = compare(receipt({"n": [["a", "b", "c"]]}), receipt({"n": [["a", "c"], ["b"]]}))
        self.assertEqual(r["lost"], 1)

    def test_same_cardinality_changed_identity_rejected(self):
        with self.assertRaisesRegex(ValueError, "pad identities"):
            compare(receipt({"n": [["a", "b"]]}), receipt({"n": [["a", "c"]]}))

    def test_disappearing_net_rejected(self):
        with self.assertRaisesRegex(ValueError, "net sets"):
            compare(receipt({"n": [["a", "b"]]}), receipt({}))

    def test_duplicate_pad_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            compare(receipt({"n": [["a", "b"]]}), receipt({"n": [["a", "b"], ["a"]]}))

    def test_missing_refill_rejected(self):
        b = receipt({"n": [["a", "b"]]})
        a = copy.deepcopy(b)
        a["refilled"] = False
        with self.assertRaisesRegex(ValueError, "refill"):
            compare(b, a)

    def test_inconsistent_count_rejected(self):
        b = receipt({"n": [["a", "b"]]})
        a = copy.deepcopy(b)
        a["pad_island_joins"] = 1
        with self.assertRaisesRegex(ValueError, "disagree"):
            compare(b, a)

    def test_api_increase_rejected(self):
        self.assertEqual(compare(receipt({"n": [["a", "b"]]}, 0),
                                 receipt({"n": [["a", "b"]]}, 1))["verdict"], "FAIL")

    def test_hash_bound_to_actual_board(self):
        with tempfile.TemporaryDirectory() as tmp:
            board = Path(tmp) / "board.kicad_pcb"
            board.write_bytes(b"fixture")
            b = receipt({"n": [["a", "b"]]})
            b["sha256"] = hashlib.sha256(b"fixture").hexdigest()
            check_board(b, board)
            board.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "stale"):
                check_board(b, board)


if __name__ == "__main__":
    unittest.main()
