"""Locate failed R5051 annular contact in exact completed native geometry."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H/'field-power'));sys.path.insert(0,str(H/'sbc-power'))
import contact_layout as C
OUT=H/'R9-R5051-exact-actual-zone-flash-diagnosis-r117'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir()
    gp=H/'SAFE-exploratory-native-trial-r9/measure/actual-full-refill-geometry.json';assert sha(gp)=='20a225d2bfbd30206979609c10ccb5803f311c2a4c6b11afb0fdb067359e65b1'
    geom=json.loads(gp.read_bytes());p=Point(292.,209.375);ann=p.buffer(.3,quad_segs=256).difference(p.buffer(.15,quad_segs=256))
    mp=H/'sbc-power/SAFE-repaired-owned-zone-normalization-r160/model.pkl';model=pickle.loads(mp.read_bytes());rows=[]
    for q in geom['zones']:
        if 'In3.Cu' not in q['layers']:continue
        intended=unary_union(C.poly(q['outline']));actual=unary_union(C.poly(q['fills'].get('In3.Cu',[])))
        if intended.distance(p)>2. and actual.distance(p)>2.:continue
        rows.append({'UUID':q['uuid'],'raw_net':q['net'],'priority':q['priority'],'min_thickness_mm':q['min_thickness_mm'],'island_removal':q['island_removal'],'outline_distance_to_via_mm':intended.distance(p),'actual_filled_Cu_distance_to_via_mm':actual.distance(p),'outline_annular_overlap_mm2':intended.intersection(ann).area,'actual_annular_overlap_mm2':actual.intersection(ann).area,'actual_Cu_on_original_outline_mm2':actual.intersection(intended).area})
        for role,s in [('intended',intended),('actual',actual)]:
            (OUT/(q['uuid']+'.'+role+'.local.wkb')).write_bytes(s.intersection(p.buffer(3.,quad_segs=256)).wkb)
    proposals=[]
    for q in model[3]:
        if q['layer']!='In3.Cu' or q['shape'].distance(p)>2.:continue
        proposals.append({'UUID':q['uuid'],'raw_net':q['net'],'physical_annular_overlap_mm2':q['shape'].intersection(ann).area,'native_intended_annular_overlap_mm2':q.get('zone_outline_shape',q['shape']).intersection(ann).area,'physical_distance_mm':q['shape'].distance(p)})
    record={'verdict':'ACTUAL_NATIVE_R5051_FLASH_FAILURE_CAUSAL_GEOMETRY_DIAGNOSTIC','geometry_sha256':sha(gp),'host_model_sha256':sha(mp),'via_UUID':'18701851-0390-4dc4-b03d-f8e1cd66c395','via_mm':[292.,209.375],'native_diameter_drill_mm':[.6,.3],'native_zone_rows':rows,'host_proposal_rows':proposals,'native_jobs':0,'board_written':False,'adopted':False}
    (OUT/'receipt.json').write_text(json.dumps(record,indent=1)+'\n');print(json.dumps(record),flush=True)
if __name__=='__main__':main()
