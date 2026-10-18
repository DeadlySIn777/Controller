"""Fit source-reviewed converter groups to a COPY, preserving all old copper.

This is a geometry review candidate only. Dedicated loop routes require a
separate parent transaction; old dangling stubs are not fabrication proof.
"""
from pathlib import Path
import pcbnew,json,math,argparse,hashlib,shutil,collections
def mm(v):return pcbnew.ToMM(v)
def rect(bb):return (mm(bb.GetLeft()),mm(bb.GetTop()),mm(bb.GetRight()),mm(bb.GetBottom()))
def overlap(a,b):return a[0]<b[2] and a[2]>b[0] and a[1]<b[3] and a[3]>b[1]
def inflate(a,n):return(a[0]-n,a[1]-n,a[2]+n,a[3]+n)
def box(f):
 shapes=[rect(s.GetBoundingBox())for s in f.GraphicalItems()if s.GetLayer() in [pcbnew.F_CrtYd,pcbnew.B_CrtYd]]
 if not shapes:return rect(f.GetBoundingBox(False,False))
 return(min(a[0]for a in shapes),min(a[1]for a in shapes),max(a[2]for a in shapes),max(a[3]for a in shapes))
def copper(b):return sorted((str(t.m_Uuid.AsString()),t.GetNetname(),t.GetLayer(),t.GetWidth(pcbnew.F_Cu) if isinstance(t,pcbnew.PCB_VIA) else t.GetWidth(),t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y)for t in b.GetTracks())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--recipes',type=Path,required=True);ap.add_argument('--output-dir',type=Path,required=True);a=ap.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True)
 before=hashlib.sha256(a.board.read_bytes()).hexdigest();b=pcbnew.LoadBoard(str(a.board.resolve()));fs={f.GetReference():f for f in b.GetFootprints()};original=copper(b);groups=json.loads(a.recipes.read_text())['groups'];moving={r for g in groups.values()for r in g}
 obstacles=[('FP '+r,inflate(box(f),.05))for r,f in fs.items()if r not in moving]
 obstacles += [('CU '+str(t.m_Uuid.AsString()),inflate(rect(t.GetBoundingBox()),.20))for t in b.GetTracks()if t.IsOnLayer(pcbnew.F_Cu)]
 grid=collections.defaultdict(list);unit=5.0
 def cells(r):return[(x,y)for x in range(math.floor(r[0]/unit),math.floor(r[2]/unit)+1)for y in range(math.floor(r[1]/unit),math.floor(r[3]/unit)+1)]
 def add(o):
  idx=len(obstacles_used);obstacles_used.append(o)
  for cell in cells(o[1]):grid[cell].append(idx)
 obstacles_used=[]
 for o in obstacles:add(o)
 bounds=rect(b.GetBoardEdgesBoundingBox());receipt=[]
 for name,seed in groups.items():
  rel=[]
  for r,(x,y,ang)in seed.items():
   f=pcbnew.FOOTPRINT(fs[r]);f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y)));f.SetOrientationDegrees(ang);rel.append((r,box(f)))
  ext=(min(r[0]for _,r in rel),min(r[1]for _,r in rel),max(r[2]for _,r in rel),max(r[3]for _,r in rel))
  primary=next(r for r in seed if r.startswith('U'));old=fs[primary].GetPosition();origin=(mm(old.x),mm(old.y))
  candidates=[(x,y)for x in range(5,456,2)for y in range(5,336,2)if bounds[0]+1<x+ext[0] and x+ext[2]<bounds[2]-1 and bounds[1]+1<y+ext[1]and y+ext[3]<bounds[3]-1]
  candidates.sort(key=lambda p:math.hypot(p[0]-origin[0],p[1]-origin[1]));winner=None
  for ox,oy in candidates:
   clear=True
   for r,q in rel:
    bb=(q[0]+ox,q[1]+oy,q[2]+ox,q[3]+oy);ids={i for cell in cells(bb)for i in grid.get(cell,[])}
    if any(overlap(bb,obstacles_used[i][1])for i in ids):clear=False;break
   if clear:winner=(ox,oy);break
  if winner is None:receipt.append(dict(group=name,fit=False));continue
  ox,oy=winner
  for r,(x,y,ang)in seed.items():
   f=fs[r];f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x+ox),pcbnew.FromMM(y+oy)));f.SetOrientationDegrees(ang);add(('NEW '+r,inflate(box(f),.05)))
  receipt.append(dict(group=name,fit=True,source_origin_mm=list(origin),new_origin_mm=list(winner),refs=list(seed),copper_or_other_footprint_AABB_intersections=0))
 assert original==copper(b)
 target=a.output_dir/'power-groups-geometry-candidate.kicad_pcb';pcbnew.SaveBoard(str(target),b)
 for suffix in ['.kicad_pro','.kicad_dru']:
  p=a.board.with_suffix(suffix)
  if p.exists():shutil.copyfile(p,target.with_suffix(suffix))
 (a.output_dir/'fp-lib-table').write_text((a.board.parent/'fp-lib-table').read_text().replace('${KIPRJMOD}',a.board.parent.resolve().as_posix()))
 assert before==hashlib.sha256(a.board.read_bytes()).hexdigest()
 (a.output_dir/'placement-receipt.json').write_text(json.dumps(dict(source_board=str(a.board),source_board_sha256=before,source_board_unchanged=True,copper_items_before=len(original),copper_items_after=len(original),all_copper_geometry_and_net_records_preserved=True,groups=receipt,routed=False,hotloops_routed=False,manufacturing_ready=False),indent=2)+'\n')
 print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
