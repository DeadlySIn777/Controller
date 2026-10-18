"""Preserve R188 compile failure; correct only generated-source escaping."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'construct_B3_exact_subset_faces_r188.py').read_text(encoding='utf-8').replace('r188','r189').replace('R188','R189').replace('new="""','new=r"""')
exec(compile(s,str(H/'construct_B3_exact_subset_faces_r188.py'),'exec'))
