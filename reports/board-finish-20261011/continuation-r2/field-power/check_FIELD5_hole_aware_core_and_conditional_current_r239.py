"""Separate own plated drill voids from feed-core omissions; conditional model only."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
proc=psutil.Process();proc.cpu_affinity(list(range(16,28)));proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,math
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely import set_precision
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'sbc-power'))
import contact_layout as C
import regional_guarded_declared_projection_r140 as P
from inventory import sha
O=H/'FIELD5-hole-aware-core-and-conditional-current-r239'
def main():
 assert not O.exists();O.mkdir();base=H/'R54-native-wider-IO3-monitor-joint-audit-r214';nom=H/'FIELD5-actual-IO3-preserving-alternate-r225';correction=H/'FIELD5-current-reference-envelope-correction-r238';g,h,b,z,bc=pickle.loads((base/'model.pkl').read_bytes());q=pickle.loads((correction/'proposed-corrected-zone.pkl').read_bytes())[0];row=json.loads((nom/'receipt.json').read_text(encoding='utf-8'))['rows'][0];line=LineString(row['source_bridge']['points_mm']);raw=q['net'];holes=[];hole_rows=[]
 for pad in h['pads']:
  if pad['net']==raw and pad.get('num'):
   for shape in C.poly(pad.get('hole')or[]):holes.append(shape)
 for via in h['vias']:
  if via['net']==raw:
   shape=Point(via['x'],via['y']).buffer(via['drill']/2,quad_segs=64);holes.append(shape)
   if shape.intersects(line.buffer(.175)):hole_rows.append({'via_UUID':via['uuid'],'xy_mm':[via['x'],via['y']],'diameter_drill_mm':[via['d'],via['drill']],'actual_flashes':list(via['flashed'])})
 ownholes=unary_union(holes);tests=[]
 for width in (.35,.34,.30):
  core=line.buffer(width/2,quad_segs=64);required=core.difference(ownholes);tests.append({'core_width_mm':width,'full_capsule_missing_physical_mm2':core.difference(q['shape']).area,'own_plated_drill_void_intersection_mm2':core.intersection(ownholes).area,'after_own_drill_void_subtraction_missing_mm2':required.difference(q['shape']).area,'missing_from_intended_mm2':core.difference(q['zone_outline_shape']).area})
 # Explicit inherited screening assumptions; these are not physical guarantees.
 current=.36;cases=[]
 for thickness_um,temperature_c in [(35,60),(25,125)]:
  rho=1.724e-8*(1+.00393*(temperature_c-20));width_mm=.35;resistance=rho*(line.length/1000)/(width_mm/1000*thickness_um/1e6);cases.append({'Cu_thickness_um':thickness_um,'temperature_c':temperature_c,'resistivity_ohm_m':rho,'length_mm':line.length,'declared_constructor_core_mm':width_mm,'current_a':current,'uniform_strip_R_ohm':resistance,'strip_drop_v':current*resistance,'strip_Joule_w':current*current*resistance,'basis':'conditional uniform strip only; actual core omissions, source necks, spreading, barrels, return and load sharing remain separate'})
 receipt={'verdict':'HOLE_AWARE_CORE_AND_CURRENT_DIAGNOSTIC_NO_CAPACITY_QUALIFICATION','corrected_zone_sha256':sha(correction/'proposed-corrected-zone.pkl'),'hole_core_tests':tests,'endpoint_native_barrels':hole_rows,'conditional_strip_screens':cases,'complete_current_policy_a':current,'device_output_limits_and_concurrency_unchanged':True,'non_drill_core_constrictions_actual_sheet_barrel_return_thermal_transient_native':'OPEN','native_jobs':0,'board_written':False};(O/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8');print(json.dumps(receipt),flush=True);print('R239 complete',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
