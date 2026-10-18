from pathlib import Path
import json
R=Path(__file__).resolve().parent
source=(R/'route_candidate.py').read_text().split('nets={name:')[0]
source=source.replace("S = .05","S = .025").replace("CLEAR = .17","CLEAR = .155")
source=source.replace("board = p.LoadBoard(str(ROOT/'adapter.kicad_pcb'))","board = p.LoadBoard(str(ROOT/'buck-en-join/source-moved-r21.kicad_pcb'))")
scope={'__file__':str(R/'route_candidate.py')};exec(compile(source,'router-prefix','exec'),scope)
p=scope['p'];board=scope['board'];layers=scope['LAYERS'];tracks=[];vias=[]
for tr in board.GetTracks():
 if tr.GetClass()=='PCB_VIA':
  pos=tr.GetPosition();vias.append((tr.GetNetname(),(p.ToMM(pos.x)-100,p.ToMM(pos.y)-100)))
 else:
  layer=board.GetLayerName(tr.GetLayer())
  if layer not in layers:continue
  a=tr.GetStart();b=tr.GetEnd();tracks.append((tr.GetNetname(),layers.index(layer),(p.ToMM(a.x)-100,p.ToMM(a.y)-100),(p.ToMM(b.x)-100,p.ToMM(b.y)-100),p.ToMM(tr.GetWidth())))
scope['tracks']=tracks;scope['vias']=vias;scope['routes']=[];scope['obstacle_cache'].clear()
for net,pin in [('/BUCK_EN','2'),('/BUCK_VIN','1')]:
 start=next(pad for pad in scope['padlist'] if pad['ref']=='R21' and pad['pin']==pin)
 targets=[dict(ref='MANUAL_VIA',pin='existing',net='/BUCK_EN',x=7.85,y=16.1,layers=[0,1,2])] if net=='/BUCK_EN' else [pad for pad in scope['padlist'] if pad['ref']=='D22' and pad['pin']=='1']
 result=scope['search'](net,start,targets)
 if result:
  path,target=result;scope['savepath'](net,path,start,target)
  print('FOUND',net,flush=True)
 else:
  print('NO_PATH',net,flush=True);break
(R/'buck-en-join/proposed-routes.json').write_text(json.dumps(scope['routes'],indent=2)+'\n')
print(json.dumps(scope['routes'],indent=2))
