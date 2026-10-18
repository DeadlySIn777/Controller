"""R306 preserved; fix only literal LOGIC_GND graph lookup spelling."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'repair_ED_integer_boundary_without_reference_loss_r306.py').read_text(encoding='utf-8')
s=s.replace('REG-explicit-local-integer-boundary-reference-repair-r306','REG-explicit-local-integer-boundary-reference-repair-r307')
s=s.replace("('LOGIC_GND','J11001')","('/LOGIC_GND','J11001')")
exec(compile(s,str(H/'repair_ED_integer_boundary_without_reference_loss_r306.py'),'exec'))
