"""Derive the already-reviewed isolated full-core runners for capture-only r2."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;OUT=H/'event-capture-select-r2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    root_source=H.parent/'efinity-bram-behavior-r1/run_isolated_runtime.py'
    text=root_source.read_text();marker=' if args.mutation:\n';assert text.count(marker)==1
    overlay=" shutil.copyfile(Path('C:/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/board-finish-20261017/release-review/event-capture-select-r2/cnc3_runtime_events.v'),inputs/'cnc3_runtime_events.v')\n"
    runtime=OUT/'run_full_runtime_with_capture.py';assert not runtime.exists();runtime.write_text(text.replace(marker,overlay+marker))
    mapsource=H/'map_event_dispatch_r1.py'
    maptext=mapsource.read_text().replace('event-dispatch-r1','event-capture-select-r2').replace('dispatch-map','capture-map').replace('DISPATCH','CAPTURE').replace('dispatch plus','capture selector plus')
    mapping=H/'map_event_capture_full_r2.py';assert not mapping.exists();mapping.write_text(maptext)
    record={'runtime_source':str(root_source),'runtime_source_SHA256':sha(root_source),'runtime_candidate_SHA256':sha(runtime),'runtime_delta':'additional isolated capture-only events overlay; frozen tests and CPU controls unchanged','mapping_source':str(mapsource),'mapping_source_SHA256':sha(mapsource),'mapping_candidate_SHA256':sha(mapping),'mapping_delta':'capture-only candidate path, unique output folder and descriptive metadata','adopted':False}
    (OUT/'runner-derivation.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
if __name__=='__main__':main()
