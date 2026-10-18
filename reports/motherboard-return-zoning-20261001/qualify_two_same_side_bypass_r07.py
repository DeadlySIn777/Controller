"""Read back the completed native restoration; exact Source/Cu/pose freeze."""
from pathlib import Path
import sys,json,copy,subprocess,concurrent.futures
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_merge_bounded_pcb_delta import parse,dump,children,reference,without_generated_fills,objects,zone_definition
from hardware_populate_motherboard_pcb import sha,write,pad_template
from hardware_route_logic_return import identity
from hardware_route_critical_digital_wip_r03 import source_clusters,clusters_preserved
parent=Path('reports/motherboard-return-zoning-20261001')
p=parent/'ROOT101-two-same-side-bypass-restored-r06';board=p/'motherboard-two-same-side-bypass-candidate.kicad_pcb'
base=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-U25-C19033-merged-trial-r101')
baseline=base/'motherboard-bounded-merged-candidate.kicad_pcb'
donor=parent/'ROOT101-three-moved-same-side-routing-r05'
assert not(p/'receipt.json').exists()
assert sha(baseline)=='81c0d8c2f4cc70140deff90266c92fd693e9c34923da62610eee49305f413226'
before=pcbnew.LoadBoard(str(baseline));b=pcbnew.LoadBoard(str(board));b.BuildConnectivity()
oldtree=parse(without_generated_fills(baseline.read_text()));tree=parse(without_generated_fills(board.read_text()))
oldfps={reference(f):f for f in children(oldtree,'footprint')};fps={reference(f):f for f in children(tree,'footprint')}
assert set(oldfps)==set(fps)
changed={r for r in oldfps if dump(oldfps[r])!=dump(fps[r])};assert changed=={'C13006','C13007'}
assert dump(oldfps['C13011'])==dump(fps['C13011'])
oldcu={t.m_Uuid.AsString():identity(t)for t in before.GetTracks()};cu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()}
assert all(cu.get(u)==v for u,v in oldcu.items())
new=json.loads((donor/'receipt.json').read_text());ids=[u for g in new['owned_loops']for u in g['new_UUIDs']]
assert set(cu)-set(oldcu)==set(ids)and len(ids)==6
assert {u:zone_definition(z)for u,z in objects(oldtree,'zone').items()}=={u:zone_definition(z)for u,z in objects(tree,'zone').items()}
clusters=clusters_preserved(source_clusters(before),b)
drc=json.loads((p/'drc.json').read_text());assert not drc['violations']and not drc['ignored_checks']
groups=json.loads((base/'current106-bypass-manifest.json').read_text())
assert len(groups['owned_loops'])==106
assert not set(changed)&{g['ref']for g in groups['owned_loops']}
groups['owned_loops'].extend(new['owned_loops']);groups['board_sha256']=sha(board)
write(p/'current108-bypass-manifest.json',groups)
scope=dict(electrical_source_unchanged=True,reviewed_footprint_references=sorted(changed),reviewed_copper_delta_UUIDs=ids,reviewed_added_zone_UUIDs=[],reviewed_scope_reason='Two actual Source receiving bypass loops: existing capacitor poses only and six added conductors, failed C13011 pose restored exactly. Full current native return/power/Source/cut proofs required; no source or rail rating changes.')
write(p/'bounded-scope.json',scope)
write(p/'receipt.json',dict(passed=True,board_sha256=sha(board),baseline_sha256=sha(baseline),native_DRC_errors=0,native_DRC_warnings=0,ignored_checks=[],remaining_required_joins=b.GetConnectivity().GetUnconnectedCount(False),exact_added_Cu=ids,changed_poses=sorted(changed),prior_Source_clusters=clusters,unrelated_Cu_and_zones_unchanged=True,failed_pose_C13011_restored=True,correction='r06 native and literal restoration completed; receipt writer needed explicit False argument for current KiCad GetUnconnectedCount API',not_yet_adopted=True,manufacturing_ready=False))
py='C:/Program Files/KiCad/10.0/bin/python.exe'
jobs=[
 ['tools/hardware_map_motherboard_domains.py','--board',str(board),'--source','hardware/motherboard','--out',str(p/'domain-map')],
 ['tools/hardware_verify_owned_bypass_batch.py','--board',str(board),'--owners','reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json','--receipt',str(p/'current108-bypass-manifest.json'),'--out',str(p/'combined108-proof.json')],
 ['reports/motherboard-pcb-integration-20261001/check-current-relative-power-r03.py','--board',str(board),'--out',str(p/'current-full-delta-power-proof.json')],
]
def run(row):
 target=p/(Path(row[0]).stem+'-command.log')
 with target.open('w')as stream:r=subprocess.run([py,*row],stdout=stream,stderr=subprocess.STDOUT)
 result=dict(command=[py,*row],returncode=r.returncode,log=str(target),sha256=sha(target));print(json.dumps(result),flush=True);return result
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:results=list(pool.map(run,jobs))
write(p/'first-native-checks.json',dict(results=results,all_commands_completed=all(r['returncode']==0 for r in results)))
