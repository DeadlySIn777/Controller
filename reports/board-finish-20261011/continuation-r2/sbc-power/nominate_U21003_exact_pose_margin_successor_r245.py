"""Exact derived R241 geometry with the three independently identified margins repaired.

Preserves the failed R241/R242 records; the quiet UV stem and both foreign vias
remain hard. No native write or claimed paired return is made by this nomination.
"""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'nominate_U21003_pullup_rotated_return_r241.py').read_text()
assert s.count('s=prior.read_text();start=')==1
s=s.replace('s=prior.read_text();start=',"s=prior.read_text().replace('dx=.525','dx=.4225');start=")
s=s.replace('-.25','-.4').replace('r241','r245').replace('R241','R245')
exec(compile(s,str(__file__),'exec'))
