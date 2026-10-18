"""Preserve R468 partial diagnosis; encode empty target-fill bounds as null."""
from pathlib import Path
H=Path(__file__).resolve().parent;base=H/'diagnose_Q0_R466_ground_neck_and_new_SMD_r468.py'
code=base.read_text().replace('Q0-R466-ground-neck-and-new-SMD-r468','Q0-R466-ground-neck-safe-empty-geometry-r470').replace('Q0_R468_','Q0_R470_').replace("'target_fill_bounds':fillisland.bounds","'target_fill_bounds':None if fillisland.is_empty else fillisland.bounds")
exec(compile(code,str(base),'exec'))
