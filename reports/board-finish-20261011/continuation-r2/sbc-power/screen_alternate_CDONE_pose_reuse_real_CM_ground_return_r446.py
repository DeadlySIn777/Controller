"""Diagnostic alternate original CDONE pose, selected LG16 reuse, no new hole."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'exact-expanded-active-R300-solid-LG-drill-CM79-ground-r434.py').read_text(encoding='utf-8')
s=s.replace('CM79-active-R300-minimal-CDONE-one-new-ordinary-ground-return-r434','CM79-alternate-CDONE-northwest-pose-selected-real-LG16-reuse-r446')
needle="actual=packet['current_Cu_and_local_native_pads'];h="
replacement="actual=copy.deepcopy(packet['current_Cu_and_local_native_pads']);subsetFile=P/'CM51-pruned-real-source-before-safe-subset-incident-terminal-handoffs-r442/only-source-before-connected-safe-CM-subset-no-old-edits.pkl';assert sha(subsetFile)=='f88507f06651daeeaa5ca904b4cd04f0c710cea427d59a599588f3b75c0331ab';subset=pickle.loads(subsetFile.read_bytes());actual['tracks']+=subset['tracks'];actual['vias']+=subset['vias'];r443=P/'CM51-retained-CORE-no-new-hole-constructive-F-DC-source-joins-r443/only-new-constructive-DC-F-tracks-no-holes-no-old-edits.pkl';assert sha(r443)=='7de6002db2fafc160769b86c6288a1184075051929dda14823e9d02ab3627bef';extra=pickle.loads(r443.read_bytes());actual['tracks']+=extra['new_tracks'];h="
assert needle in s;s=s.replace(needle,replacement)
old="rv={'uuid':'31a0cdf9-98e1-5e65-8573-5a1327438cda','net':NET,'x':117.164998,'y':199.28645,'d':.5,'drill':.2,'span':K.LAYERS,'flashed':K.LAYERS,'locked':False,'mask_provenance':'PROSPECTIVE ordinary via, actual native masks OPEN'}\n assert rv['uuid']not in {v['uuid']for v in actual['vias']}"
new="rv=next(v for v in actual['vias']if v['uuid']=='16236c3d-d499-5fe4-aa40-bd3e92ff94fc');assert(rv['x'],rv['y'],rv['d'],rv['drill'])==(116.350223,199.307697,.5,.2);assert '31a0cdf9-98e1-5e65-8573-5a1327438cda'not in {v['uuid']for v in actual['vias']}"
assert old in s;s=s.replace(old,new)
s=s.replace("vectors=[(.25,-.025)]","vectors=[(-.270,-.225)]")
# Existing prospective return is its own named barrel; own drill and pitch
# checks are vacuous only for that exact UUID, not for any other Cu/hole.
s=s.replace("if n==NET or r['uuid']==uid:continue","if n==NET or r['uuid']==uid:continue")
s=s.replace("if u!=uid and rp.distance(sh)-.1<.28","if u not in {uid,rv['uuid']}and rp.distance(sh)-.1<.28")
s=s.replace("if u!=uid and rp.distance(vp[int(j)])<.815","if u not in {uid,rv['uuid']}and rp.distance(vp[int(j)])<.815")
s=s.replace("'ground_return_unchanged':False,'only_new_ground_via':rv","'ground_return_unchanged':True,'only_new_ground_via':None,'reused_selected_prospective_ground_via':rv")
s=s.replace("'CM79-R434-","'CM79-R446-").replace("print('R434_COMPLETE'","print('R446_COMPLETE'")
s=s.replace("'active_R300_native_intent_binding':rr","'R435_frozen_NOT_ADOPTED_or_replaced':'this is an alternate diagnostic; no R435 pose/31a0/CM79 tracks replayed','selected_CM_R442_packet_SHA256':sha(subsetFile),'R443_extra_tracks_SHA256':sha(r443),'ground_return_reuse_no_extra_hole':True,'active_R300_native_intent_binding':rr")
E=P/'exact-expanded-alternate-CDONE-selected-LG16-return-r446.py';assert not E.exists();compile(s,str(E),'exec');E.write_text(s,encoding='utf-8');exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
