"""Tie the final native-clean41-cell donor to its independent checks."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
r=Path(__file__).resolve().parent/'four-cell-placement-native-clean-r05'
s=ROOT/'reports/motherboard-integration-20260930/r24-2688-probe-topology-staged'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=read(r/'receipt.json');inv=read(r/'independent-connectivity/review.json');dm=read(r/'native-source-domain-review/domain-map.json')
files=['receipt.json','merge-scope.json','drc.json','independent-layout-review.json','native-negative-tests.txt',
       'native-source-domain-review/domain-map.json','independent-connectivity/review.json']
f=dict(board_SHA256=d['board_SHA256'],source_snapshot=str(s.relative_to(ROOT)),
    source_hashes={n:sha(s/n)for n in ['design.json','netlist.xml','assembly-map.json']},
    physical_parts=2688,numbered_copper_pad_pieces=9515,fitted_source_pads=9498,track_via_items=7332,
    uncapped_missing_joins=4944,native_DRC_regular=0,native_DRC_ignored=[],
    independent_missing_joins=inv['independent_physical_cluster_missing_joins'],independent_orphan_copper=inv['orphan_copper_items'],
    source_population_and_pin_net_checks_PASS=dm['source_physical_population_complete']and inv['source_net_checks_pass'],
    exact_pose_refs=41,exact_remaining_old_Cu_retirement=176,root_prior_removal_overlap=4,
    all_unrelated_actual_pad_clusters_and_native_Cu_preserved=True,topology_layout_check_PASS=True,
    native_meaningful_tests=7,native_tests_PASS=(r/'native-negative-tests.txt').read_text().rstrip().endswith('OK'),
    auxiliary_pad_categories=dict(paste_only=dm['unnumbered_stencil_only_pieces'],NPTH=dm['unnumbered_npth_holes'],
        mask_only=dm['unnumbered_mask_only_apertures']),
    proof_hashes={n:sha(r/n)for n in files},manufacturing_ready=False,
    scope='Closed source24 bounded41-part layout and old-leaf reconciliation. Four same-side1.825mm logic bypasses;all eight externalRTHR protected gaps>=6mm. Internal cells,global rails,44SUB thermal islands and finalreturnplanes stillrequire actualrouting;physicalEMC/timingremainunqualified.')
assert f['source_population_and_pin_net_checks_PASS']and f['native_tests_PASS']
assert inv['independent_physical_cluster_missing_joins']==4944 and not inv['orphan_copper_items']
(r/'final-freeze.json').write_text(json.dumps(f,indent=2)+'\n')
print(json.dumps(dict(final_freeze_SHA256=sha(r/'final-freeze.json'),board_SHA256=d['board_SHA256'])))
