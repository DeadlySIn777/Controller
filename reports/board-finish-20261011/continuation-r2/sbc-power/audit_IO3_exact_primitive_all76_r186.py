"""Fresh all76/source/strict-positive-reference audit of the minimal correction."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'audit_original_IO3_all76_incremental_r180.py').read_text()
s=s.replace('original-IO3-full-all76-incremental-audit-r180','IO3-exact-primitive-all76-incremental-audit-r186').replace('R180_','R186_')
exec(compile(s,str(P/'audit_original_IO3_all76_incremental_r180.py'),'exec'))
