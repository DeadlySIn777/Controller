"""Literal monitor UV node and old raw UV copper, outside zone-net scopes."""
import copy,hashlib,json,pickle,sys,traceback
from pathlib import Path
H=Path(__file__).resolve().parent.parent
for d in ('sbc-power','field-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import audit_c10036_r24_full_independent_r30 as Q
from audit_field_io3_crossings_r15e import losses
O=H/'sbc-power/positive-joint-literal-UV-node-regression-r212'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,r):Path(p).write_text(json.dumps(r,indent=1)+'\n')
def keys(xs):return {(r['kind'],r['uuid']) for r in xs if r['kind'] in ('pad','track','via')}
def inventory(model,net,kind):return {r['uuid']:r for r in model[kind] if C.norm(r['net'])==net}
def main():
 assert not O.exists();O.mkdir()
 mp=H/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl'
 assert sha(mp)=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e'
 rp=mp.with_name('receipt.json');assert sha(rp)=='e8eaa4704155b733da2bf32b241a5dcca98d08b5d24d8e7b1ecf4e9b4df73d9e'
 g,h,b,z,after=pickle.loads(mp.read_bytes())
 mon=H/'SAFE-native-monitor-rotation-composition-r69/owned-operation.pkl';md=pickle.loads(mon.read_bytes())['exact_monitor_delta']
 source=H/'field-monitor-R9026-rotation-source-termination-r66/owned-delta.pkl'
 assert sha(source)=='2669504846249102a6afe479c78f627b7729d0992c48bc64f79a330f431149c5'
 original_md=pickle.loads(source.read_bytes());assert md['removed_old_track']==original_md['removed_old_track'] and md['tracks']==original_md['tracks'] and md['vias']==original_md['vias']
 endpoints=[('R9025','2'),('R9026','1'),('U9003','14')]
 ps=[next(p for p in after['pads'] if (p['ref'],p['num'])==pair) for pair in endpoints]
 raw=ps[0]['net'];net=C.norm(raw);assert all(p['net']==raw for p in ps)
 assert net=='/motherboard_motor_power/MOTOR_PWR_FIELD_A_1_UV'
 tokens={p['net'] for kind in ('pads','tracks','vias','zones','shapes') for p in after[kind] if C.norm(p.get('net',''))==net}
 assert tokens=={raw},('native raw spelling collision',tokens)
 removed=md['removed_old_track'];assert C.norm(removed['net'])==net
 oldtracks=inventory(g,net,'tracks');oldvias=inventory(g,net,'vias');oldpads=inventory(g,net,'pads')
 ht=inventory(h,net,'tracks');at=inventory(after,net,'tracks');av=inventory(after,net,'vias');ap=inventory(after,net,'pads')
 assert oldtracks[removed['uuid']]==removed and removed['uuid'] not in ht and ht==at
 retained={u:r for u,r in oldtracks.items() if u!=removed['uuid']}
 assert all(at.get(u)==r for u,r in retained.items()),'unapproved old raw UV track change'
 assert all(av.get(u)==r for u,r in oldvias.items()),'unapproved old raw UV via change'
 newUV=[r for r in md['tracks'] if C.norm(r['net'])==net];assert len(newUV)==1
 assert set(at)==set(retained)|{newUV[0]['uuid']} and at[newUV[0]['uuid']]==newUV[0]
 assert set(av)==set(oldvias) and set(ap)==set(oldpads)
 originalUVtokens={r['net'] for rows in (oldpads,oldtracks,oldvias) for r in rows.values()};assert originalUVtokens=={raw}
 # R9026.1 may move only to the exact actual native R68 rotated pad.
 native=H/'field-monitor-native-R9026-rotation-r68/receipt.json';assert sha(native)=='3fbf5fa8c80a3bb9e03328108b677777482ae884786aef4d5ea2c09612a0baa4'
 r73=H/'SAFE-monitor-real-source-reference-patch-r73/model.pkl';assert sha(r73)=='719da50c88dc6e2c64b988f81c850875f5f228e9f7407eab5c3cd17e8a44f011'
 r73h=pickle.loads(r73.read_bytes())[1];nativepad=next(p for p in r73h['pads'] if(p['ref'],p['num'])==('R9026','1'))
 assert ap[nativepad['uuid']]==nativepad
 for u,p in oldpads.items():
  if u!=nativepad['uuid']:assert ap[u]==p,('unapproved old UV pad change',u)
 # Omit only the explicitly owned obsolete track from old group comparison.
 old=copy.deepcopy(g);old['tracks']=[t for t in g['tracks'] if t['uuid']!=removed['uuid']]
 fg_before=F.graph(old,net);fg_after=F.graph(after,net);fastloss=losses(fg_before,fg_after)
 _,physical_before=Q.physical(old,net);_,physical_after=Q.physical(after,net)
 physical_loss=losses(physical_before,physical_after)
 endpoint_UUIDs={p['uuid'] for p in ps};containing=[i for i,xs in enumerate(physical_after) if endpoint_UUIDs<=keys(xs)]
 # keys includes a (kind,UUID) tuple; require literal pad roles.
 containing=[i for i,xs in enumerate(physical_after) if {('pad',u) for u in endpoint_UUIDs}<=keys(xs)]
 assert len(containing)==1,('three-pad physical node not one group',[(i,sorted({(r.get('ref'),r.get('pin')) for r in xs if r['kind']=='pad'})) for i,xs in enumerate(physical_after)])
 group=physical_after[containing[0]]
 allretained={('track',u) for u in retained}|{('via',u) for u in oldvias}|{('pad',u) for u in oldpads}
 missing=sorted(allretained-keys(group))
 # Physical pieces are separately retained, not merely a UUID total.
 piece_losses=[]
 from collections import defaultdict
 for i,xs in enumerate(physical_before):
  prior={r['key'] for r in xs if r['kind'] in ('track','via','pad')};new={r['key'] for r in group if r['kind'] in ('track','via','pad')}
  lost=prior-new
  # Only R9026 pad shape is authorized; its pad physical key remains the UUID.
  if lost:piece_losses.append({'old_group':i,'lost_physical_piece_keys':[list(k) for k in sorted(lost)]})
 ok=not fastloss and not physical_loss and not missing and not piece_losses
 put(O/'literal-native-UV-endpoint-and-retained-copper-ledger.json',{'raw_net':raw,'endpoints':[{'ref':p['ref'],'pin':p['num'],'UUID':p['uuid'],'x':p['x'],'y':p['y'],'layers':list(p['layers'])} for p in ps], 'authorized_only_removed_old_track':removed,'retained_old_tracks':list(retained.values()),'retained_old_vias':list(oldvias.values()),'exact_new_UV_track':newUV[0],'unchanged_native_raw_net_token':True,'R9026_1_exact_actual_R68_pad_matches_R73':True})
 (O/'groups.pkl').write_bytes(pickle.dumps({'old_physical_groups':physical_before,'new_physical_groups':physical_after,'old_fast_groups':fg_before,'new_fast_groups':fg_after},protocol=5))
 put(O/'receipt.json',{'verdict':'PASS_LITERAL_UV_THREE_PAD_NODE_AND_ALL_RETAINED_RAW_UV_COPPER' if ok else 'FAIL_LITERAL_UV_NODE_OR_RETAINED_RAW_COPPER','exact_positive_R214_model_sha256':sha(mp),'R214_receipt_sha256':sha(rp),'raw_UV_net':raw,'literal_endpoint_refs':[r+'.'+p for r,p in endpoints],'all_three_actual_projected_physical_pad_UUIDs_one_group':len(containing)==1,'physical_group_id':containing[0],'retained_original_UV_tracks':len(retained),'retained_original_UV_vias':len(oldvias),'original_UV_pad_UUIDs':len(oldpads),'only_authorized_old_UV_track_removed_UUID':removed['uuid'],'old_track_geometry_bound_to_original_g_and_R66':True,'old_fast_graph_contact_losses':fastloss,'old_drill_subtracted_physical_contact_losses':physical_loss,'missing_retained_keys_from_actual_three_pad_group':[list(k) for k in missing],'old_UV_physical_piece_keys_lost':piece_losses,'raw_native_token_normalization_collisions':0,'R9026_exact_R68_actual_native_pad_attestation_sha256':sha(native),'monitor_delta_R66_sha256':sha(source),'monitor_owned_operation_R69_sha256':sha(mon),'groups_sha256':sha(O/'groups.pkl'),'outside76_plane_net_scope':True,'source_threshold_sensitivity_R78_and_actual_local_ground_noise_current_native_qualification':'SEPARATE_OPEN','native_jobs':0,'board_written':False,'no_area_or_contact_waiver':True,'script_sha256':sha(__file__)})
 print('R212_COMPLETE',ok,sha(O/'receipt.json'),'UV',len(oldpads),len(retained),len(oldvias),'physical_groups',len(physical_after),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__),'native_jobs':0,'board_written':False})
  raise
