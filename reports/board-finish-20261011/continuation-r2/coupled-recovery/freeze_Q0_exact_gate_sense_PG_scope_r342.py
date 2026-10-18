"""Read-only source selectors and full current contact obligations for peer CM."""
import os,psutil
for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
from pathlib import Path
import sys,json,hashlib,pickle
H=Path(__file__).resolve().parent;sys.dont_write_bytecode=True
for p in(H.parent/'field-power',H.parent/'sbc-power',H):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
from shapely.strtree import STRtree
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
model=H.parent/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl';assert sha(model)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
g,h,b,q,current=pickle.loads(model.read_bytes());source=H.parent/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(source)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';iv=K.C.inventory(source.read_bytes());prefixes=['9963e84b','ff87aa4e','6faa01ce','7b8f7e31','fe8ccdb0'];selected=[]
for prefix in prefixes:
 rows=[('track',x)for x in current['tracks']if x['uuid'].startswith(prefix)]+[('via',x)for x in current['vias']if x['uuid'].startswith(prefix)];assert len(rows)==1;kind,t=rows[0];assert t['uuid']in iv[3];selected.append((kind,t))
out=H/'Q0-actual-gate-sense-PG-contact-obligations-r342';assert not out.exists();out.mkdir();context=K.hole_context(current);netgroups={};records={};bank=[]
for net in sorted({K.L.norm(t['net'])for kind,t in selected}):
 uf,groups=K.physical(current,net,context);netgroups[net]=groups;records[net]=[r for xs in groups for r in xs]
for kind,t in selected:
 uid=t['uuid'];raw=iv[3][uid];chunk=out/(uid+'.original-native-chunk');chunk.write_bytes(raw);net=K.L.norm(t['net']);groups=netgroups[net];containing=[xs for xs in groups if any(r['kind']==kind and r['uuid']==uid for r in xs)];assert containing
 layers=sorted({r['layer']for xs in containing for r in xs if r['kind']==kind and r['uuid']==uid});hits=[]
 for layer in layers:
  targets=[r for xs in containing for r in xs if r['kind']==kind and r['uuid']==uid and r['layer']==layer]
  for row in records[net]:
   if row['layer']!=layer or row['uuid']==uid:continue
   for target in targets:
    d=target['shape'].distance(row['shape'])
    if d>.000002:continue
    intersection=target['shape'].intersection(row['shape']);hit={'kind':row['kind'],'uuid':row['uuid'],'layer':layer,'raw_net':row['net'],'ref':row.get('ref'),'pin':row.get('pin'),'contact_distance_mm':d,'finite_physical_overlap_mm2':intersection.area,'physical_overlap_WKB_sha256':K.C.sha(intersection.wkb),'native_selector_still_needs_complete_actual_native_contact_gate':True};hits.append(hit)
    if not intersection.is_empty:(out/(uid+'-'+row['uuid']+'-'+layer+'.contact.wkb')).write_bytes(intersection.wkb)
 bank.append({'kind':kind,'uuid':uid,'exact_current_native_geometry':t,'original_native_chunk_file':str(chunk),'original_native_chunk_sha256':sha(chunk),'all_original_design_via_masks_and_flags_unchanged':True,'currently_used_physical_layers':layers,'actual_drilled_current_group_count':len(containing),'all_current_group_pad_identities':sorted({(r['uuid'],r['ref'],str(r['pin']))for xs in containing for r in xs if r['kind']=='pad'}),'all_current_group_retained_layer_keys':sorted({tuple(k)for xs in containing for k in K.keys(xs)}),'every_direct_same_layer_contact':hits,'selected_peer_wall_UUIDs_are_currently_untouched':True})
put(out/'exact-source-and-current-contact-obligations.json',bank)
r={'verdict':'READ_ONLY_CM_WALL_SOURCE_IDENTITIES_AND_CONTACT_OBLIGATIONS_NO_ROUTING_ACCEPTANCE','current_head_file':str(model),'current_head_sha256':sha(model),'native_original_parent_file':str(source),'native_original_parent_sha256':sha(source),'exact_selected_wall_count':5,'rows_file':str(out/'exact-source-and-current-contact-obligations.json'),'rows_sha256':sha(out/'exact-source-and-current-contact-obligations.json'),'all_current_original_wall_chunks_retained':True,'original_signed_widths_endpoints_interior_contacts_actual_vias_all_layers_must_be_retained':True,'full_reference_source_current_native_no_loss_gates':'OPEN; exact R155 physical failure scope remains bound separately','native_jobs':0,'models_or_board_written':False,'adopted':False,'helper_sha256':sha(__file__)};put(out/'receipt.json',r);print(json.dumps({'receipt_file':str(out/'receipt.json'),'receipt_sha256':sha(out/'receipt.json'),'selected':[(r['uuid'],r['exact_current_native_geometry'],len(r['every_direct_same_layer_contact']))for r in bank]}),flush=True)
