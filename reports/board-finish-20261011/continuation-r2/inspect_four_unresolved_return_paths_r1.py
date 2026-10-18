import sys,json,collections
from pathlib import Path
h=Path(__file__).resolve().parent;sys.path.insert(0,str(h/'field-power'))
import inventory as I
I.NET=h/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net';parts,pins,nets=I.load()
out={}
for start in ('R19051','R19053','R11071','R11073'):
 refs={start};front={start}
 for i in range(3):
  new={node['ref'] for ref in front for p in pins[ref] for node in nets[p['net']] if not p['net'].endswith(('FIELD_GND','FIELD_B_0V','LOGIC_GND','FIELD_5V','DOB_FIELD_3V3')) and len(nets[p['net']])<12}
  front=new-refs;refs|=new
 out[start]={ref:parts[ref] for ref in sorted(refs)}
folder=h/'unresolved-field-return-inspection-r1';folder.mkdir();(folder/'receipt.json').write_text(json.dumps(out,indent=1));print(json.dumps(out,indent=1))
