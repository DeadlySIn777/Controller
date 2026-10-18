"""Actual retained ROOT87 contacts and whole Source-cluster preservation.

Complements current complete route/return proofs; grants no manufacture status.
"""
from pathlib import Path
import sys,json,argparse
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_populate_motherboard_pcb import sha,write
from hardware_route_logic_return import identity
from hardware_route_critical_digital_wip_r03 import source_clusters,clusters_preserved
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact
ap=argparse.ArgumentParser()
ap.add_argument('--board',type=Path,required=True)
ap.add_argument('--out',type=Path,required=True)
a=ap.parse_args();assert not a.out.exists()
root=Path('reports/motherboard-pcb-integration-20261001')
baseline=root/'source26-seven-path-larger-IO3-cleanup-trial-r87/motherboard-bounded-merged-candidate.kicad_pcb'
strict=Path('reports/motherboard-owned-bypass-routing-20261001/source26-r76-strict-same-side-r01')
stub=Path('reports/motherboard-return-zoning-20261001/source26-r81-two-redundant-ground-spurs-r01')
paths=[a.board,baseline,strict/'owned-bypass-loop-candidate.kicad_pcb',strict/'bounded-scope.json',strict/'independent-native-cut-proof.json',stub/'receipt.json',stub/'old101-native-bypass-proof.json',stub/'bounded-scope.json',Path(__file__)]
frozen={str(p.resolve()):sha(p)for p in paths}
read=lambda p:json.loads(p.read_text())
assert read(strict/'independent-native-cut-proof.json')['passed']
assert read(stub/'receipt.json')['passed'] and read(stub/'old101-native-bypass-proof.json')['passed']
b=pcbnew.LoadBoard(str(a.board));b.BuildConnectivity()
old=pcbnew.LoadBoard(str(baseline));prior=clusters_preserved(source_clusters(old),b)
co=b.GetConnectivity();cu={t.m_Uuid.AsString():t for t in b.GetTracks()}
ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()}
donor=pcbnew.LoadBoard(str(strict/'owned-bypass-loop-candidate.kicad_pcb'))
dc={t.m_Uuid.AsString():identity(t)for t in donor.GetTracks()}
new9=read(strict/'bounded-scope.json')['reviewed_copper_delta_UUIDs'];assert len(new9)==9
assert all(identity(cu[u])==dc[u]for u in new9)
retired=read(stub/'receipt.json')['removed_exact_obsolete_Cu'];assert not set(retired)&set(cu)
checks=[]
for row in read(stub/'receipt.json')['retained_actual_ground_routes']:
 pad=ps[row['ref'],row['pin']];via=cu[row['actual_retained_via']]
 assert pad.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in co.GetConnectedItems(via)}
 for layer in row['actual_flashed_native_reference_contacts']:assert physical_reference_contact(via,b.GetLayerID(layer),co)
 checks.append(row)
assert all(sha(Path(p))==h for p,h in frozen.items())
write(a.out,dict(passed=True,board_sha256=sha(a.board),baseline_sha256=sha(baseline),input_sha256=frozen,prior_SOURCE_clusters=prior,exact_retained_nine_Cu=new9,retired_obsolete_Cu_still_absent=retired,actual_retained_ground_contacts=checks,manufacturing_ready=False))
print(json.dumps(dict(passed=True,prior_SOURCE_clusters=prior)),flush=True)
