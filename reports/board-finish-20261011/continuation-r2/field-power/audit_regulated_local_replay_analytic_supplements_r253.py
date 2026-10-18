"""Full exact-head audit of minimal owned replays and analytic guard additions."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_all_REG_corrected_envelopes_conservative_delta_r242.py').read_text(encoding='utf-8')
s=s.replace('REG-seven-corrected-current-head-conservative-delta-audit-r242','REG-seven-minimal-owned-replay-analytic-guard-audit-r253')
s=s.replace('immutable_baseline_guard_delta_projection_r236','immutable_baseline_analytic_guard_supplements_r252')
start=s.index(" correction=H/'B3-subset-inherited-FBG-native-LOGIC-guard-correction-r241'")
end=s.index(" field=H/'FIELD5-current-reference-envelope-correction-r238'",start)
s=s[:start]+" # The rejected R240/R241 broad return trims are deliberately excluded.\n correction=H/'B3-envelope-scoped-LOGIC-projection-r233'\n "+s[end:]
s=s.replace("old=q[role];q[role]=set_precision(old.difference(cut),1e-6)","old=q[role];q[role]=set_precision(set_precision(old,0).difference(set_precision(cut,0)),1e-6,mode='pointwise')\n   # Resolve any positive snap gain only at its own exact local neighbourhood.\n   for local_iteration in range(8):\n    gain=set_precision(q[role],0).difference(set_precision(old,0))\n    if gain.area<1e-12:break\n    local_cut=P.bounded_buffer(gain,.000003);q[role]=set_precision(set_precision(q[role],0).difference(set_precision(local_cut,0)),1e-6,mode='pointwise')\n   assert q[role].difference(old).area<1e-12,('owned replay snap gained Cu',q['uuid'],role)\n")
s=s.replace("'owned_FBG_guard_correction_sha256':sha(correction/'receipt.json')","'rejected_owned_FBG_R240_R241_excluded':True,'exact_untrimmed_FBG_R233_model_sha256':sha(correction/'derived-full-input-model.pkl'),'local_owned_replay_zero_tag_then_pointwise_bound':True")
s=s.replace('R242','R253')
exec(compile(s,str(H/'audit_all_REG_corrected_envelopes_conservative_delta_r242.py'),'exec'))
