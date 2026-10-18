"""Host extraction/whole-group rollback controls; not native KiCad evidence."""
import copy
import types
import unittest

from extract_e1 import collect
from native_group_gate import copper, filter_board, stage
from protected_net_selector import Selector

NET = "/motherboard_status/RGB_DRIVER_18"


def job(net=NET, end="2"):
    return {"kind": "power", "net": net, "from": ["U1", "1"], "to": ["U2", end]}


def main_route(net=NET, index=1):
    return {"kind": "power", "net": net, "job_index": index, "layer": "F.Cu", "width": 0.2, "points": [[0, 0], [1, 0]]}


def partitions(net=NET):
    return {"nets": {net: [["U1.1#0"], ["U2.2#0"]]}}


class Item:
    serial = 100

    def __init__(self, board=None, uuid=None):
        Item.serial += 1
        self.uid = uuid or f"new-{Item.serial}"
        self.m_Uuid = types.SimpleNamespace(AsString=lambda: self.uid)
        self.net = NET
        self.start = types.SimpleNamespace(x=0, y=0)
        self.end = types.SimpleNamespace(x=1_000_000, y=0)
        self.width, self.layer, self.locked = 200_000, 0, True

    def GetClass(self): return "PCB_TRACK"
    def GetNetname(self): return self.net
    def GetWidth(self): return self.width
    def IsLocked(self): return self.locked
    def GetStart(self): return self.start
    def GetEnd(self): return self.end
    def GetLayer(self): return self.layer
    def SetStart(self, value): self.start = value
    def SetEnd(self, value): self.end = value
    def SetWidth(self, value): self.width = value
    def SetLayer(self, value): self.layer = value
    def SetLocked(self, value): self.locked = value
    def SetNet(self, value): self.net = value.name


class Board:
    def __init__(self):
        self.items = [Item(uuid="old")]
        self.ambiguous = False

    def GetTracks(self): return self.items
    def FindNet(self, name): return types.SimpleNamespace(name=name) if name == NET else None
    def GetLayerID(self, layer): return 0 if layer == "F.Cu" else -1
    def Add(self, item): self.items.append(item)
    def RemoveNative(self, item): self.items.remove(item)
    def GetFootprints(self):
        footprints = []
        for reference, number in (("U1", "1"), ("U2", "2")):
            pad = types.SimpleNamespace(GetNumber=lambda number=number: number, GetNetname=lambda: NET)
            pads = [pad] * (2 if self.ambiguous else 1)
            footprints.append(types.SimpleNamespace(GetReference=lambda reference=reference: reference, Pads=lambda pads=pads: pads))
        return footprints


API = types.SimpleNamespace(PCB_TRACK=Item, FromMM=lambda value: round(value * 1_000_000),
                            VECTOR2I=lambda x, y: types.SimpleNamespace(x=x, y=y))


class ExtractorControls(unittest.TestCase):
    def test_whole_net_preserves_unindexed_aux_records(self):
        auxiliary = dict(main_route(), kind="stub")
        auxiliary.pop("job_index")
        groups, withheld = collect([job()], {"done": 1, "tracks": [main_route(), auxiliary], "failures": []}, partitions(), Selector())
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]["items"]), 2)
        self.assertFalse(withheld)

    def test_partial_checkpoint_does_not_claim_net_complete(self):
        groups, withheld = collect([job(), job(end="3")], {"done": 1, "tracks": [main_route()], "failures": []}, partitions(), Selector())
        self.assertFalse(groups)
        self.assertEqual(withheld[0]["withheld_reason"], "net_has_unattempted_jobs_in_partial_checkpoint")

    def test_unaccounted_completed_net_job_is_withheld(self):
        groups, withheld = collect([job(), job(end="3")], {"done": 2, "tracks": [main_route()], "failures": []}, partitions(), Selector())
        self.assertFalse(groups)
        self.assertEqual(withheld[0]["withheld_reason"], "net_has_unaccounted_completed_jobs")

    def test_already_joined_base_net_is_withheld(self):
        groups, withheld = collect([job()], {"done": 1, "tracks": [main_route()], "failures": []},
                                   {"nets": {NET: [["U1.1#0", "U2.2#0"]]}}, Selector())
        self.assertFalse(groups)

    def test_protected_net_is_not_extracted(self):
        net = "/STEP0_FPGA"
        groups, withheld = collect([job(net)], {"done": 1, "tracks": [main_route(net)], "failures": []}, partitions(net), Selector())
        self.assertFalse(groups)
        self.assertEqual(withheld[0]["withheld_reason"], "protected")

    def manifest(self):
        groups, withheld = collect([job()], {"done": 1, "tracks": [main_route(), main_route()], "failures": []}, partitions(), Selector())
        return {"catalog": {}, "groups": groups}

    def test_native_stage_adapter_preserves_all_original_copper(self):
        board = Board()
        original = copper(board)
        ledger = stage(board, API, self.manifest())
        self.assertEqual(len(ledger["new_uuid_group"]), 2)
        self.assertEqual(copper(board)["old"], original["old"])

    def test_native_stage_refuses_ambiguous_endpoints_before_add(self):
        board = Board()
        board.ambiguous = True
        with self.assertRaises(ValueError): stage(board, API, self.manifest())
        self.assertEqual(len(board.items), 1)

    def test_whole_group_rollback_removes_only_new_items(self):
        board = Board()
        ledger = stage(board, API, self.manifest())
        uuid = next(iter(ledger["new_uuid_group"]))
        result = filter_board(board, ledger, {"violations": [{"type": "clearance", "severity": "error", "items": [{"uuid": "old"}, {"uuid": uuid}]}]})
        self.assertEqual(result["new_items_removed"], 2)
        self.assertEqual(result["old_items_removed"], 0)
        self.assertEqual([item.uid for item in board.items], ["old"])

    def test_old_only_warning_never_removes_copper(self):
        board = Board()
        ledger = stage(board, API, self.manifest())
        result = filter_board(board, ledger, {"violations": [{"type": "duplicate", "severity": "warning", "items": [{"uuid": "old"}]}]})
        self.assertEqual(result["new_items_removed"], 0)
        self.assertEqual(result["accepted_groups"], [NET])

    def test_missing_old_copper_or_missing_drc_list_refuses(self):
        board = Board()
        ledger = stage(board, API, self.manifest())
        with self.assertRaises(ValueError): filter_board(board, ledger, {})
        board.items.pop(0)
        with self.assertRaises(ValueError): filter_board(board, ledger, {"violations": []})


if __name__ == "__main__":
    unittest.main(verbosity=2)
