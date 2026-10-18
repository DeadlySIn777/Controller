from pathlib import Path
P=Path(__file__).resolve().parent;s=(P/'field_supply_census_r38.py').read_text().replace('field-supply-census-r38','field-supply-census-r39').replace("('B_DO_PG','U11038','6')", "('B_DO_PG','U11038','7')")
s=s.replace("'r32_rejected_and_r36_pending_excluded':True", "'r32_rejected_and_r36_pending_excluded':True,'r38_PG_pad6_NC_diagnostic_corrected_to_actual_pad7':True")
(P/'field_supply_census_r39.py').write_text(s,encoding='utf-8');compile(s,'field_supply_census_r39.py','exec')
