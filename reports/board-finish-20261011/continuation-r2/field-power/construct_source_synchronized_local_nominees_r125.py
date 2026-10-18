"""Use frozen R116 hard geometry for adapter-local nominees while R123 projects.

The two rejected R116 inner walls remain conservative hard bodies only.
Final source/reference replay will use the corrected successor, never this
diagnostic source geometry as acceptance evidence.
"""
from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'construct_source_synchronized_outer_joins_r124.py').read_text().replace('regulated-source-synchronized-outer-joins-r124','regulated-source-synchronized-local-nominees-r125').replace('regulated-indexed-reference-wall-repair-base-r123','regulated-source-contact-reference-audit-r116').replace('controller-regulated-outer-r124/','controller-regulated-outer-r125/')
exec(compile(s,str(p/'construct_source_synchronized_outer_joins_r124.py'),'exec'))
