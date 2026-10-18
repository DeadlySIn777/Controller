"""Reuse the independent actual-copper cut check for the exact CMOS grounds."""
from pathlib import Path
here=Path(__file__).parent
source=here/'verify-digital-bias-returns-native-r02.py'
target=here/'verify-CMOS-ground-stitches-native-r01.py'
assert not target.exists()
s=source.read_text().replace('source26-r71-digital-bias-r02','source26-r73-plus3-CMOS-stitches-r01').replace('digital-bias-return-candidate.kicad_pcb','exact-CMOS-ground-candidate.kicad_pcb').replace('source26-r71-r01/domain-map.json','source26-r73-r01/domain-map.json')
line="assert any(row['reference']=='R10027'for row in r['already_connected']), 'Known actual existing Source return was not recognized'\n"
assert line in s
s=s.replace(line,'')
s=s.replace('Independently recheck exact new bias returns and remove their real copper.','Independently recheck exact CMOS ground returns and remove their real copper.')
assert 'known_vias and all(isinstance(v,pcbnew.PCB_VIA)'in s
target.write_text(s)
print(dict(prepared=True,known_existing_typed_via_positive_control_retained=True))
