"""Independent true-Cu/drill and full-body reference screen on exact R245 poses."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'audit_U21003_two_pose_wall_scope_r240.py').read_text()
s=s.replace('U21003-two-pose-independent-wall-scope-r240','U21003-exact-margin-pose-independent-wall-scope-r246').replace('U21003-cap-pullup-translated-return-nominees-r238','U21003-cap-pullup-rotated-return-nominees-r245').replace('c2b8d56cbdbcd81befd83620526fe72646b3b677f78c785eae457a540608e09b','2e8e7da3b72ea8f74bd0bd2b754cacc24df5164cd986c5bd41b6ce8f9ab875a2').replace('assert len(nt)==8','assert len(nt)==6').replace('EIGHT_TRACK','SIX_TRACK').replace('R238_recipe_sha256','R245_recipe_sha256').replace('R240_COMPLETE','R246_COMPLETE')
exec(compile(s,str(__file__),'exec'))
