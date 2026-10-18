"""Preserve R180, refine the same source-bound mesh without changing geometry."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'solve_U10017_actual_annular_sheet_r180.py').read_text(encoding='utf-8')
s=s.replace("O=H/'U10017-actual-annular-sheet-full-branch-r180'","O=H/'U10017-refined-annular-sheet-full-branch-r182'")
s=s.replace('for step in (.05,.025,.0125):','for step in (.05,.025,.0125,.00625):')
s=s.replace("'grid_convergence':convergence","'grid_convergence':convergence,'last_two_grid_relative_difference_below_1_percent':convergence[-1]['effective_squares_relative_difference']<.01,'preserved_prior_R180_receipt_sha256':sha(H/'U10017-actual-annular-sheet-full-branch-r180/receipt.json')")
exec(compile(s,str(H/'solve_U10017_actual_annular_sheet_r180.py'),'exec'))
