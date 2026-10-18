"""Successor preserves failed R145 wrong-path run, with correct reports root."""
from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'qualify_u11017_static_enable_power_loop_r145.py').read_text()
assert "pinned=H.parents[3]" in s
s=s.replace("pinned=H.parents[3]", "pinned=H.parents[2]")
s=s.replace("u11017-static-enable-power-loop-review-r145", "u11017-static-enable-power-loop-review-r146")
s=s.replace("print('R145'", "print('R146'")
exec(compile(s,str(p/'qualify_u11017_static_enable_power_loop_r145.py'),'exec'))
