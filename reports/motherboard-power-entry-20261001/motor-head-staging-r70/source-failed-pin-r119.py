import pcbnew
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/motor-bank-A-stitches-r96/motor-bank-A-stitches-candidate.kicad_pcb')
for p in b.GetPads():
 if p.m_Uuid.AsString()=='fcf75346-d02d-4f3b-ad57-72d92c82c382':print(p.GetParentFootprint().GetReference(),p.GetNumber(),p.GetNetname())
