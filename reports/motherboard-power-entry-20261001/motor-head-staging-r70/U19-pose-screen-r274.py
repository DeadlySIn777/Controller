import sys,json,math,shutil
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm,xy,identity
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_local_signals import paths
from hardware_place_owned_capacitors_native import side_box
from hardware_populate_motherboard_pcb import intersects
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-two-health-real-Source-collars-r01/motherboard-two-health-Source-reference-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/ROOT101-health-U19-pose-screen-r274');O.mkdir(exist_ok=False)
o=pcbnew.LoadBoard(str(B));fp={f.GetReference():f for f in o.GetFootprints()};ps={(r,p.GetNumber()):p for r,f in fp.items()for p in f.Pads()if p.GetNumber()};nets=[ps['U11019',p].GetNetname()for p in ['4','6']];ret={t.m_Uuid.AsString()for t in o.GetTracks()if t.GetNetname()in nets}
for r in ['U11019','C11078']:
 for p in fp[r].Pads():
  pt=mm(p.GetPosition());ret|={t.m_Uuid.AsString()for t in o.GetTracks()if not isinstance(t,pcbnew.PCB_VIA) and t.GetNetname()==p.GetNetname()and pt in[mm(t.GetStart()),mm(t.GetEnd())]}
t=parse(without_generated_fills(B.read_text()));t=[v for v in t if not(isinstance(v,list)and v and v[0]in ['segment','via']and value(child(v,'uuid')[1])in ret)];D=O/'literal-retired-U19-local-input.kicad_pcb';D.write_text(dump_board(t));
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),D.with_suffix(e))
b=pcbnew.LoadBoard(str(D));fs={f.GetReference():f for f in b.GetFootprints()};results=[]
for pos in [(343,174.5),(342.8,174.5),(343.2,174.5),(343,175),(342.9,175.25),(342.9,173.75),(343.4,174.5),(343.5,174.25),(342.5,174.25)]:
 f=fs['U11019'];f.SetPosition(xy(pos));f.SetOrientationDegrees(180);ps={(r,p.GetNumber()):p for r,f in fs.items()for p in f.Pads()if p.GetNumber()};cp=(ps['U11019','5'].GetPosition());cx,cy=mm(cp);fs['C11078'].SetPosition(xy((cx,cy-.775)));fs['C11078'].SetOrientationDegrees(90)
 courts={r:[z.GetReference()for z in fs.values()if z.GetReference()!=r and z.GetLayer()==fs[r].GetLayer()and intersects(side_box(fs[r]),side_box(z),0)]for r in ['U11019','C11078']};g=FastGeometry(b)
 rows=[]
 for rp,up in [('1','6'),('3','4')]:
  a=mm(ps['U11020',rp].GetPosition());z=mm(ps['U11019',up].GetPosition());n=ps['U11020',rp].GetNetname();ss=[v for v in paths(a,z)if g.clear(v,n,pcbnew.F_Cu,.2)];rows.append(dict(pin=rp,a=a,z=z,native_paths=ss))
 results.append(dict(pose=pos,court_conflicts=courts,local_controls=rows));print(results[-1],flush=True)
(O/'screen.json').write_text(json.dumps(dict(before_board=str(B),exact_retired_copper=sorted(ret),candidates=results),indent=2))
