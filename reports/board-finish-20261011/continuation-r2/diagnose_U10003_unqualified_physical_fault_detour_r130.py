"""Preserve R129 syntax-level failure; keep mandatory return deficits explicit."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'diagnose_U10003_physical_fault_detour_without_reference_credit_r129.py';wrapper=source.read_text()
wrapper=wrapper.replace("U10003-physical-fault-detour-unqualified-return-diagnosis-r129","U10003-unqualified-physical-fault-detour-r130")
wrapper=wrapper.replace("free=win.difference(unary_union(obstacles)) # diagnostic only; raw mandatory paired-return deficits stay explicit","free=win.difference(unary_union(obstacles))")
exec(compile(wrapper,str(source),'exec'))
