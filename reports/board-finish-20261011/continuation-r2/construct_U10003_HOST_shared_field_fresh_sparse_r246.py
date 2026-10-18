"""Rebuild combined HOST/field operations from the clean DIC ancestor.

Every original/native fill projection is freshly derived, avoiding stale holes
from the old unadopted return position. This is a diagnostic, never adoption.
"""
import copy,hashlib,json,pickle,sys
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import guarded_power_projection_r44 as Z
import immutable_local_fill_subtraction_r254 as IM
OUT=H/'U10003-HOST-shared-field-fresh-R262-sparse-current-diagnostic-r246';assert not OUT.exists();OUT.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=H/'coupled-recovery/DIC-C1022-exact-R250-original-guard-construction-r262/model.pkl';assert sha(base)=='64a1f6e1597c9d757b187c3b6db85d79685ee376399bdd4738f915b87b1a0144';g,h0,b0,q0,before=pickle.loads(base.read_bytes())
hostfile=H/'R10007-HOST-current-fresh-native-pad-authority-r238/model.pkl';assert sha(hostfile)=='8bc676155f72e590cc8dd77f6315f0990d60b421f54a3c7928dc8e66ba48f91d';sg,hh,sb,sq,prior=pickle.loads(hostfile.read_bytes());assert sg==g
folder=H/'U10003-shared-return-two-source-seeded-new-FG-plane-explicit-source-bridge-nomination-r243';pr=folder/'receipt.json';assert sha(pr)=='2a2b2211a9c64fd80c2ec41fa7116913be01fc17c4867a9c656e4b6d83724e1b';r=json.loads(pr.read_bytes());packetfile=folder/'proposed-two-plane-and-joint-geometry.pkl';assert sha(packetfile)==r['packet_sha256'];d=pickle.loads(packetfile.read_bytes());joint=d['joint_geometry'];newplanes=d['replace_only_two_FG_zones'];replaced={z['uuid']for z in newplanes};assert len(replaced)==2
h=copy.deepcopy(hh);h['tracks']=[t for t in h['tracks']if t['uuid']not in joint['only_nine_unadopted_field_tracks_withdrawn']]+joint['new_tracks']+joint['exact_native_clock_track_restore'];shared=joint['new_shared_ground_via'];h['vias']=[v for v in h['vias']if v['uuid']!=shared['uuid']]+[shared]
oldtracks={t['uuid']:t for t in h0['tracks']};oldvias={v['uuid']:v for v in h0['vias']};currenttracks={t['uuid']:t for t in h['tracks']};removed=set(oldtracks)-set(currenttracks);nt=[t for t in h['tracks']if t['uuid']not in oldtracks];nv=[v for v in h['vias']if v['uuid']not in oldvias];assert len(removed)==6 and len(nt)==13 and len(nv)==4
assert all(currenttracks[u]==t for u,t in oldtracks.items()if u not in removed);assert all(next(v for v in h['vias']if v['uuid']==u)==v for u,v in oldvias.items());assert all(t['w']==.2 for t in nt)and all(v['d']==.5 and v['drill']==.2 for v in nv)
q=copy.deepcopy(q0);b=copy.deepcopy(b0);dom=h['domains_normalized'];gap=lambda a,c:.15 if dom[K.L.norm(a)]==dom[K.L.norm(c)]else.6;newpads=[p for p in h['pads']if p['ref']=='R10007'];qrows=[];raw=[]
def cuts_for(net,layer,local,physical):
 cuts=[]
 for t in nt:
  if t['layer']==layer and K.L.norm(t['net'])!=K.L.norm(net):cuts.append(Z.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+max(local,gap(t['net'],net))+.025))
 for v in nv:
  same=K.L.norm(v['net'])==K.L.norm(net)
  if same and not physical:continue
  radius=v['drill']/2 if same else max(v['drill']/2+.275,v['d']/2+max(local,gap(v['net'],net))+.025);cuts.append(Z.bounded_disk(v,radius))
 for p in newpads:
  if K.L.norm(p['net'])!=K.L.norm(net):cuts.extend(Z.bounded_buffer(s,max(local,gap(p['net'],net))+.025)for s in K.L.poly(p['layers'].get(layer,[])))
 return cuts
