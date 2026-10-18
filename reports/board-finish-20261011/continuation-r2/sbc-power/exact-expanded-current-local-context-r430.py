"""Exact active Cu and current owned profiles, with explicitly BEFORE fills.

No current SOURCE graph or native-after mask is asserted by this context.
Every pad/footprint touching the CM ROI must remain exact in the active pose.
"""
import sys,json,pickle,time,copy,collections
from pathlib import Path
from shapely.geometry import Point,box
P=Path(__file__).resolve().parent;H=P.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
K=N.K;L=N.L;A=K.A;sha=N.sha
OUT=P/'CM79-R300-exact-current-local-context-BEFORE-fill-only-r430'
def main():
 started=time.monotonic();assert not OUT.exists();OUT.mkdir();base=H/'field-power/R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763/actual-full-R157-before-model.pkl';cur=H/'combined-R753-all-Cu-explicit-retained-actual-via-scope-r300/all-copper-expected.json';pose=H/'combined-R753-one-full-native-fill-cached-DRC-r299/native-full/before-native-all-FP-pad-pose.json';stage=H/'field-power/FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r753';board=stage/'FIELD-ROOT-Q0-DIC-DI6-known-failure-diagnostic.kicad_pcb';rolefile=stage/'only-final-shared-owned-roles-and-Q0-positive-NOT_MODEL.pkl'
 for p,digest in [(base,'dbeba66691d45ee12206f77e5060b4c845681014d19b3d9e633e9aed08a2b0c2'),(cur,'13a6a92d39e33f05a38107c7b9348c29847239671ee5b4c0ffa48a89536dead3'),(pose,'ffa3ff0880c004a6c4ad443b60bed9015a8094a04c952bdd56d09ec60d59b91d'),(board,'7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2')]:assert sha(p)==digest
 before=pickle.loads(base.read_bytes());expected=json.loads(cur.read_bytes());currentPose=json.loads(pose.read_bytes());roles=pickle.loads(rolefile.read_bytes());roi=box(108,191,126,211);local=[];padIndex=currentPose['pads']
 for p in before['pads']:
  data=padIndex[p['uuid']];xy=[data[2]/1e6,data[3]/1e6];touch=roi.covers(Point(*xy))or any(sh.intersects(roi)for ss in p['layers'].values()for sh in L.poly(ss))
  if not touch:continue
  assert str(p['num'])==str(data[0])and p['net']==data[1]and(p['x'],p['y'])==tuple(xy),('CM local current pad pose differs',p['ref'],p['num']);local.append(p['uuid'])
 assert set(padIndex)=={p['uuid']for p in before['pads']}
 current=copy.deepcopy(before);current.pop('_rooted_refs',None);current['tracks']=[];current['vias']=[];oldV={v['uuid']:v for v in before['vias']};newUnknown=[]
 for uid,r in expected['copper'].items():
  if r['kind']=='segment':current['tracks'].append({'uuid':uid,'net':r['raw_net'],'a':[x/1e6 for x in r['start_IU']],'b':[x/1e6 for x in r['end_IU']],'w':r['width_IU']/1e6,'layer':r['layer'],'locked':r['locked_yes']})
  elif r['kind']=='via':
   diam=set(r['diameters_IU'].values());assert len(diam)==1;v={'uuid':uid,'net':r['raw_net'],'x':r['at_IU'][0]/1e6,'y':r['at_IU'][1]/1e6,'d':next(iter(diam))/1e6,'drill':r['drill_IU']/1e6,'span':K.LAYERS,'locked':r['locked_yes']}
   if uid in oldV and all(v[k]==oldV[uid][k]for k in ('net','x','y','d','drill')):v['flashed']=oldV[uid]['flashed'];v['mask_provenance']='exact observed BEFORE mask retained; actual-current after still pending'
   else:v['flashed']=K.LAYERS;v['mask_provenance']='ALL layers conservative guard ONLY, no observed-mask or SOURCE claim';newUnknown.append(uid)
   current['vias'].append(v)
  else:raise AssertionError(('unsupported active Cu kind',r['kind']))
 shared=roles['shared_roles'];positive=roles['Q0_positive'];q=(list(shared.values())if isinstance(shared,dict)else list(shared))+([positive]if isinstance(positive,dict)and 'uuid'in positive else list(positive));assert all(isinstance(x,dict)and all(k in x for k in ('uuid','net','layer','shape'))for x in q)
 assert not {'de03bc75-a546-50e2-86eb-bb1dd0e34a9e','31a0cdf9-98e1-5e65-8573-5a1327438cda'}&set(expected['copper']);nativeBefore=N.R157/'copy/board.kicad_pcb';iv0=A.C.inventory(nativeBefore.read_bytes());iv1=A.C.inventory(board.read_bytes());localRefs={p['ref']for p in before['pads']if p['uuid']in local};fpUUIDs={uid for uid,rec in currentPose['footprints'].items()if rec[0]in localRefs};assert all(iv0[3][uid]==iv1[3][uid]for uid in fpUUIDs),'local actual FP/padstack/pose changed';packet={'current_Cu_and_local_native_pads':current,'actual_BEFORE_model':before,'current_owned_roles_raw_intended':q,'active_board':str(board),'no_after_fill_equivalence':True};(OUT/'only-exact-current-Cu-local-pad-pose-profiles-and-BEFORE-fill-context.pkl').write_bytes(pickle.dumps(packet,protocol=5));receipt={'status':'ACTIVE_R300_CURRENT_CU_CURRENT_LOCAL_NATIVE_PADSTACK_PROFILES_BEFORE_FILL_CONTEXT','active_board_SHA256':sha(board),'active_Cu_inventory_SHA256':sha(cur),'active_native_pad_pose_SHA256':sha(pose),'actual_BEFORE_model_SHA256':sha(base),'current_raw_role_packet_SHA256':sha(rolefile),'local_pad_count_bitexact_pose':len(local),'local_FP_count_bitexact_AST':len(fpUUIDs),'current_tracks_vias':[len(current['tracks']),len(current['vias'])],'current_owned_role_count':len(q),'full_current_raw_profile_inventory_additional_binding_required':True,'current_NEW_or_changed_via_masks_conservative_unknown_count':len(newUnknown),'current_AFTER_source_graph_fill_or_flash_evidence':False,'all49_unqualified_CM_excluded':True,'context_packet_SHA256':sha(OUT/'only-exact-current-Cu-local-pad-pose-profiles-and-BEFORE-fill-context.pkl'),'native_jobs_or_edits':0,'adopted':False,'elapsed_seconds':time.monotonic()-started};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1,allow_nan=False)+'\n',encoding='utf-8');print('R430_COMPLETE',sha(OUT/'receipt.json'),len(q),len(local),flush=True)
if __name__=='__main__':main()
