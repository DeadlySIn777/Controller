"""Independently bind one global area2 run to exact qualified overlay hashes."""
from pathlib import Path
import hashlib,json,re
H=Path(__file__).resolve().parent;OUT=H/'event-capture-global-area2-r7'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    path=OUT/'native-full-map/receipt.json';record=json.loads(path.read_bytes())
    baseline=json.loads((H/'event-capture-select-r2/native-full-map/receipt.json').read_bytes())
    assert record['execution']['exit']==0 and record['canonical_sources_unchanged'] and record['project_semantics_unchanged']
    by_name={Path(r['copy']).name:r for r in record['source_inventory']}
    assert by_name['cnc3_event_bank.v']['copy_SHA256']=='6f034f17c2f70c7161ad13dc605e7ab484844bd71688f6af04bc4bbe46a43841'
    assert by_name['cnc3_runtime_events.v']['copy_SHA256']=='4a42ebe2f669d1854da0d19477a375279201da171b9fa82ebea43b15e0fb1da9'
    report=OUT/'native-full-map/outflow/cnc3_runtime_sim.map.rpt';text=report.read_text()
    assert re.search(r'^mode\s*:\s*area2\s*$',text,re.M)
    console=OUT/'native-full-map/full-SIM2-global-area2-map.console.log'
    assert re.search(r'map\s*:\s*PASS',console.read_text())
    resources=record['resources'];screen=resources['EFX_LUT4']+resources['EFX_ADD']
    result={'status':'ONE_GLOBAL_AREA2_NATIVE_MAP_PASS_EXACT_QUALIFIED_SOURCES_COARSE_DEVICE_SCREEN_EXCEEDED','resources':resources,'coarse_LUT4_plus_ADD':screen,'T20_equivalent_LE_screen':19728,'over_screen':screen-19728,'LUT4_saved_vs_qualified_speed':baseline['resources']['EFX_LUT4']-resources['EFX_LUT4'],'execution':record['execution'],'scope':'disconnected SIM2 functional top map only, insert-ios0; physical wrapper fit/place/route/static timing unexecuted','source_delta_from_qualified_r2':False,'further_global_setting_sweep':False,'adopted':False,'manufacturing_ready':False,'input_SHA256':{str(p):sha(p) for p in [Path(__file__),path,report,console,OUT/'preparation-receipt.json',H/'event-capture-select-r2/reviewable-two-file-overlay-packet.json']}}
    (OUT/'independent-review-receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['status','resources','coarse_LUT4_plus_ADD','over_screen','LUT4_saved_vs_qualified_speed']}))
if __name__=='__main__':main()
