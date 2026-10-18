"""Bind U10003 distances to current geometry; preserve the earlier draft ledger."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'freeze_saved_operator_return_window_failures_r178.py';code=source.read_text()
code=code.replace('supplemental-failure-r178','supplemental-failure-r179')
needle="'U10003_R176_designated_pairs_mm':[.8266868844496132,1.321091034751669]";assert code.count(needle)==1
replace="'U10003_R176_designated_pairs_mm':u_dist,'U10003_R176_exact_model_sha256':sha(u_model)"
code=code.replace(needle,replace)
needle="out=H/'saved-operator-return-window-supplemental-failure-r179'";assert code.count(needle)==1
extra="""u_model=H/'U10003-preserved-branch-exact-two-port-reference-construction-r176/model.pkl';assert sha(u_model)=='c13b478b0cea7b09a510c221913d3a4d0774fcc74042605c17d69b35b37a9d20'
uh=pickle.loads(u_model.read_bytes())[1];uv={v['uuid']:v for v in uh['vias']};newsignal=uv['7f2431b3-4dcd-5b17-88ce-8aae4c3d66d4'];central=next(v for v in uh['vias']if v['net'].replace('{slash}','/')=='/motherboard_motors/FIELD_GND'and(v['x'],v['y'])==(216.04,142.95));retA=next(v for v in uh['vias']if v['net'].replace('{slash}','/')=='/motherboard_motors/FIELD_GND'and(v['x'],v['y'])==(219.17568,142.190789));oldsignal=uv['2938cbdd-1d38-4238-9455-504b30f06e5e'];u_dist=[math.dist([oldsignal['x'],oldsignal['y']],[retA['x'],retA['y']]),math.dist([newsignal['x'],newsignal['y']],[central['x'],central['y']])]
"""
code=code.replace(needle,extra+needle)
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
