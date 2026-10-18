"""Correct B5 lookup to its literal source namespace; preserve R369 diagnostic."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'census_all_five_regulated_actual_source_pads_r369.py').read_text(encoding='utf-8')
s=s.replace('all-five-regulated-actual-drilled-source-census-r369','all-five-regulated-actual-drilled-literal-source-census-r370').replace('/motherboard_do/DOB_FIELD_5V_PRE','/motherboard_safety_sensor/FIELD_B_5V_PRE').replace('R369','R370')
exec(compile(s,str(H/'census_all_five_regulated_actual_source_pads_r369.py'),'exec'))
