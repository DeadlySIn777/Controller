from pathlib import Path
folder=Path(__file__).parent/'native-fixture-r06'
folder.mkdir()
text=(Path(__file__).parent/'native-fixture-r05/build_fixture.py').read_text()
old="anchor_track=pcbnew.PCB_TRACK(b);anchor_track.SetNet(nets['/LOGIC_GND']);anchor_track.SetLayer(pcbnew.F_Cu);anchor_track.SetStart(xy((5.95,5.95)));anchor_track.SetEnd(xy((14,9)));anchor_track.SetWidth(pcbnew.FromMM(.2));b.Add(anchor_track)"
new="""ground=next(p for f in b.GetFootprints() if f.GetReference()=='U1' for p in f.Pads() if p.GetNumber()=='3');start=ground.GetPosition();elbow=pcbnew.VECTOR2I(start.x,pcbnew.FromMM(9))
 for first,last in [(start,elbow),(elbow,xy((14,9)))]:
  anchor_track=pcbnew.PCB_TRACK(b);anchor_track.SetNet(nets['/LOGIC_GND']);anchor_track.SetLayer(pcbnew.F_Cu);anchor_track.SetStart(first);anchor_track.SetEnd(last);anchor_track.SetWidth(pcbnew.FromMM(.2));b.Add(anchor_track)"""
assert old in text
(folder/'build_fixture.py').write_text(text.replace(old,new))
