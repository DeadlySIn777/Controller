"""Bounded new-signal-only knot correction preserving a real old IO3 feature."""
from pathlib import Path
import sys,json,shutil,subprocess
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path(__file__).parent)]
import pcbnew
import check_literal_CCK_CORE_preservation_r04 as core
from hardware_route_logic_return import identity,xy,mm
P=Path(__file__).parent;OLD=P/'actual-source26-root84-FPGA-CCK-C1022-In2-knot-r07/motherboard-FPGA-flash-CCK-candidate.kicad_pcb';O=P/'actual-source26-root84-FPGA-CCK-C1022-In2-knot-r08';O.mkdir(exist_ok=False)
b=pcbnew.LoadBoard(str(OLD));cu={t.m_Uuid.AsString():t for t in b.GetTracks()};changed=[]
for uid,which in [('0affcca0-07d2-4deb-86fa-5ed3dfa2ecc5','end'),('6228395d-eb7d-4824-8e2a-f5da3effc4c2','start')]:
    t=cu[uid];old=identity(t);assert t.GetNetname()=='/fpga_core/FPGA_FLASH_CCK_SOURCE'and t.GetLayer()==pcbnew.In2_Cu and t.GetWidth()==pcbnew.FromMM(.35)
    assert mm(t.GetEnd()if which=='end'else t.GetStart())==(94.30,44.)
    if which=='end':t.SetEnd(xy((94.425,44.)))
    else:t.SetStart(xy((94.425,44.)))
    changed.append(dict(uuid=uid,before_identity=old,after_identity=identity(t)))
dest=O/'motherboard-FPGA-flash-CCK-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(OLD.with_suffix(suffix),dest.with_suffix(suffix))
for file in OLD.parent.iterdir():
    if file.is_dir()and file.suffix=='.pretty':shutil.copytree(file,O/file.name)
    elif file.name=='fp-lib-table':shutil.copyfile(file,O/file.name)
plan=json.loads((P/'actual-source26-root84-FPGA-CCK-C1022-F-In2-r06/proposed-delta.json').read_text());plan['In2_trunk'][1]=[94.425,44.]
plan['new_local_knot_scope']=dict(before=[94.25,44.],after=[94.425,44.],reason='Preserve actual pre-existing IO3 narrow feature identified by unchanged r07',changed_native_signal_objects=changed,no_source_architecture_change=True)
(O/'proposed-delta.json').write_text(json.dumps(plan,indent=2)+'\n')
(O/'knot-correction-ledger.json').write_text(json.dumps(dict(before_board_sha256=core.sha(OLD),changed_native_objects=changed,only_two_new_CCK_segment_ends_changed=True,prior_failed_native_IO3_feature_report='CCK-IO3-lost-features-native-r05/review.json',native_IO3_CORE_and_full_returns_pending=True,adopted=False,manufacturing_ready=False),indent=2)+'\n')
with (O/'native-command.log').open('w')as log:r=subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--refill-zones','--save-board','--format','json','--severity-all','--all-track-errors','-o',str(O/'native.json'),str(dest)],stdout=log,stderr=subprocess.STDOUT)
print(json.dumps(dict(command_exit=r.returncode,board_sha256=core.sha(dest),adopted=False)))
