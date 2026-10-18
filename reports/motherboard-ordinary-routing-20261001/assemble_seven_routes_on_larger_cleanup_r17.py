"""Copy exact verified65 route items onto the larger physical cleanup trial."""
from pathlib import Path
import sys,json,shutil,subprocess
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_critical_digital_wip_r05 as authority
from hardware_route_logic_return import identity,pad_identity
e=authority.engine;p=Path(__file__).parent;base=p/'IO3-literal-unused-tip-cleanup-r02/motherboard-IO3-literal-tip-cleanup-candidate.kicad_pcb';donor=Path('reports/motherboard-pcb-integration-20261001/source26-seven-path-OBS29-repair-trial-r86/motherboard-bounded-merged-candidate.kicad_pcb');out=Path('reports/motherboard-pcb-integration-20261001/source26-seven-path-larger-IO3-cleanup-trial-r87')
native=e.read(base.parent/'native.json');assert not native['violations']and not native['ignored_checks']
assert e.sha(donor)=='282e0e5b6cf7684ea844f693fd184d70ab18b72ac2c4a0b5a3c8064d4e817cb7'
proof=e.read(donor.parent/'combined-seven-pair-source-return-proof/review.json');assert proof['passed']and not proof['includes_power_verification']and len(proof['actual_persisted_route_cuts'])==7
plan=e.read(donor.parent/'proposed-groups.json');ids={u for g in plan['groups']for u in g['new_copper_UUIDs']};assert len(ids)==65
b=pcbnew.LoadBoard(str(base));d=pcbnew.LoadBoard(str(donor));bc={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};dc={t.m_Uuid.AsString():identity(t)for t in d.GetTracks()}
assert set(dc)-set(bc)==ids and all(dc[u]==row for u,row in bc.items())
assert {q.m_Uuid.AsString():pad_identity(q)for q in b.GetPads()}=={q.m_Uuid.AsString():pad_identity(q)for q in d.GetPads()}
tree=e.parse(base.read_text());dtree=e.parse(donor.read_text());nodes=[node for node in dtree if isinstance(node,list)and node and node[0]in('segment','via','arc')and e.value(e.child(node,'uuid')[1])in ids];assert len(nodes)==65
tree.extend(nodes);out.mkdir(exist_ok=False);dest=out/'motherboard-bounded-merged-candidate.kicad_pcb';dest.write_text(authority.dump_native_board(tree)+'\n')
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(base.with_suffix(suffix),dest.with_suffix(suffix))
for f in base.parent.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,out/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,out/f.name)
e.write(out/'route-assembly-proposal.json',dict(input_sha256={str(base):e.sha(base),str(donor):e.sha(donor),str(donor.parent/'combined-seven-pair-source-return-proof/review.json'):e.sha(donor.parent/'combined-seven-pair-source-return-proof/review.json')},exact_new_Cu=sorted(ids),all_base_Cu_and_native_lands_preserved=True,only_large_cleanup_zone_retained=True,no_small_cleanup_zone_copied=True,complete_native_checks_and_independent_power_cleanup_proof_required=True,adopted=False,manufacturing_ready=False))
with(out/'drc-command.txt').open('w')as log:r=subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--refill-zones','--save-board','--format','json','--severity-all','--all-track-errors','-o',str(out/'drc.json'),str(dest)],stdout=log,stderr=subprocess.STDOUT)
print(json.dumps(dict(command_exit=r.returncode,board_sha256=e.sha(dest),adopted=False)))