for z in q:
 assert z['uuid']not in replaced
 for role in ('shape','zone_outline_shape'):
  old=z[role];cuts=[s for s in cuts_for(z['net'],z['layer'],float(z['clearance_mm']),role=='shape')if s.intersects(old)]
  if not cuts:continue
  cutter=unary_union(cuts);new=old.difference(cutter);z[role]=new;gain=new.difference(old);outside=old.difference(new).difference(cutter);row={'UUID':z['uuid'],'role':role,'before_WKB_sha256':hashlib.sha256(old.wkb).hexdigest(),'after_WKB_sha256':hashlib.sha256(new.wkb).hexdigest(),'removed_mm2':old.difference(new).area,'gained_empty':gain.is_empty,'gained_mm2':gain.area,'removed_outside_declared_cutter_empty':outside.is_empty,'outside_mm2':outside.area};qrows.append(row)
  if not gain.is_empty or not outside.is_empty:raw.append(row)
q+=copy.deepcopy(newplanes);qby={z['uuid']:z for z in q};baseq={z['uuid']:z for z in q0};zones=[];fillrows=[]
for old in before['zones']:
 if old['uuid']in baseq:
  z=qby[old['uuid']]
  if z['shape'].wkb==baseq[old['uuid']]['shape'].wkb:zones.append(old)
  else:zones.append({**old,'fills':{z['layer']:K.GE.records(z['shape'])}})
  continue
 z={**old,'fills':{}}
 for layer,rs in old['fills'].items():
  shape=unary_union(K.L.poly(rs));cuts=[s for s in cuts_for(z['net'],layer,float(z['clearance_mm']),True)if s.intersects(shape)]
  for n in newplanes:
   if n['layer']==layer and K.L.norm(n['net'])!=K.L.norm(z['net']):
    cutter=Z.bounded_buffer(n['shape'],max(float(n['clearance_mm']),float(z['clearance_mm']),gap(n['net'],z['net']))+.025)
    if cutter.intersects(shape):cuts.append(cutter)
  if cuts:z['fills'][layer],row=IM.subtract(rs,cuts,OUT,z['uuid']+'-'+layer);fillrows.append({'UUID':z['uuid'],'net':z['net'],'layer':layer,**row})
  else:z['fills'][layer]=rs
 zones.append(z)
for z in newplanes:zones.append({**{k:v for k,v in z.items()if k not in ('shape','zone_outline_shape','layer')},'fills':{z['layer']:K.GE.records(z['shape'])},'prospective_not_native':True})
after={**h,'zones':zones};out=OUT/'model.pkl';out.write_bytes(pickle.dumps((g,h,b,q,after),protocol=5));(OUT/'owned-role-negative-ledger.json').write_text(json.dumps(qrows,indent=1)+'\n');(OUT/'native-filled-fresh-negative-ledger.json').write_text(json.dumps(fillrows,indent=1)+'\n');(OUT/'raw-literal-owned-role-failures.json').write_text(json.dumps(raw,indent=1)+'\n');operation={'removed_original_tracks':[oldtracks[u]for u in sorted(removed)],'new_tracks':nt,'new_vias':nv,'R10007_native_masks_file':str(hostfile.resolve()),'replaced_only_two_new_FG_planes':newplanes};(OUT/'full-sparse-operation.pkl').write_bytes(pickle.dumps(operation,protocol=5))
result={'verdict':'FRESH_R262_COMBINED_HOST_SHARED_FIELD_CURRENT_DIAGNOSTIC_ALL_ACTUAL_GATES_OPEN','base_model_sha256':sha(base),'native_HOST_model_sha256':sha(hostfile),'field_plane_packet_sha256':sha(packetfile),'model_sha256':sha(out),'original_track_replacements':len(removed),'new_tracks':len(nt),'new_ordinary_vias':len(nv),'all_original_vias_masks_positions_exact':True,'old_unadopted_return_hole_not_reused_as_native_fill_source':True,'only_R10007_FP_native_attested_rigid_pose_changed':True,'raw_literal_owned_failures':len(raw),'fresh_native_filled_scopes':len(fillrows),'full_source_direct_reference_current_native_fill_DRC':'OPEN; source arrays and new roles must be independently rebound, inherited DIC/core/r5051 failures held','native_jobs':0,'adopted':False,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n');print('R246_CURRENT',sha(out),'RECEIPT',sha(OUT/'receipt.json'),'RAW_ROLE_FAILS',len(raw),flush=True)
