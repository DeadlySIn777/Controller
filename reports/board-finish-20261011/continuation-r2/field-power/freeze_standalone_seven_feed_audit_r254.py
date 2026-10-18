"""Expand the established audit before adapting its owned projection scope."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_all_REG_corrected_envelopes_conservative_delta_r242.py').read_text(encoding='utf-8')
old="exec(compile(s,str(H/'audit_u17_u10017_coupled_power_repairs_r155.py'),'exec'))"
new="target=H/'audit_regulated_local_replay_analytic_supplements_r254.py';assert not target.exists();target.write_text(s,encoding='utf-8')"
assert s.count(old)==1
exec(compile(s.replace(old,new),__file__,'exec'),{'__file__':__file__})
