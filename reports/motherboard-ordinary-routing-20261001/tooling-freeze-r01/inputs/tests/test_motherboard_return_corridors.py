"""Real six-layer native-fill tests for signal-via return exceptions."""
from pathlib import Path
import json,shutil,subprocess,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
try:
 import pcbnew
 import hardware_check_return_corridors as h
except ModuleNotFoundError:pcbnew=None
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')


def xy(x,y):return pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))


def track(board,net,a,b,layer,width=.20):
 t=pcbnew.PCB_TRACK(board);t.SetNet(net);t.SetStart(xy(*a));t.SetEnd(xy(*b));t.SetLayer(layer);t.SetWidth(pcbnew.FromMM(width));board.Add(t);return t


def via(board,net,p):
 v=pcbnew.PCB_VIA(board);v.SetNet(net);v.SetPosition(xy(*p));v.SetWidth(pcbnew.FromMM(.60));v.SetDrill(pcbnew.FromMM(.30));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);board.Add(v);return v


def pad(board,net,ref,p,layer):
 fp=pcbnew.FOOTPRINT(board);fp.SetReference(ref);fp.SetValue('native-test-pad');fp.SetAttributes(pcbnew.FP_SMD);fp.SetPosition(xy(*p));fp.Reference().SetVisible(False);fp.Value().SetVisible(False)
 q=pcbnew.PAD(fp);q.SetNumber('1');q.SetAttribute(pcbnew.PAD_ATTRIB_SMD);q.SetShape(pcbnew.PAD_SHAPE_RECT);q.SetSize(xy(.60,.70));q.SetPosition(xy(*p));q.SetNet(net)
 mask=pcbnew.LSET();mask.AddLayer(layer);mask.AddLayer(pcbnew.F_Mask if layer==pcbnew.F_Cu else pcbnew.B_Mask);mask.AddLayer(pcbnew.F_Paste if layer==pcbnew.F_Cu else pcbnew.B_Paste);q.SetLayerSet(mask);fp.Add(q)
 border=pcbnew.PCB_SHAPE(fp);border.SetShape(pcbnew.SHAPE_T_RECT);border.SetStart(xy(p[0]-.55,p[1]-.60));border.SetEnd(xy(p[0]+.55,p[1]+.60));border.SetLayer(pcbnew.F_CrtYd if layer==pcbnew.F_Cu else pcbnew.B_CrtYd);border.SetWidth(pcbnew.FromMM(.05));fp.Add(border)
 board.Add(fp);return q


def zone(board,net,layer,points,rule=False):
 z=pcbnew.ZONE(board);z.SetLayer(layer);z.SetLocalClearance(pcbnew.FromMM(.25));z.SetMinThickness(pcbnew.FromMM(.20));z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
 if rule:z.SetIsRuleArea(True);z.SetDoNotAllowZoneFills(True);z.SetDoNotAllowTracks(False);z.SetDoNotAllowVias(False);z.SetDoNotAllowPads(False);z.SetDoNotAllowFootprints(False)
 else:z.SetNet(net)
 z.Outline().NewOutline()
 for x,y in points:z.Outline().Append(pcbnew.FromMM(x),pcbnew.FromMM(y))
 board.Add(z);return z


