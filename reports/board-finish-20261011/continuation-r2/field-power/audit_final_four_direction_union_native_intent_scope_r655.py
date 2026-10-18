"""Preserve R653 eager-default schema failure; require actual flashed field."""
from pathlib import Path
s=Path(__file__).with_name('audit_final_four_direction_union_native_intent_scope_r653.py').read_text(encoding='utf-8')
s=s.replace("exec(compile(s,str(Path(__file__)),'exec'))","s=s.replace(\"v.get('flashed',v['span'])\",\"v['flashed']\").replace('final-four-direction-union-native-intent-scope-readonly-r653','final-four-direction-union-native-intent-scope-readonly-r655').replace('R653','R655')\nexec(compile(s,str(Path(__file__)),'exec'))")
exec(compile(s,str(Path(__file__)),'exec'))
