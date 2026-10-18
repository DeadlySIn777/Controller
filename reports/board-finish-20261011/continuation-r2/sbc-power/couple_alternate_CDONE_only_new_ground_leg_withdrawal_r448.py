"""Retain R446; withdraw only prospective R443 CM85 leg for later reconnect."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'exact-expanded-alternate-CDONE-selected-LG16-return-r446.py').read_text(encoding='utf-8')
s=s.replace('CM79-alternate-CDONE-northwest-pose-selected-real-LG16-reuse-r446','CM79-alternate-CDONE-LG16-ONLY_NEW-CM85-leg-controlled-r448')
old="actual['tracks']+=extra['new_tracks'];h="
new="retiredONLYNEW='65f3a90e-a953-5caa-8493-4623cfc05f2f';assert retiredONLYNEW not in {t['uuid']for t in packet['current_Cu_and_local_native_pads']['tracks']};assert any(t['uuid']==retiredONLYNEW for t in extra['new_tracks']);actual['tracks']+=[t for t in extra['new_tracks']if t['uuid']!=retiredONLYNEW];h="
assert old in s;s=s.replace(old,new)
s=s.replace("LineString([[117.45,200.05],[117.7,200.025]])","LineString([[117.45,200.05],[117.18,199.825]])")
s=s.replace("'CM79-R446-","'CM79-R448-").replace("print('R446_COMPLETE'","print('R448_COMPLETE'")
s=s.replace("'ground_return_reuse_no_extra_hole':True","'ground_return_reuse_no_extra_hole':True,'controlled_only_NEW_ground_leg_withdrawal':retiredONLYNEW,'original_Cu_retirement':False,'new_CM85_ground_path_reconnect':'OPEN_REQUIRED_BEFORE_PROMOTION'")
E=P/'exact-expanded-alternate-CDONE-only-new-CM85-leg-r448.py';assert not E.exists();compile(s,str(E),'exec');E.write_text(s,encoding='utf-8');exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
