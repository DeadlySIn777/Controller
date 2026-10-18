"""Build a new native CORE placement review fixture; never writes source PCB.

This is a placement-only loop recipe fixture, not a routed/manufacturing board.
All existing source footprints/nets are copied; unconnected counts are retained.
"""
from pathlib import Path
import json,hashlib,argparse
import pcbnew
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--board',required=True,type=Path);ap.add_argument('--recipes',required=True,type=Path);ap.add_argument('--group',default='CORE7');ap.add_argument('--output-dir',required=True,type=Path);a=ap.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True)
 digest=hashlib.sha256(a.board.read_bytes()).hexdigest();old=pcbnew.LoadBoard(str(a.board.resolve()));by={f.GetReference():f for f in old.GetFootprints()}
 recipe=json.loads(a.recipes.read_text());seed=recipe.get('groups',{}).get(a.group,recipe['CORE7_relative_seed'])
 out=pcbnew.BOARD();netnames=sorted({p.GetNetname()for r in seed for p in by[r].Pads()if p.GetNetname()});nets={}
 for name in netnames:n=pcbnew.NETINFO_ITEM(out,name);out.Add(n);nets[name]=n
 rows=[]
 for ref,(x,y,ang) in seed.items():
  f=pcbnew.FOOTPRINT(by[ref]);f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x+30),pcbnew.FromMM(y+30)));f.SetOrientationDegrees(ang)
  for p in f.Pads():
   name=p.GetNetname()
   if name:p.SetNet(nets[name])
  out.Add(f);box=f.GetBoundingBox(False,False)
  rows.append(dict(ref=ref,position_mm=[x+30,y+30],angle_deg=ang,pads=[dict(pin=p.GetNumber(),net=p.GetNetname(),position_mm=[pcbnew.ToMM(p.GetPosition().x),pcbnew.ToMM(p.GetPosition().y)])for p in f.Pads()]))
 for x1,y1,x2,y2 in [(10,10,80,10),(80,10,80,55),(80,55,10,55),(10,55,10,10)]:
  l=pcbnew.PCB_SHAPE();l.SetShape(pcbnew.SHAPE_T_SEGMENT);l.SetLayer(pcbnew.Edge_Cuts);l.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1),pcbnew.FromMM(y1)));l.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2),pcbnew.FromMM(y2)));l.SetWidth(pcbnew.FromMM(.05));out.Add(l)
 target=a.output_dir/'CORE7-placement-loop-fixture.kicad_pcb';pcbnew.SaveBoard(str(target),out)
 # Project retains normal .15 mm geometry checks; unrouted remains reported.
 pro=dict(board=dict(design_settings=dict(rules=dict(min_clearance=.15,min_hole_clearance=.15,min_track_width=.15,min_via_annular_width=.15,min_via_diameter=.5,min_through_hole_diameter=.2),rule_severities={})),pcbnew=dict(last_paths={}),meta=dict(filename='CORE7-placement-loop-fixture.kicad_pro',version=1))
 target.with_suffix('.kicad_pro').write_text(json.dumps(pro,indent=2)+'\n')
 (a.output_dir/'fp-lib-table').write_text((a.board.parent/'fp-lib-table').read_text().replace('${KIPRJMOD}',a.board.parent.resolve().as_posix()))
 assert digest==hashlib.sha256(a.board.read_bytes()).hexdigest()
 (a.output_dir/'placement-pad-receipt.json').write_text(json.dumps(dict(source_board_sha256=digest,source_board_unchanged=True,fixture_only=True,geometry_qualified=False,routed=False,manufacturing_ready=False,components=rows),indent=2)+'\n')
 print(json.dumps(dict(components=len(rows),fixture=str(target),routed=False)))
if __name__=='__main__':main()
