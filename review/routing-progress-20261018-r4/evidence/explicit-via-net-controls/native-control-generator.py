"""Tiny native controls: explicit via nets must not suppress real DRC errors."""
from pathlib import Path
import json,hashlib,sys
import pcbnew
import math
HERE=Path(__file__).resolve().parent;B=HERE.parent
OUT=HERE/'explicit-via-net-controls-root-r1';OUT.mkdir(exist_ok=False)
SOURCE=B/'power-review/zone-priority-pad-aperture-fixture-r1/pad_only-selected-both.kicad_pcb'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source_hash=sha(SOURCE);manager=pcbnew.GetSettingsManager()
assert manager.LoadProject(str(SOURCE.with_suffix('.kicad_pro')))
project=manager.GetProject(str(SOURCE.with_suffix('.kicad_pro')))
b=pcbnew.LoadBoard(str(SOURCE));b.SetProject(project)
def inside(x,y,ring):
 result=False
 for (ax,ay),(bx,by) in zip(ring,ring[1:]+ring[:1]):
  if (ay>y)!=(by>y) and x<(bx-ax)*(y-ay)/(by-ay)+ax:result=not result
 return result
def edge_distance(x,y,ring):
 answer=float('inf')
 for (ax,ay),(bx,by) in zip(ring,ring[1:]+ring[:1]):
  dx,dy=bx-ax,by-ay;norm=dx*dx+dy*dy;t=max(0,min(1,((x-ax)*dx+(y-ay)*dy)/norm)) if norm else 0
  answer=min(answer,math.hypot(x-ax-t*dx,y-ay-t*dy))
 return answer
boxes=[p.GetBoundingBox() for f in b.GetFootprints() for p in f.Pads()]
def away_from_pads(x,y):
 for bb in boxes:
  dx=max(bb.GetX()-x,0,x-bb.GetX()-bb.GetWidth());dy=max(bb.GetY()-y,0,y-bb.GetY()-bb.GetHeight())
  if math.hypot(dx,dy)<1000000:return False
 return True
candidates=[]
for z in b.Zones():
 if z.GetIsRuleArea():continue
 for layer in z.GetLayerSet().Seq():
  if layer==pcbnew.F_Cu:continue
  p=z.GetFilledPolysList(layer)
  for i in range(p.OutlineCount()):
   rings=[p.COutline(i)]+[p.CHole(i,j) for j in range(p.HoleCount(i))]
   rings=[[(r.CPoint(j).x,r.CPoint(j).y) for j in range(r.PointCount())] for r in rings]
   outer=rings[0];xs=[x for x,y in outer];ys=[y for x,y in outer]
   area=abs(sum(ax*by-bx*ay for (ax,ay),(bx,by) in zip(outer,outer[1:]+outer[:1])))
   for x in range(min(xs)+1000000,max(xs),1000000):
    for y in range(min(ys)+1000000,max(ys),1000000):
     if inside(x,y,outer) and not any(inside(x,y,h) for h in rings[1:]) and min(edge_distance(x,y,r) for r in rings)>900000 and away_from_pads(x,y):candidates.append((area,x,y,z.GetNetname()))
assert candidates
_,x,y,ground=max(candidates);at=pcbnew.VECTOR2I(x,y)
rows=[]
for free in (False,True):
 b=pcbnew.LoadBoard(str(SOURCE));b.SetProject(project)
 net=pcbnew.NETINFO_ITEM(b,'EXPLICIT_SIGNAL_CONTROL');b.Add(net)
 via=pcbnew.PCB_VIA(b);via.SetPosition(at);via.SetWidth(600000);via.SetDrill(300000);via.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);via.SetNetCode(net.GetNetCode());via.SetIsFree(free);b.Add(via)
 uid=str(via.m_Uuid.AsString());path=OUT/('manual' if free else 'automatic');path=path.with_suffix('.kicad_pcb')
 pcbnew.SaveBoard(str(path),b)
 # Use the same project settings in CLI DRC and the same native load boundary.
 path.with_suffix('.kicad_pro').write_bytes(SOURCE.with_suffix('.kicad_pro').read_bytes())
 loaded=pcbnew.LoadBoard(str(path));loaded.SetProject(project);loaded.BuildConnectivity()
 v=next(t for t in loaded.GetTracks() if str(t.m_Uuid.AsString())==uid)
 actual=v.GetNetname();assert v.GetIsFree()==free
 if free:assert actual=='EXPLICIT_SIGNAL_CONTROL','Explicit via net did not survive genuine native load'
 else:assert actual!= 'EXPLICIT_SIGNAL_CONTROL','Negative control did not reproduce automatic net reassignment'
 pcbnew.SaveBoard(str(path),loaded)
 row={'free':free,'via_UUID':uid,'declared_net':'EXPLICIT_SIGNAL_CONTROL','actual_after_reload':actual,'ground_at_location':ground,'at_IU':[at.x,at.y],'file':str(path),'SHA256':sha(path)}
 if free:
  assert b'(free yes)' in path.read_bytes(), 'Observe actual installed serialization; never guess syntax'
  assert pcbnew.ZONE_FILLER(loaded).Fill(loaded.Zones())
  loaded.BuildConnectivity();v=next(t for t in loaded.GetTracks() if str(t.m_Uuid.AsString())==uid)
  assert v.GetNetname()=='EXPLICIT_SIGNAL_CONTROL'
  filled=OUT/'manual-refilled.kicad_pcb';pcbnew.SaveBoard(str(filled),loaded);filled.with_suffix('.kicad_pro').write_bytes(path.with_suffix('.kicad_pro').read_bytes());row['filled_file']=str(filled);row['filled_SHA256']=sha(filled)
 rows.append(row)
assert sha(SOURCE)==source_hash
(OUT/'native-controls.json').write_text(json.dumps({'status':'NATIVE_ASSIGNMENT_CONTROLS_PASSED_DRC_CONTROLS_PENDING','KiCad':pcbnew.GetBuildVersion(),'source_SHA256':source_hash,'rows':rows,'source_unchanged':True,'real_Fill_calls':1,'user_board_changed':False},indent=2)+'\n')
print('NATIVE_EXPLICIT_VIA_ASSIGNMENT_AND_REAL_REFILL_CONTROLS_PASSED',flush=True)
