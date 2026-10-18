from pathlib import Path
import sys,shutil,json
import pcbnew
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
from hardware_route_logic_return import xy
from hardware_populate_motherboard_pcb import sha
base=ROOT/'reports/motherboard-pcb-integration-20261001/isow-local-caps-merge-r28/motherboard-bounded-merged-candidate.kicad_pcb'
b0=pcbnew.LoadBoard(str(base));parts={f.GetReference():f for f in b0.GetFootprints()}
for kind in('top','bottom','missing_reference','wrong_owner'):
 folder=Path(__file__).parent/kind;folder.mkdir()
 b=pcbnew.BOARD();b.SetCopperLayerCount(6)
 nets={n:pcbnew.NETINFO_ITEM(b,n)for n in('/IO_3V3','/LOGIC_GND')}
 for n in nets.values():b.Add(n)
 for r,original,point in [('U1','U2006',(5,5)),('C1','C18001',(9,5))]:
  f=pcbnew.Cast_to_FOOTPRINT(parts[original].Duplicate(False));f.SetParent(b);f.SetReference(r);f.SetPosition(xy(point));f.SetOrientationDegrees(0)
  f.Reference().SetVisible(False);f.Value().SetVisible(False)
  if r=='C1'and kind=='bottom':f.Flip(f.GetPosition(),pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
  for p in f.Pads():
   name=('/IO_3V3'if p.GetNumber()=='1'else '/LOGIC_GND')if r=='C1'else '/IO_3V3'if p.GetNumber()=='5'else '/LOGIC_GND'if p.GetNumber()=='3'else 'unconnected-('+r+'-TEST-Pad'+p.GetNumber()+')'
   if name not in nets:nets[name]=pcbnew.NETINFO_ITEM(b,name);b.Add(nets[name])
   p.SetNet(nets[name])
  b.Add(f)
 anchor=pcbnew.PCB_VIA(b);anchor.SetNet(nets['/LOGIC_GND']);anchor.SetPosition(xy((14,9)));anchor.SetWidth(pcbnew.FromMM(.5));anchor.SetDrill(pcbnew.FromMM(.2));anchor.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);anchor.SetViaType(pcbnew.VIATYPE_THROUGH);anchor.SetIsFree(True);b.Add(anchor)
 anchor_track=pcbnew.PCB_TRACK(b);anchor_track.SetNet(nets['/LOGIC_GND']);anchor_track.SetLayer(pcbnew.F_Cu);anchor_track.SetStart(xy((5.95,5.95)));anchor_track.SetEnd(xy((14,9)));anchor_track.SetWidth(pcbnew.FromMM(.2));b.Add(anchor_track)
 for layer in([pcbnew.In1_Cu]if kind=='missing_reference'else[pcbnew.In1_Cu,pcbnew.In4_Cu]):
  z=pcbnew.ZONE(b);z.SetNet(nets['/LOGIC_GND']);z.SetLayer(layer);z.SetLocalClearance(pcbnew.FromMM(.20));z.SetMinThickness(pcbnew.FromMM(.20));z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL);z.Outline().NewOutline()
  for pt in[(.5,.5),(17.5,.5),(17.5,11.5),(.5,11.5)]:z.Outline().Append(pcbnew.FromMM(pt[0]),pcbnew.FromMM(pt[1]))
  b.Add(z)
 for a,c in[((0,0),(18,0)),((18,0),(18,12)),((18,12),(0,12)),((0,12),(0,0))]:
  edge=pcbnew.PCB_SHAPE(b);edge.SetShape(pcbnew.SHAPE_T_SEGMENT);edge.SetStart(xy(a));edge.SetEnd(xy(c));edge.SetLayer(pcbnew.Edge_Cuts);edge.SetWidth(pcbnew.FromMM(.05));b.Add(edge)
 board=folder/'fixture.kicad_pcb';pcbnew.SaveBoard(str(board),b)
 for suffix in('.kicad_pro','.kicad_dru'):shutil.copy2(base.with_suffix(suffix),board.with_suffix(suffix))
 for resource in base.parent.iterdir():
  if resource.is_dir()and(resource.suffix=='.pretty'or resource.name=='3dmodels'):shutil.copytree(resource,folder/resource.name)
  elif resource.name=='fp-lib-table':shutil.copy2(resource,folder/resource.name)
 owner=dict(source_physical_parts=2,source_capacitor_count=1,all_owner_mappings_verified=True,pending=[],errors=[],capacitors=[dict(ref='C1',owner='U1',category='distributed_IO3_reset_bypass',cap_power='1',cap_return='2',power_nodes=[dict(ref='U1',pin='2'if kind=='wrong_owner'else'5',net='IO_3V3')],return_nodes=[dict(ref='U1',pin='3',net='LOGIC_GND')])],scope='Native geometric test fixture only; no complete controller or physical hardware claim',manufacturing_ready=False)
 (folder/'owners.json').write_text(json.dumps(owner,indent=2)+'\n')
 print(kind,sha(board))
