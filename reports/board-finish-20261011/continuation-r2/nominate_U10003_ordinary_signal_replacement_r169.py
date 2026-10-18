"""Screen the approved ordinary .5/.2 replacement, keeping all failures bound."""
from pathlib import Path
H=Path(__file__).resolve().parent;wrapper=H/'nominate_U10003_signal_barrel_bound_ground_retreat_r168.py';code=wrapper.read_text()
needle="compile(code,str(wrapper),'exec');exec(compile(code,str(wrapper),'exec'))";assert code.count(needle)==1
extra="""code=code.replace('bound-ground-retreat-faces-r168','ordinary-signal-replacement-faces-r169')
tail=\"compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))\"
assert code.count(tail)==1
ordinary=\"code=code.replace('.30+gap','.25+gap').replace('.15+.275','.1+.275').replace(\\\"(.3+v['drill'])/2\\\",\\\"(.2+v['drill'])/2\\\").replace('.30+.025','.25+.025').replace('.30+max','.25+max');code=code.replace('site.buffer(.30,quad_segs=256).difference(site.buffer(.15,quad_segs=256))','site.buffer(.25,quad_segs=256).difference(site.buffer(.1,quad_segs=256))');code=code.replace(\\\"'legacy_retained_barrel_diameter_drill_mm':[.6,.3]\\\",\\\"'existing_barrel_original_diameter_drill_mm':[.6,.3],'proposed_ordinary_replacement_diameter_drill_mm':[.5,.2]\\\")\\n\"
code=code.replace(tail,ordinary+tail)
"""
code=code.replace(needle,extra+needle)
compile(code,str(wrapper),'exec');exec(compile(code,str(wrapper),'exec'))
