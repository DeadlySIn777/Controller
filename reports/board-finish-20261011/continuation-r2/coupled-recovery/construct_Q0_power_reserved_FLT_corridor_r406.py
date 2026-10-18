"""Only the old 7bb power wall is rerouted around a concrete .2 FLT corridor."""
from pathlib import Path
H=Path(__file__).resolve().parent;base=H/'construct_Q0_power_wall_SENSE_dive_coupled_r404.py'
code=base.read_text(encoding='utf-8').replace('Q0-power-wall-SENSE-dive-coupled-r404','Q0-power-reserved-FLT-corridor-r406')
# Preserve the actual FLT source endpoint and reserve one concrete fullwidth
# departure towards the original lower free component. This is not emitted Cu.
old="power_ok=route_attachments('POWER-only-7bb-two-endpoints-fullwidth-F',POWER,'F.Cu',refs['In1.Cu'],Point(228.45,158.35),Point(229.45,159.35),tracks)"
new="power_ok=route_attachments('POWER-only-7bb-two-endpoints-fullwidth-F',POWER,'F.Cu',refs['In1.Cu'],Point(228.45,158.35),Point(229.45,159.35),tracks+[{'uuid':'FLT-owned-departure-reservation-only','net':FLT,'layer':'F.Cu','a':[229.35,158.45],'b':[229.05,158.65],'w':.2}])"
assert old in code;code=code.replace(old,new);exec(compile(code,str(base),'exec'))
