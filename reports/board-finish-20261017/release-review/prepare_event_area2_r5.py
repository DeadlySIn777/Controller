"""Installed vendor mode=area2 screen; identical behavior-qualified capture RTL."""
from pathlib import Path
import hashlib,json,shutil
H=Path(__file__).resolve().parent;BASE=H/'event-capture-select-r2';OUT=H/'event-capture-area2-r5'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir()
    for f in ['cnc3_runtime_events.v','original.v']:shutil.copyfile(BASE/f,OUT/f)
    record={'status':'AREA2_SETTING_ONLY_EXPERIMENT_PREPARED','source_delta_from_capture_r2':False,'candidate_SHA256':sha(OUT/'cnc3_runtime_events.v'),'baseline_native_events_receipt_SHA256':sha(BASE/'native-events-map/receipt.json'),'setting':'synthesis mode=area2, e_option; other settings unchanged','primary_installed_docs':['C:/Efinity/2026.1/doc/topics/syn-options.html','C:/Efinity/2026.1/doc/topics/cli-map-opts.html'],'purpose':'area2 documented for optimizing large multiplexer trees; actual capacity and timing remain separate','adopted':False}
    (OUT/'preparation-receipt.json').write_text(json.dumps(record,indent=2)+'\n')
    maps=(H/'map_event_capture_r2.py').read_text().replace("RUN=H/'event-capture-select-r2'","RUN=H/'event-capture-area2-r5'")
    maps=maps.replace("[('original',RUN/'original.v'),('literal-case',RUN/'cnc3_runtime_events.v')]", "[('area2',RUN/'cnc3_runtime_events.v')]").replace('len(records)==2','len(records)==1').replace('NATIVE_EVENTS_ONLY_CAPTURE_COMPARISON_COMPLETE','NATIVE_EVENTS_ONLY_AREA2_SETTING_MAP_COMPLETE')
    marker="        ET.indent(p);xml=d/'cnc3_runtime_events.xml';"
    assert maps.count(marker)==1
    maps=maps.replace(marker,"        ET.SubElement(syn,t('param'),name='mode',value='area2',value_type='e_option')\n"+marker)
    target=H/'map_event_area2_r5.py';assert not target.exists();target.write_text(maps)
    print(json.dumps(record))
if __name__=='__main__':main()
