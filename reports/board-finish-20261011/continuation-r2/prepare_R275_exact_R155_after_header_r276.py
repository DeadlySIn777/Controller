"""Compose only ROOT's sparse geometry onto the actual R157/R155 header."""
import copy,hashlib,json,pickle,sys
from pathlib import Path
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=H/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl';assert sha(base)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';g,h0,b,q0,c0=pickle.loads(base.read_bytes());assert (len(h0['tracks']),len(h0['vias']))==(86396,8006)
current=H/'U10003-HOST-field-joint-current-exact-raw-precision-bound-r253/model.pkl';assert sha(current)=='765ce30b24ed3109b7c938f964775690a99f08504c464313bcf712b078421440';rg,rh,rb,rq,rc=pickle.loads(current.read_bytes())
op=H/'U10003-HOST-shared-field-fresh-R262-sparse-current-diagnostic-r252/full-sparse-operation.pkl';d=pickle.loads(op.read_bytes());oldtracks={t['uuid']:t for t in h0['tracks']};removed={t['uuid']for t in d['removed_original_tracks']};nt=copy.deepcopy(d['new_tracks']);nv=copy.deepcopy(d['new_vias']);assert (len(removed),len(nt),len(nv))==(6,13,4)
for t in d['removed_original_tracks']:
 old=oldtracks[t['uuid']];assert (K.L.norm(old['net']),old['layer'],old['w'],list(old['a']),list(old['b']))==(K.L.norm(t['net']),t['layer'],t['w'],list(t['a']),list(t['b']))
nativeop=json.loads((H/'U10003-HOST-joint-exact-native-Cu-and-attested-pose-packet-r263/exact-native-discrete-and-pose-operation.json').read_bytes());locks={r['uuid']:r['locked_yes']for r in nativeop if r['action']=='add'and r['kind']=='segment'}
for t in nt:t['locked']=locks[t['uuid']]
h=copy.deepcopy(h0);h['tracks']=[t for t in h['tracks']if t['uuid']not in removed]+nt;h['vias']+=nv;newpads={p['uuid']:p for p in rh['pads']if p['ref']=='R10007'};assert len(newpads)==2;h['pads']=[copy.deepcopy(newpads[p['uuid']])if p['ref']=='R10007'else p for p in h['pads']];newfp=next(p for p in rh['footprints']if p['ref']=='R10007');h['footprints']=[copy.deepcopy(newfp)if p['ref']=='R10007'else p for p in h['footprints']]
assert (len(h['tracks']),len(h['vias']))==(86403,8010)
for kind,key in(('pads','uuid'),('footprints','ref')):
 before={x[key]:x for x in h0[kind]};after={x[key]:x for x in h[kind]};assert before.keys()==after.keys();assert all(after[u]==x for u,x in before.items()if x['ref']!='R10007')
q=copy.deepcopy(q0);newplanes=[copy.deepcopy(z)for z in rq if z['uuid']in{'9fe010df-73cf-5bfb-9f7a-bd227b701c3e','ee0efe05-1705-587c-ac86-49b1a7885ef9'}];assert len(newplanes)==2 and not({z['uuid']for z in newplanes}&{z['uuid']for z in q});q+=newplanes
candidate={**h,'zones':copy.deepcopy(c0['zones'])+[copy.deepcopy(z)for z in rc['zones']if z['uuid']in{p['uuid']for p in newplanes}]}
OUT=H/'R275-exact-R155-parent-plus-only-ROOT-native-header-context-r276';assert not OUT.exists();OUT.mkdir();mp=OUT/'context.pkl';mp.write_bytes(pickle.dumps((g,h,b,q,candidate),protocol=5));recipe={'status':'EXACT_R157_R155_HEADER_PLUS_ROOT_SPARSE_OPERATION_FOR_ACTUAL_CONVERSION_ONLY','base_model_SHA256':sha(base),'ROOT_local_ancestor_model_SHA256':sha(current),'context_SHA256':sha(mp),'parent_tracks_vias':[86396,8006],'after_tracks_vias':[86403,8010],'only_old_pad_FP_changes':'R10007 actual native-attested two B pads / rigidroot pose','new_tracks':13,'new_vias':4,'old_track_deletes':6,'all_OTHER_parent_pad_FP_Cu_q_geometry_exact':True,'Q0_DIC_and_CORE_ancestor_operations_NOT_overlaid':True,'placeholder_host_selected_fills_must_be_replaced_by_actual_native_R275_dump':True,'actual_source_direct_reference_current_NATIVE_fullDRC':'OPEN','no_mask_forcing':True,'native_jobs':0,'adopted':False,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(recipe,indent=1)+'\n');print('R276_AFTER_HEADER',sha(mp),sha(OUT/'receipt.json'),flush=True)
