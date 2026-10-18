"""Bounded original detached barrels are possibilities, never SOURCE seeds."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'search_missing_CM_existing_actual_SOURCE_ground_terminals_r455.py').read_text(encoding='utf-8')
s=s.replace('CM51-missing-seven-named-existing-actual-SOURCE-F-ground-terminal-search-r455','CM51-missing-seven-original-detached-F-ground-port-handoff-diagnostic-r456')
s=s.replace("or('via',u,'F.Cu')not in rootkeys","or 'F.Cu'not in v.get('flashed',[])or('via',u,'F.Cu')in rootkeys")
s=s.replace("'actual_BEFORE_J1_SOURCE_F_key':True","'actual_BEFORE_J1_SOURCE_F_key':False,'original_observed_F_mask':True,'SOURCE_recovery_via_separate_In3_handoff_required':True")
s=s.replace("'BOUNDED_NAMED_EXISTING_SOURCE_TERMINAL_SEARCH'","'BOUNDED_ORIGINAL_DETACHED_TERMINAL_ONLY_NOT_SOURCE_CONNECTED'")
s=s.replace('CM-R455-own-existing-ground:','CM-R456-detached-ground-F:').replace("'R455_ROUTE'","'R456_ROUTE'").replace("'R455_COMPLETE'","'R456_COMPLETE'")
s=s.replace("'only-new-existing-real-SOURCE-terminal-F-handoffs.pkl'","'only-prospective-detached-barrel-F-handoffs-NOT_SOURCE.pkl'")
s=s.replace("'existing_actual_SOURCE_F_barrels_screened'","'original_observed_detached_F_barrels_screened'")
s=s.replace("'actual_current_native_AFTER_SOURCE_oldrefs_current_thermal':'OPEN'","'SOURCE_before':False,'actual_current_native_AFTER_SOURCE_oldrefs_current_thermal':'OPEN'")
E=P/'exact-expanded-original-detached-CM-ground-port-screen-r456.py';assert not E.exists();compile(s,str(E),'exec');E.write_text(s,encoding='utf-8');exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
