import json,sys,xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from hardware_populate_motherboard_pcb import native_parts_and_nets,footprint_name,sha
BASE=ROOT/'hardware/board_review/revisions/20260930-21/motherboard-populated-candidate.kicad_pcb'
model=json.loads((ROOT/'hardware/motherboard/design.json').read_text())
_,nodes=native_parts_and_nets(ROOT/'hardware/motherboard/netlist.xml',model['components'])
board=pcbnew.LoadBoard(str(BASE));board.BuildConnectivity();changes=[]
for f in board.GetFootprints():
    for p in f.Pads():
        if not p.GetNumber() or not p.IsOnCopperLayer():continue
        key=f.GetReference(),p.GetNumber();wanted=nodes[key]
        if p.GetNetname()!=wanted:
            changes.append(dict(reference=key[0],pin=key[1],old_native_net=p.GetNetname(),new_native_net=wanted,
                old_net_copper_items=sum(t.GetNetname()==p.GetNetname() for t in board.GetTracks())))
out=Path(__file__).parent/'reconcile-1585-pad-changes.json'
out.write_text(json.dumps(dict(base_sha256=sha(BASE),physical_parts=len(model['components']),changes=changes),indent=2)+'\n')
print(json.dumps(dict(changed_pads=len(changes),with_copper=[r for r in changes if r['old_net_copper_items']])))
