"""Make fresh native pad masks authoritative for the current HOST diagnostic."""
import hashlib,json,pickle,copy,sys
from pathlib import Path
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
OUT=H/'R10007-HOST-current-fresh-native-pad-authority-r238';assert not OUT.exists();OUT.mkdir()
mp=H/'R10007-HOST-exact-packet-current-diagnostic-r236/model.pkl';assert sha(mp)=='2f9e864a70afb766c7995ae8220c795c4aab3ed03dc279ba9ff9b2302685e057';g,h,b,q,f=pickle.loads(mp.read_bytes())
ap=H/'R10007-exact-native-B-pose-and-pad-mask-attestation-r237/receipt.json';assert sha(ap)=='07e29a3b923c4c8a0a73a2704d32939a5bcd10d7b712cba589639ec34b914a7d';a=json.loads(ap.read_bytes());assert a['exit_code']==0;native={p['UUID']:p for p in a['native_attestation']['native_pads']};rows=[]
for p in h['pads']:
 if p['ref']!='R10007':continue
 n=native[p['uuid']];assert p['num']==n['num']and p['net']==n['net']and(p['x'],p['y'])==(n['x'],n['y'])and p['smd'] and n['smd'];assert set(p['layers'])==set(n['layers'])=={'B.Cu'}
 for layer,rs in n['layers'].items():
  old=unary_union(K.L.poly(p['layers'][layer]));new=unary_union(K.L.poly(rs));rows.append({'pad_UUID':p['uuid'],'layer':layer,'host_predicted_WKB_sha256':hashlib.sha256(old.wkb).hexdigest(),'fresh_native_WKB_sha256':hashlib.sha256(new.wkb).hexdigest(),'host_minus_native_mm2':old.difference(new).area,'native_minus_host_mm2':new.difference(old).area,'fresh_native_unmodified_mask_authoritative':True})
 p['layers']=copy.deepcopy(n['layers']);p['hole']=n['hole']
# The current snapshot uses the same complete pad objects, now from native API.
f={**f,'pads':copy.deepcopy(h['pads'])};out=OUT/'model.pkl';out.write_bytes(pickle.dumps((g,h,b,q,f),protocol=5))
receipt={'verdict':'FRESH_NATIVE_R10007_PAD_MASKS_BOUND_CURRENT_CONTACT_REFERENCE_GEOMETRY_GATES_OPEN','base_model_sha256':sha(mp),'native_pose_receipt_sha256':sha(ap),'model_sha256':sha(out),'fresh_native_pad_rows':rows,'all_native_local_FP_AST_fields_source_nets_UUIDs_exact':True,'all_other_discrete_Cu_q_roles_fills_unchanged':True,'native_jobs':0,'adopted':False,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print('R238_CURRENT',sha(out),'RECEIPT',sha(OUT/'receipt.json'),flush=True)
