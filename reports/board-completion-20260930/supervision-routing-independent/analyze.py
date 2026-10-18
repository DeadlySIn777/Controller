"""Read-only independent native geometry review of the completed selected routing.

Uses the earlier independent KiCad geometric cluster helper. Never saves negative
controls or changes source/published boards. The item changes are compared with
the exact supplied removal/replacement bundle, rather than trusting its totals.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import pcbnew

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ROUTE = ROOT/'reports/board-completion-20260930/supervision-routing/manual-v5'
BASE = ROOT/'hardware/board_review/revisions/20260930-06/motion-card-route-candidate.kicad_pcb'
HELPER = ROOT/'reports/board-completion-20260930/selected-routing-connectivity-review/analyze.py'


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p, x): p.write_text(json.dumps(x, indent=2)+'\n', encoding='utf-8')


def main():
    HERE.mkdir(parents=True, exist_ok=True)
    helper = runpy.run_path(str(HELPER))
    files = [BASE, BASE.with_suffix('.kicad_pro'), HELPER,
             ROUTE/'motion-card-supervision-routed.kicad_pcb',
             ROUTE/'motion-card-supervision-routed.kicad_pro',
             ROUTE/'route-bundle.json', ROUTE/'review.json', ROUTE/'fp-lib-table']
    for folder in ('CNC_IS1.pretty', 'CNC_MC_Power.pretty', 'CNC_Motion.pretty'):
        files.extend(sorted((ROUTE/folder).rglob('*.kicad_mod')))
    hashes = {}
    for source in files:
        key = source.relative_to(ROOT).as_posix()
        target = HERE/'inputs'/key
        target.parent.mkdir(parents=True, exist_ok=True)
        before = sha(source)
        if target.exists(): assert sha(target) == before
        else: shutil.copy2(source, target)
        assert sha(target) == sha(source) == before
        hashes[key] = before
    baseline = HERE/'inputs'/BASE.relative_to(ROOT)
    candidate = HERE/'inputs'/(ROUTE/'motion-card-supervision-routed.kicad_pcb').relative_to(ROOT)
    bundle = json.loads((ROUTE/'route-bundle.json').read_text())
    old_receipt = json.loads((ROOT/'reports/board-completion-20260930/selected-routing-connectivity-review/review.json').read_text())
    selected = [r['net'] for r in old_receipt['published_revision06']['selected_nets']]
    assert len(selected) == 41
    before_board, before = helper['inspect'](baseline, selected)
    board, current = helper['inspect'](candidate, selected)
    assert before['pad_geometry_and_net_inventory'] == current['pad_geometry_and_net_inventory']
    assert current['footprints'] == 203 and current['pads'] == 867
    assert current['selected_fully_connected'] == 41
    assert current['selected_missing_pad_cluster_joins'] == 0
    assert current['uncapped_unconnected_ratsnest_edges'] == 497
    assert not current['copper_clusters_without_source_pads']
    olditems = {t.m_Uuid.AsString(): helper['describe'](t) for t in before_board.GetTracks()}
    newitems = {t.m_Uuid.AsString(): helper['describe'](t) for t in board.GetTracks()}
    removed = [olditems[k] for k in sorted(olditems.keys()-newitems.keys())]
    added = [newitems[k] for k in sorted(newitems.keys()-olditems.keys())]
    retained = olditems.keys() & newitems.keys()
    assert len(retained) == 294
    assert all(olditems[k] == newitems[k] for k in retained)
    assert len(removed) == 2 and len(added) == 77
    assert sorted(removed, key=lambda r:r['uuid']) == sorted(bundle['removed_input_items'], key=lambda r:r['uuid'])
    assert all(row['net'] == '/watchdog_conditioning/WD_M_WDI_BUF' for row in removed)
    assert all(newitems[row['uuid']] == row for row in bundle['replacement_items'])
    assert len(bundle['replacement_items']) == 4
    assert len(newitems) == 371
    assert all(t['width_nm'] == (600000 if t['type'] == pcbnew.PCB_VIA_T else 200000) for t in added)
    assert all(t['drill_nm'] == 300000 for t in added if t['type'] == pcbnew.PCB_VIA_T)

    # Break an actual cut edge incident on the final ARM_O_Q endpoint in memory,
    # keeping net names/width/layer intact. No board is saved.
    control = pcbnew.LoadBoard(str(candidate))
    target = pcbnew.VECTOR2I(pcbnew.FromMM(149.8625), pcbnew.FromMM(59.05))
    cut = [t for t in control.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T
           and t.GetNetname() == '/mc_permission/ARM_O_Q'
           and (t.GetStart() == target or t.GetEnd() == target)]
    assert cut
    moved = []
    for trace in cut:
        moved.append(helper['describe'](trace))
        shift = pcbnew.VECTOR2I(pcbnew.FromMM(20), 0)
        trace.SetStart(trace.GetStart()+shift)
        trace.SetEnd(trace.GetEnd()+shift)
    control.BuildConnectivity()
    pads = [p for fp in control.GetFootprints() for p in fp.Pads()
            if p.GetNetname() == '/mc_permission/ARM_O_Q']
    clusters = {tuple(sorted((p.GetParentFootprint().GetReference(), p.GetNumber())
                 for p in control.GetConnectivity().GetConnectedItems(pad)
                 if p.Type() == pcbnew.PCB_PAD_T)) for pad in pads}
    assert len(clusters) > 1
    negative_unconnected = control.GetConnectivity().GetUnconnectedCount(False)
    assert negative_unconnected > 497

    cli = 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
    command = [cli, 'pcb', 'drc', '--format', 'json', '--all-track-errors', '--severity-all',
               '--output', str(HERE/'fresh-drc.json'), str(candidate)]
    process = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace')
    (HERE/'fresh-drc.txt').write_text(process.stdout+process.stderr, encoding='utf-8')
    assert process.returncode == 0
    drc = json.loads((HERE/'fresh-drc.json').read_text())
    assert not drc['violations']
    assert len(drc['unconnected_items']) == 497
    assert not drc['schematic_parity']
    assert all(sha(ROOT/key) == value for key, value in hashes.items())
    result = {'revision':'supervision-routing-independent-r01',
              'captured_utc':datetime.now(timezone.utc).isoformat(),
              'kicad_version':pcbnew.GetBuildVersion(), 'original_inputs_unchanged':True,
              'input_sha256':hashes, 'candidate':current,
              'baseline_uncapped_unconnected':before['uncapped_unconnected_ratsnest_edges'],
              'preserved_items':len(retained), 'removed_items':removed,
              'added_items':added, 'exact_removed_replacements_match_bundle':True,
              'original867_pad_geometry_and_nets_unchanged':True,
              'negative_control':{'net':'/mc_permission/ARM_O_Q', 'moved_geometry':moved,
                                  'translation_mm':[20,0], 'pad_clusters_after':len(clusters),
                                  'uncapped_unconnected_after':negative_unconnected, 'saved':False},
              'fresh_native_drc_command':command,
              'fresh_native_regular_violations':0, 'fresh_native_unconnected':497,
              'manufacturing_ready':False, 'full_card_routing_complete':False,
              'scope':'203-part revision06 supervision candidate, not later 327-part integrated board',
              'physical_measurement':False}
    write(HERE/'review.json', result)
    print(json.dumps({'selected_connected':41, 'selected_total':41,
                      'uncapped_unconnected':497, 'regular_DRC_violations':0,
                      'original_pads_preserved':867, 'retained_items':294,
                      'removed_authorized_WDI_items':2, 'new_items':77,
                      'final_track_via_items':371, 'negative_control_uncapped':negative_unconnected,
                      'all_original_inputs_unchanged':True}))


if __name__ == '__main__': main()