def fixture(folder,kind='healthy'):
 b=pcbnew.BOARD();b.SetCopperLayerCount(6)
 nets={n:pcbnew.NETINFO_ITEM(b,n)for n in ['/DATA','/LOGIC_GND','/FIELD_B_0V']}
 for n in nets.values():b.Add(n)
 pad(b,nets['/DATA'],'J1',(1,5),pcbnew.F_Cu);pad(b,nets['/DATA'],'J2',(9,5),pcbnew.B_Cu)
 anchor_net=nets['/FIELD_B_0V']if kind=='wrong_domain'else nets['/LOGIC_GND']
 pad(b,anchor_net,'G1',(5,7.5),pcbnew.F_Cu)
 signal=via(b,nets['/DATA'],(5,5))
 a=track(b,nets['/DATA'],(1,5),(5,5),pcbnew.F_Cu);c=track(b,nets['/DATA'],(5,5),(9,5),pcbnew.B_Cu)
 stitch_position=(5,6.15)if kind=='too_far'else(5,5.99)if kind=='one_side_open'else(5,5.85)
 stitch=via(b,anchor_net,stitch_position)
 if kind!='name_only':track(b,anchor_net,stitch_position,(5,7.5),pcbnew.F_Cu)
 for layer in [pcbnew.In1_Cu,pcbnew.In4_Cu]:
  n=nets['/FIELD_B_0V']if kind=='wrong_reference'and layer==pcbnew.In4_Cu else nets['/LOGIC_GND']
  zone(b,n,layer,[(.3,.3),(9.7,.3),(9.7,9.7),(.3,9.7)])
 if kind=='slot':zone(b,None,pcbnew.In4_Cu,[(6.2,4.5),(6.4,4.5),(6.4,5.5),(6.2,5.5)],True)
 if kind=='large_hole':
  for layer in [pcbnew.In1_Cu,pcbnew.In4_Cu]:zone(b,None,layer,[(4.2,4.2),(5.8,4.2),(5.8,5.8),(4.2,5.8)],True)
 if kind=='one_side_open':zone(b,None,pcbnew.In4_Cu,[(4.85,5.86),(5.15,5.86),(5.15,6.16),(4.85,6.16)],True)
 for a0,c0 in [((0,0),(10,0)),((10,0),(10,10)),((10,10),(0,10)),((0,10),(0,0))]:
  edge=pcbnew.PCB_SHAPE(b);edge.SetShape(pcbnew.SHAPE_T_SEGMENT);edge.SetStart(xy(*a0));edge.SetEnd(xy(*c0));edge.SetLayer(pcbnew.Edge_Cuts);edge.SetWidth(pcbnew.FromMM(.05));b.Add(edge)
 p=Path(folder)/'native.kicad_pcb';pcbnew.SaveBoard(str(p),b)
 # Use the reviewed board's real complete rule severities, rather than KiCad's
 # default five ignored categories. No exception is introduced by this fixture.
 rules=ROOT/'reports/motherboard-pcb-integration-20260930/current-source-population-r24f/motherboard-current-source-candidate'
 for suffix in ['.kicad_pro','.kicad_dru']:shutil.copy2(rules.with_suffix(suffix),p.with_suffix(suffix))
 command=[str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(Path(folder)/'drc.json'),str(p)]
 r=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace')
 (Path(folder)/'native-command.txt').write_text(r.stdout+'\n'+r.stderr,encoding='utf-8')
 if not(Path(folder)/'drc.json').is_file():raise RuntimeError(r.stdout+r.stderr)
 drc=json.loads((Path(folder)/'drc.json').read_text(encoding='utf-8'))
 fresh=pcbnew.LoadBoard(str(p));fresh.BuildConnectivity()
 rows={'/DATA':dict(type='ordinary_logic',layers=['F.Cu','B.Cu'],reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},
  return_net='/LOGIC_GND',reference_corridor_margin_mm=.10,return_stitch_distance_mm=1.0,
  allow_vias=True,via_diameter_mm=.60,via_drill_mm=.30)}
 return fresh,{h.uid(v)for v in [signal,a,c]},rows,drc


@unittest.skipUnless(pcbnew,'Requires the actual KiCad pcbnew runtime and native CLI')
class ReturnCorridors(unittest.TestCase):
 def run_kind(self,kind):
  with tempfile.TemporaryDirectory()as folder:
   b,added,rows,drc=fixture(folder,kind)
   return h.return_corridor_check(b,added,rows),drc

 def test_real_endpoint_antipads_accept_connected_both_side_stitch(self):
  with tempfile.TemporaryDirectory()as folder:
   b,added,rows,drc=fixture(folder)
   from hardware_route_selected_additive import return_corridor_check as frozen_old_check
   with self.assertRaisesRegex(ValueError,'boundary, slot or hole'):frozen_old_check(b,added,rows)
   receipt=h.return_corridor_check(b,added,rows)
  self.assertTrue(receipt['passed']);self.assertEqual(receipt['new_copper_items_checked'],3)
  self.assertEqual(drc.get('ignored_checks',[]),[])
  self.assertEqual(drc.get('violations',[]),[])
  self.assertEqual(len([r for r in receipt['items']if r.get('signal_via_uuid')]),1)

 def test_wrong_domain_stitch_cannot_hide_reference_void(self):
  with self.assertRaisesRegex(ValueError,'own-return annulus|physically connected same-domain'):self.run_kind('wrong_domain')

 def test_actual_reference_plane_must_exist_on_both_sides(self):
  with self.assertRaisesRegex(ValueError,'own-reference plane is absent'):self.run_kind('wrong_reference')

 def test_same_net_name_without_source_pad_connection_is_rejected(self):
  with self.assertRaisesRegex(ValueError,'physically connected same-domain'):self.run_kind('name_only')

 def test_stitch_beyond_1mm_is_rejected(self):
  with self.assertRaisesRegex(ValueError,'physically connected same-domain'):self.run_kind('too_far')

 def test_slot_away_from_endpoint_is_not_an_antipad_exception(self):
  with self.assertRaisesRegex(ValueError,'boundary, slot or hole'):self.run_kind('slot')

 def test_large_hole_at_endpoint_fails_actual_annulus(self):
  with self.assertRaisesRegex(ValueError,'continuous own-return annulus'):self.run_kind('large_hole')

 def test_stitch_nearby_with_one_side_reference_keepout_is_rejected(self):
  with self.assertRaisesRegex(ValueError,'physically connected same-domain'):self.run_kind('one_side_open')

 def test_manifest_via_geometry_cannot_be_substituted(self):
  with tempfile.TemporaryDirectory()as folder:
   b,added,rows,drc=fixture(folder);rows['/DATA']['via_drill_mm']=.20
   with self.assertRaisesRegex(ValueError,'geometry differs'):h.return_corridor_check(b,added,rows)


if __name__=='__main__':unittest.main()
