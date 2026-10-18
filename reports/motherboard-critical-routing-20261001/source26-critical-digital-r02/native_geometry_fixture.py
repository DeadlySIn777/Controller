"""Persist real 0.35 mm prototype route and exact annulus/union negatives.

Bare-pad fixtures only; cannot substitute this result for motherboard routing.
"""
from pathlib import Path
import json,sys,hashlib,shutil
import pcbnew
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent/'native-geometry-controls-r03'
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tests')]
import hardware_check_return_corridors_r03 as fast
from test_motherboard_return_corridors import fixture
CLI=ROOT/'tools/hardware_route_selected_additive_r02.py'
import hardware_route_selected_additive_r02 as prior
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run():
 OUT.mkdir(exist_ok=False);results=[]
 for case in ['healthy','wrong_domain','missing_reference_annulus']:
  d=OUT/case;d.mkdir();b,added,rows,drc=fixture(d,'wrong_domain'if case=='wrong_domain'else'healthy')
  # The original small fixture's source is only 1 mm from its board edge.
  # A .575 mm projected half-corridor legitimately exceeds that native .5 mm
  # edge fill boundary. Move only our new bare test source pads inward, rather
  # than relaxing the real return guard or mistaking this for a valid escape.
  for fp in b.GetFootprints():
   if fp.GetReference()in ['J1','J2']:
    fp.Move(pcbnew.VECTOR2I(pcbnew.FromMM(.5 if fp.GetReference()=='J1'else-.5),0))
  for t in b.GetTracks():
   if t.GetNetname()=='/DATA'and not isinstance(t,pcbnew.PCB_VIA):
    t.SetWidth(pcbnew.FromMM(.35))
    for side in ['Start','End']:
     p=getattr(t,'Get'+side)()
     if p.x in [pcbnew.FromMM(1),pcbnew.FromMM(9)]:
      p.x+=pcbnew.FromMM(.5 if p.x==pcbnew.FromMM(1)else-.5);getattr(t,'Set'+side)(p)
  rows['/DATA'].update(type='critical_digital',width_mm=.35,clearance_mm=.20,reference_corridor_margin_mm=.40)
  path=d/'prototype-route.kicad_pcb';pcbnew.SaveBoard(str(path),b)
  for suffix in ['.kicad_pro','.kicad_dru']:shutil.copy2((d/'native.kicad_pcb').with_suffix(suffix),path.with_suffix(suffix))
  try:drc=prior.native_drc(path,d,'prototype-drc',refill=True)
  except ValueError:
   if case=='healthy':raise
   actual=prior.read(d/'prototype-drc.json')
   assert not actual.get('ignored_checks')
   drc=dict(rejected=True,actual_native_violations=actual['violations'],ignored_checks=[])
  b=pcbnew.LoadBoard(str(path));b.BuildConnectivity()
  if case=='missing_reference_annulus':
   for z in b.Zones():
    if z.IsOnLayer(pcbnew.In4_Cu):z.UnFill()
   pcbnew.SaveBoard(str(path),b);b=pcbnew.LoadBoard(str(path));b.BuildConnectivity()
  try:
   proof=fast.return_corridor_check(b,added,rows)
   if case!='healthy':raise AssertionError('Negative native fixture escaped:'+case)
   old=fast.strict.ActualAnnulusReturnCheck(b,rows);new=fast.NativeCollectedAnnulusCheck(b,rows);equiv=[]
   for layer in [pcbnew.In1_Cu,pcbnew.In4_Cu]:
    a=old.reference('/LOGIC_GND',layer);c=new.reference('/LOGIC_GND',layer)
    assert a.Area()==c.Area()and a.OutlineCount()==c.OutlineCount()
    assert [[tuple(v)for v in a.COutline(i).CPoints()]for i in range(a.OutlineCount())]==[[tuple(v)for v in c.COutline(i).CPoints()]for i in range(c.OutlineCount())]
    equiv.append(dict(layer=b.GetLayerName(layer),native_area=a.Area(),all_native_outline_vertices_identical=True))
   result=dict(case=case,passed=True,regular_native_drc=drc,return_corridor=proof,union_equivalence=equiv)
  except ValueError as error:
   if case=='healthy':raise
   result=dict(case=case,rejected=True,reason=str(error),regular_native_drc_before_resource_removal=drc)
  result.update(board_sha256=sha(path),actual_signal_width_mm=.35,reference_corridor_margin_mm=.40,
   production_motherboard=False,source_pad_inventory=[dict(reference=p.GetParentFootprint().GetReference(),pin=p.GetNumber(),net=p.GetNetname())for p in b.GetPads()])
  (d/'review.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result)
 report=dict(passed=True,native_cases=results,all_cases=3,production_motherboard=False,
  frozen_dependency_checks=fast.dependencies(),manufacturing_ready=False,
  input_sha256={str(p):sha(p)for p in [Path(__file__),Path(fast.__file__),Path(fast.collector.__file__),Path(fast.strict.__file__),ROOT/'tests/test_motherboard_return_corridors.py']})
 (OUT/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,native_cases=3)))
if __name__=='__main__':run()
