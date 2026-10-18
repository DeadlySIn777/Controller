"""Retain R432 failure; normalize only native polyset guard representation."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'exact-expanded-active-R300-CDONE-CM79-ground-r432.py').read_text(encoding='utf-8')
s=s.replace('CM79-active-R300-minimal-CDONE-one-new-ordinary-ground-return-r432','CM79-active-R300-minimal-CDONE-one-new-ordinary-ground-return-r433')
s=s.replace("nativeRules=packet['all_current_native_rule_areas'];q=","nativeRules=[{**r,'outline':N.O.polys(r['outline'])}for r in packet['all_current_native_rule_areas']];q=")
s=s.replace("'CM79-R432-","'CM79-R433-").replace("print('R432_COMPLETE'","print('R433_COMPLETE'")
s=s.replace("'active_R300_native_intent_binding':rr","'retained_R432_failure':'Native polyset guard schema was [outer,hole...] rather than host [outer,[holes...]]; no candidate output/adoption','active_R300_native_intent_binding':rr")
E=P/'exact-expanded-active-R300-CDONE-CM79-ground-r433.py';assert not E.exists();compile(s,str(E),'exec');E.write_text(s,encoding='utf-8');exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
