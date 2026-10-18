"""R434 schema correction: native FP UUID is bound by exact source AST."""
from pathlib import Path
H=Path(__file__).resolve().parent;base=H/'compose_Q0_exact_R428_current_filled_only_r434.py'
code=base.read_text().replace('Q0-exact-R428-current-filled-only-r434','Q0-exact-R428-current-filled-only-r436')
old="assert fp['uuid']==op['R10016_FP_UUID'];fp['x']=229.86"
new="assert 'uuid' not in fp and(fp['x'],fp['y'])==(230.36,167.162);oldfpast=K.Q.parse(Path(op['exact_FP_before_file']).read_text());assert K.Q.atom(oldfpast,'uuid')==op['R10016_FP_UUID'];assert {K.Q.atom(p,'uuid')for p in K.Q.children(oldfpast,'pad')}==padids;fp['x']=229.86"
assert old in code;code=code.replace(old,new);exec(compile(code,str(base),'exec'))
