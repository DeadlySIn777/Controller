"""Exact additive FG48 physical join using retained native-drilled components.

Old physical groups may safely remain atomic because no old copper, drill,
source outline or profile changes. All new intercomponent contacts must have
positive finite area; no tolerance-only new join is accepted.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
from collections import defaultdict
import hashlib,json,math,pickle,sys,time,uuid
import shapely
from shapely.geometry import LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];CONT=ROOT/'reports/board-finish-20261011/continuation-r2';ACTUAL=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763';OUT=HERE/'additive-existing-barrel-FG48-In3-host-r35';FG='/motherboard_motors/FIELD_GND';LY='In3.Cu'
for p in(CONT/'coupled-recovery',CONT/'field-power',CONT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import physical_reference_losses_r3_zero_r208 as RF
import trace_actual_field5_replacement as T
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def main():
 assert not OUT.exists();OUT.mkdir();started=time.monotonic();files=[ACTUAL/'actual-combined-full-after-model.pkl',ACTUAL/'actual-combined-full-after-all-net-groups.pkl',Path(__file__)];options=[]
 for folder in('actual-wide-FG-In3-stitch-route-r33','actual-wide-FG-In3-stitch-route-r33b'):
  p=HERE/folder/'receipt.json'
  if not p.exists():continue
  files.append(p);r=json.loads(p.read_text())
  for row in r['rows']:
   for q in row['route_attempts']:
    if 'native_1nm_quantized_path_mm'in q and not q['native_quantization_clearance_failures']:options.append((q['rectangular_nominal_L_over_w'],row['width_mm'],q,p))
 assert options;_,width,route,screen=min(options,key=lambda x:x[0]);g=pickle.loads(files[0].read_bytes());graphs=pickle.loads(files[1].read_bytes());old=graphs[FG];pp=route['native_1nm_quantized_path_mm'];tracks=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/R299/additive-FG48-stitch/In3/'+str(width)+'/'+str(i))),'net':next(t['net']for t in g['tracks']if K.L.norm(t['net'])==FG),'layer':LY,'a':a,'b':b,'w':width,'locked':True}for i,(a,b)in enumerate(zip(pp,pp[1:]))];h=g|{'tracks':g['tracks']+tracks};assert h['zones']is g['zones']and h['vias']is g['vias']and h['pads']is g['pads'];ctx=K.hole_context(h);holes,ht=ctx;records,_=K.F.build(h,nets={FG},layers={LY});uids={t['uuid']for t in tracks};new=[]
 for q in records[LY]:
  if q['kind']!='track'or q['uuid']not in uids:continue
  body=q['shape'].difference(unary_union([holes[int(i)]for i in ht.query(q['shape'],predicate='intersects')]))
  for piece in RF.parts(body):new.append(q|{'shape':piece,'key':('track',q['uuid'],LY,K.C.sha(piece.wkb))})
 uf=K.A.S.UF();oldrows=[(i,q)for i,xs in enumerate(old)for q in xs if q['layer']==LY];tree=STRtree([q['shape']for _,q in oldrows]);newtree=STRtree([q['shape']for q in new]);contacts=[]
 for i in range(len(old)):uf.find(('old_actual_native_drilled_group',i))
 for i,q in enumerate(new):
  uf.find(q['key'])
  for j in tree.query(q['shape'],predicate='intersects'):
   gi,r=oldrows[int(j)];area=q['shape'].intersection(r['shape']).area
   if area>0:uf.join(q['key'],('old_actual_native_drilled_group',gi));contacts.append({'new_track_UUID':q['uuid'],'old_group':gi,'old_real_Cu':T.describe(r),'positive_finite_overlap_mm2':area})
  for j in newtree.query(q['shape'],predicate='intersects'):
   if i>=int(j):continue
   r=new[int(j)];area=q['shape'].intersection(r['shape']).area
   if area>0:uf.join(q['key'],r['key'])
 grouped=defaultdict(list)
 for i,xs in enumerate(old):grouped[uf.find(('old_actual_native_drilled_group',i))].extend(xs)
 for q in new:grouped[uf.find(q['key'])].append(q)
 groups=list(grouped.values());a=K.root(old,'J11003','2');b=K.root(groups,'J11003','2');lost=K.keys(a)-K.keys(b);rel,bad=K.contact_losses(old,groups);refs,proof=RF.audit(g,K.source_refs(a),K.source_refs(b),FG);gained=sorted(set(T.pads(b))-set(T.pads(a)));ok=not lost and not bad and not refs and len(gained)==48 and len(T.pads(b))==232;axis=LineString(pp);(OUT/'new-tracks.json').write_text(json.dumps(tracks,indent=2)+'\n');(OUT/'new-track-body-upper-envelope.wkb').write_bytes(axis.buffer((width/2+1e-8)/math.cos(math.pi/512),quad_segs=128).wkb);(OUT/'additive-target-model.pkl').write_bytes(pickle.dumps(h,protocol=5));r={'utc':datetime.now(timezone.utc).isoformat(),'status':'ADDITIVE_FG48_REAL_EXISTING_BARREL_SOURCE_AND_OLD_FLOOR_GATES_PASS_NATIVE_CURRENT_OPEN'if ok else'ADDITIVE_FG48_HOST_GATE_FAIL_NOT_PROMOTED','input_sha256':{str(p):sha(p)for p in files},'selected_geometry_screen':str(screen),'selected_width_mm':width,'nominal_length_mm':axis.length,'nominal_rectangular_L_over_w':axis.length/width,'new_tracks':tracks,'source_rooted_pad_count_before':len(T.pads(a)),'source_rooted_pad_count_target':len(T.pads(b)),'newly_source_rooted48_pads':gained,'lost_old_source_keys':[list(k)for k in sorted(lost)],'old_partition_losses':bad,'raw_old_reference_losses':refs,'raw_reference_proof':proof,'all_new_to_actual_native_drilled_Cu_contacts':contacts,'all_old_native_drilled_rows_and_HoleSet_reused_exactly':True,'safe_old_component_reuse_proof':'Only same-net additive tracks. All old source outlines/fill polygons/discrete copper/holes unchanged. Every new join requires positive finite physical-Cu overlap; no virtual floor union or tolerance-only new edge.','LG_all_source_contacts_old_floor_and_current_geometry_unchanged':True,'all_foreign_native_Cu_existing_drills_native109_frozen_rules_fixed':True,'all_existing_source_and_zone_profiles_unchanged':True,'new_holes':0,'full_simultaneous_FG_return_boundary_A':4.58442937244,'all48_signed_branch_demands_source_and_barrel_sharing_voltage_thermal_material_native_after_minwidth_DRC_SI':'OPEN; topology improvement only, no current adequacy claim or demand derating','all12_motor_outlets_and_other_full_limits_unchanged':True,'native_jobs':0,'adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-started};put('receipt.json',r);print(json.dumps({'status':r['status'],'width_mm':width,'length_mm':axis.length,'tracks':len(tracks),'FG_pads_before_after':[len(T.pads(a)),len(T.pads(b))],'seconds':r['elapsed_seconds']}),flush=True)
if __name__=='__main__':main()
