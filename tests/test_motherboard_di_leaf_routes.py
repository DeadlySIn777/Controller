"""Shared return trunks cannot be mistaken for moved-capacitor leaf routes."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from hardware_di_leaf_routes import leaf_branches


class LeafProof(unittest.TestCase):
    def test_leaf_stops_at_shared_junction(self):
        a,b,c,d,e=[(i,0,0) for i in range(5)]
        edges={'leaf1':(a,b),'leaf2':(b,c),'trunk':(c,d),'other':(c,e)}
        removed,proof=leaf_branches(edges,{a})
        self.assertEqual(removed,{'leaf1','leaf2'})
        self.assertEqual(proof[0]['retained_boundary'],list(c))
        self.assertEqual(proof[0]['boundary_degree'],3)

    def test_unmoved_pad_anchor_stops_branch(self):
        a,b,c=[(i,0,0) for i in range(3)]
        removed,_=leaf_branches({'leaf':(a,b),'preserved':(b,c)},{a},{b})
        self.assertEqual(removed,{'leaf'})

    def test_touching_shared_junction_does_not_remove_anything(self):
        a,b,c=[(i,0,0) for i in range(3)]
        removed,_=leaf_branches({'left':(a,b),'right':(b,c)},{b})
        self.assertFalse(removed)

    def test_via_anchor_is_retained(self):
        a,b,c=[(i,0,0) for i in range(3)]
        removed,_=leaf_branches({'leaf':(a,b),'trunk':(b,c)},{a},{b})
        self.assertEqual(removed,{'leaf'})

    def test_middle_of_segment_unmodified_pad_blocks_removal(self):
        a,b,c=[(i,0,0) for i in range(3)]
        removed,_=leaf_branches({'leaf':(a,b),'touches_pad':(b,c)},{a},protected={'touches_pad'})
        self.assertEqual(removed,{'leaf'})

    def test_cross_layer_vertices_are_not_equivalent(self):
        a,b=(0,0,0),(1,0,0);c,d=(1,0,31),(2,0,31)
        removed,_=leaf_branches({'front':(a,b),'back':(c,d)},{a})
        self.assertEqual(removed,{'front'})

    def test_zero_length_unreviewed_edge_rejected(self):
        with self.assertRaises(ValueError):leaf_branches({'bad':((0,0,0),(0,0,0))},{(0,0,0)})


if __name__=='__main__':unittest.main()
