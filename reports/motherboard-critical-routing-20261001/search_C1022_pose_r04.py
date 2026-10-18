"""Finite actual one-cap pose search, native land/Cu/courtyard and owner constraints."""
from pathlib import Path
import sys,json,math,time
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_owned_bypass_loops_wip_r03 as w
from hardware_route_logic_return import xy,mm,segment_distance
from hardware_populate_motherboard_pcb import write,sha
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-FPGA-flash-MISO-r84/motherboard-bounded-merged-candidate.kicad_pcb')
OUT=Path(sys.argv[1]);OUT.mkdir(parents=True,exist_ok=False)
b=pcbnew.LoadBoard(str(BASE));b.BuildConnectivity();parts={f.GetReference():f for f in b.GetFootprints()};cap=parts['C1022'];original=(mm(cap.GetPosition()),cap.GetOrientationDegrees());owner=next(p for p in parts['U1001'].Pads()if p.GetNumber()=='L6')
for f in b.GetFootprints():f.BuildCourtyardCaches()
nearby=[f for f in b.GetFootprints()if f.GetReference()!='C1022' and math.dist(mm(f.GetPosition()),(98,46))<10]
padlist=[p for f in nearby for p in f.Pads()if p.IsOnLayer(pcbnew.B_Cu)]
cu=[t for t in b.GetTracks()if(t.Type()==pcbnew.PCB_VIA_T or t.GetLayer()==pcbnew.B_Cu)and min(math.dist(mm(t.GetPosition()if t.Type()==pcbnew.PCB_VIA_T else t.GetStart()),(98,46)),math.dist(mm(t.GetPosition()if t.Type()==pcbnew.PCB_VIA_T else t.GetEnd()),(98,46)))<10]
results=[];tested=0;reasons={};t0=time.monotonic()
for angle in (0,90,180,270):
 cap.SetOrientationDegrees(angle)
 for ix in range(92*4,104*4+1):
  for iy in range(40*4,52*4+1):
   centre=(ix/4,iy/4);cap.SetPosition(xy(centre));tested+=1;pads={p.GetNumber():p for p in cap.Pads()};power=pads['1'];distance=math.dist(mm(power.GetPosition()),mm(owner.GetPosition()))
   # Bound conservative physical shortest-pad gap by 2mm engineering owner target.
   if distance>3.0:continue
   cap.BuildCourtyardCaches();cy=cap.GetCourtyard(pcbnew.B_CrtYd);bad=False
   for other in nearby:
    ocy=other.GetCourtyard(pcbnew.B_CrtYd)
    if not ocy.OutlineCount():continue
    if cy.Collide(ocy):bad=True;reasons['courtyard']=reasons.get('courtyard',0)+1;break
   if bad:continue
   for p in pads.values():
    shape=p.GetEffectiveShape(pcbnew.B_Cu)
    for q in padlist:
     if q.GetNetname()!=p.GetNetname() and shape.Collide(q.GetEffectiveShape(pcbnew.B_Cu),pcbnew.FromMM(.20-1e-6)):
      bad=True;break
    if bad:reasons['foreign_pad']=reasons.get('foreign_pad',0)+1;break
    for t in cu:
     if t.GetNetname()==p.GetNetname():continue
     other=pcbnew.SHAPE_CIRCLE(t.GetPosition(),t.GetWidth(pcbnew.B_Cu)//2)if t.Type()==pcbnew.PCB_VIA_T else pcbnew.SEG(t.GetStart(),t.GetEnd())
     margin=pcbnew.FromMM(.20-1e-6)+(0 if t.Type()==pcbnew.PCB_VIA_T else t.GetWidth()//2)
     if shape.Collide(other,margin):bad=True;break
    if bad:reasons['foreign_Cu']=reasons.get('foreign_Cu',0)+1;break
   if bad:continue
   # The required CCK and Source-ground through-via sites must both be clear of moved lands.
   for at,net in [((95.2,46.4),'/fpga_core/FPGA_FLASH_CCK_SOURCE'),((94.4,46.4),'/LOGIC_GND')]:
    shape=pcbnew.SHAPE_CIRCLE(xy(at),pcbnew.FromMM(.25))
    if any(p.GetNetname()!=net and p.GetEffectiveShape(pcbnew.B_Cu).Collide(shape,pcbnew.FromMM(.20-1e-6))for p in pads.values()):bad=True;break
   if bad:reasons['required_signal_via']=reasons.get('required_signal_via',0)+1;continue
   results.append(dict(centre=centre,angle=angle,power_pad_xy=mm(pads['1'].GetPosition()),ground_pad_xy=mm(pads['2'].GetPosition()),owner_pin_xy=mm(owner.GetPosition()),owner_pin_centre_distance_mm=distance,move_mm=math.dist(centre,original[0])))
results.sort(key=lambda r:(r['owner_pin_centre_distance_mm'],r['move_mm']))
write(OUT/'review.json',dict(base_sha256=sha(BASE),tested=tested,actual_clear_pose_candidates=results,fail_reasons=reasons,seconds=time.monotonic()-t0,owner_limit_is_engineering_not_manufacturer=True,no_source_or_board_file_changed=True,local_HF_loop_and_return_power_proofs_pending=True,manufacturing_ready=False))
print(json.dumps(dict(tested=tested,seconds=time.monotonic()-t0,candidate_count=len(results),first20=results[:20])))
