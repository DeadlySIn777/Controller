"""Bind native transport-overlay result to qualified exact three-file sources."""
from pathlib import Path
import hashlib,json,re
H=Path(__file__).resolve().parent;OUT=H/'transport-cmd-alignment-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    raw=OUT/'native-full-map/receipt.json';record=json.loads(raw.read_bytes())
    packet=OUT/'reviewable-transport-overlay-packet.json';behavior=json.loads(packet.read_bytes())
    baseline_path=H/'event-capture-global-area2-r7/independent-review-receipt.json';baseline=json.loads(baseline_path.read_bytes())
    assert record['execution']['exit']==0 and record['canonical_sources_unchanged'] and record['project_semantics_unchanged']
    expected={'cnc3_event_bank.v':'6f034f17c2f70c7161ad13dc605e7ab484844bd71688f6af04bc4bbe46a43841',
              'cnc3_runtime_events.v':'4a42ebe2f669d1854da0d19477a375279201da171b9fa82ebea43b15e0fb1da9',
              'cnc3_spi_transport_stateful.v':'c909378cb28cf87c7113b1b92c6cdd82f71e166c64eb87548a8880ba85c9d4cc'}
    inventory={Path(r['copy']).name:r for r in record['source_inventory']}
    for name,digest in expected.items():assert inventory[name]['copy_SHA256']==sha(Path(inventory[name]['copy']))==digest
    for row in inventory.values():assert sha(Path(row['canonical']))==row['canonical_SHA256']
    report=OUT/'native-full-map/outflow/cnc3_runtime_sim.map.rpt';text=report.read_text()
    assert re.search(r'^mode\s*:\s*area2\s*$',text,re.M)
    console=OUT/'native-full-map/full-SIM2-transport-area2-map.console.log'
    assert re.search(r'map\s*:\s*PASS',console.read_text())
    resources=record['resources'];screen=resources['EFX_LUT4']+resources['EFX_ADD']
    result={'status':'THREE_FILE_TRANSPORT_OVERLAY_NATIVE_GLOBAL_AREA2_MAP_PASS_PHYSICAL_FIT_OPEN',
      'behavior_packet_SHA256':sha(packet),'exact_overlay_SHA256':expected,'resources':resources,'coarse_LUT4_plus_ADD':screen,
      'T20_equivalent_LE_screen':19728,'over_screen':screen-19728,'LUT4_saved_vs_prior_global_area2':baseline['resources']['EFX_LUT4']-resources['EFX_LUT4'],
      'ADD_saved_vs_prior_global_area2':baseline['resources']['EFX_ADD']-resources['EFX_ADD'],'execution':record['execution'],
      'native_scope':'disconnected functional SIM2 top, insert-ios0, T20F256/I4 map, global area2; complete physical wrapper, place/route and static timing unexecuted',
      'inherited_console_caption':'raw runner caption mentions capture/RAM; exact source_inventory and SHA ledger include qualified transport overlay',
      'canonical_sources_and_tests_unchanged':True,'adopted':False,'PNR_bitstream_or_programming':False,'manufacturing_ready':False,
      'input_SHA256':{str(p):sha(p) for p in [Path(__file__),raw,packet,report,console,baseline_path,OUT/'native-map-preparation-receipt.json',OUT/'full-runtime/receipt.json']}}
    (OUT/'native-resource-supplement.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['status','resources','coarse_LUT4_plus_ADD','over_screen','LUT4_saved_vs_prior_global_area2']}))
if __name__=='__main__':main()
