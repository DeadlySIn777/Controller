from pathlib import Path
p=Path(__file__).with_name('stationary_three_real_cut_case_r01.py')
q=p.with_name('stationary_three_real_cut_case_r02.py')
assert not q.exists()
s=p.read_text()
old="power_via=next(tracks[u]for u in group['new_UUIDs']if tracks[u].Type()==pcbnew.PCB_VIA_T and tracks[u].GetNetname()==cp.GetNetname())"
new="""if a.reload:
    assert sha(dest)==meta['board_sha256'],'Persisted actual cut changed'
    assert set(group['new_UUIDs'])-set(tracks)=={uid},'Unexpected additional group Cu loss'
power_via=next(tracks[u]for u in group['new_UUIDs']if u in tracks and tracks[u].Type()==pcbnew.PCB_VIA_T and tracks[u].GetNetname()==cp.GetNetname())"""
assert s.count(old)==1
s=s.replace(old,new).replace("'.fresh-native-review.json'if a.reload", "'.fresh-native-review-r02.json'if a.reload")
q.write_text(s)
q.with_suffix('.reason.txt').write_text('R01 fresh reload attempted to resolve an intentionally deleted group UUID before choosing its retained power via. R02 checks the exact saved cut SHA and exactly one bounded missing group UUID, then resolves only retained physical objects. No board, positive proof or original generator changed. The nine previous KeyError failures remain historical execution evidence.\n')
