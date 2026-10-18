"""Literal report-only F/In3 CCK trial; every receiving/reference check remains."""
from pathlib import Path
import sys,json,shutil,subprocess,copy
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path(__file__).parent)]
import pcbnew
import check_literal_CCK_CORE_preservation_r04 as c
import hardware_route_owned_bypass_loops_wip_r03 as w
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck
from hardware_route_logic_return import segment_distance,mm,identity
P=Path(__file__).parent;S=P/'CORE-literal-antipad-join-cck-r03/motherboard-CORE-literal-antipad-join-candidate.kicad_pcb';O=P/'actual-source26-root84-CCK-F-In3-trial-r11';O.mkdir(exist_ok=False)
b=pcbnew.LoadBoard(str(S));b.BuildConnectivity();cu={t.m_Uuid.AsString():t for t in b.GetTracks()};net='/fpga_core/FPGA_FLASH_CCK_SOURCE';changed=[]
for uid in ('0affcca0-07d2-4deb-86fa-5ed3dfa2ecc5','6228395d-eb7d-4824-8e2a-f5da3effc4c2','d83397af-9eef-4fd8-bf06-619b48edde98','0642c0e0-1811-44b3-90b7-50791f26142a'):
    t=cu[uid];old=identity(t);assert t.GetLayer()==pcbnew.In2_Cu and t.GetNetname()==net and t.GetWidth()==pcbnew.FromMM(.35);t.SetLayer(pcbnew.In3_Cu);changed.append(dict(uuid=uid,before=old,after=identity(t)))
row=json.loads((P/'source26-critical-digital-r02/prototype-route-geometry-review.json').read_text())['nets'][net];row=copy.deepcopy(row);row.update(reference_layers={'F.Cu':'In1.Cu','In3.Cu':'In4.Cu'})
checker=NativeCollectedAnnulusCheck(b,{net:row});g=w.Geometry(b);errors=[];checks=[]
for r in changed:
    t=cu[r['uuid']];start,end=mm(t.GetStart()),mm(t.GetEnd());seg=pcbnew.SEG(t.GetStart(),t.GetEnd());obstacles=[]
    for p,_ in g.pads.candidates(start,end,.75):
        if p.IsOnLayer(pcbnew.In3_Cu)and p.GetNetname()!=net and p.GetEffectiveShape(pcbnew.In3_Cu).Collide(seg,pcbnew.FromMM(.375-1e-6)):obstacles.append(dict(kind='native_foreign_pad',ref=p.GetParentFootprint().GetReference(),pin=p.GetNumber(),net=p.GetNetname()))
    for other,a,z,width in g.tracks[pcbnew.In3_Cu].candidates(start,end,.8):
        if other!=net and segment_distance(start,end,a,z)<.175+width/2+.20-1e-6:obstacles.append(dict(kind='native_foreign_Cu',net=other,start=a,end=z))
    try:proof=checker.segment(t,row);ref_error=None
    except Exception as ex:proof=None;ref_error=str(ex)
    checks.append(dict(uuid=r['uuid'],reference_proof=proof,reference_error=ref_error,physical_obstacles=obstacles))
    if obstacles or ref_error:errors.append(dict(uuid=r['uuid'],reference_error=ref_error,physical_obstacles=obstacles))
pre=dict(passed=not errors,literal_layer_declaration=row['reference_layers'],input_board_sha256=c.sha(S),exact4_changed_new_signal_layers=changed,preflight_only=True,not_Source_piece_qualification=True,actual_layer_checks=checks,errors=errors,source_sha256=c.sha(c.SOURCE),frozen_F_B_manifest_unchanged=True,CORE_and_IO3_native_capacity_proofs_still_required=True,manufacturing_ready=False)
(O/'preflight.json').write_text(json.dumps(pre,indent=2)+'\n');print(json.dumps(dict(preflight_passed=pre['passed'],errors=errors)),flush=True)
if errors:raise SystemExit('Actual native-collision/reference preflight rejects In3 trial; no candidate emitted')
dest=O/'motherboard-CCK-F-In3-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(S.with_suffix(suffix),dest.with_suffix(suffix))
for file in S.parent.iterdir():
    if file.is_dir()and file.suffix=='.pretty':shutil.copytree(file,O/file.name)
    elif file.name=='fp-lib-table':shutil.copyfile(file,O/file.name)
(O/'proposed-delta.json').write_bytes((P/'actual-source26-root84-FPGA-CCK-C1022-F-In2-r06/proposed-delta.json').read_bytes())
with(O/'native-command.log').open('w')as log:r=subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--refill-zones','--save-board','--format','json','--severity-all','--all-track-errors','-o',str(O/'native.json'),str(dest)],stdout=log,stderr=subprocess.STDOUT)
print(json.dumps(dict(native_command=r.returncode,board_sha256=c.sha(dest),adopted=False)))
