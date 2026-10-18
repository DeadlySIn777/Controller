"""R240 independent primitive audit, exact smaller R241 pose successor."""
from pathlib import Path
P=Path(__file__).resolve().parent;src=P/'audit_U21003_two_pose_wall_scope_r240.py';s=src.read_text()
s=s.replace('U21003-two-pose-independent-wall-scope-r240','U21003-rotated-pose-independent-wall-scope-r242').replace('U21003-cap-pullup-translated-return-nominees-r238','U21003-cap-pullup-rotated-return-nominees-r241').replace('c2b8d56cbdbcd81befd83620526fe72646b3b677f78c785eae457a540608e09b','f02175213ed2a5886d3cb5bc77dc5ff45cfe9222edd1d975c477cd803e26f797').replace('assert len(nt)==8','assert len(nt)==6').replace('EIGHT_TRACK','SIX_TRACK').replace('R238_recipe_sha256','R241_recipe_sha256').replace('R240_COMPLETE','R242_COMPLETE')
exec(compile(s,str(__file__),'exec'))
