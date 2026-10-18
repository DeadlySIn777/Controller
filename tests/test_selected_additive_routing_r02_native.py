"""Actual additive native copper, auto-stitch, source-land and fault fixtures."""
from pathlib import Path
import copy,json,shutil,sys,tempfile,unittest,uuid
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
try:
 import pcbnew
 import hardware_route_selected_additive_r02 as h
 from hardware_check_return_corridors import uid
 from test_motherboard_return_corridors import xy,pad,track,zone
except ModuleNotFoundError:pcbnew=None


def make_fixture(folder,bend=False,protect_bend_leg=False):
 """Small real six-layer source fixture, explicitly not a controller PCB."""
 b=pcbnew.BOARD();b.SetCopperLayerCount(6)
 nets={n:pcbnew.NETINFO_ITEM(b,n)for n in ['/DATA','/LOGIC_GND','/FIELD_B_0V','/RETAINED']}
 for n in nets.values():b.Add(n)
 pad(b,nets['/DATA'],'J1',(1,5),pcbnew.F_Cu);pad(b,nets['/DATA'],'J2',(9,5),pcbnew.B_Cu)
 pad(b,nets['/FIELD_B_0V'],'F1',(9,1),pcbnew.F_Cu)
 ground=pad(b,nets['/LOGIC_GND'],'G1',(5,7.0),pcbnew.F_Cu)
 ground.SetAttribute(pcbnew.PAD_ATTRIB_PTH);ground.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
 ground.GetParentFootprint().SetAttributes(pcbnew.FP_THROUGH_HOLE)
 ground.SetSize(xy(1.2,1.2));ground.SetDrillSize(xy(.6,.6));ground.SetLayerSet(pcbnew.LSET.AllCuMask())
 olda=pad(b,nets['/RETAINED'],'R1',(1,8.5),pcbnew.F_Cu)
 oldb=pad(b,nets['/RETAINED'],'R2',(9,8.5),pcbnew.F_Cu)
 old=track(b,nets['/RETAINED'],(1,8.5),(9,8.5),pcbnew.F_Cu)
 for layer in [pcbnew.In1_Cu,pcbnew.In4_Cu]:
  zone(b,nets['/LOGIC_GND'],layer,[(.3,.3),(9.7,.3),(9.7,9.7),(.3,9.7)])
 for a,c in [((0,0),(10,0)),((10,0),(10,10)),((10,10),(0,10)),((0,10),(0,0))]:
  edge=pcbnew.PCB_SHAPE(b);edge.SetShape(pcbnew.SHAPE_T_SEGMENT);edge.SetStart(xy(*a));edge.SetEnd(xy(*c))
  edge.SetLayer(pcbnew.Edge_Cuts);edge.SetWidth(pcbnew.FromMM(.05));b.Add(edge)
 # Real, nonempty fixture library identities are necessary for native SES
 # import; an empty image name creates invalid `(component )` session syntax.
 library=Path(folder)/'Native_Fixture.pretty';library.mkdir()
 for fp in b.GetFootprints():
  fp.SetFPID(pcbnew.LIB_ID('Native_Fixture',fp.GetReference()))
  if fp.GetReference()=='J2':fp.SetLayer(pcbnew.B_Cu)
  pcbnew.PCB_IO_KICAD_SEXPR().FootprintSave(str(library),fp)
 (Path(folder)/'fp-lib-table').write_text('(fp_lib_table (version 7)(lib (name "Native_Fixture")(type "KiCad")(uri "${KIPRJMOD}/Native_Fixture.pretty")(options "")(descr "Explicit toy native routing test lands")))\n',encoding='utf8')
 p=Path(folder)/'base.kicad_pcb';pcbnew.SaveBoard(str(p),b)
 rules=ROOT/'reports/motherboard-pcb-integration-20260930/current-source-population-r24f/motherboard-current-source-candidate'
 for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(rules.with_suffix(ext),p.with_suffix(ext))
 h.native_drc(p,Path(folder),'base-drc',refill=True)
 original=h.parse(p.read_text(encoding='utf8'));donor=copy.deepcopy(original);added=[]
 routes=[('segment','(start 1 5)(end 5 5)(width .2)(layer "F.Cu")')]
 routes+=([('segment','(start 5 5)(end 5.45 5.45)(width .2)(layer "B.Cu")'),
           ('segment','(start 5.45 5.45)(end 9 5)(width .2)(layer "B.Cu")')]if bend else
          [('segment','(start 5 5)(end 9 5)(width .2)(layer "B.Cu")')])
 routes+=[('via','(at 5 5)(size .6)(drill .3)(layers "F.Cu" "B.Cu")')]
 for kind,args in routes:
  ident=str(uuid.uuid4());added.append(ident)
  donor.append(h.parse('('+kind+' '+args+'(net "/DATA")(uuid "'+ident+'"))'))
 rows={'/DATA':dict(type='ordinary_logic',controlled_impedance=False,maximum_voltage_v=3.6,
  layers=['F.Cu','B.Cu'],reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},return_net='/LOGIC_GND',
  width_mm=.2,clearance_mm=.15,reference_corridor_margin_mm=.10,return_stitch_distance_mm=1.,
  allow_vias=True,via_diameter_mm=.6,via_drill_mm=.3)}
 merged,added=h.merge_tree(original,donor,rows)
 dest=Path(folder)/'candidate.kicad_pcb';dest.write_text(h.dump(merged)+'\n',encoding='utf8')
 for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2(p.with_suffix(ext),dest.with_suffix(ext))
 h.native_drc(dest,Path(folder),'signal-drc',refill=True)
 normalization=h.normalize_new_via_bends(dest,set(added)-({added[1]}if protect_bend_leg else set()),rows)
 if bend:
  if bool(normalization)==bool(protect_bend_leg):raise AssertionError('New-only bend protection failed')
 if normalization:
  added=[i for i in added if i not in {j for r in normalization for j in r['removed_new_segment_uuids']}]
  h.native_drc(dest,Path(folder),'normalized-drc',refill=True)
 h.write(Path(folder)/'normalization.json',normalization)
 ledger=h.add_return_stitches(dest,set(added),rows)
 drc=h.native_drc(dest,Path(folder),'final-drc',refill=True)
 fresh=h.parse(dest.read_text(encoding='utf8'));board=pcbnew.LoadBoard(str(dest));board.BuildConnectivity()
 if h.immutable_objects(original)!=h.immutable_objects(fresh):raise AssertionError('Actual old lands/source/zone definitions changed')
 before={h.value(h.child(t,'uuid')[1]):h.dump(t)for k in ('segment','via','arc')for t in h.children(original,k)}
 after={h.value(h.child(t,'uuid')[1]):h.dump(t)for k in ('segment','via','arc')for t in h.children(fresh,k)}
 if any(after.get(k)!=v for k,v in before.items()):raise AssertionError('Actual retained copper changed')
 expected={('J1','1'):'/DATA',('J2','1'):'/DATA',('G1','1'):'/LOGIC_GND',
           ('R1','1'):'/RETAINED',('R2','1'):'/RETAINED',('F1','1'):'/FIELD_B_0V'}
 actual={(p.GetParentFootprint().GetReference(),p.GetNumber()):p.GetNetname()for p in board.GetPads()}
 if actual!=expected:raise AssertionError('Actual fixture source-pad/net inventory changed')
 return board,set(added),rows,ledger,drc,dest


