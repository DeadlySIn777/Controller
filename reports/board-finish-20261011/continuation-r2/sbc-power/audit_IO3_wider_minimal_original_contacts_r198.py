"""Retained exact original198b/DC936 five-rail source obligations after wider join."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'audit_full_power_sources_r94.py').read_text().replace("OUT=L.OUT/'full-power-source-contact-audit-r94'","OUT=L.OUT/'IO3-wider-minimal-original198b-DC936-contact-audit-r198'")
exec(compile(s,str(P/'audit_full_power_sources_r94.py'),'exec'))
