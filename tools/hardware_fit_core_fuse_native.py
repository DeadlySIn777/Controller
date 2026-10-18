"""Move only CORE fuse holder into a checked service/copper-clear envelope."""
import argparse,json,math,shutil,subprocess,collections
from pathlib import Path
import pcbnew
from hardware_fit_power_recipes_native import box,rect,inflate,overlap
from hardware_route_logic_return import identity,pad_identity,mm,xy
from hardware_apply_fuse_geometry_upgrade import sha
from hardware_populate_motherboard_pcb import footprint_name
from hardware_build_assembly import parse,dump,child,value
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True);b=pcbnew.LoadBoard(str(a.board.resolve()));b.BuildConnectivity();fs={f.GetReference():f for f in b.GetFootprints()};f=fs['F11001'];assert footprint_name(f)=='CNC_MB_Fuse:Keystone_3568_M55';old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};attached={t.m_Uuid.AsString()for p in f.Pads()for t in b.GetConnectivity().GetConnectedItems(p)if t.Type()in[pcbnew.PCB_TRACE_T,pcbnew.PCB_VIA_T]};removed=[]
 for p in f.Pads():
  for t in b.GetConnectivity().GetConnectedItems(p):
   if t.Type()==pcbnew.PCB_PAD_T:assert t.GetParentFootprint().GetReference()=='F11001','An actual remote source path needs separate reviewed rerouting'
 if attached:
  removed=[dict(uuid=u,identity=old[u],reason='Exact old branch joins only pads of the moving CORE holder; no unchanged source/observer pad is attached')for u in sorted(attached)];tree=parse(a.board.read_text());tree[:]=[v for v in tree if not(isinstance(v,list)and v and v[0]in['segment','via','arc']and value(child(v,'uuid')[1])in attached)];cleared=a.out/'fuse-private-cleared-input.kicad_pcb';cleared.write_text(dump(tree)+'\n');b=pcbnew.LoadBoard(str(cleared.resolve()));fs={f.GetReference():f for f in b.GetFootprints()};f=fs['F11001'];old={u:v for u,v in old.items()if u not in attached}
 obstacles=[('FP '+r,inflate(box(v),.05))for r,v in fs.items()if r!='F11001'and v.GetLayer()==pcbnew.F_Cu];obstacles += [('Cu '+t.m_Uuid.AsString(),inflate(rect(t.GetBoundingBox()),.2))for t in b.GetTracks()if t.IsOnLayer(pcbnew.F_Cu)or isinstance(t,pcbnew.PCB_VIA)]
 original=mm(f.GetPosition());f.SetPosition(xy((0,0)));relative=box(f);winner=None;examined=0
 candidates=[(x,y)for x in range(290,337)for y in range(185,225)];candidates.sort(key=lambda p:math.dist(p,(306,206)))
 for x,y in candidates:
  # 2 mm lateral service allowance is a declared engineering target, not a
  # manufacturer insertion-force or installed enclosure qualification.
  service=inflate((relative[0]+x,relative[1]+y,relative[2]+x,relative[3]+y),2.);examined+=1
  if not any(overlap(service,q)for name,q in obstacles):winner=(x,y);break
 assert winner is not None,'No actual free fuse service envelope';f.SetPosition(xy(winner));dest=a.out/'core-fuse-service-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
 for ext in['.kicad_pro','.kicad_dru']:shutil.copyfile(a.board.with_suffix(ext),dest.with_suffix(ext))
 for p in a.board.parent.iterdir():
  if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,a.out/p.name)
  elif p.name=='fp-lib-table':(a.out/p.name).write_text(p.read_text().replace('${KIPRJMOD}',a.board.parent.resolve().as_posix()))
 q=pcbnew.LoadBoard(str(dest.resolve()));assert {t.m_Uuid.AsString():identity(t)for t in q.GetTracks()}==old;poses=[]
 for p in q.GetPads():
  r=p.GetParentFootprint().GetReference()
  if r!='F11001':assert pad_identity(p)==oldpads[p.m_Uuid.AsString()]
  else:poses.append(dict(uuid=p.m_Uuid.AsString(),pin=p.GetNumber(),net=p.GetNetname(),position_mm=mm(p.GetPosition())))
 run=subprocess.run([CLI,'pcb','drc','--format','json','--severity-all','--all-track-errors','-o',str(a.out/'drc.json'),str(dest)],capture_output=True,text=True);assert run.returncode==0;d=json.loads((a.out/'drc.json').read_text());assert not any(v['severity']=='error'for v in d['violations']);r=dict(source_board=str(a.board),source_sha256=sha(a.board),candidate_sha256=sha(dest),ref='F11001',old_position_mm=original,new_position_mm=winner,actual_courtyard_mm=box(next(f for f in q.GetFootprints()if f.GetReference()=='F11001')),reserved_service_envelope_mm=service,lateral_service_allowance_mm=2,vertical_fuse_entry=True,installed_enclosure_vertical_extraction_qualified=False,all_other_pad_and_copper_identities_preserved=True,old_attached_copper=removed,actual_pad_rows=poses,native_DRC_types=dict(collections.Counter(v['type']for v in d['violations'])),physical_mating_qualified=False,manufacturing_ready=False);(a.out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
if __name__=='__main__':main()
