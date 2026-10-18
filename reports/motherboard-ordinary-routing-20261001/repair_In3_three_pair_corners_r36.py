"""Move six new segment ends to preserve full square-ended reference corridors."""
from pathlib import Path
import sys,json,copy,shutil,subprocess
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_ordinary_wip_r05 as o
from hardware_route_logic_return import identity,xy
e=o.engine;p=Path(__file__).parent
src=p/'actual-source26-DI7-In3-extended-r29';out=p/'actual-source26-In3-three-pair-corner-repair-r36';out.mkdir(exist_ok=False)
base=src/'motherboard-ordinary-In2-batch-candidate.kicad_pcb';b=pcbnew.LoadBoard(str(base))
cu={t.m_Uuid.AsString():t for t in b.GetTracks()};old={u:identity(t)for u,t in cu.items()}
changes={
 '1eb05fec-beb2-4c41-bb4e-55fbe8fb74de':('end',(110.1375,203.75)),
 'c703e537-3207-4410-bb07-ad0179d2714a':('start',(110.1375,203.75)),
 '2b8237e1-cd7a-452d-a8c0-73b60652c4c1':('end',(110.451681,203.175975)),
 '5da5c12d-20a9-449c-b057-092bc2d7b26e':('start',(110.451681,203.175975)),
 'b684c41c-9d77-4377-adc0-21f6ed3ae04a':('end',(115.25,205.8625)),
 '4630c49a-4abc-4f35-8d29-0591d444543b':('start',(115.25,205.8625))}
plan=e.read(src/'proposed-groups.json');newids=set(plan['new_copper_UUIDs']);assert set(changes)<=newids
for uid,(which,pt)in changes.items():
 t=cu[uid];assert t.Type()==pcbnew.PCB_TRACE_T
 (t.SetStart if which=='start'else t.SetEnd)(xy(pt))
current={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()}
assert {u for u in old if old[u]!=current[u]}==set(changes)
plan['groups'][0]['start']['front_path_mm'][1]=[110.1375,203.75]
plan['groups'][0]['back_path_mm'][1]=[110.451681,203.175975]
plan['groups'][2]['start']['front_path_mm'][1]=[115.25,205.8625]
plan['physical_corner_repairs']=[dict(uuid=u,before=old[u],after=current[u])for u in changes]
plan['original_failed_donor_sha256']=e.sha(base)
dest=out/base.name;pcbnew.SaveBoard(str(dest),b)
for ext in('.kicad_pro','.kicad_dru'):shutil.copyfile(base.with_suffix(ext),dest.with_suffix(ext))
for f in src.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,out/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,out/f.name)
e.write(out/'proposed-groups.json',plan);shutil.copyfile(src/'manifest.json',out/'manifest.json')
with(out/'drc-command.txt').open('w')as log:
 r=subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--refill-zones','--save-board','--format','json','--all-track-errors','--severity-all','-o',str(out/'drc.json'),str(dest)],stdout=log,stderr=subprocess.STDOUT)
assert r.returncode==0
print(json.dumps(dict(board_sha256=e.sha(dest),native_violations=len(e.read(out/'drc.json')['violations']),adopted=False)))
