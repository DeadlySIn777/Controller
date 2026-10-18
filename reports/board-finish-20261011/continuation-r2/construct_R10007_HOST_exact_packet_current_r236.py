"""Project only the exact HOST/resistor packet, retaining every raw failure."""
import copy,hashlib,json,pickle,sys
from pathlib import Path
from shapely import affinity,set_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import guarded_power_projection_r44 as Z
import immutable_local_fill_subtraction_r254 as IM
OUT=H/'R10007-HOST-exact-packet-current-diagnostic-r236';assert not OUT.exists();OUT.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
pp=H/'R10007-HOST-exact-native-six-track-one-via-rigid-pose-r235/exact-discrete-and-rigid-pose-packet.pkl';assert sha(pp)=='5af6bf795629fbb70854e0b61dde7e02decc9bedbf3141c5969147cd56a13402';d=pickle.loads(pp.read_bytes())
mp=H/'U10003-preserved-branch-exact-two-port-compliant-clock-fault-ground-construction-r196/model.pkl';assert sha(mp)=='dfb8050d5f45f5602692f2f4bb11c4706937a7821d57fac55a6733042314cae5';g,h0,b0,q0,before=pickle.loads(mp.read_bytes());h=copy.deepcopy(h0);q=copy.deepcopy(q0);b=copy.deepcopy(b0)
nt=d['tracks'];nv=d['vias'];assert len(nt)==6 and len(nv)==1 and not d['original_native_Cu_deletes'];assert not {t['uuid']for t in nt}&{t['uuid']for t in h['tracks']};assert nv[0]['uuid']not in {v['uuid']for v in h['vias']}
angle,dx,dy=d['model_rigid_pose_degrees_dx_dy'];assert angle==180 and (dx,dy)==(-10.5,-3.5)
transform=lambda s:affinity.translate(affinity.rotate(s,angle,origin=(218,145.217)),dx,dy)
oldpads=[p for p in h['pads']if p['ref']=='R10007'];assert len(oldpads)==2
for p in h['pads']:
 if p['ref']!='R10007':continue
 p['x'],p['y']=map(lambda x:round(x,9),transform(Point(p['x'],p['y'])).coords[0])
 p['layers']={l:K.GE.records(set_precision(transform(unary_union(K.L.poly(rs))),1e-9,mode='pointwise'))for l,rs in p['layers'].items()}
 if p.get('hole'):p['hole']=K.GE.records(set_precision(transform(unary_union(K.L.poly(p['hole']))),1e-9,mode='pointwise'))
for f in h['footprints']:
 if f['ref']!='R10007':continue
 f['x'],f['y']=d['target_root_mm_deg'][:2];f['courtyard']={side:K.GE.records(set_precision(transform(unary_union(K.L.poly(rs))),1e-9,mode='pointwise'))for side,rs in f['courtyard'].items()}
h['tracks']+=nt;h['vias']+=nv
dom=h['domains_normalized'];gap=lambda a,c:.15 if dom[K.L.norm(a)]==dom[K.L.norm(c)]else.6
newpads=[p for p in h['pads']if p['ref']=='R10007'];cutrows=[];qrows=[];raw=[]
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
 for role in ('shape','zone_outline_shape'):
  old=z[role];cuts=[s for s in cuts_for(z['net'],z['layer'],float(z['clearance_mm']),role=='shape')if s.intersects(old)]
  if not cuts:continue
  cutter=unary_union(cuts);new=old.difference(cutter);z[role]=new;gain=new.difference(old);outside=old.difference(new).difference(cutter)
  row={'UUID':z['uuid'],'role':role,'before_WKB_sha256':hashlib.sha256(old.wkb).hexdigest(),'after_WKB_sha256':hashlib.sha256(new.wkb).hexdigest(),'removed_mm2':old.difference(new).area,'gained_empty':gain.is_empty,'gained_area_mm2':gain.area,'removed_outside_exact_cutter_empty':outside.is_empty,'removed_outside_exact_cutter_area_mm2':outside.area,'only_new_discrete_and_rigid_pads':True};qrows.append(row)
  if not gain.is_empty or not outside.is_empty:raw.append({'scope':'owned_role_literal_negative','row':row})
zones=[]
for old in before['zones']:
 z={**old,'fills':{}}
 for layer,rs in old['fills'].items():
  shape=unary_union(K.L.poly(rs));cuts=[s for s in cuts_for(z['net'],layer,float(z['clearance_mm']),True)if s.intersects(shape)]
  if cuts:
   z['fills'][layer],row=IM.subtract(rs,cuts,OUT,z['uuid']+'-'+layer);cutrows.append({'UUID':z['uuid'],'layer':layer,**row})
  else:z['fills'][layer]=rs
 zones.append(z)
after={**h,'zones':zones};out=OUT/'model.pkl';out.write_bytes(pickle.dumps((g,h,b,q,after),protocol=5));(OUT/'actual-filled-negative-ledger.json').write_text(json.dumps(cutrows,indent=1)+'\n');(OUT/'owned-role-literal-negative-ledger.json').write_text(json.dumps(qrows,indent=1)+'\n');(OUT/'raw-literal-role-failures.json').write_text(json.dumps(raw,indent=1)+'\n')
receipt={'verdict':'EXACT_HOST_PACKET_PROSPECTIVE_CURRENT_DIAGNOSTIC_ALL_INDEPENDENT_SOURCE_REFERENCE_NATIVE_GATES_OPEN','packet_sha256':sha(pp),'base_model_sha256':sha(mp),'model_sha256':sha(out),'new_tracks':6,'new_ordinary_vias':1,'native_discrete_Cu_deletes':0,'native_R10007_local_FP_AST_exact':True,'predicted_native_IU_rigid_masks_require_API_attestation':True,'original_all_vias_native_positions_masks_geometry_exact':all(next(v for v in h['vias']if v['uuid']==o['uuid'])==o for o in h0['vias']),'changed_fill_scopes':len(cutrows),'owned_changed_roles':len(qrows),'raw_literal_role_failure_count':len(raw),'R196_FG_CLK_FLT_ordinary_return_reference_failures_remain':True,'R233_nine_body_withdrawal_only_nomination_requires_full_joint_FG_CLK_FLT_repair':True,'native_jobs':0,'adopted':False,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print('R236_CURRENT',sha(out),'RECEIPT',sha(OUT/'receipt.json'),'RAW_ROLE_FAILS',len(raw),flush=True)
