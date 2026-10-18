"""Read-only timed diagnosis of native reference-checker work."""
import faulthandler,json,sys,threading,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import pcbnew
from hardware_validate_motherboard_return_planes import validate
root=Path(__file__).resolve().parents[2]
log=open(Path(__file__).with_suffix('.log'),'w',encoding='utf-8')
faulthandler.enable(log)
faulthandler.dump_traceback_later(25,file=log)
threading.Timer(45,lambda:(log.flush(),os._exit(3))).start()
b=pcbnew.LoadBoard(str(root/'reports/motherboard-return-zoning-20261001/source25-r46-cmos-adc-anchor-merge-r01/motherboard-bounded-merged-candidate.kicad_pcb'))
m=json.loads((root/'reports/motherboard-return-zoning-20261001/source25-r46-isolation-domain-map-r01/domain-map.json').read_text())
r=validate(b,m)
log.write('Completed actual source-resource checker\n');log.flush()
os._exit(0)
