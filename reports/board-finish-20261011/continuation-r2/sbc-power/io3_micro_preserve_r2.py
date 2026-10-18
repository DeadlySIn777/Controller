"""Preserve exact original unloaded tiny IO3 Cu pieces and their old contacts."""
import json,hashlib
from shapely import from_wkb
from shapely.ops import unary_union
import core_lane_r2 as R
L=R.L;p=R.p
def main():
    g,h,scope,native,*_=R.model();input=L.OUT/'CORE-In2-after-IO3-fingers-r4.wkb';plane=from_wkb(input.read_bytes());pieces=[];ledger=[]
    plane_guard=plane.buffer(.2)
    for z in g['zones']:
        if p.norm(z['net'])!='/IO_3V3':continue
        for poly_i,poly in enumerate(p.base.polygons(z['fills'].get('In2.Cu',[]))):
            for component_i,part in enumerate(p.hubs.components(poly)):
                if part.area<=.05 and part.intersects(plane_guard):
                    pieces.append(part);ledger.append({'source_component':z['uuid']+'@In2.Cu@'+str(poly_i)+'@'+str(component_i),'source_zone_chunk_sha256':hashlib.sha256(native[z['uuid']]).hexdigest(),'original_component_wkb_sha256':hashlib.sha256(part.wkb).hexdigest(),'area_mm2':part.area,'bounds':part.bounds,'old_native_copper_preserved_entirely':True,'all_old_adjacent_plane_contacts_and_track_contacts_required':True})
    forbidden=unary_union(pieces).buffer(.2);new=plane.difference(forbidden);file=L.OUT/'CORE-In2-micro-IO3-preserved-r2.wkb';file.write_bytes(new.wkb)
    d=json.loads((L.OUT/'CORE-banks-r3.json').read_text());d['candidate_CORE_plane_file']=str(file.resolve());d['candidate_plane_sha256']=hashlib.sha256(file.read_bytes()).hexdigest();d['IO3_micro_piece_ledger']=ledger;d['additional_IO3_original_Cu_reservation_area_mm2']=plane.area-new.area;d['host_projection_preserves_old_exact_IO3_micro_Cu']=all(new.distance(part)>=.2-1e-7 for part in pieces);d['final_IO3_native_full_contact_guard_open']=True
    (L.OUT/'CORE-banks-micro-preserved-r2.json').write_text(json.dumps(d,indent=2)+'\n');print('PRESERVED_IO3',len(pieces),'CORE_REDUCTION',plane.area-new.area,'PASS',d['host_projection_preserves_old_exact_IO3_micro_Cu'])
if __name__=='__main__':main()
