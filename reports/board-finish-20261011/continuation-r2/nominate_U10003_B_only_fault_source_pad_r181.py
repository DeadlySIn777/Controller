"""Fresh R180 successor with the required coupled-contact module directory."""
from pathlib import Path
H=Path(__file__).resolve().parent
source=H/'nominate_U10003_B_only_fault_source_pad_r180.py'
code=source.read_text().replace('r180','r181')
needle="code=code.replace('fault-two-existing-barrel-one-layer-replacement-r128','B-only-fault-source-pad-nomination-r181')"
assert code.count(needle)==1
code=code.replace(needle,needle+"\ncode=code.replace(\"for d in ('field-power','sbc-power'):\",\"for d in ('field-power','sbc-power','coupled-recovery'):\")")
compile(code,str(source),'exec')
exec(compile(code,str(source),'exec'))
