from pathlib import Path
p=Path(__file__).parent
s=(p/'review-same-side-cache-r01.py').read_text()
s=s.replace('same-side-native-cache-controls-r01.json','same-side-native-cache-controls-r02.json')
s=s.replace("and z.HasFilledPolysForLayer(pcbnew.In1_Cu))", "and z.HasFilledPolysForLayer(pcbnew.In1_Cu)and z.GetFilledPolysList(pcbnew.In1_Cu).OutlineCount()>0)")
s=s.replace("z.UnFill();rejected('refill_removed_after_cache')", "z.UnFill();assert board_geometry_digest(b)!=c._board_digest, 'Negative must actually alter a nonempty reference resource';rejected('refill_removed_after_cache')")
(p/'review-same-side-cache-r02.py').write_text(s)
