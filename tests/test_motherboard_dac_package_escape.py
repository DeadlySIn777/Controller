"""Real MSOP land/trace clearance, including early-splay and trunk-width negatives."""
from pathlib import Path
import copy,json,subprocess,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
try:
 import pcbnew
 import hardware_prepare_dac_package_escape as h
except ModuleNotFoundError:pcbnew=None
@unittest.skipUnless(pcbnew,'Actual KiCad native runtime required')
class PackageEscape(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=ROOT/'reports/motherboard-return-zoning-20261001/source26-r56-AO1-secondary-return-r04/motherboard-AO1-secondary-return-candidate.kicad_pcb'
  cls.base=pcbnew.LoadBoard(str(p));cls.dac=next(f for f in cls.base.GetFootprints()if f.GetReference()=='U14626')
  cls.review=h.engine.read(ROOT/h.critical.SOURCE_REVIEW);cls.project=p.with_suffix('.kicad_pro')
 def fixture(self,mode):
  folder=Path(self.tmp.name);board=pcbnew.BOARD();f=pcbnew.FOOTPRINT(self.dac);f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(20),pcbnew.FromMM(20)));board.Add(f)
  pads={p.GetNumber():p for p in f.Pads()}
  names={pin:p.GetNetname()for pin,p in pads.items()};nets={}
  for name in set(names.values()):
   n=pcbnew.NETINFO_ITEM(board,name);board.Add(n);nets[name]=n
  for pin,p in pads.items():p.SetNetCode(nets[names[pin]].GetNetCode())
  for pin in h.PINS:
   p=pads[pin];r=h.recipe(p,'U14626',self.review);points=r['points_mm']
   if mode=='early_splay':points=[points[0],points[-1]]
   for start,end in zip(points,points[1:]):
    t=pcbnew.PCB_TRACK(board);t.SetStart(pcbnew.VECTOR2I(*[pcbnew.FromMM(v)for v in start]));t.SetEnd(pcbnew.VECTOR2I(*[pcbnew.FromMM(v)for v in end]));t.SetLayer(pcbnew.F_Cu);t.SetWidth(pcbnew.FromMM(.35 if mode=='wide'else .2));t.SetNetCode(p.GetNetCode());board.Add(t)
  out=folder/(mode+'.kicad_pcb');pcbnew.SaveBoard(str(out),board)
  project=json.loads(self.project.read_text());out.with_suffix('.kicad_pro').write_text(json.dumps(project))
  out.with_suffix('.kicad_dru').write_text('(version 1)\n(rule "New neck clearance" (condition "A.Type == \'Track\' || B.Type == \'Track\'") (constraint clearance (min 0.20mm)))\n')
  report=folder/(mode+'.json');run=subprocess.run([str(h.engine.CLI),'pcb','drc','--format','json','--all-track-errors','--severity-all','--output',str(report),str(out)],capture_output=True,text=True,encoding='utf8',errors='replace')
  self.assertEqual(0,run.returncode,run.stderr);return json.loads(report.read_text())
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
 def test_native_correct_delayed_splay_clears_every_actual_adjacent_pad(self):
  r=self.fixture('bounded');errors=[v for v in r['violations']if v['severity']=='error'and v['type']in('clearance','shorting_items')]
  self.assertEqual([],errors)
 def test_native_trunk_width_cannot_exit_actual_pitch(self):
  r=self.fixture('wide');self.assertTrue(any(v['type']=='clearance'for v in r['violations']))
 def test_native_early_splay_is_rejected_instead_of_assuming_point_clearance(self):
  r=self.fixture('early_splay');self.assertTrue(any(v['type']=='clearance'for v in r['violations']))
 def test_wrong_pin_or_land_is_rejected_before_any_route_proposal(self):
  pads={p.GetNumber():p for p in self.dac.Pads()}
  with self.assertRaises(ValueError):h.recipe(pads['9'],'U14626',self.review)
  bad=pads['6'].Duplicate();bad.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.5),pcbnew.FromMM(.4)))
  with self.assertRaisesRegex(ValueError,'land changed'):h.recipe(bad,'U14626',self.review)
if __name__=='__main__':unittest.main()
