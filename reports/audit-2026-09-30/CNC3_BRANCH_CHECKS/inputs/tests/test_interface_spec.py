"""Tests for the IS-1 interface-specification validator (tools/interface_spec_validate.py).

The first tests run the validator on the real specification files. The fault-injection tests copy
the specification into a temporary directory, break one thing and prove that the validator reports
it. These are specification checks; they test no RTL, firmware or hardware.
"""
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import interface_spec_validate as isv  # noqa: E402


class RealFiles(unittest.TestCase):
    def test_validator_passes_on_is1(self):
        r = isv.validate(ROOT, render=True, docs=True)
        self.assertEqual([], r.problems)
        self.assertGreater(r.passed, 10000)

    def test_cli_check_mode_exits_zero_and_writes_nothing(self):
        before = {n: os.path.getmtime(os.path.join(ROOT, "spec", n + ".json")) for n in isv.SPEC_FILES}
        proc = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "interface_spec_validate.py"), "--check", "--no-render"],
                              capture_output=True, text=True)
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        self.assertIn("0 problems", proc.stdout)
        after = {n: os.path.getmtime(os.path.join(ROOT, "spec", n + ".json")) for n in isv.SPEC_FILES}
        self.assertEqual(before, after)

    def test_every_file_carries_is1(self):
        for n in isv.SPEC_FILES:
            with open(os.path.join(ROOT, "spec", n + ".json"), encoding="utf-8") as fh:
                self.assertEqual("IS-1", json.load(fh)["spec_revision"])
        for rel in isv.DOCS:
            with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
                self.assertTrue(fh.readline().startswith("Interface specification revision: IS-1"), rel)


