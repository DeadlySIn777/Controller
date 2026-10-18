import sys,json,collections
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_populate_motherboard_pcb import footprint_name
b=pcbnew.LoadBoard(str(Path('reports/motherboard-pcb-integration-20261001/adc-cell-iso1212-entry-substrate-source25-r46/motherboard-bounded-merged-candidate.kicad_pcb').resolve()))
m=json.loads(Path('hardware/motherboard/design.json').read_text())['components']
rows=[]
for f in b.GetFootprints():
 r=f.GetReference()
 if f.GetValue()!=m[r]['value']:
  rows.append(dict(reference=r,board_value=f.GetValue(),source_value=m[r]['value'],board_fields={x.GetName():x.GetText()for x in f.GetFields()},source_mpn=m[r]['mpn'],board_footprint=footprint_name(f),source_footprint=m[r]['footprint']))
out=Path('reports/motherboard-pcb-integration-20261001/source26-preexisting-value-differences-r01.json')
out.write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2))
