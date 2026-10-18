"""Use the literal adjacent reference for outer F/B traces; internal unchanged."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'route_U10003_fault_existing_barrel_replacement_r128.py';code=source.read_text()
needle="OUT=H/'U10003-fault-two-existing-barrel-one-layer-replacement-r128'";assert code.count(needle)==1
code=code.replace(needle,"OUT=H/'U10003-fault-outer-adjacent-source-reference-replacement-r136'")
needle="for layer in ('In2.Cu','In3.Cu','F.Cu','In4.Cu'):";assert code.count(needle)==1
code=code.replace(needle,"for layer in ('F.Cu','B.Cu'):")
needle="        for margin in (4.,10.,20.):";assert code.count(needle)==1
code=code.replace(needle,"        required_layers=('In1.Cu',) if layer=='F.Cu' else ('In4.Cu',)\n        reference=refs[required_layers[0]].union(port_disks)\n"+needle)
needle="gap={l:outside.difference(refs[l]).area for l in refs}";assert code.count(needle)==1
code=code.replace(needle,"gap={l:outside.difference(refs[l]).area for l in required_layers}")
needle="'old_cap_before_source_support_NOT_YET_QUALIFIED':True";assert code.count(needle)==1
code=code.replace(needle,needle+",'literal_outer_adjacent_reference_layers':list(required_layers),'all_secondary_raw_reference_gaps_reported':rawgap")
exec(compile(code,str(source),'exec'))
