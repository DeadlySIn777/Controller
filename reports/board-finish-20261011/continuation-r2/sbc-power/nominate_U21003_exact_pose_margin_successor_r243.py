"""Use the literal R244 foreign primitives for minimal pose-margin changes."""
from pathlib import Path
P=Path(__file__).resolve().parent;prior=P/'nominate_U21003_pullup_rotated_return_r241.py';s=prior.read_text();start=s.index("exec(compile(s,str(__file__),'exec'))")
# The first compile call is inside the generated wrapper text. Add the final
# effective-main edits immediately before that inner evaluation.
s=s[:start]+"""s=s.replace('U21003-cap-pullup-rotated-return-nominees-r241','U21003-exact-pose-margin-return-nominees-r243').replace('U21003-coupled-return-r241:','U21003-coupled-return-r243:').replace('R241_','R243_').replace('dx=.525','dx=.4225').replace('-.25','-.4')
"""+s[start:]
exec(compile(s,str(__file__),'exec'))
