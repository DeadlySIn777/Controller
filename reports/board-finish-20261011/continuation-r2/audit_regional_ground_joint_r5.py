"""Independent exact current/R48 no-loss and analytic final-plane audit."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[n]='2'
import hashlib,json,math,pickle,sys
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'field-power'));sys.path.insert(0,str(H/'sbc-power'))
import contact_layout as C
import fast_contacts as F
from audit_field_io3_crossings_r15e import losses
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=1)+'\n')
def main():
 assert len(sys.argv)==3,'regional_model.pkl fresh_output_dir'
 mp,out=map(lambda p:Path(p).resolve(),sys.argv[1:]);assert out.is_relative_to(H) and not out.exists()
 mr=mp.with_name('receipt.json');r=json.loads(mr.read_bytes());assert sha(mp)==r['model_sha256']
 base=H/'sbc-power/core-pocket-outward-round-guards-r69/model.pkl';assert sha(base)=='48ce8a3f9708402708a139c8c642a447bf07e071c4e0b9216d51d8184ba54cff'
 r48=H/'sbc-power/remaining-core-feeds-r48/model.pkl';assert sha(r48)=='3e4e42806786d7d15f66f8029f674db50c4df235adcea16d2f5d7a19b7757baa'
 old,h,b,zones,current=pickle.loads(mp.read_bytes());bo,bh,bb,bz,bc=pickle.loads(base.read_bytes());_,rh,rb,rz,rc=pickle.loads(r48.read_bytes())
 assert old==bo and h==bh and b==bb and not r['new_holes'] and not r['old_Cu_deleted'] and not r['old_native_zone_outlines_changed']
 added=pickle.loads(mp.with_name('proposed-zones.pkl').read_bytes());assert sha(mp.with_name('proposed-zones.pkl'))==r['proposed_zones_sha256']
 byid={q['uuid']:q for q in zones};assert len(byid)==len(zones)
 assert all(q['uuid'] in byid and q['shape'].equals(byid[q['uuid']]['shape']) and q.get('zone_outline_shape',q['shape']).equals(byid[q['uuid']].get('zone_outline_shape',byid[q['uuid']]['shape'])) for q in bz)
 assert set(byid)-{q['uuid']for q in bz}=={q['uuid']for q in added}
 assert all(q['shape'].equals(byid[q['uuid']]['shape']) for q in added)
 out.mkdir();records,trees=F.build({**h,'zones':[]});physical_errors=[];zone_errors=[]
 def required(raw,other,local=.15):return max(.15 if h['domains_normalized'][C.norm(raw)]==h['domains_normalized'][C.norm(other)] else .6,local)+.025
 def analytic_gap(shape,q):
  if q['kind']=='via':
   v=q['source'];return shape.distance(Point(v['x'],v['y']))-v['d']/2
  if q['kind']=='track':
   t=q['source'];return shape.distance(LineString([t['a'],t['b']]))-t['w']/2
  return shape.distance(q['shape'])
 for z in zones:
  for i in trees[z['layer']].query(z['shape'].buffer(1.5),predicate='intersects'):
   q=records[z['layer']][int(i)]
   if q['net']==z['net']:continue
   gap=analytic_gap(z['shape'],q);need=required(z['net'],q['net'],float(z.get('clearance_mm',.15)))
   if gap<need-1e-9:physical_errors.append({'zone_uuid':z['uuid'],'other_uuid':q['uuid'],'other_kind':q['kind'],'layer':z['layer'],'analytic_gap_mm':gap,'required_mm':need})
 for i,z in enumerate(zones):
  for q in zones[i+1:]:
   if z['layer']!=q['layer'] or z['net']==q['net']:continue
   d=z['shape'].distance(q['shape']);need=required(z['net'],q['net'],max(float(z.get('clearance_mm',.15)),float(q.get('clearance_mm',.15))))
   if d<need-1e-9:zone_errors.append({'first_uuid':z['uuid'],'second_uuid':q['uuid'],'layer':z['layer'],'gap_mm':d,'required_mm':need})
 write(out/'analytic-geometry.json',{'physical_errors':physical_errors,'foreign_new_zone_pairs':zone_errors})
 nets=sorted({C.norm(q['net']) for q in bz+zones}|{C.norm(q['net'])for q in rz});rows=[];groups={}
 for net in nets:
  now=F.graph(current,net);before=F.graph(bc,net);early=F.graph(rc,net);lc=losses(before,now);le=losses(early,now);groups[net]=now
  row={'net':net,'R69_groups':len(before),'R48_groups':len(early),'final_groups':len(now),'R69_retained_contact_losses':lc,'R48_retained_contact_losses':le,'verdict':'PASS'if not lc and not le else 'FAIL'};rows.append(row);write(out/'checkpoint.json',rows);print('GROUND_JOINT',net,row['verdict'],len(lc),len(le),flush=True)
 sources=[('/LOGIC_GND','J11001','2'),('/motherboard_motors/FIELD_GND','J11003','2'),('/motherboard_do/FIELD_B_0V','J11005','2'),('/mc_local_power/CORE_5V','R11022','2'),('/motherboard_power_entry/FIELD_A_24V_PROTECTED','U11004','17'),('/motherboard_power_entry/FIELD_B_24V_PROTECTED','U11006','17'),('/motherboard_safety_sensor/FIELD_B_5V_PRE','L19001','2'),('/IO_3V3','R18001','2')]
 roots=[]
 for net,ref,pin in sources:
  gs=groups.get(net) or F.graph(current,net);root=next(xs for xs in gs if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin)for q in xs));rooted={q['uuid']for q in root if q['kind']=='pad'and q['pin']}
  detached=[{'pads':[C.identity(q)for q in xs if q['kind']=='pad'and q['pin']],'contact_count':len(xs)}for xs in gs if xs is not root and any(q['kind']=='pad'and q['pin']for q in xs)]
  roots.append({'net':net,'actual_source':ref+'.'+pin,'rooted_named_pads':len(rooted),'detached_named_groups':detached})
 (out/'groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));ok=not physical_errors and not zone_errors and all(x['verdict']=='PASS'for x in rows)
 report={'verdict':'PASS_REGIONAL_GROUND_CURRENT_R48_RETAINED_AND_ANALYTIC_PLANES_NATIVE_CURRENT_OPEN'if ok else'FAIL_REGIONAL_GROUND_JOINT_GEOMETRY_OR_RETAINED_CONTACTS','model_sha256':sha(mp),'input_sha256':{str(p.resolve()):sha(p)for p in(Path(__file__),mp,mr,base,base.with_name('receipt.json'),r48,mp.with_name('proposed-zones.pkl'),Path(F.__file__),Path(C.__file__))},'original_native_Cu_source_poses_rule_areas_outline_and_original_zone_definitions_exact_to_R69':True,'physical_errors':physical_errors,'foreign_new_zone_pairs':zone_errors,'rows':rows,'actual_source_roots':roots,'native_original198b_dc936_r06_r07_C9_fullsource_and_reference_current_mesh_barrel_thermal_gates':'SEPARATE_OPEN','adopted':False,'native_jobs':0,'board_written':False};write(out/'receipt.json',report)
 print(json.dumps({'verdict':report['verdict'],'physical_errors':len(physical_errors),'foreign_zone_errors':len(zone_errors),'lost_nets':[x['net']for x in rows if x['verdict']=='FAIL'],'roots':[{k:x[k]for k in('net','actual_source','rooted_named_pads')}|{'detached_named_groups':len(x['detached_named_groups'])}for x in roots]}),flush=True)
if __name__=='__main__':main()
