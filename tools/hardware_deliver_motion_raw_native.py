"""Actual receiving-array/inner-sheet feed for the two motor load switches.

The sheet feeds the present 1.3464 A motor receiving load. It does not grant
the source's complete 6 A rating to every branch or qualify fault thermals.
"""
import argparse,json,shutil,subprocess,collections,math
from pathlib import Path
import pcbnew
from hardware_route_current_delivery_native import Geometry,sha
from hardware_route_logic_return import identity,pad_identity,mm,xy
from hardware_zone_motherboard_returns import rectangle,polygon,duplicate,inflation,build_side_polygons,split_polygons
from hardware_map_motherboard_domains import native,classify,positioned
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True);inputs={str(p):sha(p)for p in [a.board,Path(__file__),Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml')]};b=pcbnew.LoadBoard(str(a.board));b.BuildConnectivity();old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};op={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};oldzones={z.m_Uuid.AsString()for z in b.Zones()};ps={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()if p.GetNumber()};source=ps['C11046','1'];net=source.GetNetname();assert net=='/motherboard_power_entry/MOTION_5V_RAW'
 cf=next(f for f in b.GetFootprints()if f.GetReference()=='C11069');old_cap_pose=dict(point=mm(cf.GetPosition()),angle=cf.GetOrientationDegrees(),pads={p.m_Uuid.AsString():op[p.m_Uuid.AsString()]for p in cf.Pads()});co=b.GetConnectivity()
 for p in cf.Pads():assert not[t for t in co.GetConnectedItems(p)if t.Type()==pcbnew.PCB_PAD_T and t.m_Uuid.AsString()!=p.m_Uuid.AsString()],'Previously connected field bypass requires separate bounded copper transaction'
 cf.SetOrientationDegrees(0);cf.SetPosition(xy((345.75,181.75)));g=Geometry(b);added=[];zs=[]
 of=next(f for f in b.GetFootprints()if f.GetReference()=='C11070');old_output_pose=dict(point=mm(of.GetPosition()),angle=of.GetOrientationDegrees(),pads={p.m_Uuid.AsString():op[p.m_Uuid.AsString()]for p in of.Pads()})
 for p in of.Pads():assert not[t for t in co.GetConnectedItems(p)if t.Type()==pcbnew.PCB_PAD_T and t.m_Uuid.AsString()!=p.m_Uuid.AsString()]
 ox,oy=mm(of.GetPosition());of.SetPosition(xy((ox,oy)));g=Geometry(b)
 df=next(f for f in b.GetFootprints()if f.GetReference()=='C11068');old_dvdt_pose=dict(point=mm(df.GetPosition()),angle=df.GetOrientationDegrees(),pads={p.m_Uuid.AsString():op[p.m_Uuid.AsString()]for p in df.Pads()})
 for p in df.Pads():assert not[t for t in co.GetConnectedItems(p)if t.Type()==pcbnew.PCB_PAD_T and t.m_Uuid.AsString()!=p.m_Uuid.AsString()]
 dx,dy=mm(df.GetPosition());df.SetPosition(xy((dx,dy)))
 retired_ids={'91e988f3-254c-49f8-b874-a72258fc6b06','af80479f-1536-477e-8348-13a5fc6237ff'};retired=[t for t in list(b.GetTracks())if t.m_Uuid.AsString()in retired_ids];assert len(retired)==2
 for t in retired:assert t.GetNetname()=='/motherboard_power_entry/FIELD_HEALTH_B_LED_MID';b.Remove(t)
 g=Geometry(b)
 def track(s,e,n,w,layer):
  assert g.clear([s,e],n,layer,w),(s,e,n,w);t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(n));t.SetLayer(layer);t.SetWidth(pcbnew.FromMM(w));t.SetStart(xy(s));t.SetEnd(xy(e));b.Add(t);g.add(t);added.append(dict(uuid=t.m_Uuid.AsString(),identity=identity(t)))
 def via(pt,n):
  assert all(g.clear([pt,pt],n,l,.5)for l in [pcbnew.F_Cu,pcbnew.B_Cu]),(pt,n);v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(n));v.SetPosition(xy(pt));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);g.add(v);added.append(dict(uuid=v.m_Uuid.AsString(),identity=identity(v)));return v
 def zone(layer,shape,name,priority=120,minimum=.2,n=net):
  assert shape.OutlineCount()==1;z=pcbnew.ZONE(b);z.SetLayer(layer);z.SetNet(b.FindNet(n));z.SetZoneName(name);z.SetAssignedPriority(priority);z.SetLocalClearance(pcbnew.FromMM(.15));z.SetMinThickness(pcbnew.FromMM(minimum));z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL);z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS);z.Outline().Append(shape);b.Add(z);zs.append(dict(uuid=z.m_Uuid.AsString(),net=n,layer=b.GetLayerName(layer),name=name));return z
 # These three B capacitors form U11015's actual own-field cell. Full-land
 # placement is qualified by native DRC; no nearest-rail substitute is used.
 from hardware_route_local_signals import paths
 mid='/motherboard_power_entry/FIELD_HEALTH_B_LED_MID';via((350.45,181.635),mid);track((350.85,181.635),(350.45,181.635),mid,.2,pcbnew.F_Cu);track((350.45,181.635),(349.85,181.635),mid,.2,pcbnew.B_Cu)
 field_checks=[]
 def own_loop(ref,pin,targetref,targetpin,width):
  cap=ps[ref,str(pin)];owner=ps[targetref,str(targetpin)];n=cap.GetNetname();assert n==owner.GetNetname();s=mm(cap.GetPosition());e=mm(owner.GetPosition());winner=None
  preferred={('C11069','1'):[(345.25,181.25)],('C11069','2'):[(347.225,183.9)],('C11070','1'):[(350.4,178.4)],('C11068','1'):[(350.15,183)]}
  candidates=preferred.get((ref,str(pin)),[])+[(e[0]+dx,e[1]+dy)for dx,dy in [(1.6,.4),(1.8,.4),(2.0,.4),(2.2,.4),(2,0),(.8,.4),(.9,.4),(1.1,.4),( .8,.5),(.8,0),(.8,-.5),(1,0),(-.8,0),(-.8,.5),(-.8,-.5)]]+[(s[0]+dx,s[1]+dy)for dx,dy in [(0,0),(-.7,0),(.7,0),(0,-.7),(0,.7),(-1.1,0),(1.1,0),(0,-1.1),(0,1.1)]]
  for pt in candidates:
   if not all(g.clear([pt,pt],n,l,.5)for l in [pcbnew.F_Cu,pcbnew.B_Cu]):continue
   bp=next((pp for pp in paths(s,pt)if g.clear(pp,n,pcbnew.B_Cu,width)),None);fp=next((pp for pp in paths(e,pt)if g.clear(pp,n,pcbnew.F_Cu,width)),None)
   if bp and fp:winner=(pt,bp,fp);break
  if winner is None:
   for pt in candidates:
    if not all(g.clear([pt,pt],n,l,.5)for l in [pcbnew.F_Cu,pcbnew.B_Cu]):continue
    bp=next((pp for pp in paths(s,pt)if g.clear(pp,n,pcbnew.B_Cu,width)),None)
    if not bp:continue
    fp=g.grid(e,pt,n,pcbnew.F_Cu,width,step=.2,padding=4,max_nodes=3500)
    if fp:winner=(pt,bp,fp);break
  if winner is None:pcbnew.SaveBoard(str(a.out/'rejected-field-debug.kicad_pcb'),b)
  assert winner is not None,(ref,pin,targetref,targetpin)
  pt,bp,fp=winner
  for pp,l in [(bp,pcbnew.B_Cu),(fp,pcbnew.F_Cu)]:
   for x,y in zip(pp,pp[1:]):
    if math.dist(x,y)>1e-7:track(x,y,n,width,l)
  v=via(pt,n);field_checks.append(dict(capacitor=ref,pin=str(pin),owner=targetref,owner_pin=str(targetpin),net=n,via_mm=pt,F_path=fp,B_path=bp,width_mm=width))
 for ref,pin,owner in [('C11069',1,1),('C11069',2,6),('C11070',1,10),('C11070',2,6),('C11068',1,8),('C11068',2,11)]:own_loop(ref,pin,'U11015',owner,.3 if ref!='C11068' else .2)
 rtn=ps['U11015','11'].GetNetname();assert rtn!=ps['U11015','6'].GetNetname()
 for pin in ['3','5']:
  p=ps['U11015',pin];ep=ps['U11015','11'];assert p.GetNetname()==rtn;pp=next((pp for pp in paths(mm(p.GetPosition()),mm(ep.GetPosition()))if g.clear(pp,rtn,pcbnew.F_Cu,.2)),None);assert pp is not None,('U11015',pin)
  for x,y in zip(pp,pp[1:]):track(x,y,rtn,.2,pcbnew.F_Cu)
 # Source array is wholly in the real positive polymer land. These via-in-
 # pad transitions require manufacturer filling/planarization confirmation.
 cx,cy=mm(source.GetPosition())
 for dx in [-.8,0,.8]:
  for dy in [-.8,0,.8]:via((cx+dx,cy+dy),net)
 for l in [pcbnew.F_Cu,pcbnew.B_Cu]:zone(l,rectangle([cx-1.15,cy-1.15,cx+1.15,cy+1.15]),'MOTION_RAW_source_nine_'+b.GetLayerName(l))
 for ref in ['U11010','U11011']:
  ep=ps[ref,'11'];x,y=mm(ep.GetPosition());assert ep.GetNetname()==net
  for dy in [-.7,0,.7]:
   point=next((pt for pt in [(x-.3,y+dy),(x-.2,y+dy),(x-.1,y+dy),(x,y+dy)]if all(g.clear([pt,pt],net,l,.5)for l in [pcbnew.F_Cu,pcbnew.B_Cu])),None);assert point is not None,(ref,dy);via(point,net)
  zone(pcbnew.F_Cu,rectangle([x-1.3,y-.25,x+.55,y+.8]),ref+'_actual_VIN_VBIAS_EP_join',130)
  for l in [pcbnew.B_Cu,pcbnew.In3_Cu]:zone(l,rectangle([x-.55,y-1.3,x+.55,y+1.3]),ref+'_three_actual_input_barrels_'+b.GetLayerName(l),131)
 # Complete the third actual switch-input bypass, at its unchanged B land.
 cp=ps['C11059','1'];pt=(340.5,182.5);track(mm(cp.GetPosition()),pt,net,.4,pcbnew.B_Cu);via(pt,net)
 cn=ps['C11059','2'];ground=cn.GetNetname();assert ground=='/LOGIC_GND';gt=(340.5,184.35);track(mm(cn.GetPosition()),gt,ground,.4,pcbnew.B_Cu);via(gt,ground)
 model=json.loads(Path('hardware/motherboard/design.json').read_text());parts={r:c for r,c in model['components'].items()if c.get('physical',c.get('role')!='schematic_boundary_not_orderable')};nodes,nc,functions=native(Path('hardware/motherboard/netlist.xml'));domains,barriers,_floating,_coupling=classify(parts,nodes,nc);mapping=positioned(b,parts,nodes,nc,functions,domains,barriers);assert not mapping['errors'];exclusion=pcbnew.SHAPE_POLY_SET()
 for side in ['In1.Cu','In4.Cu']:
  regions,barrier,ungrounded=build_side_polygons(mapping,b,side);exclusion.Append(barrier);exclusion.Append(ungrounded)
  for region in regions.values():exclusion.Append(inflation(region,.25))
 exclusion.Simplify();body=rectangle([249,167.5,347.0,188.0]);body.BooleanSubtract(exclusion);body.Simplify()
 for k,piece in enumerate(split_polygons(body)):zone(pcbnew.In3_Cu,piece,'MOTION_RAW_actual_motor_input_distribution_'+str(k),121,2)
 # This own local return matches the unchanged receiving-side bypass/IC.
 own=rectangle([339.8,181.7,345.9,187.5]);own.BooleanSubtract(exclusion);own.Simplify()
 for k,piece in enumerate(split_polygons(own)):zone(pcbnew.In1_Cu,piece,'MOTION_switch_actual_receiving_return_'+str(k),132,.2,ground)
 pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();connected={t.m_Uuid.AsString()for t in b.GetConnectivity().GetConnectedItems(source)};remove=[]
 for z in list(b.Zones()):
  uid=z.m_Uuid.AsString()
  if uid not in oldzones and z.GetNetname()==net and uid not in connected:remove.append(uid);b.Remove(z)
 zs=[r for r in zs if r['uuid']not in remove];pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();dest=a.out/'motion-raw-delivery-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
 for ext in ['.kicad_pro','.kicad_dru']:shutil.copyfile(a.board.with_suffix(ext),dest.with_suffix(ext))
 for f in a.board.parent.iterdir():
  if f.name=='fp-lib-table':(a.out/f.name).write_text(f.read_text().replace('${KIPRJMOD}',a.board.parent.resolve().as_posix()))
  elif f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,a.out/f.name)
 q=pcbnew.LoadBoard(str(dest));q.BuildConnectivity();qp={p.m_Uuid.AsString():p for p in q.GetPads()};assert all(op[k]==pad_identity(p)for k,p in qp.items()if k not in old_cap_pose['pads']and k not in old_output_pose['pads']and k not in old_dvdt_pose['pads']);qc={t.m_Uuid.AsString():identity(t)for t in q.GetTracks()};assert all(qc[k]==v for k,v in old.items()if k not in retired_ids);assert not(retired_ids&set(qc));reachable={t.m_Uuid.AsString()for t in q.GetConnectivity().GetConnectedItems(qp[source.m_Uuid.AsString()])};checks=[]
 for ref,pins in [('U11010',['3','4','11']),('U11011',['3','4','11']),('C11059',['1']),('C11057',['1'])]:
  for pin in pins:
   p=ps[ref,pin];checks.append(dict(reference=ref,pin=pin,pad_uuid=p.m_Uuid.AsString(),actual_source_connected=p.m_Uuid.AsString()in reachable))
 subprocess.run([CLI,'pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(a.out/'drc.json'),str(dest)],check=True,capture_output=True,text=True);d=json.loads((a.out/'drc.json').read_text());errors=[v for v in d['violations']if v['severity']=='error'];scope=dict(electrical_source_unchanged=True,reviewed_scope_reason='Actual receiving input arrays/short VIN and VBIAS join for two fitted motor5 switches, source polymer transition and dedicated own-domain In3 supply sheet; unchanged third switch-input bypass receives source and return; C11069 moves off the logic VIN land and C11068/C11070 shift within the same U11015 field cell into its own U11015 FIELD_A input/return cell; no source/old copper/old zone definitions changed',reviewed_footprint_references=['C11069'],reviewed_copper_delta_UUIDs=[v['uuid']for v in added],reviewed_added_zone_UUIDs=[v['uuid']for v in zs],reviewed_removed_copper_UUIDs=sorted(retired_ids));(a.out/'bounded-scope.json').write_text(json.dumps(scope,indent=2)+'\n');r=dict(input_hashes=inputs,board_sha256=sha(dest),exact_added_copper=added,exact_retired_copper=[dict(uuid=t.m_Uuid.AsString(),identity=old[t.m_Uuid.AsString()])for t in retired],exact_added_zones=zs,actual_source_endpoint_checks=checks,field_cell_actual_pin_loops=field_checks,C11069_old_pose=old_cap_pose,C11069_new_pose=dict(point=mm(cf.GetPosition()),angle=cf.GetOrientationDegrees()),C11070_old_pose=old_output_pose,C11070_new_pose=dict(point=mm(of.GetPosition()),angle=of.GetOrientationDegrees()),C11068_old_pose=old_dvdt_pose,C11068_new_pose=dict(point=mm(df.GetPosition()),angle=df.GetOrientationDegrees()),native_errors=errors,native_types=dict(collections.Counter(v['type']for v in d['violations'])),native_joins=q.GetConnectivity().GetUnconnectedCount(False),present_motor_input_load_a=1.3464,upstream_motion_converter_design_a=6,receiving_branch_6a_delivery_qualified=False,full_IR_drop_qualified=False,via_in_pad_factory_process_required=True,manufacturing_ready=False);assert all(sha(Path(p))==h for p,h in inputs.items());(a.out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k not in ['input_hashes','exact_added_copper','exact_added_zones','native_errors']}))
if __name__=='__main__':main()








