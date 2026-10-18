"""Meaningful host geometry controls, no native calls or source mutation."""
import json
import math
import time
from pathlib import Path
import unittest

import screen_c06 as S
from shapely.geometry import Point,LineString,box


class GeometryControls(unittest.TestCase):
    def route(self,free,a,b):
        p={'uuid':'physical-start','kind':'pad'};q={'uuid':'physical-end','kind':'track'}
        return S.astar(free,[(a,p)],[(b,q)],time.monotonic()+3,node_cap=10000)

    def test_half_grid_endpoints_retained_exactly(self):
        a=(.035,.047);b=(1.465,.753)
        path,search=self.route(box(-.1,-.1,1.6,.9),a,b)
        self.assertIsNotNone(path)
        self.assertEqual(path['points_mm'][0],list(a))
        self.assertEqual(path['points_mm'][-1],list(b))
        self.assertTrue(box(-.1,-.1,1.6,.9).covers(LineString(path['points_mm'])))

    def test_off_grid_connected_detour(self):
        free=box(-.1,-.1,2.1,1.1).difference(box(.7,-.1,1.3,.65))
        a=(.045,.053);b=(1.945,.049)
        path,search=self.route(free,a,b)
        self.assertIsNotNone(path)
        self.assertTrue(free.covers(LineString(path['points_mm'])))
        self.assertEqual(path['points_mm'][0],list(a));self.assertEqual(path['points_mm'][-1],list(b))

    def test_severed_components_refused(self):
        free=box(0,0,2,1).difference(box(.8,-1,1.2,2))
        path,search=self.route(free,(.1,.45),(1.9,.55))
        self.assertIsNone(path);self.assertEqual(search['reason'],'bounded open set exhausted')

    def test_blocked_exact_endpoint_cannot_snap_through_wall(self):
        free=box(0,0,2,1).difference(box(.03,.02,.09,.09))
        path,search=self.route(free,(.05,.05),(1.8,.5))
        self.assertIsNone(path)
        self.assertEqual(search['reason'],'no exact grid attachment')

    def test_diagonal_grid_shortcut_refused(self):
        free=box(0,0,.3,.3).difference(box(.045,.045,.055,.055))
        path,search=self.route(free,(0.,0.),(.1,.1))
        self.assertIsNotNone(path)
        self.assertTrue(free.covers(LineString(path['points_mm'])))
        self.assertGreater(LineString(path['points_mm']).length,math.sqrt(.02))

    def test_zero_budget_is_explicit(self):
        p={'uuid':'a','kind':'pad'};q={'uuid':'b','kind':'pad'}
        path,search=S.astar(box(0,0,20,20),[((.05,.05),p)],[((19.95,19.95),q)],time.monotonic()-1)
        self.assertIsNone(path);self.assertEqual(search['reason'],'time budget exhausted')


if __name__=='__main__':unittest.main(verbosity=2)
