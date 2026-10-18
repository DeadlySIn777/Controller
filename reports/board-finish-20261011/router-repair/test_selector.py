"""Host checks for read-only eligibility. No KiCad or router calls."""
import copy
import unittest

from protected_net_selector import Selector, normalize, select_jobs


class SelectorControls(unittest.TestCase):
    def test_retained_critical_source_scopes_are_protected(self):
        names = ["/mc_motor_buffers{slash}DIR9_TO_MX4", "/STEP0_FPGA", "/DIR11_FPGA",
                 "/motherboard_operator/ENC0_A_FPGA", "/motherboard_operator/MPG_MUL_X1_ACTIVE",
                 "/motherboard_analog_input/AI0_BUFFERED", "/motherboard_analog_output/AO0_MON_5V",
                 "/fpga_core/FPGA_CDONE", "/mc_permission{slash}OUT_PERMIT",
                 "/watchdog_conditioning/WD_O_WDI_BUF", "/motherboard_safety_sensor/CONTACTOR_FB",
                 "/motherboard_motors/MOTOR8_LED_MID", "/motherboard_di/DI20_LOGIC",
                 "/motherboard_do/DO04_SW", "/motherboard_compute/CM_AUX_3V3",
                 "/motherboard_acc_control/ACC_MR_N", "/motherboard_comms/CAN_CTRL_CLOCK_RAW"]
        for name in names:
            with self.subTest(name=name):
                self.assertFalse(Selector().select(name)["eligible"])
                self.assertEqual(Selector().select(name)["disposition"], "protected")

    def test_top_level_critical_names_are_protected(self):
        for name in ("/TX_PERMIT", "/BANK_B_BUFFER_ENABLE_QUALIFIED", "/FPGA_USER_RESET_N",
                     "/ENC3_Z_FPGA", "/ALM9_FPGA", "/WD_M_HEALTH", "/CORE_1V2", "/IO_3V3", "/LOGIC_GND"):
            with self.subTest(name=name):
                self.assertEqual(Selector().select(name)["disposition"], "protected")

    def test_indicator_families_only_are_eligible(self):
        for name in ("/motherboard_status/RGB_DRIVER_18", "/motherboard_status/OBS27_K",
                     "/motherboard_status/OUT7_R_MID", "/motherboard_status/RGB_MOTION_G_K"):
            with self.subTest(name=name):
                self.assertTrue(Selector().select(name)["eligible"])

    def test_fault_indicator_and_unknown_status_names_require_protection_or_review(self):
        self.assertEqual(Selector().select("/motherboard_status/RGB_MOTION_HW_FAULT")["disposition"], "protected")
        self.assertEqual(Selector().select("/motherboard_status/RGB_MOTION_HW_RED")["disposition"], "review_required")
        self.assertFalse(Selector().select("/unrecognized_control")["eligible"])

    def test_exact_source_sets_override_ordinary_indicator_pattern(self):
        name = "/motherboard_status/OBS27_K"
        for field in ("plane_nets", "pair_nets", "power_nets", "zone_nets"):
            with self.subTest(field=field):
                self.assertEqual(Selector(**{field: [name]}).select(name)["disposition"], "protected")

    def test_slash_spelling_normalization_preserves_identity(self):
        self.assertEqual(normalize("/motherboard_status{slash}OBS27_K"), "/motherboard_status/OBS27_K")
        self.assertTrue(Selector().select("/motherboard_status{slash}OBS27_K")["eligible"])
        self.assertEqual(Selector(pair_nets=["/PAIR{slash}P"]).select("/PAIR/P")["disposition"], "protected")

    def test_no_input_job_mutation_or_hidden_jobs(self):
        jobs = [{"kind": "power", "net": "/motherboard_status/OBS27_K"},
                {"kind": "power", "net": "/STEP0_FPGA"},
                {"kind": "power", "net": "/uncategorized"}]
        before = copy.deepcopy(jobs)
        eligible, withheld = select_jobs(jobs, Selector())
        self.assertEqual(jobs, before)
        self.assertEqual([x["source_job_index"] for x in eligible], [1])
        self.assertEqual([x["source_job_index"] for x in withheld], [2, 3])
        self.assertEqual(len(eligible) + len(withheld), len(jobs))

    def test_invalid_source_identity_refuses(self):
        for name in (None, "", 1, False):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    Selector().select(name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
