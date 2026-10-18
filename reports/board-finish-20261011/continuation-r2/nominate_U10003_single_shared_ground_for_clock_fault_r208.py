"""Fix generated indentation before running the unchanged finite shared-return screen."""
from pathlib import Path
H=Path(__file__).resolve().parent;src=H/'nominate_U10003_single_shared_ground_for_clock_fault_r207.py'
wrapper=src.read_text().replace('shared-ground-return-faces-r207','shared-ground-return-faces-r208')
needle="exec(compile(code,str(src),'exec'))"
assert wrapper.count(needle)==1
wrapper=wrapper.replace(needle,"code=code.replace(\"\\nprint('R198\",\"\\n print('R198\")\n"+needle)
exec(compile(wrapper,str(src),'exec'))
