from pathlib import Path
folder=Path(__file__).parent/'native-fixture-r07'
folder.mkdir()
text=(Path(__file__).parent/'native-fixture-r06/build_fixture.py').read_text()
text=text.replace("('top','bottom','missing_reference','wrong_owner')","('top','bottom','missing_reference','wrong_owner','reference_slot')")
needle=" for a,c in[((0,0),(18,0)),((18,0),(18,12)),((18,12),(0,12)),((0,12),(0,0))]:"
replacement=""" if kind=='reference_slot':
  slot=pcbnew.ZONE(b);slot.SetIsRuleArea(True);slot.SetLayer(pcbnew.In1_Cu);slot.SetDoNotAllowCopperPour(True);slot.SetDoNotAllowTracks(False);slot.SetDoNotAllowVias(False);slot.SetDoNotAllowPads(False);slot.Outline().NewOutline()
  for pt in[(7.,3.2),(7.4,3.2),(7.4,7.),(7.,7.)]:slot.Outline().Append(pcbnew.FromMM(pt[0]),pcbnew.FromMM(pt[1]))
  b.Add(slot)
"""+needle
assert needle in text
(folder/'build_fixture.py').write_text(text.replace(needle,replacement))
