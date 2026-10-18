"""Review one complete ordinary SOURCE pair; emit a persisted exact cut copy.

No source, existing copper, lands, poses, or zone definition may change.
Full retained-loop/resource/power and refilled cut receipts are separate.
"""
from pathlib import Path
import sys,json,shutil
sys.path[:0]=[str(Path('tools').resolve()),str(Path(__file__).parent.resolve())]
import pcbnew
import hardware_route_ordinary_wip_r05 as ordinary
import hardware_route_critical_digital_wip_r03 as old
import hardware_merge_bounded_pcb_delta as merger
from hardware_route_logic_return import identity,pad_identity
e=ordinary.engine
BASE=Path('reports/motherboard-return-zoning-20261001/ROOT102-health-current110-composed-r31/motherboard-bounded-merged-candidate.kicad_pcb')
OUT=Path('reports/motherboard-ordinary-routing-20261001/ROOT31-PROC-literal-F-tunnel-r35')
DEST=OUT/'motherboard-ordinary-F-PROC-candidate.kicad_pcb'
MAP=OUT/'fresh-domain-map-r01/domain-map.json'
plan=e.read(OUT/'proposed-groups.json');manifest=e.read(OUT/'manifest.json')
assert len(plan['groups'])==1
g=plan['groups'][0]
assert g['source_pair']==['U14404.2','U14402.13']
assert g['net']=='/mc_permission/PROC_PERMIT' and not g['ground_UUIDs']
inputs={str(p.resolve()):e.sha(p)for p in(BASE,DEST,MAP,OUT/'manifest.json',OUT/'proposed-groups.json',OUT/'native.json',Path(__file__),Path(merger.__file__),Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))}
native=e.read(OUT/'native.json');assert not native['violations']and not native['ignored_checks']
ordinary.INPUT_BOARD=BASE;ordinary.MAPPING=e.read(MAP)
assert ordinary.MAPPING['input_sha256'][str(DEST.resolve())]==e.sha(DEST)
scope=ordinary.frozen_review_check(manifest,Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
before=pcbnew.LoadBoard(str(BASE));after=pcbnew.LoadBoard(str(DEST));before.BuildConnectivity();after.BuildConnectivity()
population,_=e.native_source_check(after,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
oldcu={t.m_Uuid.AsString():identity(t)for t in before.GetTracks()};newcu={t.m_Uuid.AsString():identity(t)for t in after.GetTracks()}
added=set(g['new_copper_UUIDs'])
assert set(newcu)-set(oldcu)==added and len(added)==32
assert all(newcu.get(u)==v for u,v in oldcu.items())
assert {p.m_Uuid.AsString():pad_identity(p)for p in before.GetPads()}=={p.m_Uuid.AsString():pad_identity(p)for p in after.GetPads()}
oldtree=e.parse(merger.without_generated_fills(BASE.read_text()));newtree=e.parse(merger.without_generated_fills(DEST.read_text()))
assert {u:merger.zone_definition(z)for u,z in merger.objects(oldtree,'zone').items()}=={u:merger.zone_definition(z)for u,z in merger.objects(newtree,'zone').items()}
assert {u:e.dump(f)for u,f in merger.objects(oldtree,'footprint').items()}=={u:e.dump(f)for u,f in merger.objects(newtree,'footprint').items()}
assert all(t.Type()==pcbnew.PCB_TRACE_T and t.GetLayer()==pcbnew.F_Cu and t.GetWidth()==pcbnew.FromMM(.20)and t.GetNetname()==g['net']for t in after.GetTracks()if t.m_Uuid.AsString()in added)
clusters=old.clusters_preserved(old.source_clusters(before),after)
def joined(board):
 board.BuildConnectivity();pads={p.m_Uuid.AsString():p for p in board.GetPads()};p,q=[pads[u]for u in g['source_pad_UUIDs']]
 assert p.GetNetname()==q.GetNetname()==g['net']
 return q.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in board.GetConnectivity().GetConnectedItems(p)}
assert joined(after)and not joined(before)
returns=ordinary.actual_return_check(after,added,manifest['nets'])
assert not returns['actual_signal_via_reference_audits']
e.write(OUT/'exact-Source-return-positive-r01.json',dict(passed=True,input_sha256=inputs,board_sha256=e.sha(DEST),source_scope=scope,source_population=population,actual_source_pair=g['source_pair'],new_copper_count=32,no_added_vias=True,exact_all_old_copper_pads_poses_zone_definitions_preserved=True,prior_SOURCE_clusters=clusters,actual_filled_Source_anchored_return_guard=returns,native_errors=0,native_warnings=0,ignored_checks=[],saved_refilled_cut_pending=True,manufacturing_ready=False))
cutdir=OUT/'actual-PROC-cut-r01';cutdir.mkdir(exist_ok=False);cutpath=cutdir/'motherboard-PROC-cut-candidate.kicad_pcb'
cut=pcbnew.LoadBoard(str(DEST));exact={t.m_Uuid.AsString():t for t in cut.GetTracks()}
for u in added:cut.Remove(exact[u])
pcbnew.SaveBoard(str(cutpath),cut)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(DEST.with_suffix(suffix),cutpath.with_suffix(suffix))
assert not joined(cut)
e.write(cutdir/'cut-proposal.json',dict(input_board_sha256=e.sha(DEST),source_pair=g['source_pair'],net=g['net'],literal_removed_copper_UUIDs=sorted(added),saved_board_sha256=e.sha(cutpath),immediate_native_pair_disconnected=True,native_refill_fresh_reload_pending=True))
assert all(e.sha(p)==h for p,h in inputs.items())
print(json.dumps(dict(passed=True,new_copper=32,actual_source_pair=g['source_pair'],prior_Source_clusters_preserved=True,cut_path=str(cutpath),saved_refilled_cut_pending=True)))
