"""Remove only newly created, source-free F fill scraps from the bounded bus."""
import json,hashlib
from pathlib import Path
from shapely import from_wkb
from shapely.geometry import Point
import local_copper_r3 as T
def main():
    L=T.L;p=T.p;d=json.loads((L.OUT/'SBC-F-bounded-bus-r3.json').read_text());plane=from_wkb(Path(d['allocated_SBC_F_plane_file']).read_bytes());pieces=p.hubs.components(plane);source=Point(117.126875,162.283594);main=next(q for q in pieces if q.covers(source));file=L.OUT/'SBC-F-bounded-bus-r4.wkb';file.write_bytes(main.wkb)
    result={**d,'allocated_SBC_F_plane_file':str(file.resolve()),'allocated_plane_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'allocated_area_mm2':main.area,'only_new_unloaded_source_free_fill_scraps_removed_mm2':plane.area-main.area,'source_r3_recipe_sha256':hashlib.sha256((L.OUT/'SBC-F-bounded-bus-r3.json').read_bytes()).hexdigest()}
    (L.OUT/'SBC-F-bounded-bus-r4.json').write_text(json.dumps(result,indent=2)+'\n');print('SOURCE_COMPONENT',main.area,'NEW_SCRAPS_REMOVED',plane.area-main.area)
if __name__=='__main__':main()
