"""Read-only exact CM1 original-wall selectors/contact inventory for peer.

No routing, mutation, native job or source/width/current waiver. Run only
serially in the existing recovery host budget after the Q0 audit releases.
"""
from pathlib import Path
import sys,pickle,json,hashlib,time
H=Path(__file__).resolve().parent;P=H.parent
for d in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
from shapely.geometry import Point
from shapely.ops import unary_union
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
out=H/'CM1-two-other-signal-net-original-wall-obligations-r538';assert not out.exists();out.mkdir();start=time.monotonic();mp=P/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl';assert sha(mp)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';_,h,_,_,current=pickle.loads(mp.read_bytes());sp=P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(sp)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';sb=sp.read_bytes();iv=K.C.inventory(sb);pad=next(p for p in h['pads']if(p['ref'],str(p['num']))==('J15001','1'));assert(pad['x'],pad['y'])==(133.052,167.175);body=unary_union(K.L.poly(pad['layers']['F.Cu']));net=K.L.norm(pad['net']);excluded=('57aa8602','403d578d','b2ed828b');rank=[]
for t in current['tracks']:
 if t['layer']!='F.Cu'or t['uuid']not in iv[3]or K.L.norm(t['net'])==net:continue
 shape=K.A.shape({'kind':'segment',**t});d=shape.distance(body)
 if d>1.5:continue
 parsed=K.A.G.parse(t['uuid'],iv[3][t['uuid']],{});assert(parsed['net'],parsed['layer'],parsed['a'],parsed['b'],parsed['w'])==(K.L.norm(t['net']),t['layer'],t['a'],t['b'],t['w']);rank.append({'uuid':t['uuid'],'raw_net':t['net'],'layer':t['layer'],'a':t['a'],'b':t['b'],'width_mm':t['w'],'physical_pad_body_gap_mm':d,'previous_R314_CS_wall':any(t['uuid'].startswith(s)for s in excluded)})
rank.sort(key=lambda r:(r['physical_pad_body_gap_mm'],r['uuid']));put(out/'all-exact-original-F-walls-within1p5mm-of-CM1-native-pad.json',rank);selected=[r for r in rank if K.L.norm(r['raw_net'])!='/motherboard_compute/CM_HOST_SPI_CS_CMD_N'][:2];assert len(selected)==2;ctx=K.hole_context(current);groups={};rows=[]
for n in {K.L.norm(r['raw_net'])for r in selected}:groups[n]=K.physical(current,n,ctx)[1]
for wall in selected:
 uid=wall['uuid'];ch=iv[3][uid];assert sb.count(ch)==1;cp=out/(uid+'.exact-original-native-chunk');cp.write_bytes(ch);xs=groups[K.L.norm(wall['raw_net'])];own=[g for g in xs if any(r['kind']=='track'and r['uuid']==uid for r in g)];assert own;targets=[r for g in own for r in g if r['kind']=='track'and r['uuid']==uid];hits=[]
 for target in targets:
  for r in(r for g in xs for r in g if r['layer']==target['layer']and r['uuid']!=uid):
   d=target['shape'].distance(r['shape'])
   if d>.000002:continue
   overlap=target['shape'].intersection(r['shape']);hit={'kind':r['kind'],'UUID':r['uuid'],'raw_net':r['net'],'layer':r['layer'],'ref':r.get('ref'),'pin':r.get('pin'),'contact_distance_mm':d,'literal_overlap_empty':overlap.is_empty,'literal_overlap_mm2':overlap.area,'overlap_WKB_sha256':K.C.sha(overlap.wkb)};hits.append(hit)
   if not overlap.is_empty:(out/(uid+'-'+r['uuid']+'-'+r['layer']+'-exact-direct-contact.wkb')).write_bytes(overlap.wkb)
 rows.append({**wall,'exact_source_chunk_file':str(cp),'exact_source_chunk_sha256':sha(cp),'all_actual_group_pad_UUID_ref_pin_identities':sorted({(r['uuid'],r['ref'],str(r['pin']))for g in own for r in g if r['kind']=='pad'}),'all_surviving_actual_layer_contact_keys':sorted({k for g in own for k in K.keys(g)}),'all_direct_exact_same_layer_contacts':hits,'original_endpoint_interior_contact_width_raw_net_native_flags_and_source_reference_obligations_mandatory':True})
put(out/'two-nearest-additional-original-wall-source-and-contact-obligations.json',rows);result={'verdict':'READ_ONLY_CM1_ORIGINAL_NATIVE_WALL_SELECTORS_AND_CONTACTS_NO_ROUTING_ACCEPTANCE','current_source_model_sha256':sha(mp),'original_native_parent_sha256':sha(sp),'actual_native_ground_pad_UUID':pad['uuid'],'actual_ground_pad_net':pad['net'],'actual_ground_pad_xy_mm':[pad['x'],pad['y']],'ranked_original_wall_count':len(rank),'additional_two_rows_file':str(out/'two-nearest-additional-original-wall-source-and-contact-obligations.json'),'additional_two_rows_sha256':sha(out/'two-nearest-additional-original-wall-source-and-contact-obligations.json'),'selected_exact_original_wall_UUIDs':[r['uuid']for r in rows],'no_Cu_pose_hole_model_source_or_native_writes':True,'current_reference_source_native_and_peer_CM49_CM79_mutual':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-start};put(out/'receipt.json',result);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),**result}),flush=True)
