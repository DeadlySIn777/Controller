"""Sparse REG/U25 operations on exact current CORE/DIC; no stale overlay."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,copy,sys,time
from pathlib import Path
from shapely import set_precision,get_precision
from shapely.geometry import LineString,Polygon,MultiPolygon
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for x in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/x))
import audit_aux_exact_raw as A
import contact_layout as L
import complete_geometry_r2 as G
import guarded_declared_settings_projection_r58 as N
import immutable_local_fill_subtraction_r254 as IM
import restore_SAFE_generated_precision_states_r168 as PS
from inventory import sha
ED='ed7b6af5-93e5-5f20-8977-d10ca721564d';D8='d8d8bdad-3845-5659-b172-4d0e231cdadc';IDS={ED,D8}
O=H/'REG312-U25-sparse-actual-R256-current-composition-r354'
B=H.parent/'coupled-recovery/DIC-C1022-exact-R250-current-construction-r256'
R=H/'REG7-native-support-minimal-current-delta-r312';U=H/'U11025-exact-health-ground-native-owned-recipe-r350'
def write(f,v):f.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def digest(s):return A.C.sha(s.wkb)
def native_cut(shape,cut):
 before=set_precision(shape,0);after=set_precision(before.difference(set_precision(cut,0)),1e-6,mode='pointwise');rows=[]
 for k in range(24):
  gain=set_precision(after,0).difference(before)
  if gain.area<=1e-12:break
  reserve=set_precision(N.bounded_buffer(gain,.000003),0);after=set_precision(set_precision(after,0).difference(reserve),1e-6,mode='pointwise');rows.append({'iteration':k,'actual_gain_SHA256':digest(gain),'actual_gain_mm2':gain.area,'only_local_3nm_negative_reserve_SHA256':digest(reserve)})
 else:raise AssertionError('integer remove-only operation did not converge')
 assert set_precision(after,0).difference(before).area<=1e-12
 return after,rows
def move_vertex(shape,old,new):
 result=[];hits=0
 for p in IM.RF.parts(shape):
  rings=[]
  for r in (p.exterior,*p.interiors):
   cs=[]
   for xy in r.coords:
    if tuple(xy)==tuple(old):cs.append(tuple(new));hits+=1
    else:cs.append(tuple(xy))
   rings.append(cs)
  result.append(Polygon(rings[0],rings[1:]))
 assert hits==1,('bound exact local vertex missing or duplicated',hits)
 return set_precision(result[0] if len(result)==1 else MultiPolygon(result),1e-6,mode='pointwise')
def main():
 assert not O.exists();O.mkdir();started=time.monotonic();assert sha(B/'model.pkl')=='7b4c123a051f7b177c928b7a02c479776237c198989f3c1a24d722c29dd25573';g,h0,b0,z0,before=pickle.loads((B/'model.pkl').read_bytes());PS.restore_bound_generated_precision_states(b0,z0);h=copy.deepcopy(h0);b=copy.deepcopy(b0);z=copy.deepcopy(z0)
 manifest=json.loads((R/'owned-file-manifest.json').read_text());assert sha(R/'receipt.json')=='6aaa5037a045da3f492bb46315f2f69e509501299af8257364cb2e7948b518c3'
 for name,s in manifest.items():assert sha(R/name)==s
 assert sha(U/'receipt.json')=='9dea5de413ac3531e28275d05d589adadc7242e73d6cba4c8a8fa6657161944c';rd=pickle.loads((R/'new-REG-discrete.pkl').read_bytes());ud=pickle.loads((U/'proposed-discrete.pkl').read_bytes());nz=pickle.loads((R/'new-REG7-zones.pkl').read_bytes());assert(len(nz),len(rd['vias']),len(rd['tracks']),len(ud['vias']),len(ud['tracks']))==(7,4,10,1,6)
 source=H.parent/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';raw=A.read(source);assert A.C.sha(raw)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';identity=A.N.SourceNets(raw);iv=A.C.inventory(raw);oldtracks={t['uuid']:t for t in h['tracks']};deleted={};delete_rows=[]
 for row in json.loads((R/'three-exact-owned-U17-delete-rows.json').read_text()):
  uid=row['uuid'];ch=A.read(row['chunk_path']);assert A.C.sha(ch)==row['exact_original_chunk_sha256'];assert iv[3][uid]==ch;deleted[uid]=ch;delete_rows.append({'owner':'REG_U17',**row})
 ur=json.loads((U/'receipt.json').read_text())
 for row in ur['delete_rows']:
  uid=row['uuid'];path=row.get('chunk_path',row.get('exact_chunk_path'));ch=A.read(path);assert iv[3][uid]==ch;deleted[uid]=ch;delete_rows.append({'owner':'U25_HEALTH',**row})
 assert len(deleted)==14 and set(deleted)<=set(oldtracks)
 for uid,ch in deleted.items():
  pp=A.G.parse(uid,ch,{});t=oldtracks[uid];assert(pp['kind'],pp['net'],pp['layer'],pp['w'],pp['a'],pp['b'])==('segment',L.norm(t['net']),t['layer'],t['w'],t['a'],t['b'])
 nt=rd['tracks']+ud['tracks'];nv=rd['vias']+ud['vias'];oldids={p['uuid']for p in h['tracks']+h['vias']};newids={p['uuid']for p in nt+nv};assert len(newids)==21 and not newids&oldids
 for item in nt+nv+nz:assert identity.raw(L.norm(item['net']))==item['net'],('raw net drift',item['uuid'],item['net'])
 h['tracks']=[t for t in h['tracks']if t['uuid']not in deleted]+nt;h['vias']+=nv
 for key in h0:
  if key not in ('tracks','vias'):assert h[key]==h0[key],key
 oldmap={q['uuid']:q for q in z0};zm={q['uuid']:q for q in z};assert not {q['uuid']for q in nz}&set(zm);cache={};role_rows=[]
 def primitives(net,local,layer,physical=True):
  rows=[]
  for v in nv:
   same=L.norm(net)==L.norm(v['net'])
   if same and not physical:continue
   radius=v['drill']/2 if same else max(v['drill']/2+.275+.000100,v['d']/2+max(G.gap(h,net,v['net']),local)+.025+.000100);key=('via',v['uuid'],radius)
   if key not in cache:cache[key]=set_precision(N.bounded_disk(v,radius),0)
   rows.append((v['uuid'],'own_physical_drill_only'if same else'new_foreign_annulus_drill_guard',cache[key]))
  for t in nt:
   if t['layer']!=layer or L.norm(net)==L.norm(t['net']):continue
   radius=t['w']/2+max(G.gap(h,net,t['net']),local)+.025+.000100;key=('track',t['uuid'],radius)
   if key not in cache:cache[key]=set_precision(N.bounded_buffer(LineString([t['a'],t['b']]),radius),0)
   rows.append((t['uuid'],'new_true_track_caps_guard',cache[key]))
  for q in nz:
   if q['layer']!=layer or L.norm(net)==L.norm(q['net']):continue
   distance=max(G.gap(h,net,q['net']),local,q.get('clearance_mm',.15))+.025;key=('zone',q['uuid'],distance)
   if key not in cache:cache[key]=set_precision(N.bounded_buffer(q['zone_outline_shape'],distance),0)
   rows.append((q['uuid'],'new_REG_declared_intended_outline_guard',cache[key]))
  return rows
 # Every owned current role is the starting point. Only truly intersecting
 # newly introduced masks are replayed; unrelated WKB/settings stay exact.
 for q in z:
  for role in ('shape','zone_outline_shape'):
   old=q[role];local=[r for r in primitives(q['net'],q.get('clearance_mm',.15),q['layer'],role=='shape')if r[2].intersects(old)]
   if not local:continue
   cut=unary_union([r[2]for r in local]);after=set_precision(old,0).difference(cut)if role=='shape'and q['uuid']in IDS else native_cut(old,cut)[0];q[role]=after;cf=O/(q['uuid']+'-'+role+'-only-new-primitives.wkb');cf.write_bytes(cut.wkb);role_rows.append({'UUID':q['uuid'],'role':role,'step':'fresh_current_new_primitives_only','before_SHA256':digest(old),'after_SHA256':digest(after),'only_local_cut_file':str(cf.resolve()),'only_local_cut_SHA256':sha(cf),'new_primitive_UUIDs':[r[0]for r in local],'positive_mm2':set_precision(after,0).difference(set_precision(old,0)).area})
 # Frozen local reference/actual-native point cut families, replayed onto
 # these current roles. Never restore a prototype's full replacement q.
 for cut in pickle.loads((R/'only-two-local-owned-correction-cutters.pkl').read_bytes()):
  q=zm[cut['owned_UUID']];mask=set_precision(cut['shape'],0);assert sha(Path(cut['cutter_file']))==cut['cutter_file_SHA256']
  for role in ('shape','zone_outline_shape'):
   old=q[role];after=set_precision(old,0).difference(mask)if role=='shape'else native_cut(old,mask)[0];q[role]=after;role_rows.append({'UUID':q['uuid'],'role':role,'step':cut['kind'],'before_SHA256':digest(old),'after_SHA256':digest(after),'exact_R312_cutter_SHA256':digest(mask),'positive_mm2':set_precision(after,0).difference(set_precision(old,0)).area})
 localops=[]
 for op in pickle.loads((R/'native-intended-only-local-operations.pkl').read_bytes()):
  uid=op.get('owned_UUID',op.get('UUID'));q=zm[uid];old=q['zone_outline_shape']
  if op['kind']=='native_intended_only_local_gain_cut':after=native_cut(old,op['shape'])[0]
  else:assert op['kind']=='exact_integer_vertex_replacement_only';after=move_vertex(old,op['explicit_old_vertex_mm'],op['explicit_new_vertex_mm'])
  gain=set_precision(after,0).difference(set_precision(old,0));q['zone_outline_shape']=after;localops.append({'UUID':uid,'kind':op['kind'],'before_SHA256':digest(old),'after_SHA256':digest(after),'positive_intended_only_mm2':gain.area,'positive_intended_only_SHA256':digest(gain),'no_effective_physical_added_credit':True})
 for uid in IDS:
  q=zm[uid];old=set_precision(q['shape'],0);after=old.intersection(set_precision(q['zone_outline_shape'],0));assert after.difference(old).is_empty;q['shape']=after;role_rows.append({'UUID':uid,'role':'shape','step':'literal_physical_inside_final_current_native_intended','before_SHA256':digest(old),'after_SHA256':digest(after),'positive_mm2':0,'unsupported_after_mm2':after.difference(set_precision(q['zone_outline_shape'],0)).area})
 z+=nz
 for q in nz:
  for role in ('shape','zone_outline_shape'):
   ww=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert q[role].wkb==ww
 # Immutable actual current records receive only fresh primitive masks and
 # literal changed-role withdrawals. Deleted tracks never reclaim old fill.
 actual=[];fill_rows=[]
 for old in before['zones']:
  qq=copy.deepcopy(old);isowned=old['uuid']in oldmap
  for layer,recs in old['fills'].items():
   original=unary_union(L.poly(recs));rows=[r for r in primitives(old['net'],old.get('clearance_mm',.15),layer,True)if r[2].intersects(original)];cuts=[r[2]for r in rows]
   if isowned:
    withdrawal=set_precision(oldmap[old['uuid']]['shape'],0).difference(set_precision(zm[old['uuid']]['shape'],0))
    if not withdrawal.is_empty:cuts.append(withdrawal)
   if not cuts:continue
   result,proof=IM.subtract(recs,cuts,O,old['uuid']+'-'+layer);qq['fills'][layer]=result;fill_rows.append({'UUID':old['uuid'],'raw_net':old['net'],'layer':layer,'owned_current_record':isowned,'fresh_primitive_UUIDs':[r[0]for r in rows],'only_bound_owned_role_withdrawal':isowned,'immutable_per_original_record_proof':proof})
  actual.append(qq)
 for q in nz:
  actual.append({k:v for k,v in q.items()if k not in ('shape','zone_outline_shape')}|{'fills':{q['layer']:IM.records(set_precision(q['shape'],0))}})
 current={**h,'zones':actual};states=[]
 for q in z:
  for role in ('shape','zone_outline_shape'):
   grid=0 if q['uuid']in IDS and role=='shape'else 1e-6;rawrole=q[role].wkb;q[role]=set_precision(q[role],grid,mode='pointwise');assert rawrole==q[role].wkb;states.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':grid,'mode':'pointwise','unchanged_WKB_SHA256':digest(q[role]),'exact_WKB_unchanged':True})
 b['generated_precision_state_ledger']=states;b['REG312_U25_exact_sparse_current_composition']={'baseline_model_SHA256':sha(B/'model.pkl'),'REG_packet_SHA256':sha(R/'receipt.json'),'U25_packet_SHA256':sha(U/'receipt.json'),'new_owned_original_track_deletes':sorted(deleted),'new_Cu_UUIDs':sorted(newids),'no_old_effective_fill_overlay':True,'no_18701851_packet_or_native_flash_credit':True,'inherited_CORE93_041959_body_current_native_FAIL_OPEN':True}
 write(O/'exact-before-original-track-delete-ledger.json',delete_rows);write(O/'only-current-owned-role-cut-replay-ledger.json',role_rows);write(O/'explicit-native-intended-local-operation-ledger.json',localops);write(O/'immutable-current-actual-filled-record-ledger.json',fill_rows);write(O/'generated-precision-state-ledger.json',states);(O/'new-owned-discrete.pkl').write_bytes(pickle.dumps({'tracks':nt,'vias':nv,'removed':sorted(deleted)},protocol=5));(O/'new-REG-zones.pkl').write_bytes(pickle.dumps(nz,protocol=5));(O/'only-changed-current-owned-roles.pkl').write_bytes(pickle.dumps([q for q in z if q['uuid']in oldmap and any(q[r].wkb!=oldmap[q['uuid']][r].wkb for r in ('shape','zone_outline_shape'))],protocol=5));(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,current),protocol=5))
 rec={'verdict':'EXPLORATORY_EXACT_SPARSE_CURRENT_REG_U25_COMPOSITION_FULL_GATES_OPEN','baseline_R256_model_SHA256':sha(B/'model.pkl'),'REG_R312_packet_SHA256':sha(R/'receipt.json'),'U25_R350_packet_SHA256':sha(U/'receipt.json'),'new_zones':7,'new_vias':5,'new_tracks':16,'exact_before_original_track_deletes':14,'changed_old_owned_UUIDs':sorted({r['UUID']for r in role_rows}),'physical_fullrole_replacements_not_used':True,'new_native_intended_positive_operation_is_explicit':True,'intended_positive_mm2':sum(r['positive_intended_only_mm2']for r in localops),'native_actual_or_owned_records_only_remove_from_exact_current_baseline':True,'old_original_source_geometry_or_rule_definitions_changed':False,'no_whole_older_h_q_or_effective_fill_overlay':True,'inherited_CORE_wholebody_reference_gap_mm2':93.04195929171794,'inherited_ROOT42_body_current_native_FAIL_OPEN_preserved':True,'full_joint_source_directlayer_oldreference_trueCu_aperture_current_native':'OPEN','model_SHA256':sha(O/'model.pkl'),'native_jobs':0,'board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-started};write(O/'receipt.json',rec);print(json.dumps({'receipt_SHA256':sha(O/'receipt.json'),'model_SHA256':rec['model_SHA256'],'new_current_fill_delta_rows':len(fill_rows),'changed_roles':rec['changed_old_owned_UUIDs']}),flush=True)
if __name__=='__main__':main()
