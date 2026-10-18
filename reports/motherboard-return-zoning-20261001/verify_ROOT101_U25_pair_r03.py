"""Read-only exact U25 barrel/Source/control/current-C80 receiving proof."""
from pathlib import Path
import sys,json,math,subprocess,argparse
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path.cwd()/'reports/motherboard-return-zoning-20261001')]
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import xy,mm
from hardware_check_return_corridors import circle,covered
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck
from hardware_route_owned_bypass_loops_r02 import actual_receiving_return_anchors
from check_exact_endpoint_antipad_union_r01 import ExactEndpointUnionCheck
p=argparse.ArgumentParser();p.add_argument('--board',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();B=a.board;O=a.out;assert not O.exists();O.mkdir()
G=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-two-local-barrel-correction-r03/generation.json');M=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-U25-C19033-merged-trial-r101/current106-bypass-manifest.json');OWN=Path('reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json')
inputs={str(q):sha(q)for q in[B,G,M,OWN,Path(__file__)]}
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();co=b.GetConnectivity();cu={t.m_Uuid.AsString():t for t in b.GetTracks()};pads={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()if p.GetNumber()}
PV=cu['0901cf4a-0f1c-4f5a-8c92-68ccf5d1bfe3'];GV=cu['9557a691-472b-4af0-87c3-b0e91cf52409'];assert PV.Type()==GV.Type()==pcbnew.PCB_VIA_T;assert mm(PV.GetPosition())==(332.5,192.65)and mm(GV.GetPosition())==(333.4,192.8)
def joined(p,q):return q.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in co.GetConnectedItems(p)}
pairs=[]
for aa,bb in[(('U11025','5'),('C11080','1')),(('U11025','2'),('C11080','2')),(('U11025','2'),('U11026','2'))]:
 u,v=pads[aa],pads[bb];pairs.append(dict(start=list(aa),end=list(bb),literal_net=u.GetNetname(),passed=u.GetNetname()==v.GetNetname()and joined(u,v)))
ret=GV.GetNetname();assert ret==pads['U11025','2'].GetNetname()==pads['C11080','2'].GetNetname();assert joined(GV,pads['U11025','2'])and joined(GV,pads['C11080','2']);assert joined(PV,pads['U11025','5'])and joined(PV,pads['C11080','1']);assert all(r['passed']for r in pairs)
drill_rows=[]
for v in(PV,GV):
 x,y=mm(v.GetPosition());radius=pcbnew.ToMM(v.GetDrillValue())/2;rows=[]
 for q in b.GetPads():
  if q.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD or not q.IsOnCopperLayer():continue
  z=q.GetBoundingBox();x0,y0,x1,y1=[pcbnew.ToMM(w)for w in(z.GetX(),z.GetY(),z.GetRight(),z.GetBottom())];gap=math.hypot(max(x0-x,0,x-x1),max(y0-y,0,y-y1))-radius
  if gap<1.:rows.append(dict(reference=q.GetParentFootprint().GetReference(),pin=q.GetNumber(),drill_to_conservative_fitted_land_mm=gap))
 rows.sort(key=lambda r:r['drill_to_conservative_fitted_land_mm']);assert rows and rows[0]['drill_to_conservative_fitted_land_mm']>.15
 drill_rows.append(dict(uuid=v.m_Uuid.AsString(),position_mm=mm(v.GetPosition()),nearest=rows[:8],no_drill_intersects_fitted_SMD=True,minimum_registration_clearance_screen_mm=.15))
checker=NativeCollectedAnnulusCheck(b,{})
annuli=[]
for layer in(pcbnew.In1_Cu,pcbnew.In4_Cu):
 assert GV.FlashLayer(layer)and co.IsConnectedOnLayer(GV,layer);assert covered(circle(tuple(GV.GetPosition()),pcbnew.FromMM(.24)),checker.reference(ret,layer))
 annuli.append(dict(layer=b.GetLayerName(layer),flashed=True,native_connected=True,full_024mm_filled_circle=True,actual_numbered_Source_pin='U11025.2',actual_cap_return='C11080.2'))
manifest=json.loads(M.read_text());generation=json.loads(G.read_text());group=next(g for g in manifest['owned_loops']if g['ref']=='C11080');assert all(u in cu for u in group['new_UUIDs']);group['new_UUIDs']=list(dict.fromkeys(group['new_UUIDs']+generation['exact_added_Cu_UUIDs']));group['exact_modified_Cu_UUIDs']=generation['exact_modified_Cu_UUIDs'];group['explicit_rebind_reason']='Actual old C80 Ground drill inside its fitted SMD land removed; exact same two barrel UUIDs moved off-land and Source VCC leaf changed into three axis-aligned F segments.';manifest.update(board_sha256=sha(B),bounded_current106_C80_rebind=True)
write(O/'current106-C80-rebound-manifest.json',manifest)
focused=dict(manifest,owned_loops=[group]);write(O/'focused-C80-rebound-manifest.json',focused)
cmd=[sys.executable,'tools/hardware_verify_owned_bypass_batch.py','--board',str(B),'--owners',str(OWN),'--receipt',str(O/'focused-C80-rebound-manifest.json'),'--out',str(O/'actual-C80-strict-loop-proof.json')]
r=subprocess.run(cmd,capture_output=True,text=True);(O/'actual-C80-command.txt').write_text(r.stdout+r.stderr);assert r.returncode==0,'Focused actual C80 .10 strict receiving loop failed'
decl=dict(return_net=ret,reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.,reference_corridor_margin_mm=.4);private={pads['U11026',n].GetNetname()for n in('1','3')};check=ExactEndpointUnionCheck(b,{n:decl for n in private});controls=[]
for t in cu.values():
 if t.GetNetname()not in private:continue
 try:
  result=check.via(t,decl)if t.Type()==pcbnew.PCB_VIA_T else check.segment(t,decl);controls.append(dict(uuid=t.m_Uuid.AsString(),passed=True,review=result))
 except ValueError as e:controls.append(dict(uuid=t.m_Uuid.AsString(),passed=False,error=str(e)))
write(O/'actual-U26-Source-controls-proof.json',dict(passed=all(r['passed']for r in controls),board_sha256=sha(B),unchanged_margin_mm=.4,rows=controls));assert all(r['passed']for r in controls),'U26 actual Source/control .40 remains obstructed'
assert all(sha(q)==h for q,h in inputs.items());write(O/'receipt.json',dict(passed=True,board_sha256=sha(B),input_sha256=inputs,actual_pairs=pairs,drilled_land_review=drill_rows,actual_Source_Ground_reference_annuli=annuli,actual_U26_controls_checked=len(controls),positive_return_pair_distance_mm=math.dist(mm(PV.GetPosition()),mm(GV.GetPosition())),global_power_and_remaining_U20_controls_pending=True,Source26_unchanged=True,Source27_adopted=False,manufacturing_ready=False));print(json.dumps(dict(passed=True,C80_strict=True,U26_controls=len(controls),board_sha256=sha(B))),flush=True)
