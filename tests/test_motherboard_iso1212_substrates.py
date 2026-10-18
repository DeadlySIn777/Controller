"""Native source identity and separate-substrate thermal geometry checks."""
import copy,json,os
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
try:
    import pcbnew
    import hardware_add_iso1212_substrates as h
except ModuleNotFoundError:pcbnew=None
ROOT=Path(__file__).resolve().parents[1]
MAP=ROOT/'reports/motherboard-return-zoning-20261001/r40-actual-domain-map-r01/domain-map.json'
BOARD=ROOT/'reports/motherboard-pcb-integration-20261001/probe-motor-y2-source24-merge-r40/motherboard-bounded-merged-candidate.kicad_pcb'


@unittest.skipUnless(pcbnew,'Requires actual KiCad native runtime')
class Substrates(unittest.TestCase):
    def setUp(self):
        self.board=pcbnew.LoadBoard(str(BOARD));self.mapping=json.loads(MAP.read_text())

    def test_real_source_has_exact44_independent_SUB_islands(self):
        rows=h.substrate_recipe(self.board,self.mapping)
        self.assertEqual(len(rows),44);self.assertEqual(len({r['net']for r in rows}),44)
        for r in rows:
            a,b,c,d=r['zone_bounds_mm'];self.assertAlmostEqual(c-a,2.010);self.assertAlmostEqual(d-b,2.010)
            #The horizontal own-pad escape must precede the diagonal via leg;
            #a direct diagonal could hit the neighbouring FGND land.
            self.assertEqual(r['segment_points_mm'][0][1],r['segment_points_mm'][1][1])

    def test_wrong_source_pin_cannot_receive_SUB_copper(self):
        p=next(p for p in self.mapping['pads']if p['domain'].startswith('SUB:'));p['pin']='14'
        with self.assertRaises(ValueError):h.substrate_recipe(self.board,self.mapping)

    def test_same_net_two_SUB_pads_is_rejected(self):
        p=[p for p in self.mapping['pads']if p['domain'].startswith('SUB:')];p[0]['net']=p[1]['net']
        with self.assertRaises(ValueError):h.substrate_recipe(self.board,self.mapping)

    def test_native_land_change_requires_new_review(self):
        fp=next(f for f in self.board.GetFootprints()if f.GetReference()=='U8001')
        p=next(p for p in fp.Pads()if p.GetNumber()=='12');p.SetSize(pcbnew.VECTOR2I(1500000,410000))
        with self.assertRaises(ValueError):h.substrate_recipe(self.board,self.mapping)

    def test_wrong_component_side_requires_new_review(self):
        fp=next(f for f in self.board.GetFootprints()if f.GetReference()=='U8001');fp.Flip(fp.GetPosition(),False)
        with self.assertRaises(ValueError):h.substrate_recipe(self.board,self.mapping)


if __name__=='__main__':unittest.main()
