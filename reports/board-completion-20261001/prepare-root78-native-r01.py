from pathlib import Path
p=Path(__file__).parent/'native-skipped-cases-r01/run_native.py'
d=p.parent.parent/'source26-root78-native-r01';d.mkdir()
s=p.read_text().replace("sys.path[:0]=[str(ROOT/","sys.path[:0]=[str(ROOT),str(ROOT/",1)
s=s.replace('source26-ground-routing-host-r01/receipt.json','source26-root78-host-r01/receipt.json')
s=s.replace('source26-ground-routing-host-r02/run_validation.py','source26-root78-host-r01/run_validation.py')
a=s.index("for name in('test_motherboard_return_plane_track_anchors'")
z=s.index('assert ids',a);s=s[:a]+s[z:]
(d/'run_native.py').write_text(s)
print('Prepared exact current host-skipped native case runner with workspace imports')
