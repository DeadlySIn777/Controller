"""Preserve R490 wrapper failure; transform only the actual full auditor."""
from pathlib import Path
H=Path(__file__).resolve().parent;base=H/'audit_Q0_R488_final_owned_current_r490.py'
code=base.read_text().replace('Q0-R488-final-owned-current-r490','Q0-R488-final-owned-exact-wrapper-r492').replace('Q0_R490_','Q0_R492_').replace('if "start=time.monotonic();out=H/"in source:',"if source.startswith('\"\"\"Independent sparse actual-fill audit;'):")
exec(compile(code,str(base),'exec'))
