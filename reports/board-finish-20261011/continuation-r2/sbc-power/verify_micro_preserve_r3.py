"""Verify the preserved native IO3 tiny pieces against the actual CORE Cu."""
import json,hashlib
from shapely import from_wkb
import core_lane_r2 as R
L=R.L;p=R.p
def main():
    g,*_=R.model();d=json.loads((L.OUT/'CORE-banks-micro-preserved-r3.json').read_text());plane=from_wkb((L.OUT/'CORE-In2-micro-IO3-preserved-r2.wkb').read_bytes());zones={z['uuid']:z for z in g['zones']};checks=[]
    for row in d['IO3_micro_piece_ledger']:
        z,l,poly_i,part_i=row['source_component'].split('@');part=p.hubs.components(p.base.polygons(zones[z]['fills'][l])[int(poly_i)])[int(part_i)]
        assert hashlib.sha256(part.wkb).hexdigest()==row['original_component_wkb_sha256']
        checks.append({'source_component':row['source_component'],'actual_CORE_gap_mm':plane.distance(part),'required_gap_mm':.175,'original_Cu_overlap_mm2':plane.intersection(part).area,'pass':plane.distance(part)>=.175-1e-7 and plane.intersection(part).is_empty})
    result={'exact_board':L.live.SHA,'CORE_sha256':d['candidate_plane_sha256'],'verdict':'PASS' if all(c['pass'] for c in checks) else 'FAIL','original_IO3_micro_components':len(checks),'min_actual_CORE_gap_mm':min(c['actual_CORE_gap_mm'] for c in checks),'checks':checks,'native_full_source_plane_contact_guard_open':True,'board_written':False,'native_jobs':0}
    (L.OUT/'IO3-micro-preservation-verified-r3.json').write_text(json.dumps(result,indent=2)+'\n');print(result['verdict'],len(checks),result['min_actual_CORE_gap_mm'])
if __name__=='__main__':main()
