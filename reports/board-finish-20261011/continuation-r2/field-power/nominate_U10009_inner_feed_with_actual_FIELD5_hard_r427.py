"""Preserve R425 mutual collision; bind the actual new FIELD5 as hard Cu."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'nominate_U10009_retained_lower_VS_barrel_r397.py').read_text(encoding='utf-8')
s=s.replace('U10009-retained-lower-VS-ordinary-barrel-coupled-nomination-r397','U10009-retained-lower-VS-R407-hard-In3-In2-feed-nomination-r427')
needle="g,h,b,q,c=pickle.loads(M.read_bytes());d=pickle.loads"
replacement="""g,h,b,q,c=pickle.loads(M.read_bytes());fieldpath=H/'FIELD5-R393-only-new-plane-margin-and-native-boundary-correction-r407/only-new-FIELD5-q-replacement.pkl';assert sha(fieldpath.parent/'receipt.json')=='87b418d8c60d700f179e8f1cd0776bf36a385ea0a4576fe35fb7d56d1f1b65c0';fq=pickle.loads(fieldpath.read_bytes());assert fq['uuid']=='8d0d8533-168b-59d0-b231-cdd89cb7bd4e'
 for role in ('shape','zone_outline_shape'):
  ww=fq[role].wkb;fq[role]=set_precision(fq[role],1e-6,mode='pointwise');assert ww==fq[role].wkb
 q=[qq for qq in q if qq['uuid']!='61cb8179-7754-5031-bbea-0da464bf816f']+[fq];d=pickle.loads"""
assert s.count(needle)==1;s=s.replace(needle,replacement)
s=s.replace("for layer in ('In1.Cu','In4.Cu','In2.Cu','In3.Cu'):","for layer in ('In3.Cu','In2.Cu'):")
s=s.replace("uuid.NAMESPACE_URL,vid+'/inner'","uuid.NAMESPACE_URL,vid+'/inner/R427/'+layer")
s=s.replace("'outer_B_reference_full_body':'OPEN'","'outer_B_reference_full_body':'OPEN','R411_In1_ground_and_reference_failure_preserved':True,'R425_FIELD5_peer_overlap_mm2':2.680528985676804,'hard_FIELD5_R407_packet_sha256':sha(fieldpath),'hard_only_not_whole_field_model_overlay':True,'only_new_positive_plane_layers_searched':['In3.Cu','In2.Cu']")
s=s.replace('R397 candidate','R427 candidate')
exec(compile(s,str(H/'nominate_U10009_retained_lower_VS_barrel_r397.py'),'exec'))
