"""Bound the two OTHER native signal nets, separately from CS chain extensions."""
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'freeze_CM1_two_other_original_F_wall_obligations_r534.py'
code=base.read_text().replace('CM1-two-other-original-F-wall-obligations-r534','CM1-two-other-signal-net-original-wall-obligations-r538')
old="selected=[r for r in rank if not r['previous_R314_CS_wall']][:2]"
assert code.count(old)==1
code=code.replace(old,"selected=[r for r in rank if K.L.norm(r['raw_net'])!='/motherboard_compute/CM_HOST_SPI_CS_CMD_N'][:2]")
derived=H/'CM1-two-other-signal-net-original-wall-obligations-r538-derived-reader.py';assert not derived.exists();derived.write_text(code)
exec(compile(code,str(derived),'exec'))
