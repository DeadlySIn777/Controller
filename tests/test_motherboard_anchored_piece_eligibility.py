"""Native negative controls prevent same-named isolated metal becoming return."""
from pathlib import Path
import copy,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(ROOT/'tests'))
try:
    import pcbnew
    import hardware_scope_anchored_reference_pieces as h
    import test_motherboard_return_plane_anchors as fixtures
except ModuleNotFoundError:pcbnew=None

@unittest.skipUnless(pcbnew,'Requires native KiCad runtime')
class AnchoredPieces(unittest.TestCase):
    def setUp(self):
        self.board,self.mapping=fixtures.ReturnAnchors().fixture(two_pieces=True)
        self.row=dict(return_net='/LOGIC_GND',reference_layers={'F.Cu':'In1.Cu'},
                      reference_corridor_margin_mm=.10,allow_vias=False)
        self.checker=h.SourceAnchoredPiecesCheck(self.board,{'/TEST_SIGNAL':self.row},self.mapping)
        self.board.Add(pcbnew.NETINFO_ITEM(self.board,'/TEST_SIGNAL'))

    def segment(self,a,b):
        t=pcbnew.PCB_TRACK(self.board);t.SetNet(self.board.FindNet('/TEST_SIGNAL'))
        t.SetWidth(pcbnew.FromMM(.20));t.SetLayer(pcbnew.F_Cu)
        t.SetStart(pcbnew.VECTOR2I(*(pcbnew.FromMM(v)for v in a)))
        t.SetEnd(pcbnew.VECTOR2I(*(pcbnew.FromMM(v)for v in b)))
        return t

    def test_real_SOURCE_piece_allows_route_while_global_failure_remains(self):
        r=self.checker.segment(self.segment((2.5,2),(3,2)),self.row)
        self.assertTrue(r['full_geometric_projected_corridor_covered'])
        self.assertFalse(self.checker.full_native_report['passed'])
        self.assertEqual(1,len(self.checker.full_native_report['unanchored_components']))

    def test_same_named_unanchored_piece_cannot_cover_signal(self):
        with self.assertRaisesRegex(ValueError,'reference boundary'):
            self.checker.segment(self.segment((10.5,2),(12,2)),self.row)

    def test_route_cannot_cross_gap_between_qualified_and_orphan_pieces(self):
        with self.assertRaisesRegex(ValueError,'reference boundary'):
            self.checker.segment(self.segment((3,2),(11,2)),self.row)

    def test_false_pass_without_literal_SOURCE_witness_rejected(self):
        report=copy.deepcopy(self.checker.full_native_report)
        report['filled_components'][1]['passed']=True
        with self.assertRaisesRegex(ValueError,'anchor'):
            h.eligible(report,{'/LOGIC_GND'},{'In1.Cu'})

    def test_foreign_domain_has_no_eligible_piece(self):
        with self.assertRaisesRegex(ValueError,'no real SOURCE'):
            h.eligible(self.checker.full_native_report,{'/motherboard_do/FIELD_B_0V'},{'In1.Cu'})

if __name__=='__main__':unittest.main()
