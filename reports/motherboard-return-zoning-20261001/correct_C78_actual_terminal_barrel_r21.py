"""Bounded actual C78 terminal/barrel correction; frozen failed bend trials stay intact."""
import sys,json,shutil,subprocess
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import identity,pad_identity,xy
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_route_owned_bypass_loops import drc
from hardware_stitch_owned_return_planes import definitions
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-facing-health-actual-Source-collars-r14/motherboard-facing-health-Source-collars-candidate.kicad_pcb')
D=B.parent;O=D.with_name('ROOT101-facing-health-C78-terminal-barrel-r21');assert not O.exists();O.mkdir()
assert sha(B)=='c6277fed7822a3436cf975eeda7f4acfc5bf3e73b9f4b4cb6699ec90d2c0797e'
M=D/'current108-final-bypass-manifest.json'
inputs={str(p):sha(p)for p in(B,M,B.with_suffix('.kicad_pro'),B.with_suffix('.kicad_dru'),Path(__file__))}
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity()
oldcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()}
nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};oldcl=native_pad_clusters(b,nets)
cu={t.m_Uuid.AsString():t for t in b.GetTracks()}
vertical='6f49e7ba-a6f7-4165-a682-06b8e9291a8e';terminal='0e678fe0-3353-45a1-ae9c-5e720d87de74'
barrel='9d7ff79f-eaf2-47e4-b28d-6b7138e8acf8';back='2c3fb5ed-2496-489e-9df0-6ddc143bd63b'
ids=[vertical,terminal,barrel,back]
assert tuple(cu[vertical].GetStart())==tuple(xy((342.8,175))) and tuple(cu[vertical].GetEnd())==tuple(xy((342.8,176.3)))
assert tuple(cu[terminal].GetStart())==tuple(xy((342.8,176.3))) and tuple(cu[terminal].GetEnd())==tuple(xy((343,176.3)))
assert tuple(cu[barrel].GetPosition())==tuple(xy((343,176.3))) and cu[barrel].Type()==pcbnew.PCB_VIA_T
assert tuple(cu[back].GetEnd())==tuple(xy((343,176.3)))
cu[vertical].SetEnd(xy((342.8,175.85)))
cu[terminal].SetStart(xy((342.8,175.85)));cu[terminal].SetEnd(xy((343,176.65)))
cu[barrel].SetPosition(xy((343,176.65)));cu[barrel].SetIsFree(True)
cu[back].SetEnd(xy((343,176.65)))
dest=O/'motherboard-facing-health-C78-terminal-candidate.kicad_pcb'
for ext in('.kicad_pro','.kicad_dru'):shutil.copy2(B.with_suffix(ext),dest.with_suffix(ext))
for q in D.iterdir():
 if q.is_dir()and(q.suffix=='.pretty'or q.name=='3dmodels'):shutil.copytree(q,O/q.name)
 elif q.name=='fp-lib-table':shutil.copy2(q,O/q.name)
pcbnew.SaveBoard(str(dest),b)
write(O/'generation.json',dict(input_sha256=inputs,before_board=str(B),before_board_sha256=sha(B),modified_Cu_UUIDs=ids,turn_mm=[342.8,175.85],barrel_before_mm=[343,176.3],barrel_after_mm=[343,176.65],reason='Keep the .25 mm terminal conductor inside the real SC6 pad gap until the lower pad edge, then end the outside-antipad diagonal at the actual moved positive barrel. Exact .50/.20 geometry, Source return, lands and power arrays stay unchanged.'))
write(O/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=ids,reviewed_added_zone_UUIDs=[],reviewed_scope_reason='C78 actual positive barrel and its three attached dedicated leaves only; no receiving Ground/parts/lands/power array/zone edits.'))
print('Native refill exact C78 terminal/barrel correction',flush=True)
n=drc(dest,O,'native');assert not n['violations']and not n['ignored_checks'],'Native error/warning; preserve rejected trial'
after=pcbnew.LoadBoard(str(dest));after.BuildConnectivity();now={t.m_Uuid.AsString():identity(t)for t in after.GetTracks()}
assert set(now)==set(oldcu)and all(oldcu[u]==now[u]for u in oldcu if u not in ids)
assert oldpads=={p.m_Uuid.AsString():pad_identity(p)for p in after.GetPads()}and definitions(B)==definitions(dest)
newcl=native_pad_clusters(after,nets);assert clusters_survive(oldcl,newcl)
write(O/'all-prior-Source-clusters.json',dict(passed=True,before=oldcl,after=newcl))
manifest=json.loads(M.read_text());group=next(g for g in manifest['owned_loops']if g['ref']=='C11078')
group['exact_modified_Cu_UUIDs']=ids;group['explicit_rebind_reason']='Facing C78 exact positive barrel and three attached terminal leaves move to place the actual bend outside its own endpoint antipad, preserving SC6 land spacing.'
manifest['board_sha256']=sha(dest);write(O/'current108-final-bypass-manifest.json',manifest);write(O/'C78-focused-manifest.json',dict(manifest,owned_loops=[group]))
run=subprocess.run([sys.executable,'tools/hardware_verify_owned_bypass_batch.py','--board',str(dest),'--owners','reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json','--receipt',str(O/'C78-focused-manifest.json'),'--out',str(O/'C78-actual-strict-loop-proof.json')],capture_output=True,text=True)
(O/'C78-strict-command.txt').write_text(run.stdout+run.stderr);assert run.returncode==0,'Actual C78 strict reference failed; preserve rejected trial'
assert all(sha(Path(q))==h for q,h in inputs.items())
write(O/'receipt.json',dict(passed=True,board=str(dest),board_sha256=sha(dest),before_board=str(B),before_board_sha256=sha(B),native_errors=0,native_warnings=0,all_old_Source_clusters=True,exact_four_object_scope=True,actual_C78_strict_loop=True,global_full108_controls_resources_power_pending=True,manufacturing_ready=False))
print(json.dumps(dict(passed=True,board_sha256=sha(dest))),flush=True)
