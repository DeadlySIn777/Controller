from pathlib import Path
p=Path('reports/motherboard-critical-routing-20261001/review_actual_CCK_r06.py');s=p.read_text().replace("OUT=P/'actual-native-source-return-r01'","OUT=P/'actual-native-source-return-r02'")
start=s.index('cuts=[]');end=s.index("cap=pads['C1022','1']")
s=s[:start]+'''e.write(OUT/'signal-return-screen.json',dict(passes=results,failures=failures,actual_board_sha256=e.sha(BP),manufacturing_ready=False))
cuts=[]
cut_board=pcbnew.LoadBoard(str(BP));cut_board.BuildConnectivity();cut_parts={p.m_Uuid.AsString():p for f in cut_board.GetFootprints()for p in f.Pads()};cut_tracks={t.m_Uuid.AsString():t for t in cut_board.GetTracks()};a,z=[cut_parts[v]for v in plan['actual_Source_pad_UUIDs']]
for u in plan['new_signal_UUIDs']:
 t=cut_tracks[u];cut_board.Remove(t);cut_board.BuildConnectivity();cuts.append(dict(uuid=u,actual_native_SOURCE_pair_disconnected=not connected(cut_board,a,z)));cut_board.Add(t);cut_board.BuildConnectivity();assert connected(cut_board,a,z)
'''+s[end:]
Path('reports/motherboard-critical-routing-20261001/review_actual_CCK_r06_r02.py').write_text(s)
