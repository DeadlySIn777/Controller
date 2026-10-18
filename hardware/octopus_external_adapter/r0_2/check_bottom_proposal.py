from pathlib import Path
import json,pcbnew as p
R=Path(__file__).resolve().parent;T=R/'bottom-validation';T.mkdir(exist_ok=True)
data=json.loads((R/'bottom-placement-proposal.json').read_text());parts={}
for f in ['logic_spec.json','power_spec.json']:
 s=json.loads((R/f).read_text())['parts'];parts.update(s if isinstance(s,dict) else {v['reference']:v for v in s})
layout=dict(data['parts']);layout.update({r:[*v,'bottom' if r in ['J1','J2'] else 'top'] for r,v in data['fixed_th'].items()})
board=p.BOARD();board.SetCopperLayerCount(4);boxes={};pads=[]
def v(x,y):return p.VECTOR2I(p.FromMM(100+x),p.FromMM(100+y))
def bbox(b):return [p.ToMM(b.GetLeft())-100,p.ToMM(b.GetTop())-100,p.ToMM(b.GetRight())-100,p.ToMM(b.GetBottom())-100]
for ref,(x,y,a,side) in layout.items():
 lib,name=parts[ref]['footprint'].split(':');folder=R/(lib+'.pretty');folder=folder if folder.exists() else Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')/(lib+'.pretty')
 fp=p.FootprintLoad(str(folder),name);fp.SetReference(ref);fp.SetValue(parts[ref]['value']);fp.SetPosition(v(x,y));board.Add(fp)
 if side=='bottom':fp.Flip(v(x,y),False)
 fp.SetOrientationDegrees(fp.GetOrientationDegrees()+a)
 for field in fp.GetFields():field.SetVisible(False)
 bb=[]
 for g in fp.GraphicalItems():
  if g.GetLayer()==p.B_CrtYd:bb.append(bbox(g.GetBoundingBox()))
 if bb:boxes[ref]=[min(b[0] for b in bb),min(b[1] for b in bb),max(b[2] for b in bb),max(b[3] for b in bb)]
 for pad in fp.Pads():
  if pad.GetNumber():
   net=p.NETINFO_ITEM(board,ref+'_'+pad.GetNumber());board.Add(net);pad.SetNet(net)
  b=bbox(pad.GetBoundingBox());pads.append(dict(ref=ref,pin=pad.GetNumber(),box=b,xy=[p.ToMM(pad.GetPosition().x)-100,p.ToMM(pad.GetPosition().y)-100],drill=p.ToMM(pad.GetDrillSizeX())))
width,height=data['board_mm']
for a,b in [((0,0),(width,0)),((width,0),(width,height)),((width,height),(0,height)),((0,height),(0,0))]:
 l=p.PCB_SHAPE();l.SetShape(p.SHAPE_T_SEGMENT);l.SetStart(v(*a));l.SetEnd(v(*b));l.SetWidth(p.FromMM(.05));l.SetLayer(p.Edge_Cuts);board.Add(l)
for x,y in [(7.7,16.85),(10.2,17.)]:
 via=p.PCB_VIA(board);via.SetPosition(v(x,y));via.SetWidth(p.FromMM(.6));via.SetDrill(p.FromMM(.3));via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetViaType(p.VIATYPE_THROUGH);via.SetFrontTentingMode(p.TENTING_MODE_TENTED);via.SetBackTentingMode(p.TENTING_MODE_TENTED);board.Add(via)
p.SaveBoard(str(T/'placement.kicad_pcb'),board)
pro={'board':{'design_settings':{'rules':{'min_clearance':.15,'min_copper_edge_clearance':.25,'min_hole_clearance':.25},'rule_severities':{'missing_courtyard':'warning','footprint_type_mismatch':'warning'}}},'net_settings':{'classes':[{'name':'Default','clearance':.15,'track_width':.15,'via_diameter':.6,'via_drill':.3}]}}
(T/'placement.kicad_pro').write_text(json.dumps(pro,indent=2))
def overlap(a,b):return min(a[2],b[2])-max(a[0],b[0])>1e-6 and min(a[3],b[3])-max(a[1],b[1])>1e-6
issues=[]
refs=list(boxes)
for i,r in enumerate(refs):
 for s in refs[i+1:]:
  if overlap(boxes[r],boxes[s]):issues.append(['courtyard',r,s])
 for pad in pads:
  if pad['drill']>0 and pad['ref'] not in [r,'J1','J2']:
   b=pad['box'];b=[b[0]-.15,b[1]-.15,b[2]+.15,b[3]+.15]
   if overlap(boxes[r],b):issues.append(['through-pad clearance',r,pad['ref'],pad['pin']])
report={'native_footprints_checked':len(layout),'bottom_smt':len(data['parts']),'geometry_issues':issues,'courtyards':boxes,'pads':pads}
(R/'bottom-placement-native-review.json').write_text(json.dumps(report,indent=2))
print('native geometry issues:',issues)
print('C21 pads:',[x for x in pads if x['ref']=='C21'])
