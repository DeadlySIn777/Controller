import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from PIL import Image,ImageDraw
from hardware_route_logic_return import mm
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/motor-head-feed-r74/rejected-debug.kicad_pcb');mapping=json.load(open('reports/motherboard-domains-20261001/source26-r69-r01/domain-map.json'));domain={p['uuid']:p['domain']for p in mapping['pads']};scale=7
for layer in[pcbnew.F_Cu,pcbnew.B_Cu]:
 im=Image.new('RGB',(1050,700),'white');dr=ImageDraw.Draw(im);cv=lambda p:((p[0]-240)*scale,(p[1]-150)*scale)
 for poly in mapping['barriers']:dr.polygon([cv(p)for p in poly['polygon_mm']],fill='#dddddd')
 for t in b.GetTracks():
  if not t.IsOnLayer(layer):continue
  s,e=mm(t.GetStart()),mm(t.GetEnd());n=t.GetNetname();col='#ffbb88'if'FIELD'in n or'_RAW'in n and 'MOTION'not in n else'#99bbbb'if n=='/LOGIC_GND'else'#bbbbbb';w=pcbnew.ToMM(t.GetWidth(layer)if isinstance(t,pcbnew.PCB_VIA)else t.GetWidth());dr.line([cv(s),cv(e)],fill=col,width=max(1,round(w*scale)))
 for p in b.GetPads():
  if not p.IsOnLayer(layer):continue
  poly=p.GetEffectivePolygon(layer);col='#4488ff'if domain.get(p.m_Uuid.AsString())not in['LOGIC','NC',None]else'#aa3333';col='#77aaaa'if p.GetNetname()=='/LOGIC_GND'else col
  for k in range(poly.OutlineCount()):dr.polygon([cv(mm(poly.Outline(k).CPoint(i)))for i in range(poly.Outline(k).PointCount())],fill=col)
 for f in b.GetFootprints():
  x,y=mm(f.GetPosition())
  if f.GetReference().startswith('U') and 240<x<390 and 150<y<250:dr.text(cv((x,y)),f.GetReference(),fill='black')
 for r,pins in[('U11032',['5']),('U11034',['5']),('U11010',['5']),('U11011',['5'])]:
  f=next(f for f in b.GetFootprints()if f.GetReference()==r)
  for p in f.Pads():
   if p.GetNumber()in pins:x,y=cv(mm(p.GetPosition()));dr.ellipse((x-4,y-4,x+4,y+4),outline='purple',width=3);dr.text((x+5,y+5),r+'ON',fill='purple')
 im.save('reports/motherboard-power-entry-20261001/motor-head-staging-r70/obstacles-'+b.GetLayerName(layer)+'.png')

