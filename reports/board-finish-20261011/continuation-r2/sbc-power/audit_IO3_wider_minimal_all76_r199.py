"""Fresh strict all76/source/ref delta of R196 relative to validated R183."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'audit_original_IO3_all76_incremental_r180.py').read_text().replace('original-IO3-full-all76-incremental-audit-r180','IO3-wider-minimal-all76-incremental-audit-r199').replace('R180_','R199_')
s=s.replace('SAFE-repaired-owned-zone-normalization-r160/model.pkl','IO3-exact-unchanged-primitive-composition-r183/model.pkl').replace('d7e0fe77a8ee25fef4e45538da29aa72809c102192879330c7a5b32a200e711b','6e96338816a234e62afc309467c804c82d91785cfe0737b7b4a465f2b24b9fa5').replace('parent_R160_model_sha256','parent_R183_model_sha256')
exec(compile(s,str(P/'audit_original_IO3_all76_incremental_r180.py'),'exec'))
