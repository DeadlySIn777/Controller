"""Fresh exact widened R112 sheet, no stale narrow-sheet geometry substitution."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'solve_CORE_R100_exact_annular_sheet_r233.py').read_text()
s=s.replace('CORE-R100-actual-annular-contained-sheet-r233','CORE-R112-wide-actual-annular-contained-sheet-r247').replace('CORE-In2-owned-notch-materialized-source-proposal-r100/model.pkl','CORE-wide-reserved-IO3-immutable-R214-materialized-r112/model.pkl').replace('db01ba8f89c614c72b19688ec6479c96e8524259f1968eaa2dd3f2caeef49635','6312b10a88b2d3614e21760d1709866d2417b419d418e20e09055eb13b8e3b7e').replace('R233_','R247_')
exec(compile(s,str(__file__),'exec'))