@unittest.skipUnless(pcbnew,'Requires actual KiCad native runtime/CLI')
class NativeSelectedAdditive(unittest.TestCase):
 def test_retained_via_actual_new_leg_gets_same_domain_stitch_proof(self):
  with tempfile.TemporaryDirectory()as folder:
   b,a,r,l,d,p=make_fixture(folder)
   via=l[0]['signal_via_uuid'];retained_scope=a-{via};ledger=copy.deepcopy(l)
   ledger[0]['signal_via_was_retained']=True
   self.assertEqual(1,h.validate_added_stitches(b,retained_scope,r,ledger)['actual_signal_vias'])
   self.assertTrue(h.return_corridor_check(b,retained_scope,r)['passed'])
 def test_unanchored_new_bend_is_corrected_with_actual_native_pass(self):
  with tempfile.TemporaryDirectory()as folder:
   b,a,r,l,d,p=make_fixture(folder,bend=True)
   self.assertTrue(h.return_corridor_check(b,a,r)['passed'])
   self.assertEqual(1,len(h.read(Path(folder)/'normalization.json')))
   self.assertEqual(0,d['regular_violations'])
 def test_a_protected_existing_leg_is_never_moved_to_hide_void(self):
  with tempfile.TemporaryDirectory()as folder:
   b,a,r,l,d,p=make_fixture(folder,bend=True,protect_bend_leg=True)
   with self.assertRaisesRegex(ValueError,'boundary, slot or hole'):h.return_corridor_check(b,a,r)
 def test_added_real_signal_via_gets_physical_source_connected_return(self):
  with tempfile.TemporaryDirectory()as folder:
   b,a,r,l,d,p=make_fixture(folder);proof=h.validate_added_stitches(b,a,r,l)
   self.assertTrue(h.return_corridor_check(b,a,r)['passed']);self.assertEqual(1,proof['new_return_stitches'])
   self.assertEqual(0,d['regular_violations']);self.assertEqual([],d['ignored_checks'])
   self.assertEqual(0,d['reported_unconnected_items'])
 def test_wrong_return_assignment_rejected(self):
  with tempfile.TemporaryDirectory()as folder:
   b,a,r,l,d,p=make_fixture(folder)
   v=next(t for t in b.GetTracks()if uid(t)==l[0]['added_stitch_uuid']);v.SetNet(b.FindNet('/FIELD_B_0V'))
   # The real native assignment is rejected BEFORE connectivity can infer its
   # old domain again from stale fill. The frozen corridor tests independently
   # exercise fully refilled foreign-domain geometry and source anchors.
   with self.assertRaisesRegex(ValueError,'Assigned native return-stitch net'):h.validate_added_stitches(b,a,r,l)
 def test_actual_stitch_geometry_change_rejected(self):
  with tempfile.TemporaryDirectory()as folder:
   b,a,r,l,d,p=make_fixture(folder)
   v=next(t for t in b.GetTracks()if uid(t)==l[0]['added_stitch_uuid']);v.SetDrill(pcbnew.FromMM(.2))
   with self.assertRaisesRegex(ValueError,'differs from'):h.validate_added_stitches(b,a,r,l)
 def test_every_new_signal_via_requires_exact_ledger(self):
  with tempfile.TemporaryDirectory()as folder:
   b,a,r,l,d,p=make_fixture(folder)
   with self.assertRaisesRegex(ValueError,'Every new signal via'):h.validate_added_stitches(b,a,r,[])
 def test_beyond_bound_and_changed_position_rejected(self):
  with tempfile.TemporaryDirectory()as folder:
   b,a,r,l,d,p=make_fixture(folder)
   v=next(t for t in b.GetTracks()if uid(t)==l[0]['added_stitch_uuid']);v.SetPosition(xy(5,6.5));b.BuildConnectivity()
   with self.assertRaises(ValueError):h.validate_added_stitches(b,a,r,l)


if __name__=='__main__':unittest.main()
