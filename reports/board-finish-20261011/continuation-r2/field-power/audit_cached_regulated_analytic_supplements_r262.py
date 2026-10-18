"""Exact cached successor of preserved stopped R254; full gates unchanged."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_regulated_local_replay_analytic_supplements_r254.py').read_text(encoding='utf-8')
s=s.replace('REG-seven-minimal-owned-replay-analytic-guard-audit-r254','REG-seven-cached-exact-analytic-guard-audit-r262').replace('immutable_baseline_analytic_guard_supplements_r252','cached_immutable_analytic_guard_projection_r261').replace('R254','R262')
s=s.replace("guard_errors=[row for row in guard_checks if not row['PASS']];", "guard_errors=[row for row in guard_checks if not row['PASS']];write(O/'exact-guard-cache-proof.json',{'stats':IP.stats,'exact_original_operator_rows':IP.proofs,'guard_operator_and_required_distances_unchanged':True});")
exec(compile(s,str(H/'audit_regulated_local_replay_analytic_supplements_r254.py'),'exec'))
