"""Derive exact freed-centre geometry after only the selected power withdrawal."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'construct_c10036_continuous_return_r7.py').read_text().replace('c10036-continuous-return-diagnostic-r7.json','c10036-freed-return-diagnostic-r14.json')
s=s.replace("removed=set(prior['removed_source_UUIDs']);", "removed=set(prior['removed_source_UUIDs'])|{'75409711-7adb-4e55-b9ea-c36978361c51'};")
s=s.replace("'candidates':candidates,'obstacles':", "'candidates':candidates,'freed_by_exact_single_power_track_withdrawal':'75409711-7adb-4e55-b9ea-c36978361c51','obstacles':")
t=HERE/'construct_c10036_freed_return_region_r14.py';assert not t.exists();t.write_text(s);print(t)
