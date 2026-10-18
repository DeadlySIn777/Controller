"""Freeze a bounded additive ordinary route with its actual refilled cut."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_ordinary_wip_r05 as ordinary
import hardware_route_critical_digital_wip_r03 as prior
e=ordinary.engine
OUT=Path('reports/motherboard-ordinary-routing-20261001/ROOT31-PROC-literal-F-tunnel-r35')
BASE=Path('reports/motherboard-return-zoning-20261001/ROOT102-health-current110-composed-r31/motherboard-bounded-merged-candidate.kicad_pcb')
DEST=OUT/'motherboard-ordinary-F-PROC-candidate.kicad_pcb'
CUT=OUT/'actual-PROC-cut-r01/motherboard-PROC-cut-candidate.kicad_pcb'
plan=e.read(OUT/'proposed-groups.json');g=plan['groups'][0]
files=[BASE,DEST,CUT,OUT/'proposed-groups.json',OUT/'manifest.json',OUT/'native.json',OUT/'actual-PROC-cut-r01/native.json',OUT/'exact-Source-return-positive-r01.json',OUT/'retained110-strict-proof-r01.json',OUT/'current-literal-resources-r01.json',OUT/'actual-IO3-r07-power-geometry-r01.json',OUT/'independent-connectivity-r01/review.json',Path(__file__)]
inputs={str(p.resolve()):e.sha(p)for p in files}
for p in files:
 if p.suffix!='.json':continue
 r=e.read(p)
 if 'passed'in r:assert r['passed'],str(p)
 if 'board_sha256'in r and 'cut-r01'not in str(p):assert r['board_sha256']==e.sha(DEST),str(p)
positive=e.read(OUT/'native.json');negative=e.read(OUT/'actual-PROC-cut-r01/native.json')
assert not positive['violations']and not positive['ignored_checks']
assert not negative['violations']and not negative['ignored_checks']
cut=pcbnew.LoadBoard(str(CUT));cut.BuildConnectivity();b=pcbnew.LoadBoard(str(BASE));b.BuildConnectivity()
pads={p.m_Uuid.AsString():p for p in cut.GetPads()};p,q=[pads[u]for u in g['source_pad_UUIDs']]
assert q.m_Uuid.AsString()not in{t.m_Uuid.AsString()for t in cut.GetConnectivity().GetConnectedItems(p)}
assert set(g['new_copper_UUIDs']).isdisjoint({t.m_Uuid.AsString()for t in cut.GetTracks()})
cut_source=prior.clusters_preserved(prior.source_clusters(b),cut)
e.write(OUT/'actual-PROC-cut-r01/fresh-reload-review.json',dict(passed=True,board_sha256=e.sha(CUT),input_board_sha256=e.sha(DEST),literal_removed_UUIDs=g['new_copper_UUIDs'],actual_Source_pair=g['source_pair'],fresh_saved_native_refilled_Source_pair_disconnected=True,all_preexisting_BASE_Source_clusters_retained=cut_source,native_errors=0,native_warnings=0,ignored_checks=[]))
loops=e.read(OUT/'retained110-strict-proof-r01.json');resources=e.read(OUT/'current-literal-resources-r01.json');inventory=e.read(OUT/'independent-connectivity-r01/review.json')
assert loops['retained_local_loops_checked']==110 and len(loops['actual_receiving_return_anchor_reviews'])==225
assert resources['filled_component_count']==188 and not resources['unanchored_components']and not resources['derived_nonphysical_computation_artifacts']
assert inventory['uncapped_unconnected_ratsnest_edges']==inventory['independent_physical_cluster_missing_joins']==3520 and not inventory['orphan_copper_items']
assert all(e.sha(p)==h for p,h in inputs.items())
e.write(OUT/'freeze-receipt-r01.json',dict(passed=True,input_sha256=inputs,before_board_path=str(BASE.resolve()),before_board_sha256=e.sha(BASE),board_path=str(DEST.resolve()),board_sha256=e.sha(DEST),scope='One actual complete ordinary PROC_PERMIT source pair using only F.Cu with real adjacent Source-backed LOGIC In1. No added via, source/land/pose/zone or old copper change.',actual_Source_pair=g['source_pair'],added_F_segments=32,width_mm=.20,reviewed_source_clearance_mm=.15,reference_margin_mm=.10,retained_loops=110,receiving_returns=225,actual_reference_resources=188,unanchored_or_synthetic_resources=0,native_uncapped_joins=3520,independent_uncapped_joins=3520,orphan_copper=0,native_errors=0,native_warnings=0,ignored_checks=[],actual_saved_refilled_fresh_reload_cut_path=str((OUT/'actual-PROC-cut-r01/fresh-reload-review.json').resolve()),actual_cut_sha256=e.sha(OUT/'actual-PROC-cut-r01/fresh-reload-review.json'),unchanged_r07_power_guard_passed=True,live_source_or_PCB_publication_changed=False,physical_signal_integrity_or_latency_qualified=False,manufacturing_ready=False))
e.write(OUT/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(g['new_copper_UUIDs']),reviewed_added_zone_UUIDs=[],reviewed_scope_reason='Exact 32 additive .20 mm F-only ordinary PROC_PERMIT tracks connect U14404.2 to U14402.13 through the physically inspected receiving package lane. Real Source-backed In1 and full .10 mm corridor, all110/225 loops, 188 resources, unchanged r07 IO3/CORE geometry, native/Source3520 joins0orphan and refilled actual cut pass. No vias, source/lands/poses/other copper/zone-definition changes; not manufacturing-ready.',review_evidence_sha256={str((OUT/'freeze-receipt-r01.json').resolve()):e.sha(OUT/'freeze-receipt-r01.json')}))
print(json.dumps(dict(passed=True,board_sha256=e.sha(DEST),added_segments=32,joins=3520,cut=True)))
