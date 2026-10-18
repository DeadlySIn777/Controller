"""Preserved R94 original198b/DC936 audit on the SAFE canonical head."""
from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'audit_full_power_sources_r94.py').read_text()
s=s.replace("OUT=L.OUT/'full-power-source-contact-audit-r94'","OUT=L.OUT/'SAFE-original198b-DC936-power-contact-audit-r150'")
exec(compile(s,str(p/'audit_full_power_sources_r94.py'),'exec'))