class FaultInjection(unittest.TestCase):
    """Each test breaks one cross-reference in a temporary copy and expects a specific problem."""

    @classmethod
    def setUpClass(cls):
        cls.base = isv.load(ROOT)

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="is1-")
        os.makedirs(os.path.join(self.tmp, "spec"))
        self.specs = copy.deepcopy(self.base)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_validator(self):
        for name, data in self.specs.items():
            with open(os.path.join(self.tmp, "spec", name + ".json"), "w", encoding="utf-8", newline="\n") as fh:
                json.dump(data, fh, indent=1, ensure_ascii=False)
        return isv.validate(self.tmp, render=False, docs=False).problems

    def assertProblem(self, problems, *fragments):
        for fragment in fragments:
            self.assertTrue(any(fragment in p for p in problems), f"expected a problem containing {fragment!r}; got {problems[:8]}")

    def test_unmodified_copy_is_clean(self):
        self.assertEqual([], self.run_validator())

    def test_missing_terminal(self):
        t = self.specs["terminals"]
        t["terminals"] = [x for x in t["terminals"] if x["id"] != "XDI0.5"]
        self.assertProblem(self.run_validator(), "connector XDI0: positions are not exactly", "maps to missing terminal XDI0.5")

    def test_double_allocation(self):
        cfg = self.specs["allocations"]["configurations"][0]
        first_di = next(a for a in cfg["assignments"] if a["resource_class"] == "di")
        cfg["assignments"].append({"function": "Injected duplicate", "resource_class": "di", "channel": 23, "terminal": first_di["terminal"]})
        self.assertProblem(self.run_validator(), f"terminal {first_di['terminal']} double-allocated")

    def test_double_channel_allocation(self):
        cfg = self.specs["allocations"]["configurations"][0]
        first_do = next(a for a in cfg["assignments"] if a["resource_class"] == "do")
        dup = dict(first_do, function="Injected channel duplicate", terminal="XDO1.8")
        cfg["assignments"].append(dup)
        self.assertProblem(self.run_validator(), "double-allocated")

    def test_frame_overlap(self):
        cnf3 = self.specs["protocol"]["frames"]["fb_response_CNF3"]
        f = next(x for x in cnf3 if x["name"] == "alarm_levels")
        f["offset"] -= 1
        self.assertProblem(self.run_validator(), "frame fb_response_CNF3 field alarm_levels at 27 overlaps")

    def test_crc_not_covering_payload(self):
        cmd = self.specs["protocol"]["frames"]["cmd_command"]
        crc = cmd.pop()
        cmd[-1]["size"] += crc["size"]
        self.assertProblem(self.run_validator(), "frame cmd_command does not end in a 2-byte CRC")

    def test_enable_terminal_removed(self):
        t = self.specs["terminals"]
        t["terminals"] = [x for x in t["terminals"] if x["net"] != "M3_EN_NC"]
        self.assertProblem(self.run_validator(), "motor channel M3: EN_NC terminal missing")

    def test_alarm_without_hal_pin(self):
        x = next(x for x in self.specs["terminals"]["terminals"] if x["net"] == "M11_ALM_IN")
        x["hal_pin"] = None
        self.assertProblem(self.run_validator(), "motor channel M11: alarm has no per-channel HAL pin")

    def test_schedule_over_budget(self):
        s = self.specs["protocol"]["schedule"]
        extra = 60.0
        s["allocations_us_REQ"]["linuxcnc_compute"] += extra
        s["allocation_total_to_commit_us"] += extra
        for case in s["cases"].values():
            for k in ("completion_C_us", "thread_end_us"):
                case[k] = round(case[k] + extra, 2)
            for k in ("margin_to_700_us", "margin_to_1000_us"):
                case[k] = round(case[k] - extra, 2)
        problems = self.run_validator()
        self.assertProblem(problems, "schedule 5.00_MHz: completion 716.16 us exceeds the 700.0 us target")
        self.assertFalse(any("6.25_MHz: completion" in p for p in problems), problems)

    def test_schedule_misstated(self):
        self.specs["protocol"]["schedule"]["cases"]["5.00_MHz"]["completion_C_us"] = 600.0
        self.assertProblem(self.run_validator(), "schedule 5.00_MHz: stated completion 600.0")

    def test_connection_without_data_age(self):
        self.specs["protocol"]["connections"][3]["age"] = ""
        self.assertProblem(self.run_validator(), "no maximum data age")

    def test_unregistered_hal_pin(self):
        x = next(x for x in self.specs["terminals"]["terminals"] if x["id"] == "XDO0.1")
        x["hal_pin"] = x["hal_pin"].replace("cnc1.dout.0-current-age", "cnc1.dout.0-current-ages")
        self.assertProblem(self.run_validator(), "HAL pin cnc1.dout.0-current-ages not in the hal_pins registry")

    def test_unknown_cnc1_field(self):
        x = next(x for x in self.specs["terminals"]["terminals"] if x["id"] == "XM0.8")
        x["cnc1_field"] = "CMD.enable_mask bit 0"
        self.assertProblem(self.run_validator(), "CNC1 field CMD.enable_mask not defined in any protocol frame")

    def test_boundary_count_mismatch(self):
        mia_p2 = self.specs["modules"]["boundaries"]["MIA"][1]
        g = next(g for g in mia_p2["groups"] if g["kind"] == "fld")
        g["count"] -= 1
        g["conductors"] -= 1
        mia_p2["field_conductors_other"] -= 1
        mia_p2["contacts_used"] -= 1
        mia_p2["contacts_spare"] += 1
        self.assertProblem(self.run_validator(), "boundary MIA: 47 other field conductors routed but terminals.json has 48")

    def test_undeclared_owner_card(self):
        self.specs["terminals"]["terminals"][100]["owner_card"] = "NOPE"
        self.assertProblem(self.run_validator(), "is not a declared module")

    def test_expansion_terminal_without_mx4(self):
        cfg = self.specs["allocations"]["configurations"][0]
        cfg["assignments"].append({"function": "Injected ninth motor", "resource_class": "motor", "channel": 9, "terminal": "XM9.1-14"})
        self.assertProblem(self.run_validator(), "expansion terminal XM9.1 used without MX4")

    def test_missing_revision(self):
        del self.specs["safety"]["spec_revision"]
        self.assertProblem(self.run_validator(), "spec/safety.json: top-level spec_revision is not IS-1")

    def test_fault_to_inhibit_over_20ms(self):
        csb = self.specs["safety"]["watchdogs"]["clock_stall_budget"]
        csb["wd_max_ms"] = 17.87
        csb["motion_total_ms"] = round(17.87 + csb["downstream_total_ms"], 2)
        self.assertProblem(self.run_validator(), "clock-stall fault-to-inhibit 22.18 ms exceeds 20 ms")


    # ---------------------------------------------------------------- repair-round checks
    def test_arm_latch_without_watchdog_clear_term(self):
        perm = self.specs["safety"]["permission"]
        perm["equations"] = [e for e in perm["equations"] if not e.startswith("latch_clear_O_n")] + ["latch_clear_O_n = out_base_ok AND FPGA_ENDPOINT_READY"]
        lat = next(l for l in perm["arm_latches"] if l["id"] == "arm_latch_O")
        lat["clear_terms"] = ["out_base_ok", "FPGA_ENDPOINT_READY"]
        self.assertProblem(self.run_validator(), "arm_latch_O clear terms", "arm_latch_O clear equation does not contain WD_O_OK")

    def test_permit_input_without_default(self):
        perm = self.specs["safety"]["permission"]
        perm["defaults"] = [d for d in perm["defaults"] if d["net"] != "EXT_PERMIT_3V3"]
        self.assertProblem(self.run_validator(), "hardware permission input EXT_PERMIT_3V3 has no defined absent-driver default")

    def test_permit_out_not_held_in_selftest(self):
        perm = self.specs["safety"]["permission"]
        c = next(c for c in perm["selftest_containment"] if "PERMIT_OUT" in c["receiver"])
        c["held_off_during_selftest_by"] = ""
        fan = next(f for f in perm["fanout"] if f["net"] == "TX_PERMIT")
        fan["receivers"] = [x.replace(", gated by PERMIT_OUT_REQ", "") for x in fan["receivers"]]
        self.assertProblem(self.run_validator(), "can act in the field during SELFTEST", "PERMIT_OUT receiver is not gated by PERMIT_OUT_REQ")

    def test_non_numeric_fault_bound(self):
        sc = next(x for x in self.specs["safety"]["fault_timing"]["scenarios"] if x["id"] == "logic_power_disturbance")
        sc["t_inhibit_max_ms"] = "supervisor delay + 4.31"
        self.assertProblem(self.run_validator(), "scenario logic_power_disturbance has no numeric t_inhibit_max_ms")

    def test_watchdog_leakage_dropped(self):
        csb = self.specs["safety"]["watchdogs"]["clock_stall_budget"]
        csb["wd_max_ms"] = 12.67
        csb["motion_total_ms"] = round(12.67 + csb["downstream_total_ms"], 2)
        self.assertProblem(self.run_validator(), "stated tWD(max) 12.67 ms != recomputed 13.02 ms")

    def test_field_budget_missing_load(self):
        fb = self.specs["safety"]["power_requirements"]["field"]["FIELD_B"]
        del fb["loads_a"]["arm_lamp"]
        self.assertProblem(self.run_validator(), "FIELD_B loads_a do not sum", "no budget item arm_lamp in entry FIELD_B")

    def test_undefined_fault_name_in_fault_state(self):
        p = self.specs["protocol"]
        p["fault_word"] = [f for f in p["fault_word"] if f["name"] != "CONTACTOR_FEEDBACK"]
        self.assertProblem(self.run_validator(), "terminal XS1.7 fault_state: fault or event name CONTACTOR_FEEDBACK is not defined")

    def test_two_writers_on_motor_pos_fb(self):
        cfg = next(c for c in self.specs["allocations"]["configurations"] if c["id"].startswith("E_"))
        m = next(a for a in cfg["assignments"] if a["resource_class"] == "motor" and a["channel"] == 5)
        m["hal"]["pos_fb"] = "cnc1.5.position-fb"
        self.assertProblem(self.run_validator(), "joint 5 motor-pos-fb written by cnc1.encoder.5.position and by cnc1.5.position-fb")

    def test_gantry_unequal_home_sequence(self):
        cfg = next(c for c in self.specs["allocations"]["configurations"] if c["id"].startswith("D_"))
        cfg["hal_map"]["homing_groups"] = [{"axis": "Y", "joints": [1], "home_sequence": -1}, {"axis": "Y", "joints": [2], "home_sequence": 2}] + \
            [g for g in cfg["hal_map"]["homing_groups"] if g["axis"] != "Y"]
        self.assertProblem(self.run_validator(), "gantry Y joints [1, 2] do not share one negative HOME_SEQUENCE")

    def test_mislabelled_pendant_selector(self):
        cfg = next(c for c in self.specs["allocations"]["configurations"] if c["id"].startswith("C_"))
        a = next(a for a in cfg["assignments"] if a["function"] == "Pendant axis select Z")
        a["terminal"], a["channel"] = "XH2.2", 1
        self.assertProblem(self.run_validator(), "'Pendant axis select Z' on XH2.2 (MPG_SEL_Y)")

    def test_bus_only_spindle(self):
        cfg = next(c for c in self.specs["allocations"]["configurations"] if c["id"].startswith("E_"))
        for sp in cfg["hal_map"]["spindles"]:
            sp["run_paths"] = []
        self.assertProblem(self.run_validator(), "spindle 0 has no hardware run path")

    def test_do_peak_without_relay(self):
        cfg = self.specs["allocations"]["configurations"][0]
        a = next(a for a in cfg["assignments"] if a["resource_class"] == "do" and a["channel"] == 11)
        a["peak_a"], a["via_relay"] = 1.5, False
        self.assertProblem(self.run_validator(), "DO11 peak 1.5 A exceeds the 0.62 A current-limit minimum")

    def test_xs13_advertised_as_spindle_permit(self):
        cfg = self.specs["allocations"]["configurations"][0]
        a = next(a for a in cfg["assignments"] if a["resource_class"] == "process_permit")
        a["function"] = "Process interlock chain (spindle/torch permit)"
        self.assertProblem(self.run_validator(), "XS1.3 advertised as a spindle permit")

    def test_di_stale_limit_beyond_published_age(self):
        self.specs["protocol"]["io_link"]["age_rules"]["din_stale_limit_us"]["max"] = 2540
        self.assertProblem(self.run_validator(), "din_stale_limit_us range 250-2540 us outside")

    def test_telemetry_priority_unbounded(self):
        self.specs["protocol"]["telemetry"]["worst_case_rotation_ms"] = 45
        self.specs["protocol"]["telemetry"]["mirror_entries_is1_default"] = 45
        self.specs["protocol"]["telemetry"].pop("worst_case_rotation_ms")
        self.assertProblem(self.run_validator(), "telemetry worst-case rotation != 2 x entries")

    def test_inverted_pwm_flag(self):
        f = next(f for f in self.specs["protocol"]["frames"]["configure_io_page1_at_16"] if f["name"] == "pwm0_flags")
        f["rule"] = "b0 inverted; b1-7 zero"
        self.assertProblem(self.run_validator(), "pwm0_flags still defines an inverted PWM mode")

    def test_diagnostic_without_physical_path(self):
        d = next(d for d in self.specs["protocol"]["diagnostics"] if d["signal"] == "Card power-good and presence")
        d["transport_refs"] = ["STS.slot_presence_nowhere"]
        self.assertProblem(self.run_validator(), "transport reference STS.slot_presence_nowhere resolves to no frame field")

    def test_pricing_off_rule(self):
        self.specs["modules"]["pricing"]["ex8"] = [89, 149]
        self.assertProblem(self.run_validator(), "modules.pricing.ex8 [89, 149] does not follow the stated rule")

    def test_undefined_service_rule_reference(self):
        rules = self.specs["service"]["validator_rules"]
        self.specs["service"]["validator_rules"] = [x for x in rules if x["id"] != "V-EL-12"]
        self.assertProblem(self.run_validator(), "validator rule V-EL-12 is referenced but not defined")

    def test_unhome_registered_per_channel(self):
        h = next(h for h in self.specs["protocol"]["hal_pins"] if h["name"] == "halui.joint.{jt}.unhome")
        h["name"] = "halui.joint.{m}.unhome"
        self.assertProblem(self.run_validator(), "halui unhome must be registered per joint index")


class RenderedDocuments(unittest.TestCase):
    def test_stale_rendered_document_is_reported(self):
        tmp = tempfile.mkdtemp(prefix="is1-render-")
        try:
            for d in ("spec", "docs", os.path.join("tools", "interface_spec")):
                shutil.copytree(os.path.join(ROOT, d), os.path.join(tmp, d))
            path = os.path.join(tmp, "docs", "interface-spec", "03-terminals-and-allocations.md")
            with open(path, "a", encoding="utf-8", newline="\n") as fh:
                fh.write("hand edit\n")
            problems = isv.validate(tmp, render=True, docs=False).problems
            self.assertTrue(any("03-terminals-and-allocations.md is not current" in p for p in problems), problems)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
