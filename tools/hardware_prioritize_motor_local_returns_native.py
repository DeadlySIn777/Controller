"""Bounded same-net priority correction for seven NEW local return zones."""
import argparse,json,shutil,subprocess,collections
from pathlib import Path
import pcbnew
from hardware_route_current_delivery_native import sha
from hardware_route_logic_return import identity,pad_identity
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--receipt',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True);r=json.loads(a.receipt.read_text());assert r['board_sha256']==sha(a.board);before=sha(a.board);b=pcbnew.LoadBoard(str(a.board));oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};op={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};rows=[z for z in r['new_zones']if z['net']=='/LOGIC_GND'];assert len(rows)==7;zs={z.m_Uuid.AsString():z for z in b.Zones()};changes=[]
 for row in rows:
  z=zs[row['uuid']];assert z.GetNetname()=='/LOGIC_GND'and z.GetLayer()==pcbnew.In1_Cu and z.GetAssignedPriority()==10 and z.GetZoneName()==row['role'];z.SetAssignedPriority(11);changes.append(dict(uuid=row['uuid'],name=z.GetZoneName(),net='/LOGIC_GND',layer='In1.Cu',before=10,after=11,only_new_local_same_net=True))
 pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();dest=a.out/'motor-supply-cells-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
 for ext in ['.kicad_pro','.kicad_dru']:shutil.copyfile(a.board.with_suffix(ext),dest.with_suffix(ext))
 for f in a.board.parent.iterdir():
  if f.name=='fp-lib-table':(a.out/f.name).write_text(f.read_text().replace('${KIPRJMOD}',a.board.parent.resolve().as_posix()))
  elif f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,a.out/f.name)
 q=pcbnew.LoadBoard(str(dest));q.BuildConnectivity();assert oldcu=={t.m_Uuid.AsString():identity(t)for t in q.GetTracks()}and op=={p.m_Uuid.AsString():pad_identity(p)for p in q.GetPads()};p=subprocess.run([CLI,'pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(a.out/'drc.json'),str(dest)],capture_output=True,text=True);assert p.returncode==0;d=json.loads((a.out/'drc.json').read_text());assert not d.get('ignored_checks');r['board_sha256']=sha(dest);r['native_errors']=[v for v in d['violations']if v['severity']=='error'];assert not r['native_errors'];r['native_DRC_types']=dict(collections.Counter(v['type']for v in d['violations']));r['uncapped_joins']=q.GetConnectivity().GetUnconnectedCount(False);r['priority_only_delta']=changes;r['prior_immutable_donor']=dict(path=str(a.board),sha256=before,receipt_path=str(a.receipt),receipt_sha256=sha(a.receipt));r['priority_helper_sha256']=sha(Path(__file__));assert sha(a.board)==before;(a.out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(board_sha256=r['board_sha256'],changed_zones=len(changes),native_errors=0,uncapped_joins=r['uncapped_joins'])))
if __name__=='__main__':main()
