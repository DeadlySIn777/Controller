"""Separate physical path feasibility from the still mandatory return proof."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'route_U10003_fault_existing_barrel_replacement_r128.py';code=source.read_text()
needle="OUT=H/'U10003-fault-two-existing-barrel-one-layer-replacement-r128'";assert code.count(needle)==1
code=code.replace(needle,"OUT=H/'U10003-physical-fault-detour-unqualified-return-diagnosis-r129'")
needle="free=win.intersection(reference).difference(unary_union(obstacles))";assert code.count(needle)==1
code=code.replace(needle,"free=win.difference(unary_union(obstacles)) # diagnostic only; raw mandatory paired-return deficits stay explicit")
needle="                if any(gap.values()):continue";assert code.count(needle)==1
code=code.replace(needle,"                paired_return_qualified=not any(gap.values()) # never silently exempt a missing return")
needle="'old_cap_before_source_support_NOT_YET_QUALIFIED':True";assert code.count(needle)==1
code=code.replace(needle,needle+",'paired_return_missing_NOT_ACCEPTED':not paired_return_qualified")
code=code.replace('FAULT_EXISTING_BARREL_REPLACEMENT_NOMINATED_PAIRED_RETURN_AND_ALL_GATES_OPEN','PHYSICAL_FAULT_REPLACEMENT_DIAGNOSTIC_REQUIRED_RETURN_NOT_ACCEPTED')
exec(compile(code,str(source),'exec'))
