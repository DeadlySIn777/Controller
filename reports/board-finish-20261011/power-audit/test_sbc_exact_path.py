"""Cheap geometry fixtures for exact native endpoint preservation."""
import unittest
from shapely.geometry import box, LineString
from prepare_sbc_local_v5 import exact_path


class ExactNativeEndpoints(unittest.TestCase):
    def validate(self, free, start, goal):
        row = exact_path(free, start, goal)
        self.assertEqual(row["verdict"], "HOST_PATH", row)
        self.assertEqual(row["points"][0], list(start))
        self.assertEqual(row["points"][-1], list(goal))
        self.assertTrue(free.covers(LineString(row["points"])))
        return row

    def test_half_grid_endpoints_around_wall(self):
        free = box(0, 0, 4, 4).difference(box(1.9, 0, 2.1, 3))
        row = self.validate(free, (.35, .25), (3.65, .85))
        self.assertGreater(row["length_mm"], 5)

    def test_arbitrary_interior_goal_connector(self):
        free = box(0, 0, 4, 4).difference(box(1.9, 0, 2.1, 2.8))
        self.validate(free, (.35, .25), (3.97627198049912, 1.24496230218207))

    def test_blocked_endpoint_cannot_be_snapped_into_free_space(self):
        row = exact_path(box(0, 0, 4, 4), (-.01, 1.5), (3.65, .85))
        self.assertEqual(row["verdict"], "ENDPOINT_BLOCKED_IN_PLANNING_MASK")

    def test_disconnected_components_stay_disconnected(self):
        free = box(0, 0, 4, 4).difference(box(1.9, -.1, 2.1, 4.1))
        row = exact_path(free, (.35, .25), (3.65, .85))
        self.assertEqual(row["verdict"], "DISCONNECTED_FREE_COMPONENTS_IN_WINDOW")

    def test_direct_path_keeps_exact_coordinates(self):
        self.validate(box(0, 0, 4, 4), (.350001, .250002), (3.654321, .850003))


if __name__ == "__main__":
    unittest.main()
