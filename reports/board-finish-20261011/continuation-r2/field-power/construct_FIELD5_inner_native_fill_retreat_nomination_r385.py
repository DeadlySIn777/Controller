"""Allow ledgered original-fill retreat, preserving every owned positive body."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'construct_FIELD5_inner_reference_safe_replacement_r383.py').read_text(encoding='utf-8')
s=s.replace('reference-safe-replacement-nomination-r383','native-fill-retreat-replacement-nomination-r385').replace('R383','R385')
needle="if L.norm(z['net'])==FG:soft.append({'UUID':z['uuid'],'kind':'ACTUAL_SAME_DOMAIN_GROUND_FILLED_ROLE','shape':sh});continue"
assert s.count(needle)==1
s=s.replace(needle,needle+"\n     if z['uuid']not in{qq['uuid']for qq in q}:soft.append({'UUID':z['uuid'],'kind':'ORIGINAL_NATIVE_FILLED_CU_ONLY_NORMAL_PRIORITY124_RETREAT_OUTLINE_AND_SETTINGS_EXACT','shape':sh});continue")
s=s.replace("'same_domain_ground_cut_obligations':affected","'original_fill_and_owned_same_domain_ground_cut_obligations':affected")
s=s.replace("'same_domain_ground_cuts_not_applied':True","'same_domain_ground_and_original_filled_retreats_not_applied':True")
exec(compile(s,str(H/'construct_FIELD5_inner_reference_safe_replacement_r383.py'),'exec'))
