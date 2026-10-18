"""Move one Bank A RAW barrel 0.20mm and center its exact three incident paths."""
from pathlib import Path
import sys,json,shutil,subprocess
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_populate_motherboard_pcb import sha,write
from hardware_route_logic_return import identity,pad_identity,xy
base=Path('reports/motherboard-pcb-integration-20261001/source26-motor-bank-A-merged-native-r88/motherboard-bounded-merged-candidate.kicad_pcb')
assert sha(base)=='2af6a7bbdd8b328cd8d4f0ddbd68dd8b1f81fe2625c46767085ad23c65af9ae5'
out=Path('reports/motherboard-pcb-integration-20261001/source26-motor-bank-A-RAW-repair-trial-r89');out.mkdir(exist_ok=False)
b=pcbnew.LoadBoard(str(base));old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};pads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};cu={t.m_Uuid.AsString():t for t in b.GetTracks()}
via='bea27f9d-8fa3-4d80-be69-6c0cb475fc88';new=(272.2,177.7)
assert tuple(cu[via].GetPosition())==tuple(xy((272.,177.7)))and cu[via].Type()==pcbnew.PCB_VIA_T
edits={
 '46b5d425-1414-4461-9979-80412ab47ad9':('start',(271.925,177.75)),
 '53b00436-cf21-4f3c-b77a-8e3ccf58ad45':('end',(271.925,177.75)),
 'ee4f7a13-36b1-4c27-8acf-38462b1d7d9a':('start',(272.,177.7))}
for u,(which,expected)in edits.items():
 t=cu[u];assert t.GetNetname()==cu[via].GetNetname()=='/motherboard_power_entry/MOTION_5V_RAW'
 actual=t.GetStart()if which=='start'else t.GetEnd();assert tuple(actual)==tuple(xy(expected))
 if which=='start':t.SetStart(xy(new))
 else:t.SetEnd(xy(new))
cu[via].SetPosition(xy(new))
allowed={via,*edits};actual={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()}
assert {u for u in old if old[u]!=actual[u]}==allowed
assert pads=={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()}
dest=out/base.name;pcbnew.SaveBoard(str(dest),b)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(base.with_suffix(suffix),dest.with_suffix(suffix))
for f in base.parent.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,out/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,out/f.name)
write(out/'proposed-exact-delta.json',dict(before_board_sha256=sha(base),changed_copper=[dict(uuid=u,before=old[u],after=actual[u])for u in sorted(allowed)],all_pads_poses_and_other_Cu_preserved=True,actual_three_RAW_barrels_retained=True,native_refill_and_current_reference_checks_pending=True,manufacturing_ready=False))
write(out/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(allowed),reviewed_added_zone_UUIDs=[],reviewed_scope_reason='Move actual RAW barrel by +0.20mmX to meet simultaneous hole spacing, center its F junction and B branch; preserve all three barrels and existing source paths. Pending fresh native proof.'))
with(out/'drc-command.txt').open('w')as log:
 r=subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--refill-zones','--save-board','--format','json','--all-track-errors','--severity-all','-o',str(out/'drc.json'),str(dest)],stdout=log,stderr=subprocess.STDOUT)
assert r.returncode==0
print(json.dumps(dict(command_exit=0,board_sha256=sha(dest),adopted=False)))
