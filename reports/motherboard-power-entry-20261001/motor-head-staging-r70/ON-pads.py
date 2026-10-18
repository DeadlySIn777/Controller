import pcbnew
b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-C17014-bypass-r69/motherboard-bounded-merged-candidate.kicad_pcb')
for p in b.GetPads():
 if p.GetNetname()in['/motherboard_power_entry/MOTOR_FEED_ON_A','/motherboard_power_entry/MOTOR_FEED_ON_B']:print(p.GetParentFootprint().GetReference(),p.GetNumber(),p.GetNetname())
