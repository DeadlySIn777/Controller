"""Read-only exact intended-outline versus required physical landing census."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys
from pathlib import Path
from shapely import set_precision,get_precision
from shapely.geometry import Point,Polygon
from shapely.ops import unary_union
import contact_layout as C
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import regional_guarded_declared_projection_r140 as P
N=H/'REG-seven-cached-exact-analytic-guard-audit-r262';R=H/'REG-local-reference-true-copper-and-state-contract-r292';O=H/'REG7-and-1870-exact-native-landing-intent-census-r296'
def write(path,x):path.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def parts(sh):return [sh] if sh.geom_type=='Polygon' else [p for p in getattr(sh,'geoms',[]) if p.geom_type=='Polygon']
def main():
 assert not O.exists();O.mkdir();rr=json.loads((R/'receipt.json').read_text());assert sha(R/'model.pkl')==rr['model_SHA256'];_,h,b,z,_=pickle.loads((R/'model.pkl').read_bytes());nd=pickle.loads((N/'proposed-discrete.pkl').read_bytes());newids={q['uuid'] for q in nd['vias']};wanted=set(json.loads((N/'receipt.json').read_text())['new_plane_UUIDs']);rows=[];alias=[]
 for q in z:
  layer=q['layer'];is_reg=q['uuid'] in wanted
  for v in h['vias']:
   if C.norm(v['net'])!=C.norm(q['net']):continue
   is1870=v['uuid'].startswith('18701851') and layer=='In3.Cu'
   if not is_reg and not is1870:continue
   if v['net']!=q['net']:alias.append({'zone_UUID':q['uuid'],'via_UUID':v['uuid'],'zone_raw':q['net'],'via_raw':v['net']});continue
   point=Point(v['x'],v['y']);ann=point.buffer(v['d']/2,quad_segs=64).difference(point.buffer(v['drill']/2,quad_segs=64));overlap=ann.intersection(q['shape']).area
   if overlap<1e-9:continue
   outline=q['zone_outline_shape'];inside=outline.covers(point);rings=[]
   for component in parts(outline):
    for ring in component.interiors:
     hole=Polygon(ring)
     if hole.covers(point):rings.append({'hole_WKB_SHA256':P.digest(hole),'hole_area_mm2':hole.area,'hole_bounds_mm':list(hole.bounds),'source_drill_area_mm2':point.buffer(v['drill']/2,quad_segs=64).area,'hole_minus_source_drill_mm2':hole.difference(point.buffer(v['drill']/2,quad_segs=64)).area})
   rows.append({'zone_UUID':q['uuid'],'zone_label':q.get('label'),'layer':layer,'raw_net':q['net'],'via_UUID':v['uuid'],'centre_mm':[v['x'],v['y']],'diameter_drill_mm':[v['d'],v['drill']],'actual_or_prospective_bound_flash_mask':v.get('flashed'),'new_REG_ordinary_via':v['uuid'] in newids,'existing_1870_extra_In3_obligation':is1870,'positive_physical_annular_overlap_mm2':overlap,'required_attachment_centre_inside_intended_outline':inside,'centre_is_in_explicit_outline_hole':bool(rings),'hole_rows':rings,'physical_WKB_SHA256':P.digest(q['shape']),'intended_WKB_SHA256':P.digest(outline),'no_native_flash_or_contact_credit_from_host_overlap':True})
 write(O/'exact-annular-intended-landing-rows.json',rows);bad=[q for q in rows if not q['required_attachment_centre_inside_intended_outline']];required_bad=[q for q in bad if q['new_REG_ordinary_via'] or q['existing_1870_extra_In3_obligation']]
 rec={'verdict':'REQUIRED_LANDING_CENTRES_INSIDE_INTENDED_OUTLINES_NATIVE_CONFIRMATION_OPEN' if not required_bad and not alias else 'REQUIRED_INTENDED_LANDING_CORRECTION_NEEDED','R292_model_SHA256':sha(R/'model.pkl'),'R292_receipt_SHA256':sha(R/'receipt.json'),'new_REG_via_UUIDs':sorted(newids),'checks':len(rows),'raw_alias_collisions':alias,'all_centre_exclusions':bad,'required_new_or_extra_flash_centre_exclusions':required_bad,'actual_native_flash_source_contact_and_min_thickness_gate':'OPEN','native_jobs':0,'board_written':False,'adopted':False};write(O/'receipt.json',rec);print(json.dumps({'receipt_SHA256':sha(O/'receipt.json'),'checks':len(rows),'required_bad':required_bad,'all_bad':len(bad),'raw_aliases':len(alias)}),flush=True)
if __name__=='__main__':main()
