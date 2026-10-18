"""Actual paired In2 pour-only DFM collar; no thin-feature guard waiver."""
from pathlib import Path
import sys,json,shutil,subprocess
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path(__file__).parent)]
import pcbnew
import check_literal_CCK_CORE_preservation_r04 as c
P=Path(__file__).parent;pre=json.loads((P/'CCK-IO3-antipad-cleanup-preflight-r09/review.json').read_text());assert pre['passed']and not pre['failures']
kind=sys.argv[1];assert kind in ('baseline','cck');src=P/('CORE-literal-antipad-join-'+kind+'-r03/motherboard-CORE-literal-antipad-join-candidate.kicad_pcb');O=P/('CCK-literal-IO3-collar-'+kind+'-r09');O.mkdir(exist_ok=False)
if kind=='baseline':assert c.sha(src)==pre['board_sha256']
assert c.sha(c.SOURCE)==pre['source_sha256']and c.sha(c.FROZEN)==pre['frozen_power_guard_sha256']
b=pcbnew.LoadBoard(str(src));old=next(t for t in b.GetTracks()if t.m_Uuid.AsString()==pre['actual_old_Ground_via_UUID']);from hardware_route_logic_return import identity
assert json.loads(json.dumps(identity(old)))==pre['actual_old_via_identity']
rule=pcbnew.ZONE(b);rule.SetLayer(pcbnew.In2_Cu);rule.SetIsRuleArea(True);rule.SetZoneName('Literal unused IO3 tip at unchanged Ground93.6,44');rule.SetDoNotAllowZoneFills(True)
for method in ('SetDoNotAllowTracks','SetDoNotAllowVias','SetDoNotAllowPads','SetDoNotAllowFootprints'):getattr(rule,method)(False)
rule.Outline().Append(c.f.box(*pre['literal_bounds_mm']));b.Add(rule);dest=O/'motherboard-IO3-antipad-collar-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
uid='52b8fd3e-3b4d-4e07-84fa-1f5d81cb7ddb';text=dest.read_text();assert text.count(rule.m_Uuid.AsString())==1;dest.write_text(text.replace(rule.m_Uuid.AsString(),uid))
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(src.with_suffix(suffix),dest.with_suffix(suffix))
for file in src.parent.iterdir():
    if file.is_dir()and file.suffix=='.pretty':shutil.copytree(file,O/file.name)
    elif file.name=='fp-lib-table':shutil.copyfile(file,O/file.name)
(O/'proposal.json').write_text(json.dumps(dict(input_board_sha256=c.sha(src),source_sha256=c.sha(c.SOURCE),literal_rule_uuid=uid,literal_In2_bounds_mm=pre['literal_bounds_mm'],preflight_sha256=c.sha(P/'CCK-IO3-antipad-cleanup-preflight-r09/review.json'),actual_physical_collar_mm=.125,only_one_new_pour_only_In2_rule=True,native_existing_Cu_pads_poses_and_all_old_zone_defs_pending_exact_proof=True,adopted=False,manufacturing_ready=False),indent=2)+'\n')
with (O/'native-command.log').open('w')as log:r=subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--refill-zones','--save-board','--format','json','--severity-all','--all-track-errors','-o',str(O/'native.json'),str(dest)],stdout=log,stderr=subprocess.STDOUT)
print(json.dumps(dict(kind=kind,command_exit=r.returncode,board_sha256=c.sha(dest),adopted=False)))
