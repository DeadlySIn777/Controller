"""Protect reset polarity, bank separation, default and independent TX paths."""
import copy, json, sys
from pathlib import Path
import pytest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from hardware_build_assembly import parse
from hardware_apply_motherboard_health_source import apply_health_source
from hardware_apply_motor_feed_reset import apply_feed_reset, feed_reset_screen
from hardware_validate_motor_feed_reset import validate, native_nodes, stable_rail_latch, validate_native_functions

@pytest.fixture(scope="module")
def circuit():
    source = ROOT / "reports/motherboard-power-entry-20261001/feed-latch-reset-source-r01/source26-input-fixture"
    model = json.loads((source / "design.json").read_text())
    trees = {k: parse((source / (k + ".kicad_sch")).read_text())
             for k in ("mc_local_power", "motherboard_power_entry")}
    ht, hm, _ = apply_health_source(trees, model)
    t, m, receipt = apply_feed_reset(ht, hm)
    return ht, hm, t, m, receipt

def test_exact_additive_transform_and_source_immutability(circuit):
    ht, hm, t, m, _ = circuit
    snapshot = copy.deepcopy((ht, hm))
    assert validate(m, hm)["consistency_pass"]
    apply_feed_reset(ht, hm)
    assert (ht, hm) == snapshot
    assert m["physical_footprints"] - hm["physical_footprints"] == 10

@pytest.mark.parametrize("ref,pin,wrong", [
    ("U11035", "1", "MOTOR_FEED_CLEAR_N_B"),
    ("U11037", "1", "MOTOR_FEED_CLEAR_N_A"),
    ("U11035", "3", "MOTOR_FEED_CLEAR_N_A"),
    ("U11035", "4", "LOGIC_GND"),
    ("U11036", "5", "IO_3V3"),
    ("U11036", "4", "MOTOR_FEED_CLEAR_FAST_N_B"),
    ("R11082", "2", "FIELD_GND"),
    ("U11032", "6", "MOTOR_FEED_CLEAR_N_A"),
    ("U11024", "3", "MOTOR_FEED_ON_A"),
])
def test_tampered_bank_domain_reset_or_direct_inhibit_is_rejected(circuit, ref, pin, wrong):
    _, hm, _, m, _ = circuit
    bad = copy.deepcopy(m)
    bad["components"][ref]["pins"][pin] = wrong
    assert not validate(bad, hm)["consistency_pass"]

def test_missing_output_default_is_rejected(circuit):
    _, hm, _, m, _ = circuit
    bad = copy.deepcopy(m)
    del bad["components"]["R11082"]
    assert not validate(bad, hm)["consistency_pass"]

def test_original_one_k_pullup_and_high_off_leakage_fail():
    assert feed_reset_screen(1000)["source_min_ohm"] < 10000
    assert feed_reset_screen(off_leak=20e-6)["off_node_screen_v"] > 1.51

def test_correct_g50_accuracy_and_loaded_conditions_not_interpolated():
    s = feed_reset_screen()
    assert s["reset_threshold_corner_v"] == pytest.approx([4.58025, 4.71975])
    assert s["reset_max_positive_release_threshold_screen_v"] == pytest.approx(4.836)
    assert s["actual_RESET_node_load_different_from_timing_test"]
    assert not s["fast_output_edge_measured_qualification"]
    assert not s["reset_low_hold_during_intermediate_rail_slew_qualification"]

@pytest.mark.parametrize("index", range(4))
def test_each_actual_clear_prerequisite_drops_q(index):
    states = [True] * 4
    states[index] = False
    assert stable_rail_latch(True, *states, True) is False

def test_por_release_does_not_restart_without_new_rearm_edge():
    assert stable_rail_latch(True, False, False, True, True, False) is False
    assert stable_rail_latch(False, True, True, True, True, False) is False
    assert stable_rail_latch(False, True, True, True, True, True) is True

def test_native_candidate_exact_pin_delta(circuit):
    _, hm, _, _, _ = circuit
    candidate = ROOT / "reports/motherboard-power-entry-20261001/feed-latch-reset-source-r01/candidate-r04/motherboard"
    if not candidate.exists(): pytest.skip("Newest independent native candidate not generated")
    m = json.loads((candidate / "design.json").read_text())
    before = native_nodes(ROOT / "reports/motherboard-power-entry-20261001/feed-latch-reset-source-r01/source26-input-fixture/netlist.xml")
    assert validate(m, hm, native_nodes(candidate / "netlist.xml"), before)["consistency_pass"]

def test_native_primary_functions_and_swapped_supervisor_pin_rejected(tmp_path):
    import xml.etree.ElementTree as ET
    p = ROOT / "reports/motherboard-power-entry-20261001/feed-latch-reset-source-r01/candidate-r04/motherboard/netlist.xml"
    assert validate_native_functions(p)["consistency_pass"]
    tree = ET.parse(p)
    tree.find('.//libparts/libpart[@lib="CNC_MB_FeedReset"][@part="FEED_POR"]/pins/pin[@num="5"]').set("name", "VDD")
    wrong = tmp_path / "wrong-supervisor.xml"
    tree.write(wrong)
    assert not validate_native_functions(wrong)["consistency_pass"]
