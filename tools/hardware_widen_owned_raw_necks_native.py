"""Widen exactly three new RAW entry transitions on a native copy."""
import argparse,collections,json,shutil,subprocess
from pathlib import Path
import pcbnew
from hardware_route_current_delivery_native import Geometry,sha
from hardware_route_logic_return import identity,pad_identity,mm
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--owner',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True);frozen={str(p):sha(p)for p in [a.board,a.owner,Path(__file__)]};b=pcbnew.LoadBoard(str(a.board));g=Geometry(b);old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};pads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};cu={t.m_Uuid.AsString():t for t in b.GetTracks()};rows=[r for r in json.loads(a.owner.read_text())['exact_added_copper']if r['role']=='RAW_short_2mm_pad_neck'];assert len(rows)==3;changes=[]
 for row in rows:
  t=cu[row['uuid']];assert json.loads(json.dumps(identity(t)))==row['identity']and t.GetLayer()==pcbnew.F_Cu and pcbnew.ToMM(t.GetWidth())==2;assert g.clear([mm(t.GetStart()),mm(t.GetEnd())],t.GetNetname(),t.GetLayer(),3),t.GetNetname();t.SetWidth(pcbnew.FromMM(3));changes.append(dict(uuid=row['uuid'],before=row['identity'],after=identity(t)))
 pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();dest=a.out/'raw-neck-widened-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
 for e in ['.kicad_pro','.kicad_dru']:shutil.copyfile(a.board.with_suffix(e),dest.with_suffix(e))
 for f in a.board.parent.iterdir():
  if f.name=='fp-lib-table':(a.out/f.name).write_text(f.read_text().replace('${KIPRJMOD}',a.board.parent.resolve().as_posix()))
  elif f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,a.out/f.name)
 q=pcbnew.LoadBoard(str(dest));now={t.m_Uuid.AsString():identity(t)for t in q.GetTracks()};changed={r['uuid']for r in changes};assert all(now[k]==v for k,v in old.items()if k not in changed);assert all(now[r['uuid']]==r['after']for r in changes);assert pads=={p.m_Uuid.AsString():pad_identity(p)for p in q.GetPads()};assert all(sha(Path(p))==h for p,h in frozen.items())
 run=subprocess.run([CLI,'pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(a.out/'drc.json'),str(dest)],capture_output=True,text=True);assert run.returncode==0;d=json.loads((a.out/'drc.json').read_text());assert not d.get('ignored_checks');assert not any(v['severity']=='error'for v in d['violations']);q.BuildConnectivity();result=dict(input_hashes=frozen,board_sha256=sha(dest),exact_three_width_changes=changes,all_other_copper_pads_and_zone_definitions_preserved=True,native_DRC_types=dict(collections.Counter(v['type']for v in d['violations'])),uncapped_joins=q.GetConnectivity().GetUnconnectedCount(False),legacy_10C63um_current_screen_a=8.1220780075,plating_current_sharing_and_thermal_qualified=False);(a.out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['input_hashes','exact_three_width_changes']}))
if __name__=='__main__':main()
