"""Relocate the unadopted too-close A return instead of adding another hole."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'nominate_U10003_old_A_return_after_coupled_clock_ground_r188.py';code=source.read_text().replace('r188','r190')
anchor="compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))";assert code.count(anchor)==1
extra="""
needle="ports=[next(v for v in h['vias']if v['uuid']=='2938cbdd-1d38-4238-9455-504b30f06e5e')]"
assert code.count(needle)==1
code=code.replace(needle,"old_A_return='73811c12-9f84-5491-bfee-0c5ee985a7a8';assert len([v for v in h['vias']if v['uuid']==old_A_return and v['prospective_not_native']])==1;h={**h,'vias':[v for v in h['vias']if v['uuid']!=old_A_return]};full={**full,'vias':h['vias']};ports=[next(v for v in h['vias']if v['uuid']=='2938cbdd-1d38-4238-9455-504b30f06e5e')]")
code=code.replace("'scene_is_nomination_only_not_an_emitted_board':True","'scene_is_nomination_only_not_an_emitted_board':True,'exact_unadopted_A_return_to_relocate':old_A_return")
"""
code=code.replace(anchor,extra+'\n'+anchor)
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
