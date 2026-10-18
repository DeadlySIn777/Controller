"""Use exact integer native units for the fixed old .575 radius."""
from pathlib import Path
H=Path(__file__).resolve().parent
src=H/'bind_DI6_actual_R157_target_source_masks_void_r584.py';code=src.read_text();a="radius=target['d']/2+.25+.025;assert radius==.575";assert code.count(a)==1
code=code.replace('binding-r584','binding-r586').replace('R584_','R586_').replace(a,"diameter_IU=int(round(target['d']*1e6));assert target['d']==diameter_IU/1e6 and diameter_IU==600000;radius_IU=diameter_IU//2+250000+25000;assert radius_IU==575000;radius=radius_IU/1e6")
exec(compile(code,str(src),'exec'))
