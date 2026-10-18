from pathlib import Path
import json,shutil,pcbnew as p,hashlib
R=Path(__file__).resolve().parent;T=R/'silk-validation';T.mkdir(exist_ok=True)
layout=json.loads((R/'placement.json').read_text());texts=[]
for t in layout['texts']:
 t=dict(t)
 if t['text']=='EN':continue
 if t['text'] in ['+','GND']:t['xy']=[t['xy'][0],29.4]
 if t['text']=='OFF BEFORE SWITCH':t.update(text='OFF BEFORE\nSWITCH',xy=[10.6,36.5])
 if t['text'].startswith('1:COM'):
  texts.append(dict(text='1+ 2P- 3D- 4E-',xy=[2.95,7.3],angle=90,size=.8))
 else:texts.append(t)
b=p.LoadBoard(str(R/'adapter.kicad_pcb'))
edits=[]
for fp in b.GetFootprints():
 if fp.GetReference()=='J4':
  for g in list(fp.GraphicalItems()):
   if g.GetClass()=='PCB_SHAPE' and g.GetLayer()==p.F_SilkS and g.GetShape()==p.SHAPE_T_SEGMENT:
    a=g.GetStart();c=g.GetEnd();ay=p.ToMM(a.y)-100;cy=p.ToMM(c.y)-100
    if abs(ay-29.88)<.001 and abs(cy-29.88)<.001:
     edits.append(dict(reference='J4',operation='move_silk_segment_to_Dwgs.User',layer='F.SilkS',start=[p.ToMM(a.x)-100,ay],end=[p.ToMM(c.x)-100,cy],reason='Make room for terminal polarity labels; no change to Fab/courtyard/pads/copper'))
     g.SetLayer(p.Dwgs_User)
for obj in list(b.GetDrawings()):
 if obj.GetClass()=='PCB_TEXT':b.Remove(obj)
boxes=[]
for t in texts:
 x,y=t['xy'];o=p.PCB_TEXT(b);o.SetText(t['text']);o.SetPosition(p.VECTOR2I(p.FromMM(x+100),p.FromMM(y+100)));o.SetTextSize(p.VECTOR2I(p.FromMM(t.get('size',.8)),p.FromMM(t.get('size',.8))));o.SetTextThickness(p.FromMM(.12));o.SetLayer(p.F_SilkS);o.SetTextAngle(p.EDA_ANGLE(t.get('angle',0),p.DEGREES_T));b.Add(o)
 boxes.append(dict(text=t['text'],xy=t['xy']))
p.SaveBoard(str(T/'candidate.kicad_pcb'),b);shutil.copyfile(R/'adapter.kicad_pro',T/'candidate.kicad_pro')
out={'status':'candidate pending native silk DRC','source_board_sha256':hashlib.sha256((R/'adapter.kicad_pcb').read_bytes()).hexdigest(),'texts':texts,'footprint_silk_edits':edits,'text_boxes':boxes,'notes':['No component movement, copper edits, or DRC-rule exclusions. One J4 silkscreen outline segment is omitted.','Optional host EN label omitted to keep the cable pin legend clear; NO VM remains for orientation.','Compact cable legend retains pin numbers and polarity: 1+ means pin1 COM+, 2P-/3D-/4E- are the three sink outputs.','Terminal polarity labels moved away from terminal outline.','Power-off instruction wrapped and moved to the open lower-right area.']}
(R/'silkscreen-proposal.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(boxes,indent=2))
