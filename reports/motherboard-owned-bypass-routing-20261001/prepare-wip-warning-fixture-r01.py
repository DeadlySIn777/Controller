"""Persist an actual source-connected unfinished feed via in a native fixture."""
import json,shutil,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import pcbnew
from hardware_populate_motherboard_pcb import sha,write
from hardware_route_logic_return import xy
parent=Path('reports/motherboard-owned-bypass-routing-20261001')
original=parent/'native-fixture-r08/top';folder=parent/'wip-r03-warning-fixture-preparation-r03'
if folder.exists():raise ValueError('Fresh immutable native fixture required')
shutil.copytree(original,folder)
board=folder/'fixture.kicad_pcb';b=pcbnew.LoadBoard(str(board))
cap=next(f for f in b.GetFootprints()if f.GetReference()=='C1')
p=next(p for p in cap.Pads()if p.GetNumber()=='1')
v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(p.GetNetname()));v.SetPosition(xy((15.,2.)));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetRemoveUnconnected(True);v.SetIsFree(True);b.Add(v)
points=[p.GetPosition(),xy((8.225,3.5)),xy((15.,3.5)),v.GetPosition()]
for start,end in zip(points,points[1:]):
 t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(p.GetNetname()));t.SetLayer(pcbnew.F_Cu);t.SetWidth(pcbnew.FromMM(.2));t.SetStart(start);t.SetEnd(end);b.Add(t)
pcbnew.SaveBoard(str(board),b)
cli=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
r=subprocess.run([str(cli),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(folder/'baseline-native.json'),str(board)],capture_output=True,text=True)
(folder/'native-command.log').write_text(r.stdout+r.stderr)
if r.returncode:raise ValueError('Actual native fixture DRC failed to execute')
d=json.loads((folder/'baseline-native.json').read_text())
if d.get('ignored_checks')or len(d['violations'])!=1 or d['violations'][0]['type']!='via_dangling'or d['violations'][0]['severity']!='warning':raise ValueError('Fixture must have exactly one actual unfinished feed warning')
if d['violations'][0]['items'][0]['uuid']!=v.m_Uuid.AsString():raise ValueError('Actual unfinished feed UUID differs')
write(folder/'baseline-disposition.json',dict(board_sha256=sha(board),routing_incomplete=True,manufacturing_ready=False,known_unresolved_native_warnings=d['violations'],scope='Actual native geometric fixture; intentionally unfinished source-connected supply via. Not controller hardware or a manufacturing pass.'))
print(json.dumps(d['violations']))
