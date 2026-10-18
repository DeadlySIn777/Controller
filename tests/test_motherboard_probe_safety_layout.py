"""Actual native protected-front-end mutations; use KiCad's Python runtime."""
import importlib.util,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
try:
 import pcbnew
 from hardware_review_motherboard_probe_safety import check
except ImportError:pcbnew=None
BOARD=Path(os.environ.get('CONTROLLER_PROBE_SAFETY_TEST_BOARD',ROOT/'reports/motherboard-probe-safety-20261001/four-cell-placement-r04/motherboard-probe-safety-cells-candidate.kicad_pcb'))
@unittest.skipUnless(pcbnew is not None,'Requires actual KiCad pcbnew native runtime')
class ProbeSafetyLayout(unittest.TestCase):
 def setUp(self):
  self.board=pcbnew.LoadBoard(str(BOARD));self.fps={f.GetReference():f for f in self.board.GetFootprints()}
 def p(self,r,n):return next(p for p in self.fps[r].Pads()if p.GetNumber()==str(n))
 def test_actual_eight_source24_cells(self):self.assertEqual([],check(self.board)['errors'])
 def test_old_probe_IN_feed_is_rejected(self):
  self.p('R14069',2).SetNet(self.p('U14031',15).GetNet())
  self.assertTrue(any('RTHR must feed SENSE' in e for e in check(self.board)['errors']))
 def test_external_threshold_too_close_is_rejected(self):
  self.fps['R19001'].SetPosition(self.fps['U19001'].GetPosition()+pcbnew.VECTOR2I(pcbnew.FromMM(5.5),0))
  self.assertTrue(any('4mm protected spacing' in e for e in check(self.board)['errors']))
 def test_bypass_on_opposite_side_is_rejected(self):
  f=self.fps['C19006'];f.Flip(f.GetPosition(),pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
  self.assertTrue(any('own IC side' in e for e in check(self.board)['errors']))
 def test_field_sense_part_on_logic_side_is_rejected(self):
  self.fps['R19008'].SetPosition(self.fps['U19002'].GetPosition()+pcbnew.VECTOR2I(pcbnew.FromMM(-5.5),0))
  self.assertTrue(any('own field side' in e for e in check(self.board)['errors']))
 def test_CIN_wrong_field_return_is_rejected(self):
  self.p('C19001',2).SetNet(self.p('U14031',9).GetNet())
  self.assertTrue(any('own field domain' in e for e in check(self.board)['errors']))
 def test_SUB_island_short_is_rejected(self):
  self.p('U19003',12).SetNet(self.p('U19003',13).GetNet())
  self.assertTrue(any('independent floating SUB' in e for e in check(self.board)['errors']))
if __name__=='__main__':unittest.main()
