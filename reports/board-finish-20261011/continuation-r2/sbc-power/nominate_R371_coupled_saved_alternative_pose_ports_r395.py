"""Reuse closed pad/census nominations; vary only already eligible owned-blocker pairs."""
from pathlib import Path
P=Path(__file__).resolve().parent
source=(P/'exact-expanded-coupled-F-reconnect-joint-source-LG-r394.py').read_text(encoding='utf-8').replace('CM79-R371-coupled-F-reconnect-joint-minimal-source-LG-support-r394','CM79-R371-coupled-saved-alternative-pose-port-function-reconnect-r395').replace('R394','R395')
source=source.replace('import sys,json,pickle,hashlib,time,math,uuid,traceback','import sys,json,pickle,hashlib,time,math,uuid,traceback,copy')
old="attempts=[];winner=None;fixed={};holefixed={};additionalLGSupport=[]"
new="""attempts=[];winner=None;fixed={};holefixed={};additionalLGSupport=[]
 from nominate_R371_coupled_R7036_minimal_rigid_pad_poses_r391 import moved
 portRows=json.loads((H/'sbc-power/CM79-R371-R7035-one-ENC-ordinary-signal-via-existing-LG-return-eligibility-r388/finite-ordinary-signal-via-original-source-return-old-mask-native-guard-census.json').read_text()); selected={}
 for rr in portRows:
  if len(rr['deficits'])!=2 or {x.get('UUID',x.get('ref'))for x in rr['deficits']}!={'425e7f48-d649-4152-89d7-97554df1c73f','R7036'}:continue
  selected[(tuple(rr['host_R7035_pose']),tuple(rr['new_signal_xy']))]=rr
 prior=poses[:8]; alternatives=[]
 for rr in selected.values():
  mm35=moved(s35,rr['host_R7035_pose']);sig=Point(*rr['new_signal_xy']);currentConservativeRef=fullref.difference(Z.bounded_buffer(sig,.525));ioBody=Z.bounded_buffer(LineString(rr['successful_IO3_reconnect']['path']),.1)
  for oldpose in prior:
   mm36=oldpose['R7036']
   if mm36['court'].distance(sig)<.275 or mm36['court'].distance(mm35['court'])<.025:continue
   if any(not np['shape'].difference(currentConservativeRef).is_empty for mm in(mm35,mm36)for np in mm['pads']):continue
   if any(np['shape'].distance(sig)-.25<.175 or np['shape'].distance(sig)-.1<.28 or np['shape'].distance(ioBody)<.175 for np in mm36['pads']):continue
   if any(np['shape'].distance(op['shape'])<.175 for np in mm36['pads']for op in mm35['pads']if L.norm(np['old']['net'])!=L.norm(op['old']['net'])):continue
   np=copy.deepcopy(oldpose);np['R7035']=mm35;np['selected_ordinary_ENC_port']=rr;alternatives.append(np)
 poses=alternatives;put(O/'closed-scope-alternative-pair-count.json',{'saved_R388_exact_owned_blocker_pairs':len(selected),'already_completed_R391_minimal_R7036_poses_reused':len(prior),'actual_mutual_pad_court_reference_pass_pair_count':len(poses),'no_pad_native_census_repeated':True})"""
assert source.count(old)==1;source=source.replace(old,new)
source=source.replace("'NO_COUPLED_F_RECONNECT_IN_FIRST_40_MINIMAL_PAD_LEGAL_POSES'","'NO_COUPLED_F_RECONNECT_IN_SAVED_ALTERNATIVE_OWNED_BLOCKER_PAIRS'")
E=P/'exact-expanded-coupled-saved-alternative-pose-port-r395.py';assert not E.exists();E.write_text(source,encoding='utf-8');exec(compile(source,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
