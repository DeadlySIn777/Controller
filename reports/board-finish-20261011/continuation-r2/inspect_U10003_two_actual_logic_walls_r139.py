"""Use the actual source connector J11001.2, as bound by R220/R252."""
from pathlib import Path
H=Path(__file__).resolve().parent
source=H/'inspect_U10003_two_actual_logic_walls_r137.py'
code=source.read_text()
assert code.count('C.track(t)')==1
code=code.replace('C.track(t)','C.body(t)').replace('coupled-geometry-r137','coupled-geometry-r139')
assert code.count("('/motherboard_power/LOGIC_GND','J1','2')")==1
code=code.replace("('/motherboard_power/LOGIC_GND','J1','2')","('/LOGIC_GND','J11001','2')")
code=code.replace("if not roots:roots=[max(groups[net],key=len)]","assert roots, ('literal connector ground source absent',net,ref,pin)")
exec(compile(code,str(source),'exec'))
