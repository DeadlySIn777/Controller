"""Actual six transmitter bypass cells and three switch-cap corrections.

Existing source parts only. These local loops are electrically tested; global
supply/return current delivery remains a separate actual native transaction.
"""
import argparse,json,collections,copy,shutil,subprocess,math
from pathlib import Path
import pcbnew
from hardware_route_current_delivery_native import Geometry,sha
from hardware_route_logic_return import identity,pad_identity,mm,xy
from hardware_populate_motherboard_pcb import footprint_name
from hardware_route_local_signals import paths
from hardware_route_power_groups_native import hits
from hardware_route_logic_return import segment_distance
from hardware_map_motherboard_domains import native,classify,positioned
from hardware_zone_motherboard_returns import build_side_polygons,duplicate,inflation
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True);frozen={str(p):sha(p)for p in [a.board,Path(__file__),Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml')]};b=pcbnew.LoadBoard(str(a.board));b.BuildConnectivity();co=b.GetConnectivity();old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};fs={f.GetReference():f for f in b.GetFootprints()};parts={r:{p.GetNumber():p for p in f.Pads()if p.GetNumber()}for r,f in fs.items()};retired=[];poses=[];add=[];zs=[];checks=[]
 # Each moved cap must have no actual other fitted pad in either old cluster.
 for r,pt,angle in [('C11057',(341.0,186.3),180),('C11058',(338.5,185.75),-90),('C11060',(338.5,181.75),-90)]:
  for p in fs[r].Pads():
   reach=co.GetConnectedItems(p);other=[q for q in reach if q.Type()==pcbnew.PCB_PAD_T and q.GetParentFootprint().GetReference()!=r];assert not other,(r,[(q.GetParentFootprint().GetReference(),q.GetNumber())for q in other])
   for t in reach:
    if isinstance(t,(pcbnew.PCB_TRACK,pcbnew.PCB_VIA))and t.m_Uuid.AsString()not in retired:retired.append(t.m_Uuid.AsString())
  f=fs[r];first=(mm(f.GetPosition()),f.GetOrientationDegrees(),b.GetLayerName(f.GetLayer()))
  if f.GetLayer()!=pcbnew.B_Cu:f.Flip(f.GetPosition(),pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
  f.SetOrientationDegrees(angle);f.SetPosition(xy(pt));poses.append(dict(ref=r,before=first,after=(mm(f.GetPosition()),f.GetOrientationDegrees(),b.GetLayerName(f.GetLayer()))))
 for uid in retired:b.Remove(next(t for t in b.GetTracks()if t.m_Uuid.AsString()==uid))
 pcbnew.SaveBoard(str(a.out/'placement-debug.kicad_pcb'),b)
 g=Geometry(b)
 print('CAP_POSES',[(r,fs[r].GetOrientationDegrees(),[(p.GetNumber(),mm(p.GetPosition()),p.GetNetname())for p in fs[r].Pads()])for r in ['C11057','C11058','C11060']],flush=True)
 def track(net,pp,w=.4,l=pcbnew.F_Cu,role='actual_local_loop'):
  if l in [pcbnew.F_Cu,pcbnew.B_Cu]:assert g.clear(pp,net,l,w),(role,net,pp,w,b.GetLayerName(l))
  else:
   for s,e in zip(pp,pp[1:]):
    assert not any(hits(s,e,poly,w/2)for ref,poly in g.barriers),(role,'package_barrier')
    for p in b.GetPads():
     if p.GetNetname()==net or not p.IsOnLayer(l):continue
     polys=p.GetEffectivePolygon(l)
     for k in range(polys.OutlineCount()):assert not hits(s,e,[mm(polys.Outline(k).CPoint(i))for i in range(polys.Outline(k).PointCount())],w/2+.16),(role,'inner_foreign_pad',p.GetParentFootprint().GetReference(),p.GetNumber())
    for t in b.GetTracks():
     if t.IsOnLayer(l)and t.GetNetname()!=net:assert segment_distance(s,e,mm(t.GetStart()),mm(t.GetEnd()))>=w/2+pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)if isinstance(t,pcbnew.PCB_VIA)else t.GetWidth())/2+.16-1e-6,(role,'inner_foreign_copper',t.m_Uuid.AsString())
  for s,e in zip(pp,pp[1:]):
   if math.dist(s,e)<1e-8:continue
   t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetStart(xy(s));t.SetEnd(xy(e));t.SetWidth(pcbnew.FromMM(w));t.SetLayer(l);b.Add(t);g.add(t);add.append(dict(uuid=t.m_Uuid.AsString(),identity=identity(t),role=role))
 def via_clear(net,pt):
  if not all(g.clear([pt,pt],net,l,.5)for l in [pcbnew.F_Cu,pcbnew.B_Cu]):return False
  for t in b.GetTracks():
   if t.GetNetname()!=net and any(t.IsOnLayer(l)for l in [pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu])and segment_distance(pt,pt,mm(t.GetStart()),mm(t.GetEnd()))<.25+pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)if isinstance(t,pcbnew.PCB_VIA)else t.GetWidth())/2+.16-1e-6:return False
  return True
 def via(net,pt,role):
  assert via_clear(net,pt),(role,net,pt)
  v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(net));v.SetPosition(xy(pt));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);g.add(v);add.append(dict(uuid=v.m_Uuid.AsString(),identity=identity(v),role=role));return v
 def zone(net,layer,box,role,priority=100):
  z=pcbnew.ZONE(b);z.SetNet(b.FindNet(net));z.SetLayer(layer);z.SetZoneName(role);z.SetLocalClearance(pcbnew.FromMM(.15));z.SetMinThickness(pcbnew.FromMM(.15));z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL);z.SetAssignedPriority(priority);z.Outline().NewOutline()
  for pt in [(box[0],box[1]),(box[2],box[1]),(box[2],box[3]),(box[0],box[3])]:z.Outline().Append(*xy(pt))
  b.Add(z);zs.append(dict(uuid=z.m_Uuid.AsString(),role=role,net=net,layer=b.GetLayerName(layer),box_mm=box));return z
 for k in range(1,7):
  u,c='U600'+str(k),'C600'+str(k);p=parts[u]['16'];cp=parts[c]['1'];ground=parts[u]['8'];cg=parts[c]['2'];n=p.GetNetname();gn=ground.GetNetname();x,y=mm(fs[c].GetPosition());assert n==cp.GetNetname()==parts[u]['12'].GetNetname()and gn==cg.GetNetname()
  track(n,[mm(p.GetPosition()),mm(cp.GetPosition())],.4,role=u+'_VCC16_bypass')
  sx,sy=mm(cp.GetPosition());ux,uy=mm(parts[u]['12'].GetPosition());start=(sx,sy);end=(ux,uy);pp=next((pp for pp in paths(start,end)if g.clear(pp,n,pcbnew.F_Cu,.2)),None)or g.grid(start,end,n,pcbnew.F_Cu,.2,step=.15,padding=4);assert pp is not None,u;track(n,pp,.2,role=u+'_G_N12_safe_HIGH_tie')
  candidates=[(x+dx,y+dy)for dx,dy in [(1.4,-1.4),(-.6,-1.2),(1.4,-2.2),(-.6,-2.2),(2.5,-3.),(-1.4,-3.),(1.4,1.4),(-.6,1.4)]];choice=None
  for centre in candidates:
   if not all(g.clear([(centre[0]+dx,centre[1])]*2,n,l,.5)for dx in [-.8,0,.8]for l in [pcbnew.F_Cu,pcbnew.B_Cu]):continue
   pp=next((pp for pp in paths(mm(cp.GetPosition()),centre)if g.clear(pp,n,pcbnew.F_Cu,.4)),None)
   if pp is not None:choice=(centre,pp);break
  assert choice is not None,u;centre,pp=choice;track(n,pp,.4,role=u+'_receiving_supply_escape')
  ids=[]
  for dx in [-.8,0,.8]:ids.append(via(n,(centre[0]+dx,centre[1]),u+'_three_supply_vias').m_Uuid.AsString())
  for l in [pcbnew.F_Cu,pcbnew.B_Cu]:zone(n,l,[centre[0]-1.1,centre[1]-.3,centre[0]+1.1,centre[1]+.3],u+'_supply_array_'+b.GetLayerName(l))
  gs=mm(cg.GetPosition());q=next((pt for d in [.8,1.,1.2,1.6]for pt in [(gs[0]+d,gs[1]),(gs[0],gs[1]+d),(gs[0]+d,gs[1]+d),(gs[0],gs[1]-d)]if all(g.clear([pt,pt],gn,l,.5)for l in [pcbnew.F_Cu,pcbnew.B_Cu])and g.clear([gs,pt],gn,pcbnew.F_Cu,.4)),None);assert q is not None,c;track(gn,[gs,q],.4,role=c+'_own_cap_return');via(gn,q,c+'_own_cap_return')
  gs=mm(ground.GetPosition());qg=next((pt for d in [.8,1.,1.2,1.6]for pt in [(gs[0]-d,gs[1]),(gs[0]-d,gs[1]+d),(gs[0],gs[1]+d)]if all(g.clear([pt,pt],gn,l,.5)for l in [pcbnew.F_Cu,pcbnew.B_Cu])and g.clear([gs,pt],gn,pcbnew.F_Cu,.4)),None);assert qg is not None,u;track(gn,[gs,qg],.4,role=u+'_own_IC_return');via(gn,qg,u+'_own_IC_return')
  zone(gn,pcbnew.In1_Cu,[min(qg[0],centre[0],q[0])-.4,min(qg[1],centre[1],q[1])-.4,max(q[0],qg[0],centre[0])+.4,max(qg[1],centre[1],q[1])+.4],u+'_bounded_actual_bypass_return',10)
  checks.extend([(u,'16',c,'1'),(u,'12',c,'1'),(u,'8',c,'2')]);print('TX_LOCAL',u,flush=True)
 # Close the moved caps to the actual owning switches. No old signal cap
 # is substituted for a current supply; positive and own return are separate.
 for u,c,pin in [('U11010','C11057','3'),('U11010','C11058','9'),('U11011','C11060','9')]:
  p=parts[u][pin];cp=parts[c]['1'];cg=parts[c]['2'];gn=cg.GetNetname();n=cp.GetNetname();assert p.GetNetname()==n
  # The supply via lies outside package lands, between owner and cap.
  ps=mm(p.GetPosition());cs=mm(cp.GetPosition());vs=((ps[0]+cs[0])/2,(ps[1]+cs[1])/2)
  choices=([(343.8,184.125)]if c=='C11058'else[(343.8,180.125)]if c=='C11060'else[(340.1,185.1)])+[(cs[0]+dx,cs[1]+dy)for dx,dy in [(-.6,-1.5),(0,-.8),(.8,0),(-.8,0),(0,.8),(0,-1.2),(1.2,0),(-1.2,0),(0,1.2),(0,-1.6),(1.6,0),(-1.6,0),(0,1.6),(0,-2),(-2,0),(2,0),(0,2)]]+[vs];choice=None
  if c in ['C11058','C11060']:
   v=choices[0];cv=(cs[0]+.8,cs[1]);fp=[ps,(ps[0],v[1]),v]
   assert all(g.clear([v,v],n,l,.5)and g.clear([cv,cv],n,l,.5)for l in [pcbnew.F_Cu,pcbnew.B_Cu])and g.clear(fp,n,pcbnew.F_Cu,.3)and g.clear([cs,cv],n,pcbnew.B_Cu,.4),(u,c,'actual_two_via_inner_local_loop')
   track(n,fp,.3,role=c+'_actual_owner_bypass_branch');via(n,v,c+'_actual_owner_supply');via(n,cv,c+'_actual_cap_supply');track(n,[cs,cv],.4,pcbnew.B_Cu,c+'_actual_cap_supply');inner=[v,(v[0],183.55),(cv[0],183.55),cv]if c=='C11058'else[v,(cv[0],v[1]),cv];track(n,inner,.6,pcbnew.In3_Cu,c+'_bounded_inner_bypass_loop');choice=(v,[],[])
  for v in choices:
   if choice is not None:break
   if not all(g.clear([v,v],n,l,.5)for l in [pcbnew.F_Cu,pcbnew.B_Cu]):continue
   if any(any(hits(v,v,p,.30)for p in polys)for net,polys,top,bot,npth in g.pads.candidates(v,v,.30)):continue
   fp=next((pp for pp in paths(ps,v)if g.clear(pp,n,pcbnew.F_Cu,.3)),None)or g.grid(ps,v,n,pcbnew.F_Cu,.3,step=.15,padding=3)
   bp=next((pp for pp in paths(cs,v)if g.clear(pp,n,pcbnew.B_Cu,.4)),None)or g.grid(cs,v,n,pcbnew.B_Cu,.4,step=.15,padding=3)
   if fp is not None and bp is not None:choice=(v,fp,bp);break
  if choice is None:
   pcbnew.SaveBoard(str(a.out/(c+'-supply-debug.kicad_pcb')),b)
   print('NO_LOCAL_VIA',u,c,ps,cs,g.clear([ps,ps],n,pcbnew.F_Cu,.3),g.clear([cs,cs],n,pcbnew.B_Cu,.4),flush=True)
  assert choice is not None,(u,c);v,fp,bp=choice
  if fp:track(n,fp,.3,role=c+'_actual_owner_bypass_branch');via(n,v,c+'_actual_owner_supply');track(n,bp,.4,pcbnew.B_Cu,c+'_actual_owner_supply')
  gs=mm(cg.GetPosition());q=next((q for dx,dy in [(.4,.925),(.4,-.925),(-.4,.925),(-.4,-.925)]+[(d*dx,d*dy)for d in [.8,1.,1.2,1.6,2.,2.4]for dx,dy in [(1,0),(-1,0),(0,1),(1,1),(-1,1),(0,-1)]]for q in [(gs[0]+dx,gs[1]+dy)]if via_clear(gn,q)and g.clear([gs,q],gn,pcbnew.B_Cu,.4)),None)
  if q is None:pcbnew.SaveBoard(str(a.out/(c+'-return-debug.kicad_pcb')),b)
  assert q is not None,c;track(gn,[gs,q],.4,pcbnew.B_Cu,c+'_actual_own_return');via(gn,q,c+'_actual_own_return');checks.extend([(u,pin,c,'1'),(u,'6',c,'2')]);print('SWITCH_CAP',u,c,flush=True)
 # All three actual switch ground pins get a local source return connection.
 for u in ['U11010','U11011','U11012']:
  p=parts[u]['6'];s=mm(p.GetPosition());n=p.GetNetname();candidates=[(344.8,188)]if u=='U11010'else[(345.3,183.4)]if u=='U11011'else[];candidates.extend((s[0]+dx,s[1]+dy)for dx,dy in [(d*x,d*y)for d in [.8,1,1.2,1.6,2]for x,y in [(1,0),(0,1),(1,1),(-1,1)]]);q=next((q for q in candidates if via_clear(n,q)and g.clear([s,q],n,pcbnew.F_Cu,.3)),None);assert q is not None,u;track(n,[s,q],.3,role=u+'_ground_pin6_return');via(n,q,u+'_ground_pin6_return')
 zone('/LOGIC_GND',pcbnew.In1_Cu,[337,179,346,194], 'TPS22990_three_switch_actual_local_returns',10)
 model=json.loads(Path('hardware/motherboard/design.json').read_text());physicalparts={r:c for r,c in model['components'].items()if c.get('physical',c.get('role')!='schematic_boundary_not_orderable')};nodes,nc,functions=native(Path('hardware/motherboard/netlist.xml'));domains,barriers,floating,coupling=classify(physicalparts,nodes,nc);mapping=positioned(b,physicalparts,nodes,nc,functions,domains,barriers);assert not mapping['errors'];regions,barrierpoly,ungrounded=build_side_polygons(mapping,b,'In1.Cu');exclusion=duplicate(barrierpoly);exclusion.Append(ungrounded)
 for poly in regions.values():exclusion.Append(inflation(poly,.25))
 exclusion.Simplify();newzones={z.m_Uuid.AsString():z for z in b.Zones()}
 for row in zs:
  if row['net']!='/LOGIC_GND':continue
  z=newzones[row['uuid']];outline=duplicate(z.Outline());outline.BooleanSubtract(exclusion);outline.Simplify();z.Outline().RemoveAllContours();z.Outline().Append(outline);row['exact_source_domain_exclusions_applied']=True
 pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();dest=a.out/'motor-supply-cells-candidate.kicad_pcb';pcbnew.SaveBoard(str(dest),b)
 for e in ['.kicad_pro','.kicad_dru']:shutil.copyfile(a.board.with_suffix(e),dest.with_suffix(e))
 for f in a.board.parent.iterdir():
  if f.name=='fp-lib-table':(a.out/f.name).write_text(f.read_text().replace('${KIPRJMOD}',a.board.parent.resolve().as_posix()))
  elif f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,a.out/f.name)
 q=pcbnew.LoadBoard(str(dest));q.BuildConnectivity();now={t.m_Uuid.AsString():identity(t)for t in q.GetTracks()};assert all(now[k]==v for k,v in old.items()if k not in retired);assert all(now[r['uuid']]==r['identity']for r in add);np={p.m_Uuid.AsString():pad_identity(p)for p in q.GetPads()};moved={p.m_Uuid.AsString()for r in ['C11057','C11058','C11060']for p in fs[r].Pads()};assert all(np[k]==v for k,v in oldpads.items()if k not in moved);qp={(f.GetReference(),p.GetNumber()):p for f in q.GetFootprints()for p in f.Pads()if p.GetNumber()};reach=q.GetConnectivity();proof=[]
 for u,pin,c,cp in checks:
  p,v=qp[u,pin],qp[c,cp];assert p.GetNetname()==v.GetNetname()and v.m_Uuid.AsString()in{t.m_Uuid.AsString()for t in reach.GetConnectedItems(p)},(u,pin,c,cp);proof.append(dict(owner=u,owner_pin=pin,capacitor=c,capacitor_pin=cp,actual_connected=True,net=p.GetNetname()))
 run=subprocess.run([CLI,'pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(a.out/'drc.json'),str(dest)],capture_output=True,text=True);assert run.returncode==0;d=json.loads((a.out/'drc.json').read_text());assert not d.get('ignored_checks');assert all(sha(Path(p))==h for p,h in frozen.items());result=dict(input_hashes=frozen,board_sha256=sha(dest),exact_moved_caps=poses,retired_owned_cap_only_copper=[dict(uuid=k,identity=old[k])for k in retired],new_copper=add,new_zones=zs,actual_owner_endpoint_checks=proof,native_DRC_types=dict(collections.Counter(v['type']for v in d['violations'])),native_errors=[v for v in d['violations']if v['severity']=='error'],uncapped_joins=reach.GetUnconnectedCount(False),all_other_source_pad_and_copper_identities_preserved=True,global_supply_return_delivery_or_inductance_qualified=False);(a.out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['input_hashes','new_copper','new_zones','actual_owner_endpoint_checks','native_errors']}))
if __name__=='__main__':main()





