"""Exact successor for typed Win64 handles; no R647 frozen input changes."""
from pathlib import Path
s=(Path(__file__).with_name('export_eedf_exact_cached_BEFORE_r647.py')).read_text(encoding='utf-8')
s=s.replace('native_eedf_exact_cached_BEFORE_dump_r647.py','native_eedf_exact_cached_BEFORE_dump_r648.py').replace('eedf-original-parent-exact-cached-native-BEFORE-dump-r647','eedf-original-parent-exact-cached-native-BEFORE-dump-r648').replace('R647_COMPLETE','R648_COMPLETE')
exec(compile(s,str(Path(__file__)),'exec'))
