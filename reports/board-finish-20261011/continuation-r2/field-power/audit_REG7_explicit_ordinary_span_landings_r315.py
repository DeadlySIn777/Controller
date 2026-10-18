"""R314 preserved; explicitly include new ordinary all-six-layer span."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_REG7_all_same_raw_plated_native_intent_landings_r314.py').read_text(encoding='utf-8')
s=s.replace('REG7-all-same-raw-plated-native-intent-census-r314','REG7-all-same-raw-plated-native-intent-census-r315')
s=s.replace("q['layer'] not in v['span']","q['layer'] not in v.get('span',v.get('flashed',[]))")
exec(compile(s,str(H/'audit_REG7_all_same_raw_plated_native_intent_landings_r314.py'),'exec'))
