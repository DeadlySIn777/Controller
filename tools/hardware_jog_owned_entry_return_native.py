"""Bounded copied 4 mm entry-return correction for actual CMOS ground barrels."""
import argparse,json,math,shutil,subprocess,collections
from pathlib import Path
import pcbnew
from hardware_route_current_delivery_native import Geometry,sha
from hardware_route_logic_return import identity,pad_identity,mm,xy
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
NET='/motherboard_motors/FIELD_GND'
START=(411.08,138.0);END=(360.08,154.0)
PREFIXES=['a9289433','84b293a9','400a60a3']
VIA_POINTS=[(398.245074,138.401818),(376.825,145.0),(367.275,141.5),(365.862962,149.690043)]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True)
 inputs={str(p):sha(p)for p in [a.board,Path(__file__)]};b=pcbnew.LoadBoard(str(a.board));b.BuildConnectivity();old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};pads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};cu={t.m_Uuid.AsString():t for t in b.GetTracks()};retired={}
 for prefix in PREFIXES:
  found=[(uid,t)for uid,t in cu.items()if uid.startswith(prefix)];assert len(found)==1,prefix;uid,t=found[0];assert t.GetNetname()==NET and t.GetLayer()==pcbnew.B_Cu and t.GetWidth()==pcbnew.FromMM(4);retired[uid]=identity(t);b.Remove(t)
 # Temporary obstacle-only copies of the independent contract repair's
 # future barrels. Their actual source/branch mutation is owned elsewhere.
 temporary=[]
 for pt in VIA_POINTS:
  v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet('/LOGIC_GND'));v.SetPosition(xy(pt));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);temporary.append(v)
 g=Geometry(b);proposal=[START,(403.08,138.0),(400.8,140.2),(400.8,143.8),(396.08,142.0)]
 assert g.clear(proposal,NET,pcbnew.B_Cu,4),'First actual 4 mm detour is obstructed'
 assert proposal is not None,'No actual 4 mm outer path with source barrel clearance'
 for v in temporary:b.Remove(v)
 added=[]
 for s,e in zip(proposal,proposal[1:]):
  t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(NET));t.SetLayer(pcbnew.B_Cu);t.SetWidth(pcbnew.FromMM(4));t.SetStart(xy(s));t.SetEnd(xy(e));b.Add(t);added.append(dict(uuid=t.m_Uuid.AsString(),identity=identity(t)))
 # Four-millimetre envelope with a clearance slot around the live CMOS
 # barrel; the two parallel ligaments are explicitly current-screened.
 from hardware_zone_motherboard_returns import rectangle,polygon
 env=rectangle([367.08,143.0,380.08,147.0]);cx,cy=VIA_POINTS[1];radius=.86
 hole=polygon([(cx+radius*math.cos(k*2*math.pi/64),cy+radius*math.sin(k*2*math.pi/64))for k in range(64)]);env.BooleanSubtract(hole);z=pcbnew.ZONE(b);z.SetNet(b.FindNet(NET));z.SetLayer(pcbnew.B_Cu);z.SetAssignedPriority(110);z.SetZoneName('FA_RETURN_ACTUAL_CMOS_BARREL_SLOT');z.SetLocalClearance(pcbnew.FromMM(.6));z.SetMinThickness(pcbnew.FromMM(.15));z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL);z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS);z.Outline().Append(env);b.Add(z);zoneid=z.m_Uuid.AsString()
 b.BuildConnectivity();pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();dest=a.out/'entry-return-jog-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
 for ext in ['.kicad_pro','.kicad_dru']:shutil.copyfile(a.board.with_suffix(ext),dest.with_suffix(ext))
 q=pcbnew.LoadBoard(str(dest));q.BuildConnectivity();new={t.m_Uuid.AsString():identity(t)for t in q.GetTracks()};assert {p.m_Uuid.AsString():pad_identity(p)for p in q.GetPads()}==pads;assert set(old)-set(new)==set(retired);assert all(new[k]==v for k,v in old.items()if k not in retired)
 ps={p.m_Uuid.AsString():p for p in q.GetPads()};co=q.GetConnectivity();checks=[]
 for pth in ['entry-delivery-r05','entry-returns-r06','entry-FAraw-r08']:
  r=json.loads(Path('reports/motherboard-power-entry-20261001',pth,'receipt.json').read_text())
  for v in r['routes']:
   if v.get('already_connected_before'):continue
   p,t=ps[v['from_pad_uuid']],ps[v['to_pad_uuid']];assert t.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in co.GetConnectedItems(p)},v['name'];checks.append(dict(name=v['name'],source=v['from_pad_uuid'],target=v['to_pad_uuid'],actual_connected=True))
 assert len(checks)==9
 subprocess.run([CLI,'pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(a.out/'drc.json'),str(dest)],check=True,capture_output=True,text=True);d=json.loads((a.out/'drc.json').read_text());assert not d.get('ignored_checks');newids={x['uuid']for x in added};newissues=[v for v in d['violations']if v['severity']=='error'and any(t['uuid']in newids|{zoneid}for t in v['items'])];assert not newissues,newissues
 filled=next(v for v in q.Zones()if v.m_Uuid.AsString()==zoneid).GetFilledPolysList(pcbnew.B_Cu);profiles=[]
 for i in range(35):
  x=cx+(i-17)*.05;segments=[];start=None
  for j in range(2001):
   y=143+j*.002;active=filled.Contains(xy((x,y)))
   if active and start is None:start=y
   if not active and start is not None:segments.append((start,y-.002));start=None
  if start is not None:segments.append((start,147))
  widths=[v[1]-v[0]for v in segments];amps=[.048*10**.44*((w/25.4*1000)*(63/25.4))**.725 for w in widths];profiles.append(dict(x_mm=x,actual_parallel_ligaments_y_mm=segments,widths_mm=widths,total_mm=sum(widths),conditional_parallel_sum_a=sum(amps)))
 minwidth=min(v['total_mm']for v in profiles);assert minwidth>0
 oldlen=sum(math.dist((v[2][0]/1e6,v[2][1]/1e6),(v[3][0]/1e6,v[3][1]/1e6))for v in retired.values());length=sum(math.dist(s,e)for s,e in zip(proposal,proposal[1:]))+13;rho=1.724e-8*(1+.00393*65);extra=rho*((length-oldlen)/1000)/(.004*63e-6)+rho*.002/(minwidth/1000*63e-6)-rho*.002/(.004*63e-6)
 scope=dict(electrical_source_unchanged=True,reviewed_scope_reason='Only three formerly new FIELD_GND B entry-return segments replaced: C6032 uses a full 4 mm detour; C17013 uses a 4 mm envelope with explicit .85 mm barrel-clearance slot and two parallel return ligaments; all parts/pads/unrelated copper/old zone definitions unchanged',reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(set(retired)|newids),reviewed_added_zone_UUIDs=[zoneid])
 (a.out/'bounded-scope.json').write_text(json.dumps(scope,indent=2)+'\n');result=dict(input_hashes=inputs,board_sha256=sha(dest),exact_retired_copper=retired,exact_added_copper=added,exact_new_zone_uuid=zoneid,path_mm=proposal,actual_nine_entry_endpoint_checks=checks,future_barrel_obstacles_mm=VIA_POINTS,native_new_route_errors=newissues,native_types=dict(collections.Counter(v['type']for v in d['violations'])),old_section_length_mm=oldlen,new_section_length_mm=length,C6032_full_width_mm=4,C17013_envelope_width_mm=4,C17013_barrel_clearance_minimum_mm=radius*math.cos(math.pi/64)-.25,C17013_zone_foreign_copper_clearance_mm=.6,C17013_actual_slot_profiles=profiles,C17013_minimum_actual_total_ligament_width_mm=minwidth,C17013_legacy_parallel_sum_min_screen_a=min(v['conditional_parallel_sum_a']for v in profiles),extra_return_resistance_screen_ohm=extra,extra_6a_loss_screen_v=extra*6,current_screen_note='63um/85C assumption; two-ligament legacy IPC2221 sum excludes mutual heating/crowding. Short 2mm bottleneck resistance uses actual minimum total cross-section as an upper DC screen; current sharing/hot copper/thermal still require physical qualification. No 6A measured delivery claim.',all_unrelated_physical_copper_preserved=True,delivery_qualified=False)
 assert all(sha(Path(p))==h for p,h in inputs.items());(a.out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
