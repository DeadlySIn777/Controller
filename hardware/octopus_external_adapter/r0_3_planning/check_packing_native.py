from pathlib import Path
import json,shutil,importlib.util,hashlib
import pcbnew as p
R=Path(__file__).resolve().parent;S=R.parent/'r0_3';T=R/'packing60-validation';T.mkdir(exist_ok=True)
for name in ['parts.json','adapter.net.xml','adapter.kicad_pro','adapter.kicad_sch','Adapter.kicad_sym','fp-lib-table','sym-lib-table']:
 shutil.copy2(S/name,T/name)
for name in ['Adapter.pretty','Adapter_R03.pretty']:shutil.copytree(S/name,T/name,dirs_exist_ok=True)
shutil.copy2(R/'placement-packing-60mm.json',T/'placement.json')
spec=importlib.util.spec_from_file_location('packing_builder',S/'build_pcb.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.ROOT=T;module.build()
b=p.LoadBoard(str(T/'adapter.kicad_pcb'));boxes={};issues=[]
for fp in b.GetFootprints():
 ref=fp.GetReference();layer=p.B_CrtYd if ref in ('J1','J2') else p.F_CrtYd
 bb=[g.GetBoundingBox() for g in fp.GraphicalItems() if g.GetLayer()==layer]
 boxes[ref]=[min(p.ToMM(v.GetLeft())-100 for v in bb),min(p.ToMM(v.GetTop())-100 for v in bb),max(p.ToMM(v.GetRight())-100 for v in bb),max(p.ToMM(v.GetBottom())-100 for v in bb)]
def ov(a,b):return min(a[2],b[2])-max(a[0],b[0])>1e-6 and min(a[3],b[3])-max(a[1],b[1])>1e-6
top=[n for n in boxes if n not in ('J1','J2')]
layout=json.loads((T/'placement.json').read_text())
for i,r in enumerate(top):
 for s in top[i+1:]:
  if ov(boxes[r],boxes[s]):issues.append(['native_courtyard',r,s])
 for j,strip in enumerate(layout['header_top_service_strips']):
  if ov(boxes[r],strip):issues.append(['header_tail_strip',r,j])
 c=boxes[r]
 if min(c[0]-.25,c[1]-.25,14.99-c[2],59.75-c[3]) < -1e-6:issues.append(['courtyard_board_margin',r])
report={'status':'PASS' if not issues else 'FAIL','scope':'Native footprint transforms, courtyard envelope collisions, header solder-tail service strips and0.25mm board margin; no routing/fit proof','native_footprints':len(boxes),'top_smt':47,'top_through_hole_connectors':3,'bottom_headers':2,'top_test_pads':3,'issues':issues,'boxes':boxes,'board_sha256':hashlib.sha256((T/'adapter.kicad_pcb').read_bytes()).hexdigest()}
(R/'packing60-native-geometry.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='boxes'}))
