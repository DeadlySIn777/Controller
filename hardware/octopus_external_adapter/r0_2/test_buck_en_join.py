from pathlib import Path
import json,shutil,pcbnew as p,hashlib
R=Path(__file__).resolve().parent;T=R/'buck-en-join';T.mkdir(exist_ok=True)
base=T/'source-moved-r21.kicad_pcb'
if not base.exists():shutil.copyfile(R/'adapter.kicad_pcb',base)
routes=[{'net':'/BUCK_EN','layer':'B.Cu','width':.15,'points':[[4.775,18.85],[4.775,19.7],[5.35,19.7]],'vias':[[5.35,19.7]]}, {'net':'/BUCK_EN','layer':'In2.Cu','width':.15,'points':[[7.85,16.1],[5.9,16.1],[5.35,16.65],[5.35,19.7]],'vias':[]}]
if (T/'proposed-routes.json').exists():routes=json.loads((T/'proposed-routes.json').read_text())
b=p.LoadBoard(str(base))
def v(x,y):return p.VECTOR2I(p.FromMM(x+100),p.FromMM(y+100))
for route in routes:
 net=b.GetNetsByName()[route['net']]
 for a,c in zip(route['points'],route['points'][1:]):
  tr=p.PCB_TRACK(b);tr.SetStart(v(*a));tr.SetEnd(v(*c));tr.SetWidth(p.FromMM(route['width']));tr.SetLayer({'B.Cu':p.B_Cu,'In2.Cu':p.In2_Cu,'F.Cu':p.F_Cu}[route['layer']]);tr.SetNet(net);b.Add(tr)
 for xy in route.get('vias',[]):
  via=p.PCB_VIA(b);via.SetPosition(v(*xy));via.SetWidth(p.FromMM(.6));via.SetDrill(p.FromMM(.3));via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetViaType(p.VIATYPE_THROUGH);via.SetFrontTentingMode(p.TENTING_MODE_TENTED);via.SetBackTentingMode(p.TENTING_MODE_TENTED);via.SetNet(net);b.Add(via)
p.SaveBoard(str(T/'candidate.kicad_pcb'),b)
for ext in ['kicad_pro','kicad_dru']:
 src=R/f'adapter.{ext}'
 if src.exists():shutil.copyfile(src,T/f'candidate.{ext}')
(T/'proposed-routes.json').write_text(json.dumps(routes,indent=2)+'\n')
print('tested snapshot',hashlib.sha256(base.read_bytes()).hexdigest())
