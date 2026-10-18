"""Add exact R576 DI6 items with per-record cuts on the current head.

Original zone definitions stay exact. Only ordinary new drill physical-role
cuts may change own ground q; intention retains the real barrel center.
Every native current filled array is independently local-subtracted, no
old source reconstruction or wholesale model overlay.
"""
from pathlib import Path
import sys,json,pickle,hashlib,time,copy
H=Path(__file__).resolve().parent;P=H.parent
for d in(P,P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import immutable_local_fill_subtraction_r254 as IM
import restore_field_current_mixed_precision_states_r366 as MS
from shapely.geometry import LineString
from shapely.ops import unary_union
from shapely import set_precision
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
OUT=H/'DI6-twelve-NEW-exact-current-normal-antipads-r578'
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def digest(s):return hashlib.sha256(s.wkb).hexdigest()
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();pins={}
 def pin(p,v=None):
  p=Path(p);s=sha(p);assert v is None or v==s;pins[str(p.resolve())]=s;return p
 rp=pin(H/'DI6-positive-current-path-exact-raw-owned-chunks-r576/receipt.json','8cab96a28f7d8a202d8e84e469bb88f7d631d5bb3e619d1c749adb8d8e11383d');r=json.loads(rp.read_bytes());pf=pin(r['sparse_packet_file'],'ec40b4ee91ed3e43ead2653dd4a3db5413a9053be7a8e52b7d960a0ef998f72e');op=pickle.loads(pf.read_bytes());mp=pin(H/'DIC-retired-cutter-policy-coupled-current-r556/model.pkl','95d1636e90b8d11530cbc6ba461c60f7e68272e08d1e7cd4b5863bf0a43b46d5');g,h0,b0,q0,old=pickle.loads(mp.read_bytes());h=copy.deepcopy(h0);b=copy.deepcopy(b0);q=copy.deepcopy(q0);MS.restore_bound_field_current_precision_states(b,q);nt=op['tracks'];nv=op['vias'];newids={x['uuid']for x in nt+nv};assert len(nt)==10 and len(nv)==2 and newids.isdisjoint({x['uuid']for x in h['tracks']+h['vias']});h['tracks']+=nt;h['vias']+=nv
 sourcefile=pin(P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb','eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a');identity=K.A.N.SourceNets(sourcefile.read_bytes());identity.assert_chunks(op['exact_new_chunks']);dom=h['domains_normalized'];gap=lambda a,n:.15 if dom[K.L.norm(a)]==dom[K.L.norm(n)]else .6;zones=[];roleledger=[];forbidden=[]
 def cut(x,z):
  same=K.L.norm(x['net'])==K.L.norm(z['net']);via='d'in x;req=max(float(z['clearance_mm']),gap(x['net'],z['net']))+.025;rad=x['drill']/2 if via and same else max(x['drill']/2+.275,x['d']/2+req)if via else x['w']/2+req;mask=K.Z.bounded_disk(x,rad)if via else K.Z.bounded_buffer(LineString([x['a'],x['b']]),rad);return same,rad,mask
 for z in q:
  samecuts=[]
  for x in nt+nv:
   via='d'in x
   if not via and(x['layer']!=z['layer']or K.L.norm(x['net'])==K.L.norm(z['net'])):continue
   same,rad,mask=cut(x,z)
   for role in('shape','zone_outline_shape'):
    hit=mask.intersection(z[role])
    if not hit.is_empty and not same:forbidden.append({'new_UUID':x['uuid'],'owned_UUID':z['uuid'],'role':role,'mask_SHA256':digest(mask),'hit_WKB_SHA256':digest(hit),'required_radius_mm':rad})
   if same and via and not mask.intersection(z['shape']).is_empty:samecuts.append((x,mask))
  if not samecuts:continue
  before=z['shape'];oldsha=digest(before);shape=before.difference(unary_union([c for x,c in samecuts]));gain=set_precision(shape,0).difference(set_precision(before,0));f=OUT/(z['uuid']+'-raw-own-drill-gain.wkb');f.write_bytes(gain.wkb);assert gain.is_empty,'Strict literal physical role gain requires explicit new local repair'
  row=next(row for row in b['generated_precision_state_ledger']if(row['new_generated_UUID'],row['role'])==(z['uuid'],'shape'));assert row['unchanged_WKB_SHA256']==oldsha;grid=row['grid_mm'];tagged=set_precision(shape,grid,mode='pointwise');assert tagged.wkb==shape.wkb;z['shape']=tagged;row['unchanged_WKB_SHA256']=digest(shape);roleledger.append({'UUID':z['uuid'],'layer':z['layer'],'only_role':'shape','before_SHA256':oldsha,'after_SHA256':digest(shape),'same_RAW_NEW_drill_UUIDs':[x['uuid']for x,c in samecuts],'exact_mask_SHA256':[digest(c)for x,c in samecuts],'intended_barrel_centres_and_profile_unchanged':True,'literal_positive_gain_EMPTY':True})
 put(OUT/'unexpected-foreign-owned-role-cuts-HELD.json',forbidden);put(OUT/'only-own-drill-physical-role-negative-ledger.json',roleledger);assert not forbidden,'Current positive power/ground roles stay hard; nominate separate bounded correction if needed';MS.restore_bound_field_current_precision_states(b,q)
 ledger=[]
 for zz in old['zones']:
  z={**zz,'fills':{}}
  for ly,rs in zz['fills'].items():
   ps=K.L.poly(rs);body=unary_union(ps);cuts=[];rows=[]
   for x in nt+nv:
    via='d'in x
    if not via and(x['layer']!=ly or K.L.norm(x['net'])==K.L.norm(z['net'])):continue
    same,rad,mask=cut(x,z)
    if not mask.intersects(body):continue
    cp=OUT/(z['uuid']+'-'+ly+'-'+x['uuid']+'-exact-new-primitive-cutter.wkb');cp.write_bytes(mask.wkb);cuts.append(mask);rows.append({'new_UUID':x['uuid'],'exact_cutter_file':str(cp.resolve()),'exact_cutter_SHA256':sha(cp),'analytic_radius_mm':rad,'same_raw_net_own_drill_only':same})
   if not cuts:z['fills'][ly]=rs;continue
   after,proof=IM.subtract(rs,cuts,OUT,z['uuid']+'-'+ly);z['fills'][ly]=after;ledger.append({'zone_UUID':z['uuid'],'layer':ly,'raw_net':z['net'],'native_or_owned_local_clearance_mm':float(z['clearance_mm']),'before_WKB_SHA256':digest(body),'after_WKB_SHA256':proof['after_WKB_sha256'],'immutable_per_record_proof':proof,'cutters':rows})
  zones.append(z)
 after={**h,'zones':zones};put(OUT/'incremental-immutable-current-fill-cut-ledger.json',ledger);model=OUT/'model.pkl';model.write_bytes(pickle.dumps((g,h,b,q,after),protocol=5));packet=OUT/'only-twelve-DI6-items-and-current-local-negative-fill-role-delta.pkl';packet.write_bytes(pickle.dumps({'tracks':nt,'vias':nv,'exact_new_chunks':op['exact_new_chunks'],'original_deletes':{},'actual_fill_ledger':ledger,'same_own_drill_role_ledger':roleledger,'source_current_parent_SHA256':sha(mp)},protocol=5));rec={'verdict':'CONCRETE_DI6_NEW_ONLY_CURRENT_COMPOSITION_INDEPENDENT_ALL_GATES_OPEN','model_file':str(model.resolve()),'model_SHA256':sha(model),'sparse_operation_file':str(packet.resolve()),'sparse_operation_SHA256':sha(packet),'exact_parent_model_SHA256':sha(mp),'R576_constructor_receipt_SHA256':sha(rp),'NEW_tracks':len(nt),'NEW_ordinary_vias':len(nv),'original_native_Cu_FP_rule_outline_mask_changes':0,'owned_same_raw_physical_drill_role_changes':len(roleledger),'foreign_owned_role_changes':0,'native_current_filled_family_count':len(ledger),'all_UNMODIFIED_current_filled_arrays_retained_exact':True,'all_old_source_current_r06_r07_contacts_direct_reference_newbody_ordinary_clearance_minfeature_native_SI_current':'OPEN','all_inherited_raw_reference_CORE_R7_ROOT42_native_planner_failures_preserved':True,'input_SHA256':pins,'output_SHA256':{str(f.resolve()):sha(f)for f in OUT.iterdir()if f.is_file()},'native_jobs':0,'adopted':False,'board_written':False,'elapsed_seconds':time.monotonic()-st};put(OUT/'receipt.json',rec);print('R578_COMPLETE',sha(OUT/'receipt.json'),sha(model),len(ledger),len(roleledger),flush=True)
if __name__=='__main__':main()
