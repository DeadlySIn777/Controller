"""Screen vendor ordinary area mode on unchanged capture-only RTL."""
from pathlib import Path
import hashlib,json,shutil
H=Path(__file__).resolve().parent;BASE=H/'event-capture-select-r2';OUT=H/'event-capture-area-r6'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir()
    for f in ['cnc3_runtime_events.v','original.v']:shutil.copyfile(BASE/f,OUT/f)
    record={'status':'AREA_SETTING_ONLY_EXPERIMENT_PREPARED','source_delta_from_capture_r2':False,'candidate_SHA256':sha(OUT/'cnc3_runtime_events.v'),'baseline_native_events_receipt_SHA256':sha(BASE/'native-events-map/receipt.json'),'setting':'synthesis mode=area, e_option; other settings unchanged','primary_installed_docs':['C:/Efinity/2026.1/doc/topics/syn-options.html','C:/Efinity/2026.1/doc/topics/cli-map-opts.html'],'purpose':'ordinary area mode documented to optimize smallest area; timing remains separate','adopted':False}
    (OUT/'preparation-receipt.json').write_text(json.dumps(record,indent=2)+'\n')
    maps=(H/'map_event_area2_r5.py').read_text().replace('event-capture-area2-r5','event-capture-area-r6').replace("[('area2',", "[('area',").replace("value='area2'", "value='area'").replace('NATIVE_EVENTS_ONLY_AREA2_SETTING_MAP_COMPLETE','NATIVE_EVENTS_ONLY_AREA_SETTING_MAP_COMPLETE')
    target=H/'map_event_area_r6.py';assert not target.exists();target.write_text(maps)
    print(json.dumps(record))
if __name__=='__main__':main()
