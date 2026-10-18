"""Read-only later peer screening; no composition, fill or contact credit."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys
from pathlib import Path
from shapely.geometry import Point,LineString
import contact_layout as C
from inventory import sha
H=Path(__file__).resolve().parent;ROOT=H.parent;N=H/'REG-seven-cached-exact-analytic-guard-audit-r262';R=ROOT/'CORE-wide-reserved-IO3-immutable-R214-materialized-r112';O=H/'ROOT112-vs-REG7-exact-mutual-nominee-screen-r294'
def write(path,obj):path.write_text(json.dumps(obj,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();receipt=json.loads((R/'receipt.json').read_text());assert receipt['model_sha256']=='6312b10a88b2d3614e21760d1709866d2417b419d418e20e09055eb13b8e3b7e';assert sha(R/'model.pkl')==receipt['model_sha256']
 rz=pickle.loads((R/'proposed-new-CORE-zone.pkl').read_bytes());rd=pickle.loads((R/'proposed-discrete.pkl').read_bytes());nz=pickle.loads((N/'new-owned-zones.pkl').read_bytes());nd=pickle.loads((N/'proposed-discrete.pkl').read_bytes());assert len(rz)==1 and len(nz)==7 and len(rd['vias'])==2 and len(nd['vias'])==4
 assert all(C.norm(q['net'])=='/CORE_1V2' for q in rz+rd['vias']);assert all(C.norm(q['net']) in ('/motherboard_power_entry/FIELD_5V','/motherboard_do/DOB_FIELD_3V3') for q in nz+nd['vias'])
 checks=[]
 def add(row):row['PASS']=row['actual_mm']+1e-10>=row['required_mm'];checks.append(row)
 for a in rz:
  for b in nz:
   if a['layer']!=b['layer']:continue
   for role in ('shape','zone_outline_shape'):add({'kind':'CORE_to_REG_foreign_plane','CORE_UUID':a['uuid'],'REG_UUID':b['uuid'],'layer':a['layer'],'role':role,'required_mm':max(.6,float(a.get('clearance_mm',.15)),float(b.get('clearance_mm',.15)))+.025,'actual_mm':a[role].distance(b[role])})
  for b in nd['vias']:add({'kind':'CORE_plane_to_REG_ordinary_all6_annulus','CORE_UUID':a['uuid'],'REG_UUID':b['uuid'],'layer':a['layer'],'required_mm':.625,'actual_mm':a['shape'].distance(Point(b['x'],b['y']))-b['d']/2})
  for b in nd['tracks']:
   if b['layer']!=a['layer']:continue
   add({'kind':'CORE_plane_to_REG_track_true_caps','CORE_UUID':a['uuid'],'REG_UUID':b['uuid'],'layer':a['layer'],'required_mm':.625,'actual_mm':a['shape'].distance(LineString([b['a'],b['b']]))-b['w']/2})
 for a in rd['vias']:
  for b in nz:add({'kind':'CORE_all6_annulus_to_REG_plane','CORE_UUID':a['uuid'],'REG_UUID':b['uuid'],'layer':b['layer'],'required_mm':.625,'actual_mm':b['shape'].distance(Point(a['x'],a['y']))-a['d']/2})
  for b in nd['vias']:
   distance=Point(a['x'],a['y']).distance(Point(b['x'],b['y']));add({'kind':'CORE_to_REG_ordinary_copper','CORE_UUID':a['uuid'],'REG_UUID':b['uuid'],'required_mm':.625,'actual_mm':distance-(a['d']+b['d'])/2});add({'kind':'CORE_to_REG_ordinary_drilled_holes','CORE_UUID':a['uuid'],'REG_UUID':b['uuid'],'required_mm':.275,'actual_mm':distance-(a['drill']+b['drill'])/2})
  for b in nd['tracks']:add({'kind':'CORE_all6_annulus_to_REG_track_true_caps','CORE_UUID':a['uuid'],'REG_UUID':b['uuid'],'layer':b['layer'],'required_mm':.625,'actual_mm':Point(a['x'],a['y']).distance(LineString([b['a'],b['b']]))-(a['d']+b['w'])/2})
 errors=[q for q in checks if not q['PASS']];write(O/'exact-mutual-pair-checks.json',checks)
 rec={'verdict':'EXACT_LATE_PEER_NOMINEE_PAIRS_PASS_FULL_COMPOSITION_OPEN' if not errors else 'EXACT_LATE_PEER_NOMINEE_PAIRS_CONFLICT_REQUIRES_OWNED_REPAIR','ROOT112_receipt_SHA256':sha(R/'receipt.json'),'ROOT112_model_SHA256':sha(R/'model.pkl'),'ROOT112_new_zone_SHA256':sha(R/'proposed-new-CORE-zone.pkl'),'ROOT112_new_discrete_SHA256':sha(R/'proposed-discrete.pkl'),'REG262_failed_receipt_SHA256':sha(N/'receipt.json'),'REG7_nominee_zones_SHA256':sha(N/'new-owned-zones.pkl'),'REG_nominee_discrete_SHA256':sha(N/'proposed-discrete.pkl'),'domain_gap_authority':'native raw domain contract: CORE1V2 LOGIC vs FIELD5 FA / DOB_FIELD3V3 FB; .6+.025 unchanged','checks':len(checks),'errors':errors,'no_own_return_shape_or_native_fill_overlay_performed':True,'full_oldcontacts_sources_references_current_native_gates':'OPEN','native_jobs':0,'board_written':False,'adopted':False};write(O/'receipt.json',rec);print(json.dumps({'receipt_SHA256':sha(O/'receipt.json'),'checks':len(checks),'errors':errors}),flush=True)
if __name__=='__main__':main()
