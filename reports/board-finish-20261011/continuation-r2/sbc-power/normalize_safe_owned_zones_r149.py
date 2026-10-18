"""Preserved exact R55 operators, bound to the SAFE R148 composition."""
from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'normalize_final_owned_zones_r55.py').read_text()
s=s.replace("OUT=L.OUT/'final-owned-zone-normalization-r55'","OUT=L.OUT/'safe-owned-zone-normalization-r149'")
exec(compile(s,str(p/'normalize_final_owned_zones_r55.py'),'exec'))
