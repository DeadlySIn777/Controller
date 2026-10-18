"""Host/mock controls. These are not KiCad DRC or native connectivity tests."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import types
import unittest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("candidate_restore", HERE / "ripup_restore.py")
RESTORE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RESTORE)


def job(net="A", start="1", end="2"):
    return {"kind": "power", "net": net, "from": ["U1", start], "to": ["U2", end],
            "layer": "F.Cu", "width": 0.2, "mm": 1.0}


def track(net="A", uid="old-a", y=0.0, layer="F.Cu"):
    return {"item": "track", "uuid": uid, "net": net, "layer": layer, "width": 0.2,
            "start": [0.0, y], "end": [2.0, y], "locked": True}


def via(net="A", uid="old-v", x=0.0, y=0.0):
    return {"item": "via", "uuid": uid, "net": net, "x": x, "y": y,
            "d": 0.6, "drill": 0.3, "locked": True}


def route(net="B", index=1, y=0.3, layer="F.Cu"):
    return {"kind": "power", "net": net, "job_index": index, "layer": layer,
            "width": 0.2, "points": [[0.0, y], [2.0, y]]}


class FakeNet:
    def __init__(self, name, cls="DOM_LOGIC"):
        self.name, self.cls = name, cls

    def GetNetClassName(self):
        return self.cls


class FakeItem:
    counter = 0

    def __init__(self, board, kind):
        self.board, self.kind, self.values = board, kind, {}
        FakeItem.counter += 1
        self.m_Uuid = types.SimpleNamespace(AsString=lambda: f"mock-{FakeItem.counter}")

    def __getattr__(self, name):
        if name.startswith("Set"):
            return lambda value: self.values.__setitem__(name, value)
        raise AttributeError(name)


class FakeBoard:
    def __init__(self, classes=None, actual_vias=()):
        self.nets = {name: FakeNet(name, cls) for name, cls in (classes or {"A": "DOM_LOGIC", "B": "DOM_LOGIC"}).items()}
        self.added = []
        self.actual_vias = actual_vias

    def GetFootprints(self):
        return []

    def GetTracks(self):
        return self.actual_vias

    def FindNet(self, name):
        return self.nets.get(name)

    def GetLayerID(self, name):
        return {"F.Cu": 0, "In1.Cu": 1, "In2.Cu": 2, "In3.Cu": 3, "In4.Cu": 4, "B.Cu": 31}.get(name, -1)

    def Add(self, item):
        self.added.append(item)


class FakePcbnew:
    VIATYPE_THROUGH = "mock-through"

    def __init__(self, board):
        self.board, self.loaded, self.saved = board, [], []

    def LoadBoard(self, path):
        self.loaded.append(path)
        return self.board

    def FromMM(self, value):
        return round(value * 1_000_000)

    def VECTOR2I(self, x, y):
        return x, y

    def PCB_TRACK(self, board):
        return FakeItem(board, "track")

    def PCB_VIA(self, board):
        return FakeItem(board, "via")

    def SaveBoard(self, path, board, skip_settings):
        self.saved.append((path, board, skip_settings))
        Path(path).write_bytes(b"mock saved board")
        return True


class FakeActualVia:
    def __init__(self, net="A", x=0.0, y=0.0, diameter=0.6, drill=0.3, via_type="mock-through"):
        self.net, self.x, self.y, self.diameter, self.drill, self.via_type = net, x, y, diameter, drill, via_type

    def GetClass(self):
        return "PCB_VIA"

    def GetNetname(self):
        return self.net

    def GetViaType(self):
        return self.via_type

    def GetPosition(self):
        return types.SimpleNamespace(x=round(self.x * 1_000_000), y=round(self.y * 1_000_000))

    def GetWidth(self):
        return round(self.diameter * 1_000_000)

    def GetDrillValue(self):
        return round(self.drill * 1_000_000)


class RestoreControls(unittest.TestCase):
    def run_case(self, rip, jobs, routes, classes=None, options=(), actual_vias=()):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            board_path = folder / "board.kicad_pcb"
            board_path.write_bytes(b"input sentinel")
            output_path = folder / "out.kicad_pcb"
            output_path.write_bytes(b"output sentinel")
            project = folder / "board.kicad_pro"
            project.write_bytes(b"project sentinel")
            report_path = folder / "report.json"
            paths = []
            for name, value in (("rip", rip), ("jobs", jobs), ("routes", routes)):
                path = folder / f"{name}.json"
                path.write_text(json.dumps(value), encoding="utf-8")
                paths.append(str(path))
            board = FakeBoard(classes, actual_vias)
            api = FakePcbnew(board)
            with contextlib.redirect_stdout(io.StringIO()):
                result = RESTORE.main([str(board_path), *paths, str(output_path), str(report_path), *options], api)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(project.read_bytes(), b"project sentinel")
            self.assertEqual(board_path.read_bytes(), b"input sentinel")
            if result:
                self.assertEqual(output_path.read_bytes(), b"output sentinel")
                self.assertFalse(api.saved)
                self.assertFalse(board.added)
                self.assertFalse(report["summary"]["saved"])
            else:
                self.assertEqual(output_path.read_bytes(), b"mock saved board")
                self.assertTrue(api.saved[0][2], "SaveBoard must skip project settings")
                self.assertFalse(report["summary"]["connectivity_proven"])
                self.assertTrue(report["summary"]["native_partition_diff_lost_zero_required"])
            return result, report, api

    def base(self, rec=None):
        rec = rec or track()
        return {"ripped_nets": [rec["net"]], "removed": [rec]}

    def failed(self, j):
        return {"tracks": [], "failures": [{"job": j, "why": "no path"}]}

    def test_net_without_jobs_or_failures_is_restored(self):
        result, report, api = self.run_case(self.base(), [], {"tracks": [], "failures": []})
        self.assertEqual(result, 0)
        self.assertEqual(report["summary"]["candidates"], 1)
        self.assertEqual(report["decisions"][0]["failed_jobs"], 0)
        self.assertEqual(len(api.board.added), 1)

    def test_net_with_indexed_success_and_no_failures_is_still_covered(self):
        j = job()
        result, report, api = self.run_case(self.base(), [j], {"tracks": [route("A", y=4.0)], "failures": []})
        self.assertEqual(result, 0)
        self.assertEqual(report["accounting"]["indexed_route_jobs"], 1)
        self.assertEqual(len(api.board.added), 1)

    def test_indexed_auxiliary_copper_is_accepted_only_with_main_route(self):
        records = [route("A", y=4.0), dict(route("A", y=4.0), kind="neck"),
                   {"kind": "via", "net": "A", "x": 4.0, "y": 4.0, "d": 0.6, "drill": 0.3, "job_index": 1}]
        result, report, api = self.run_case(self.base(), [job()], {"tracks": records, "failures": []})
        self.assertEqual(result, 0)
        self.assertEqual(report["accounting"]["indexed_route_jobs"], 1)

    def test_removed_net_missing_from_ripped_header_is_covered(self):
        result, report, api = self.run_case({"ripped_nets": [], "removed": [track()]}, [], {"tracks": [], "failures": []})
        self.assertEqual(result, 0)
        self.assertEqual(report["summary"]["candidates"], 1)

    def test_conflicting_later_net_refuses_entire_restore_before_mutation(self):
        records = [track("A", y=10.0), track("Z", uid="old-z", y=0.0)]
        rip = {"ripped_nets": ["A", "Z"], "removed": records}
        result, report, api = self.run_case(rip, [job("B")], {"tracks": [route()], "failures": []},
                                            {"A": "DOM_LOGIC", "B": "DOM_LOGIC", "Z": "DOM_LOGIC"})
        self.assertEqual(result, 3)
        self.assertEqual(report["summary"]["restored_nets"], 0)
        self.assertEqual(report["summary"]["refused_conflict"], 1)
        self.assertTrue(report["decisions"][0]["would_restore"])
        self.assertFalse(any(d["restored"] for d in report["decisions"]))

    def test_original_failed_job_restore_still_works(self):
        j = job()
        result, report, api = self.run_case(self.base(), [j], self.failed(j))
        self.assertEqual(result, 0)
        self.assertEqual(report["decisions"][0]["failed_jobs"], 1)

    def test_track_geometry_net_layer_and_lock_are_preserved(self):
        rec = track(layer="B.Cu", y=3.0)
        rec["width"] = 0.37
        result, report, api = self.run_case(self.base(rec), [], {"tracks": [], "failures": []})
        values = api.board.added[0].values
        self.assertEqual(values["SetStart"], (0, 3_000_000))
        self.assertEqual(values["SetEnd"], (2_000_000, 3_000_000))
        self.assertEqual(values["SetWidth"], 370_000)
        self.assertEqual(values["SetLayer"], 31)
        self.assertEqual(values["SetNet"].name, "A")
        self.assertTrue(values["SetLocked"])

    def test_via_geometry_size_drill_type_and_lock_are_preserved(self):
        rec = via(x=4.0, y=5.0)
        result, report, api = self.run_case(self.base(rec), [], {"tracks": [], "failures": []})
        values = api.board.added[0].values
        self.assertEqual(values["SetPosition"], (4_000_000, 5_000_000))
        self.assertEqual(values["SetWidth"], 600_000)
        self.assertEqual(values["SetDrill"], 300_000)
        self.assertEqual(values["SetViaType"], api.VIATYPE_THROUGH)
        self.assertTrue(values["SetLocked"])

    def test_same_domain_clearance_refuses_below_margin(self):
        result, report, api = self.run_case(self.base(), [job("B")], {"tracks": [route(y=0.39)], "failures": []})
        self.assertEqual(result, 3)
        self.assertEqual(report["decisions"][0]["conflict"]["required_mm"], 0.2)

    def test_same_domain_clearance_accepts_at_margin(self):
        result, report, api = self.run_case(self.base(), [job("B")], {"tracks": [route(y=0.4)], "failures": []})
        self.assertEqual(result, 0)

    def test_cross_domain_clearance_margin_remains_strict(self):
        result, report, api = self.run_case(self.base(), [job("B")], {"tracks": [route(y=0.8)], "failures": []},
                                            {"A": "DOM_LOGIC", "B": "DOM_FIELD"})
        self.assertEqual(result, 3)
        self.assertEqual(report["decisions"][0]["conflict"]["required_mm"], 0.65)

    def test_cross_domain_clearance_above_margin_passes(self):
        result, report, api = self.run_case(self.base(), [job("B")], {"tracks": [route(y=0.9)], "failures": []},
                                            {"A": "DOM_LOGIC", "B": "DOM_FIELD"})
        self.assertEqual(result, 0)

    def test_tracks_on_distinct_layers_are_allowed(self):
        result, report, api = self.run_case(self.base(), [job("B")], {"tracks": [route(y=0.0, layer="B.Cu")], "failures": []})
        self.assertEqual(result, 0)

    def test_through_via_conflict_is_checked_on_other_track_layer(self):
        result, report, api = self.run_case(self.base(via()), [job("B")], {"tracks": [route(y=0.0, layer="B.Cu")], "failures": []})
        self.assertEqual(result, 3)

    def test_colocated_same_net_via_is_skipped_once(self):
        emitted = {"kind": "via", "net": "A", "x": 0.0, "y": 0.0, "d": 0.6, "drill": 0.3}
        result, report, api = self.run_case(self.base(via()), [job()], {"tracks": [route("A", y=4.0), emitted], "failures": []},
                                            actual_vias=[FakeActualVia()])
        self.assertEqual(result, 0)
        self.assertEqual(report["summary"]["duplicate_vias_skipped"], 1)
        self.assertFalse(api.board.added)

    def test_duplicate_skip_rejects_different_diameter_drill_or_position(self):
        controls = [("diameter", {"d": 0.5}), ("drill", {"drill": 0.2}), ("position", {"x": 0.005})]
        for name, delta in controls:
            with self.subTest(control=name):
                emitted = {"kind": "via", "net": "A", "x": 0.0, "y": 0.0, "d": 0.6, "drill": 0.3, **delta}
                actual = FakeActualVia(x=emitted["x"], diameter=emitted["d"], drill=emitted["drill"])
                result, report, api = self.run_case(self.base(via()), [job()],
                                                    {"tracks": [route("A", y=4.0), emitted], "failures": []}, actual_vias=[actual])
                self.assertEqual(result, 3)
                self.assertIn("non-equivalent duplicate", report["decisions"][0]["conflict"]["layer"])

    def test_duplicate_skip_requires_present_matching_through_via(self):
        emitted = {"kind": "via", "net": "A", "x": 0.0, "y": 0.0, "d": 0.6, "drill": 0.3}
        for name, present in (("absent", []), ("blind", [FakeActualVia(via_type="mock-blind")]),
                              ("wrong net", [FakeActualVia(net="B")]), ("wrong geometry", [FakeActualVia(diameter=0.5)])):
            with self.subTest(control=name):
                result, report, api = self.run_case(self.base(via()), [job()],
                                                    {"tracks": [route("A", y=4.0), emitted], "failures": []}, actual_vias=present)
                self.assertEqual(result, 3)

    def test_same_net_hole_clearance_refuses_nearby_via(self):
        emitted = {"kind": "via", "net": "A", "x": 0.5, "y": 0.0, "d": 0.6, "drill": 0.3}
        result, report, api = self.run_case(self.base(via()), [job()], {"tracks": [route("A", y=4.0), emitted], "failures": []})
        self.assertEqual(result, 3)
        self.assertEqual(report["decisions"][0]["conflict"]["required_mm"], 0.25)

    def test_unknown_net_refuses_before_save(self):
        result, report, api = self.run_case(self.base(), [], {"tracks": [], "failures": []}, {"B": "DOM_LOGIC"})
        self.assertEqual(result, 3)
        self.assertEqual(report["decisions"][0]["conflict"], "net not on board")

    def test_unknown_layer_refuses_before_save(self):
        result, report, api = self.run_case(self.base(track(layer="Unknown.Cu")), [], {"tracks": [], "failures": []})
        self.assertEqual(result, 3)
        self.assertIn("unknown layers", report["decisions"][0]["conflict"])

    def test_input_accounting_rejection_controls(self):
        j = job()
        controls = [
            ("missing outcome", [j], {"tracks": [], "failures": []}),
            ("unknown failure", [j], self.failed(job("B"))),
            ("duplicate failure", [j], {"tracks": [], "failures": [{"job": j, "why": "no path"}] * 2}),
            ("different failure payload", [j], self.failed(dict(j, width=0.3))),
            ("duplicate job", [j, j], self.failed(j)),
            ("failure plus copper", [j], {"tracks": [route("A")], "failures": [{"job": j, "why": "no path"}]}),
            ("index outside jobs", [j], {"tracks": [route("A", index=2)], "failures": []}),
            ("boolean index", [j], {"tracks": [route("A", index=True)], "failures": []}),
            ("wrong indexed net", [j], {"tracks": [route("B")], "failures": []}),
            ("main route no index", [j], {"tracks": [{k: v for k, v in route("A").items() if k != "job_index"}], "failures": []}),
            ("orphan stub", [], {"tracks": [dict(route("A"), kind="stub", job_index=1)], "failures": []}),
            ("orphan unindexed via", [], {"tracks": [{"kind": "via", "net": "A", "x": 0, "y": 0, "d": 0.6, "drill": 0.3}], "failures": []}),
            ("unsupported pair job", [dict(j, kind="pair")], {"tracks": [], "failures": []}),
            ("nan geometry", [j], {"tracks": [route("A", y=float("nan"))], "failures": []}),
            ("missing failures field", [j], {"tracks": [route("A")]}),
            ("empty geometry", [j], {"tracks": [dict(route("A"), points=[])], "failures": []}),
            ("zero geometry", [j], {"tracks": [dict(route("A"), points=[[0, 0], [0, 0]])], "failures": []}),
            ("indexed aux stub", [j], {"tracks": [dict(route("A"), kind="stub")], "failures": []}),
            ("indexed aux via", [j], {"tracks": [{"kind": "via", "net": "A", "x": 0, "y": 0, "d": 0.6, "drill": 0.3, "job_index": 1}], "failures": []}),
        ]
        for name, jobs, routes in controls:
            with self.subTest(control=name):
                result, report, api = self.run_case(self.base(), jobs, routes)
                self.assertEqual(result, 2)
                self.assertFalse(api.loaded)

    def test_destination_path_aliases_are_rejected(self):
        import os
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            paths = {name: folder / name for name in ("board", "rip", "jobs", "routes", "out", "report")}
            for path in paths.values():
                path.write_bytes(b"sentinel")
            def args(**overrides):
                return types.SimpleNamespace(**{name: str(path) for name, path in dict(paths, **overrides).items()})
            for overrides in ({"out": paths["rip"]}, {"report": paths["board"]}):
                with self.subTest(paths=overrides), self.assertRaises(RESTORE.InputError):
                    RESTORE.validate_paths(args(**overrides))
            hardlink = folder / "hardlink"
            os.link(paths["rip"], hardlink)
            with self.assertRaises(RESTORE.InputError):
                RESTORE.validate_paths(args(report=hardlink))
            part = Path(str(paths["report"]) + ".part")
            os.link(paths["board"], part)
            with self.assertRaises(RESTORE.InputError):
                RESTORE.validate_paths(args())
            for path in paths.values():
                self.assertEqual(path.read_bytes(), b"sentinel")

    def test_output_board_may_be_same_as_input_board(self):
        args = types.SimpleNamespace(board="a.pcb", out="a.pcb", rip="rip.json", jobs="jobs.json",
                                     routes="routes.json", report="report.json")
        RESTORE.validate_paths(args)

    def test_removed_geometry_rejection_controls(self):
        controls = [
            ("ripped without geometry", {"ripped_nets": ["A"], "removed": []}),
            ("duplicate uuid", {"ripped_nets": ["A"], "removed": [track(), track()]}),
            ("unsupported item", self.base(dict(track(), item="arc"))),
            ("nan old geometry", self.base(track(y=float("nan")))),
            ("negative width", self.base(dict(track(), width=-0.2))),
            ("oversize drill", self.base(dict(via(), drill=0.7))),
            ("invalid locked flag", self.base(dict(track(), locked="false"))),
        ]
        for name, rip in controls:
            with self.subTest(control=name):
                result, report, api = self.run_case(rip, [], {"tracks": [], "failures": []})
                self.assertEqual(result, 2)
                self.assertFalse(api.loaded)

    def test_nonfinite_or_nonpositive_clearance_arguments_refuse(self):
        for value in ("nan", "inf", "-0.1", "0"):
            with self.subTest(clearance=value):
                result, report, api = self.run_case(self.base(), [], {"tracks": [], "failures": []}, options=["--same-mm", value])
                self.assertEqual(result, 2)
                self.assertFalse(api.loaded)

    def test_saved_r07_accounting_and_fail_closed_geometry_replay(self):
        inputs = HERE / "inputs"
        if not (inputs / "r07-rip-r1.json").exists():
            self.skipTest("r07 source JSON snapshots have not been written")
        rip = json.loads((inputs / "r07-rip-r1.json").read_text())
        jobs = json.loads((inputs / "r07-jobs-r1-c.json").read_text())
        routes = json.loads((inputs / "r07-routes-r1-c.json").read_text())
        classes = json.loads((inputs / "r07-recorded-net-classes.json").read_text())
        candidates, recs, failures, accounting = RESTORE.validate_inputs(rip, jobs, routes)
        self.assertEqual(accounting["jobs"], 416)
        self.assertEqual(accounting["failed_jobs"], 316)
        self.assertEqual(accounting["indexed_route_jobs"], 100)
        self.assertEqual(len(candidates), 130)
        original_report = json.loads((inputs / "r07-restore-r1.json").read_text())
        original_diff = json.loads((inputs / "r07-partition_diff.json").read_text())
        original_decisions = {d["net"]: d for d in original_report["decisions"]}
        lost = {net for net, delta in original_diff["per_net"].items() if delta["lost"]}
        self.assertEqual(len(lost), 17)
        self.assertTrue(all(original_decisions[net]["restored"] is False for net in lost))
        result, report, api = self.run_case(rip, jobs, routes, classes)
        self.assertEqual(result, 3)
        decisions = {d["net"]: d for d in report["decisions"]}
        self.assertTrue(all(not decisions[net]["would_restore"] for net in lost))
        self.assertEqual(report["summary"]["candidates"], 130)
        self.assertFalse(api.saved)


if __name__ == "__main__":
    unittest.main(verbosity=2)
