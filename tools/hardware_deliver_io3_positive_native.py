"""Actual post-damper IO3 source and source-domain-derived inner supply fill.

Native COPY only. A filled plane is connectivity evidence; current/thermal/
drop margins remain separate loaded engineering and physical qualifications.
"""
import argparse,json,collections,hashlib,shutil,subprocess,math
from pathlib import Path
import pcbnew
from hardware_route_current_delivery_native import Geometry,sha
from hardware_route_logic_return import identity,pad_identity,mm,xy
from hardware_map_motherboard_domains import native,classify,positioned
from hardware_zone_motherboard_returns import build_side_polygons,remaining_logic,duplicate,inflation,split_polygons
from hardware_build_assembly import parse,children,child,value
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
RECEIVERS=[f'U603{k}'for k in range(5,10)]+['U6040']+[f'U80{k:02}'for k in range(1,13)]+['U14031','U19001','U19002','U19003']
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True);frozen={str(p):sha(p)for p in [a.board,Path(__file__),Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'),Path('tools/hardware_map_motherboard_domains.py'),Path('tools/hardware_zone_motherboard_returns.py')]};b=pcbnew.LoadBoard(str(a.board));b.BuildConnectivity();old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};op={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};old_zones={z.m_Uuid.AsString()for z in b.Zones()};co=b.GetConnectivity();groups=[];seen=set()
 for p in b.GetPads():
  uid=p.m_Uuid.AsString()
  if uid in seen:continue
  group={uid}|{t.m_Uuid.AsString()for t in co.GetConnectedItems(p)if t.Type()==pcbnew.PCB_PAD_T};seen|=group
  if len(group)>1:groups.append((uid,group))
 fs={f.GetReference():f for f in b.GetFootprints()};ps={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()if p.GetNumber()};source=ps['R18001','2'];assert source.GetNetname()=='/IO_3V3';n=source.GetNetname();g=Geometry(b);new=[];zones=[]
 def track(points,w):
  assert g.clear(points,n,pcbnew.F_Cu,w),points
  for s,e in zip(points,points[1:]):
   t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(n));t.SetLayer(pcbnew.F_Cu);t.SetStart(xy(s));t.SetEnd(xy(e));t.SetWidth(pcbnew.FromMM(w));b.Add(t);g.add(t);new.append(dict(uuid=t.m_Uuid.AsString(),identity=identity(t),role='actual_R18001_output_current_source'))
 def zone(layer,poly,name,priority=1,min_thickness=.5):
  z=pcbnew.ZONE(b);z.SetNet(b.FindNet(n));z.SetLayer(layer);z.SetZoneName(name);z.SetLocalClearance(pcbnew.FromMM(.15));z.SetMinThickness(pcbnew.FromMM(min_thickness));z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL);z.SetAssignedPriority(priority);z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS);z.Outline().Append(poly);b.Add(z);zones.append(dict(uuid=z.m_Uuid.AsString(),layer=b.GetLayerName(layer),name=name,net=n));return z
 from hardware_zone_motherboard_returns import rectangle
 centre=(61.4,24.1);track([mm(source.GetPosition()),centre],.8)
 for dx in [-.8,0,.8]:
  for dy in [-.8,0,.8]:
   pt=(centre[0]+dx,centre[1]+dy);assert all(g.clear([pt,pt],n,l,.5)for l in [pcbnew.F_Cu,pcbnew.B_Cu]),pt;v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(n));v.SetPosition(xy(pt));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);g.add(v);new.append(dict(uuid=v.m_Uuid.AsString(),identity=identity(v),role='actual_IO3_nine_source_transition_vias'))
 for l in [pcbnew.F_Cu,pcbnew.B_Cu]:zone(l,rectangle([centre[0]-1.1,centre[1]-1.1,centre[0]+1.1,centre[1]+1.1]),'IO3_actual_source_array_'+b.GetLayerName(l),100,.2)
 model=json.loads(Path('hardware/motherboard/design.json').read_text());parts={r:c for r,c in model['components'].items()if c.get('physical',c.get('role')!='schematic_boundary_not_orderable')};nodes,nc,functions=native(Path('hardware/motherboard/netlist.xml'));domains,barriers,floating,coupling=classify(parts,nodes,nc);mapping=positioned(b,parts,nodes,nc,functions,domains,barriers);assert not mapping['errors'];(a.out/'actual-domain-map.json').write_text(json.dumps(mapping,indent=2)+'\n');exclusion=pcbnew.SHAPE_POLY_SET()
 for side in ['In1.Cu','In4.Cu']:
  regions,barrier,ungrounded=build_side_polygons(mapping,b,side);exclusion.Append(barrier);exclusion.Append(ungrounded)
  for region in regions.values():exclusion.Append(inflation(region,.25))
 exclusion.Simplify();positive=rectangle([.5,.5,459.5,339.5]);positive.BooleanSubtract(exclusion)
 # Preserve the old fine-pitch source-bearing IO3 fill. A one-millimetre
 # same-net overlap connects the extension without replacing its original
 # fine thermal/minimum-feature geometry across the dense BGA region.
 old_io3=next(z for z in b.Zones()if z.m_Uuid.AsString()=='2ad20bf7-6696-4e08-85d3-1f2d4c3caa40');assert old_io3.GetNetname()==n and old_io3.GetLayer()==pcbnew.In2_Cu;positive.BooleanSubtract(inflation(old_io3.Outline(),-1));positive.Simplify()
 for k,box in enumerate([[219,.5,459.5,101],[.5,99,221,339.5],[219,99,459.5,339.5]],1):
  section=duplicate(positive);section.BooleanIntersection(rectangle(box));section.Simplify()
  for j,piece in enumerate(split_polygons(section)):zone(pcbnew.In2_Cu,piece,'IO_3V3_ACTUAL_LOGIC_DOMAIN_DISTRIBUTION_'+str(k)+'_'+str(j),k,.25)
 # Literal four-millimetre inner copper crosses the same-net fill seam.
 # Zone overlap alone is not accepted as a physical source connection.
 seam=rectangle([58.6,97,62.6,103]);test=duplicate(seam);test.BooleanIntersection(exclusion);assert test.OutlineCount()==0,'Source seam crosses a foreign domain';t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(n));t.SetLayer(pcbnew.In2_Cu);t.SetStart(xy((60.6,97)));t.SetEnd(xy((60.6,103)));t.SetWidth(pcbnew.FromMM(4));b.Add(t);new.append(dict(uuid=t.m_Uuid.AsString(),identity=identity(t),role='actual_old_to_extended_IO3_sheet_current_bridge'))
 pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity()
 # Keep only extension polygons that have a real native path to the
 # post-damper source. Empty neighbouring pockets cannot supply anything.
 connected={t.m_Uuid.AsString()for t in b.GetConnectivity().GetConnectedItems(source)}
 omitted=[]
 for z in list(b.Zones()):
  uid=z.m_Uuid.AsString()
  if uid not in old_zones and uid not in connected:
   omitted.append(dict(uuid=uid,name=z.GetZoneName(),reason='No native connection to actual post-damper source; not credited as supply'));b.Remove(z)
 zones=[r for r in zones if r['uuid']not in{v['uuid']for v in omitted}]
 pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();dest=a.out/'io3-positive-delivery-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
 for ext in ['.kicad_pro','.kicad_dru']:shutil.copyfile(a.board.with_suffix(ext),dest.with_suffix(ext))
 for f in a.board.parent.iterdir():
  if f.name=='fp-lib-table':(a.out/f.name).write_text(f.read_text().replace('${KIPRJMOD}',a.board.parent.resolve().as_posix()))
  elif f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,a.out/f.name)
 q=pcbnew.LoadBoard(str(dest));q.BuildConnectivity();tracks={t.m_Uuid.AsString():identity(t)for t in q.GetTracks()};pads={p.m_Uuid.AsString():pad_identity(p)for p in q.GetPads()};assert op==pads and all(tracks[k]==v for k,v in old.items())and all(tracks[r['uuid']]==r['identity']for r in new);qp={p.m_Uuid.AsString():p for p in q.GetPads()};qc=q.GetConnectivity()
 for uid,group in groups:assert group<=({uid}|{t.m_Uuid.AsString()for t in qc.GetConnectedItems(qp[uid])if t.Type()==pcbnew.PCB_PAD_T}),('Prior actual cluster disconnected',uid)
 reachable={t.m_Uuid.AsString()for t in qc.GetConnectedItems(qp[source.m_Uuid.AsString()])};checks=[];pending=[]
 for ref in RECEIVERS:
  for pin in ['2','3']:
   p=ps[ref,pin];assert p.GetNetname()==n;row=dict(reference=ref,pin=pin,pad_uuid=p.m_Uuid.AsString(),point_mm=mm(p.GetPosition()),source_ref='R18001',source_pin='2',actual_positive_connected=p.m_Uuid.AsString()in reachable);checks.append(row)
   if not row['actual_positive_connected']:pending.append(row)
 allIO3=[p for p in q.GetPads()if p.GetNetname()==n];run=subprocess.run([CLI,'pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(a.out/'drc.json'),str(dest)],capture_output=True,text=True);assert run.returncode==0;d=json.loads((a.out/'drc.json').read_text());assert not d.get('ignored_checks');scope=dict(electrical_source_unchanged=True,reviewed_scope_reason='Actual post-damper IO3 source transition and inner positive distribution excluding both actual foreign-side domain projections/all isolation/substrate/raw/contact barriers; no parts, old copper or old zone definitions changed',reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=[r['uuid']for r in new],reviewed_added_zone_UUIDs=[r['uuid']for r in zones]);(a.out/'bounded-scope.json').write_text(json.dumps(scope,indent=2)+'\n');rho=1.724e-8*(1+.00393*(85-20));res=rho*(math.dist(mm(source.GetPosition()),centre)/1000)/(.0008*63e-6);result=dict(input_hashes=frozen,board_sha256=sha(dest),exact_added_copper=new,exact_added_positive_zones=zones,actual_receiver_endpoint_checks=checks,pending_receiver_supply=pending,actual_IO3_pads_connected=sum(p.m_Uuid.AsString()in reachable for p in allIO3),total_IO3_pad_pieces=len(allIO3),prior_actual_clusters_preserved=len(groups),all_old_pad_copper_identities_preserved=True,native_errors=[v for v in d['violations']if v['severity']=='error'],native_types=dict(collections.Counter(v['type']for v in d['violations'])),uncapped_joins=qc.GetUnconnectedCount(False),source_branch_screen=dict(current_a=2,width_mm=.8,length_mm=math.dist(mm(source.GetPosition()),centre),outer_finished_minimum_um_assumed=63,copper_temperature_c=85,resistance_ohm=res,drop_v=res*2),inner_finished_copper_minimum_um_screen=31.5,actual_distribution_drop_and_thermal_qualified=False,manufacturing_ready=False);assert all(sha(Path(p))==h for p,h in frozen.items());(a.out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['input_hashes','exact_added_copper','actual_receiver_endpoint_checks','native_errors','pending_receiver_supply']}));print('PENDING_RECEIVERS',pending)
if __name__=='__main__':main()

