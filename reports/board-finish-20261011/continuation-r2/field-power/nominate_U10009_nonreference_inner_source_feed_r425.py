"""Preserve rejected In1 feed; search nonreference In2/In3 plane layers."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'nominate_U10009_retained_lower_VS_barrel_r397.py').read_text(encoding='utf-8')
s=s.replace('U10009-retained-lower-VS-ordinary-barrel-coupled-nomination-r397','U10009-retained-lower-VS-nonreference-In2-In3-feed-nomination-r425')
s=s.replace("for layer in ('In1.Cu','In4.Cu','In2.Cu','In3.Cu'):","for layer in ('In2.Cu','In3.Cu'):")
s=s.replace("uuid.NAMESPACE_URL,vid+'/inner'","uuid.NAMESPACE_URL,vid+'/inner/R425/'+layer")
s=s.replace("'outer_B_reference_full_body':'OPEN'","'outer_B_reference_full_body':'OPEN','R411_In1_ground_and_reference_failure_preserved':True,'only_new_positive_plane_layers_searched':['In2.Cu','In3.Cu']")
s=s.replace('R397 candidate','R425 candidate')
exec(compile(s,str(H/'nominate_U10009_retained_lower_VS_barrel_r397.py'),'exec'))
