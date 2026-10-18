"""Preserved R146 derivative: footprint metadata is keyed by its actual ref."""
from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'inspect_safe_joint_exact_delta_r146.py').read_text()
s=s.replace("safe-joint-exact-delta-inspection-r146","safe-joint-exact-delta-inspection-r147")
s=s.replace("old={q['uuid']:q for q in base[1][key]};new={q['uuid']:q for q in m[1][key]}","old={q.get('uuid',q.get('ref')):q for q in base[1][key]};new={q.get('uuid',q.get('ref')):q for q in m[1][key]}")
exec(compile(s,str(p/'inspect_safe_joint_exact_delta_r146.py'),'exec'))
