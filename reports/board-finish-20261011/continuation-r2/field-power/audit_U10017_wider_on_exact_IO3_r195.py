"""Rebase only the widened three-track/one-barrel correction on exact IO3 R183."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_SAFE_U10017_wider_full_branch_r178.py').read_text(encoding='utf-8')
s=s.replace("SAFE-U10017-wider-full-branch-audit-r178","U10017-wider-on-exact-IO3-audit-r195")
s=s.replace("sbc-power/SAFE-repaired-owned-zone-normalization-r160","sbc-power/IO3-exact-unchanged-primitive-composition-r183")
s=s.replace("d7e0fe77a8ee25fef4e45538da29aa72809c102192879330c7a5b32a200e711b","6e96338816a234e62afc309467c804c82d91785cfe0737b7b4a465f2b24b9fa5")
s=s.replace('exact_SAFE_R160_no_failed_REG6_or_U17_added','exact_corrected_IO3_R183_no_failed_REG6_or_U17_added')
s=s.replace('R178','R195').replace('r178','r195')
exec(compile(s,str(H/'audit_SAFE_U10017_wider_full_branch_r178.py'),'exec'))
