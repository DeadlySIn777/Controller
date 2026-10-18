"""Cheap independent rejection fixtures; no source/native-board reads."""
import unittest
from shapely.geometry import Point, box, mapping
import prepare_sbc_local_v6 as six


class HoleEnvelope(unittest.TestCase):
    def test_power_via_excludes_copper_radius_not_drill_radius(self):
        g = {"pads": [], "vias": [{"x": 0, "y": 0, "drill": .3}]}
        mask = six.copper_hole_obstructions(g, box(-2, -2, 2, 2), .6)
        self.assertTrue(mask.covers(Point(.65, 0)))
        self.assertFalse(mask.covers(Point(.726, 0)))

    def test_signal_small_via_still_uses_copper_radius(self):
        g = {"pads": [], "vias": [{"x": 0, "y": 0, "drill": .3}]}
        mask = six.copper_hole_obstructions(g, box(-2, -2, 2, 2), .5)
        self.assertTrue(mask.covers(Point(.6, 0)))
        self.assertFalse(mask.covers(Point(.676, 0)))

    def test_npth_edge_to_copper_gap(self):
        g = {"pads": [{"hole": [[list(box(-.5, -.5, .5, .5).exterior.coords), []]]}], "vias": []}
        mask = six.copper_hole_obstructions(g, box(-2, -2, 2, 2), .6)
        self.assertTrue(mask.covers(Point(1.0, 0)))
        self.assertFalse(mask.covers(Point(1.076, 0)))

    def test_same_net_holes_not_exempt(self):
        g = {"pads": [], "vias": [{"x": 0, "y": 0, "drill": .3, "net": "/LOGIC_GND"}]}
        self.assertTrue(six.copper_hole_obstructions(g, box(-2, -2, 2, 2), .6).covers(Point(.65, 0)))


if __name__ == "__main__":
    unittest.main()
