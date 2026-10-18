"""Real KiCad native cell-role, source-invariant and open-loop negatives."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
try:
    import pcbnew
    import hardware_route_motherboard_iso1212_cells as h
except ModuleNotFoundError:pcbnew=None


@unittest.skipUnless(pcbnew,'Requires actual KiCad pcbnew runtime')
class LocalISO1212(unittest.TestCase):
    def board(self):
        return pcbnew.LoadBoard(str(h.ROOT/'reports/motherboard-return-zoning-20261001/iso1212-local-fixture-r04/fixture-source.kicad_pcb'))

    def pad(self,b,r,p):return next(x for f in b.GetFootprints()if f.GetReference()==r for x in f.Pads()if x.GetNumber()==str(p))

    def test_actual_all16_cells_preserve_local_lands_and_close242_groups(self):
        b=self.board();old=h.land_inventory(b);rows=h.apply(b)
        self.assertEqual(h.land_inventory(b),old);self.assertEqual(len(rows['exact_passive_pose_changes']),60)
        pcbnew.ZONE_FILLER(b).Fill(b.Zones());proof=h.validate_local(b,rows['local_endpoint_checks'])
        self.assertTrue(proof['passed']);self.assertEqual(proof['checked_local_endpoint_groups'],242)
        self.assertEqual(len(rows['actual_receiving_IO3_vias']),16)
        self.assertTrue(h.validate_spacing(b)['passed'])

    def test_wrong_field_return_cannot_be_credited_as_local_return(self):
        b=self.board();self.pad(b,'C8001',2).SetNet(b.FindNet('/LOGIC_GND'))
        with self.assertRaises(ValueError):h.apply(b,{'U8001'})

    def test_retained_invalid_probe_RTHR_IN_mapping_is_rejected(self):
        b=self.board();self.pad(b,'R14069',2).SetNet(self.pad(b,'U14031',15).GetNet())
        with self.assertRaises(ValueError):h.apply(b,{'U14031'})

    def test_wrong_RSENSE_terminal_order_is_not_automatically_accepted(self):
        b=self.board();a=self.pad(b,'R8101',1);q=self.pad(b,'R8101',2);an,qn=a.GetNet(),q.GetNet();a.SetNet(qn);q.SetNet(an)
        with self.assertRaises(ValueError):h.apply(b,{'U8001'})

    def test_changed_old_passive_pose_requires_new_electrical_review(self):
        b=self.board();f=next(f for f in b.GetFootprints()if f.GetReference()=='C8001');f.SetPosition(h.xy((32,170)))
        with self.assertRaises(ValueError):h.apply(b,{'U8001'})

    def test_changed_ISO_side_cannot_reuse_front_recipe(self):
        b=self.board();f=next(f for f in b.GetFootprints()if f.GetReference()=='U8001');f.SetOrientationDegrees(180)
        with self.assertRaises(ValueError):h.apply(b,{'U8001'})

    def test_RTHR_external_spacing_is_an_actual_copper_edge_check(self):
        b=self.board();h.apply(b,{'U8001'});f=next(f for f in b.GetFootprints()if f.GetReference()=='R8001');p=h.mm(f.GetPosition());f.SetPosition(h.xy((p[0]-5,p[1])))
        self.assertFalse(h.validate_spacing(b,[h.recipes()[0]])['passed'])

    def test_removed_CIN_loop_branch_is_not_hidden_by_net_name(self):
        b=self.board();rows=h.apply(b,{'U8001'});first=next(x for x in rows['exact_added_copper']if x['kind']=='compact_CIN_SENSE')
        item=next(t for t in b.GetTracks()if t.m_Uuid.AsString()==first['uuid']);b.Remove(item)
        pcbnew.ZONE_FILLER(b).Fill(b.Zones());self.assertFalse(h.validate_local(b,rows['local_endpoint_checks'])['passed'])


if __name__=='__main__':unittest.main()
