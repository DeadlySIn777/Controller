"""Bounded native empty-outline deletion and source-cluster invariants."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
try:
    import pcbnew
    import hardware_trim_empty_return_pockets as h
    from hardware_zone_motherboard_returns import add_zone,rectangle
except ModuleNotFoundError:pcbnew=None


@unittest.skipUnless(pcbnew,'Requires actual KiCad runtime')
class TrimPockets(unittest.TestCase):
    def fixture(self):
        b=pcbnew.BOARD();b.SetCopperLayerCount(6);b.Add(pcbnew.NETINFO_ITEM(b,'/LOGIC_GND'))
        z=add_zone(b,'/LOGIC_GND',rectangle([10,10,13,13]),pcbnew.In1_Cu,10,'EXPLICIT_EMPTY_GENERATED_FIXTURE')
        return b,z

    def test_only_explicitly_allowed_empty_zone_is_deleted(self):
        b,z=self.fixture();uid=z.m_Uuid.AsString();cut={('/LOGIC_GND',pcbnew.In1_Cu):rectangle([9,9,14,14])}
        r=h.trim(b,cut,{uid});self.assertEqual(len(b.Zones()),0);self.assertEqual(r['removed'][0]['uuid'],uid)

    def test_unreviewed_existing_zone_is_never_deleted(self):
        b,z=self.fixture();uid=z.m_Uuid.AsString();h.trim(b,{('/LOGIC_GND',pcbnew.In1_Cu):rectangle([9,9,14,14])},set())
        self.assertEqual(len(b.Zones()),1);self.assertEqual(list(b.Zones())[0].m_Uuid.AsString(),uid)

    def test_original_required_plane_cannot_be_deleted(self):
        from hardware_zone_motherboard_returns import LEGACY_SOURCE
        b=pcbnew.LoadBoard(str(LEGACY_SOURCE));uid=next(iter(h.LEGACY_ZONES));z=next(z for z in b.Zones()if z.m_Uuid.AsString()==uid)
        with self.assertRaises(ValueError):h.trim(b,{(z.GetNetname(),z.GetLayer()):rectangle([0,0,220,100])},{uid})

    def test_same_net_name_does_not_hide_a_split_actual_source_cluster(self):
        old=[dict(net='/LOGIC_GND',pad_UUIDs=['A','B'])]
        bad=[dict(net='/LOGIC_GND',pad_UUIDs=['A']),dict(net='/LOGIC_GND',pad_UUIDs=['B'])]
        self.assertFalse(h.clusters_survive(old,bad));self.assertTrue(h.clusters_survive(old,old))

    def test_other_ground_name_cannot_credit_source_cluster(self):
        self.assertFalse(h.clusters_survive([dict(net='/LOGIC_GND',pad_UUIDs=['A'])],[dict(net='/FIELD_B',pad_UUIDs=['A'])]))


if __name__=='__main__':unittest.main()
