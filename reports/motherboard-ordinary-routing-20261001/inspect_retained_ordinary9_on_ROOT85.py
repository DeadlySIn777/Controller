"""Locate exact old reference corridors disturbed by proposed new signal vias."""
from pathlib import Path
import sys,json,math
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_ordinary_wip_r05 as o
from hardware_route_logic_return import mm,distance
e=o.engine;out=Path('reports/motherboard-pcb-integration-20261001/source26-seven-path-IO3-tip-trial-r85');bp=out/'motherboard-bounded-merged-candidate.kicad_pcb';mp=Path('reports/motherboard-domains-20261001/source26-r85-r01/domain-map.json')
original=Path('reports/motherboard-ordinary-routing-20261001/actual-source26-root71-local-clipped-r02');plan=e.read(original/'proposed-local-groups.json');man=e.read(original/'manifest.json')
b=pcbnew.LoadBoard(str(bp));b.BuildConnectivity();o.MAPPING=e.read(mp);check=o.LiteralPieces(b,man['nets']);cu={t.m_Uuid.AsString():t for t in b.GetTracks()}
newplan=e.read('reports/motherboard-ordinary-routing-20261001/actual-source26-root83-In2-batch-r12/proposed-groups.json');newids={u for g in newplan['groups']for u in g['signal_UUIDs']};vias=[cu[u]for u in newids if cu[u].Type()==pcbnew.PCB_VIA_T];rows=[]
for uid in plan['added_copper_UUIDs']:
 t=cu[uid]
 try:check.via(t,man['nets'][t.GetNetname()])if t.Type()==pcbnew.PCB_VIA_T else check.segment(t,man['nets'][t.GetNetname()])
 except Exception as ex:
  near=sorted([(distance(mm(v.GetPosition()),mm(t.GetStart()),mm(t.GetEnd())),v)for v in vias],key=lambda q:q[0])[:3]
  rows.append(dict(uuid=uid,net=t.GetNetname(),layer=b.GetLayerName(t.GetLayer()),start=mm(t.GetStart()),end=mm(t.GetEnd()),reason=str(ex),nearest_new_signal_vias=[dict(uuid=v.m_Uuid.AsString(),net=v.GetNetname(),position=mm(v.GetPosition()),distance_mm=d)for d,v in near]))
e.write(out/'old-ordinary9-reference-conflicts.json',dict(board_sha256=e.sha(bp),failure_count=len(rows),failures=rows,diagnostic_only=True));print(json.dumps(rows,indent=2))
