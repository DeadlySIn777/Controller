"""Route exact local bypass owners while recording known incomplete WIP warnings.

This is not power distribution. Only explicitly reviewed small local supply
bypasses are eligible. Every return via must join the actual own-domain filled
reference copper on both sides; every new power transition requires a nearby
actual own-return stitch. Native DRC and own-pin connectivity decide acceptance.
All native violations remain in the native JSON and final receipt. Only an
exact immutable warning disposition may admit existing unrelated warnings;
new errors/warnings, ignored checks and source-cluster fragmentation fail.
This is never a complete-board DRC pass or manufacturing release.
"""
import argparse,collections,json,math,shutil,subprocess
from pathlib import Path
import pcbnew
from hardware_route_local_signals import GeometryIndex,paths
from hardware_route_logic_return import identity,mm,xy,distance,segment_distance,segment_hits_box
from hardware_populate_motherboard_pcb import sha,write,pad_template
from hardware_check_return_corridors import circle,covered
from hardware_route_selected_additive import corridor_polygon
from hardware_check_return_corridors_r04 import return_corridor_check,NativeCollectedAnnulusCheck,dependencies as return_dependencies
from hardware_route_owned_bypass_loops_r02 import actual_receiving_return_anchors
from hardware_anchor_owned_cmos_returns import source_clusters
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')

def warning_key(row):
 return json.dumps(row,sort_keys=True,separators=(',',':'))

def reviewed_wip_warnings(report,disposition,board_sha):
 if report.get('ignored_checks')or any(r['severity']!='warning'for r in report['violations']):raise ValueError('WIP baseline has errors/ignored checks')
 if not disposition.get('routing_incomplete')or disposition.get('manufacturing_ready')is not False or disposition.get('board_sha256')!=board_sha:raise ValueError('Exact incomplete native board disposition required')
 allowed=disposition.get('known_unresolved_native_warnings')
 if not isinstance(allowed,list)or any(r['severity']!='warning' or r['type']not in {'via_dangling','track_dangling','isolated_copper'}for r in allowed):raise ValueError('Only exact known unfinished return/feed warnings can enter local WIP routing')
 if collections.Counter(map(warning_key,allowed))!=collections.Counter(map(warning_key,report['violations'])):raise ValueError('Actual native baseline differs from frozen WIP warning disposition')
 return set(map(warning_key,allowed))

def new_route_defects(report,known):
 if report.get('ignored_checks'):raise ValueError('Ignored native checks forbidden')
 return [r for r in report['violations']if warning_key(r)not in known]

# These are low-current local bypass branches, never bulk/distribution, analog
# references, timers, switching loops, terminal filters or Y-capacitor paths.
CATEGORIES={'supply_bypass','local_bypass','HF_supply_bypass','FPGA_ball_bypass',
 'local_VDD_bypass','logic_bypass','status_local_bypass','MCU_VDD_bypass',
 'isolation_primary_bypass','isolation_secondary_bypass','window_supply_bypass',
 'DAC_supply_bypass','amplifier_supply_bypass','ADC_supply_bypass',
 'distributed_IO3_reset_bypass','microSD_local_bypass','USB_local_bypass'}

def drc(board,out,name):
 path=out/(name+'.json');run=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(path),str(board)],capture_output=True,text=True)
 (out/(name+'.txt')).write_text(run.stdout+run.stderr)
 if run.returncode:raise ValueError('Native DRC did not execute')
 data=json.loads(path.read_text())
 if data.get('ignored_checks'):raise ValueError('Ignored native checks are forbidden')
 return data

class Geometry:
 def __init__(self,b):
  self.b=b;self.pads=GeometryIndex();self.tracks={i:GeometryIndex()for i in b.GetEnabledLayers().Seq()if pcbnew.IsCopperLayer(i)};self.holes=[]
  for p in b.GetPads():
   q=p.GetBoundingBox();box=tuple(pcbnew.ToMM(v)for v in(q.GetX(),q.GetY(),q.GetRight(),q.GetBottom()))
   self.pads.add((p,box),box)
   if p.GetAttribute()in(pcbnew.PAD_ATTRIB_NPTH,pcbnew.PAD_ATTRIB_PTH):self.holes.append((mm(p.GetPosition()),pcbnew.ToMM(max(p.GetDrillSize()))))
  self.keepouts=[]
  for z in b.Zones():
   if z.GetIsRuleArea():self.keepouts.append(z)
  for t in b.GetTracks():self.add(t)
 def add(self,t):
  via=isinstance(t,pcbnew.PCB_VIA);w=pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)if via else t.GetWidth());s,e=mm(t.GetStart()),mm(t.GetEnd())
  for layer,index in self.tracks.items():
   if t.IsOnLayer(layer):index.add((t.GetNetname(),s,e,w),(min(s[0],e[0])-w/2,min(s[1],e[1])-w/2,max(s[0],e[0])+w/2,max(s[1],e[1])+w/2))
  if via:self.holes.append((s,pcbnew.ToMM(t.GetDrillValue())))
 def clear(self,points,net,layer,width=.2):
  for s,e in zip(points,points[1:]):
   corridor=corridor_polygon(tuple(xy(s)),tuple(xy(e)),pcbnew.FromMM(width/2))
   for zone in self.keepouts:
    if zone.IsOnLayer(layer)and zone.GetDoNotAllowTracks():
     hit=pcbnew.SHAPE_POLY_SET();hit.Append(corridor);hit.BooleanIntersection(zone.Outline())
     if hit.Area():return False
   for p,box in self.pads.candidates(s,e,width/2+.25):
    if p.IsOnLayer(layer)and p.GetNetname()!=net and segment_hits_box(s,e,box,width/2+.15):return False
   for name,a,z,w in self.tracks[layer].candidates(s,e,width/2+.5):
    if name!=net and segment_distance(s,e,a,z)<width/2+w/2+.15-1e-6:return False
  return True
 def via(self,pt,net):
  if not .75<pt[0]<459.25 or not .75<pt[1]<339.25:return False
  for p,box in self.pads.candidates(pt,pt,.51):
   # No new via-in-pad, including same-net lands, without a separately quoted
   # filled/capped process. Avoid all drilled mechanical pads on all layers.
   if segment_hits_box(pt,pt,box,.25+.15):return False
  for zone in self.keepouts:
   if zone.GetDoNotAllowVias():
    hit=circle(tuple(xy(pt)),pcbnew.FromMM(.25));hit.BooleanIntersection(zone.Outline())
    if hit.Area():return False
  for index in self.tracks.values():
   for name,a,z,w in index.candidates(pt,pt,.51):
    if name!=net and distance(pt,a,z)<.25+w/2+.205-1e-6:return False
  return not any(math.dist(pt,q)<.1+d/2+.25-1e-6 for q,d in self.holes)

def connected(b,p,q):
 b.BuildConnectivity();return q.m_Uuid.AsString()in{v.m_Uuid.AsString()for v in b.GetConnectivity().GetConnectedItems(p)}

SPECIAL_NO_VIA_ADC_REFS={f'C147{i}'for i in range(40,47)}

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for key in ('board','owners','out'):ap.add_argument('--'+key,type=Path,required=True)
 ap.add_argument('--baseline-disposition',type=Path,required=True)
 ap.add_argument('--only-refs',help='Exact reviewed capacitor list, comma-separated')
 a=ap.parse_args()
 return_dependencies()
 if a.out.exists():raise ValueError('Fresh immutable output required')
 manifest=json.loads(a.owners.read_text())
 if manifest.get('errors')or manifest.get('pending')or not manifest.get('all_owner_mappings_verified'):raise ValueError('Complete reviewed capacitor owners required')
 a.out.mkdir(parents=True);dest=a.out/'owned-bypass-loop-candidate.kicad_pcb'
 for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(a.board.with_suffix(suffix),dest.with_suffix(suffix))
 for f in a.board.parent.iterdir():
  if f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,a.out/f.name)
  elif f.name=='fp-lib-table':shutil.copyfile(f,a.out/f.name)
 shutil.copyfile(a.board,dest)
 baseline=drc(dest,a.out,'baseline')
 disposition=json.loads(a.baseline_disposition.read_text());known=reviewed_wip_warnings(baseline,disposition,sha(a.board))
 b=pcbnew.LoadBoard(str(dest));fps={f.GetReference():f for f in b.GetFootprints()};old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()}
 lands={r:collections.Counter(pad_template(p)for p in f.Pads())for r,f in fps.items()};pin_nets={(r,p.m_Uuid.AsString()):p.GetNetname()for r,f in fps.items()for p in f.Pads()}
 selected=[v for v in manifest['capacitors']if (not a.only_refs or v['ref']in a.only_refs.split(','))]
 rows=[v for v in selected if v['category']in CATEGORIES and v['ref']not in SPECIAL_NO_VIA_ADC_REFS]
 dedicated=[dict(ref=v['ref'],reason='ADS8684A supply/reference cell requires dedicated same-side direct no-via routing')for v in selected if v['ref']in SPECIAL_NO_VIA_ADC_REFS]
 prior_clusters=source_clusters(b)
 groups=[];skips=list(dedicated);mapping={};g=Geometry(b);checker=NativeCollectedAnnulusCheck(b,{})
 def pin(ref,num):return next(p for p in fps[ref].Pads()if p.GetNumber()==num)
 def own_fill(pt,return_net):
  return all(covered(circle(tuple(xy(pt)),pcbnew.FromMM(.24)),checker.reference(return_net,b.GetLayerID(layer)))for layer in('In1.Cu','In4.Cu'))
 def add_route(points,net,layer,items):
  for s,e in zip(points,points[1:]):
   if math.dist(s,e)<1e-6:continue
   t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetLayer(layer);t.SetStart(xy(s));t.SetEnd(xy(e));t.SetWidth(pcbnew.FromMM(.2));b.Add(t);items.append(t);g.add(t)
 def add_via(pt,net,items):
  v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(net));v.SetPosition(xy(pt));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetRemoveUnconnected(True);v.SetIsFree(True);b.Add(v);items.append(v);g.add(v);return v
 def escapes(p):
  s=mm(p.GetPosition())
  for d in(.7,.85,1.05,1.35,1.7,2.):
   for dx,dy in((1,0),(-1,0),(0,1),(0,-1),(.707107,.707107),(-.707107,.707107),(.707107,-.707107),(-.707107,-.707107)):
    yield(round(s[0]+d*dx,6),round(s[1]+d*dy,6))
 for row in rows:
  cp=pin(row['ref'],row['cap_power']);cr=pin(row['ref'],row['cap_return']);owners=[pin(n['ref'],n['pin'])for n in row['power_nodes']];returns=[pin(n['ref'],n['pin'])for n in row['return_nodes']]
  if not owners or not returns or any(p.GetNetname()!=cp.GetNetname()for p in owners)or any(p.GetNetname()!=cr.GetNetname()for p in returns):raise ValueError('Exact owner physical nets differ '+row['ref'])
  owner=min(owners,key=lambda p:math.dist(mm(p.GetPosition()),mm(cp.GetPosition())))
  if math.dist(mm(owner.GetPosition()),mm(cp.GetPosition()))>8:skips.append(dict(ref=row['ref'],reason='Actual local owner exceeds8mm; bounded cell correction required'));continue
  if connected(b,cp,owner)and any(connected(b,cr,p)for p in returns):continue
  items=[];reason=None
  try:
   # Connect the receiving device return and capacitor return separately to
   # their actual continuous own reference. SMD ground does not touch a buried
   # plane merely because the assigned net name matches.
   for ret in [returns[0],cr]:
    peer_vias=[v for v in b.GetConnectivity().GetConnectedItems(ret)if isinstance(v,pcbnew.PCB_VIA)and v.GetNetname()==ret.GetNetname()]
    if any(math.dist(mm(v.GetPosition()),mm(ret.GetPosition()))<=2 and own_fill(mm(v.GetPosition()),ret.GetNetname())for v in peer_vias):continue
    layer=ret.GetParentFootprint().GetLayer();s=mm(ret.GetPosition())
    pt=next((pt for pt in escapes(ret)if g.via(pt,ret.GetNetname())and own_fill(pt,ret.GetNetname())and g.clear([s,pt],ret.GetNetname(),layer)),None)
    if pt is None:raise ValueError('No legal own-domain ground stitch at '+ret.GetParentFootprint().GetReference()+'.'+ret.GetNumber())
    add_route([s,pt],ret.GetNetname(),layer,items);add_via(pt,ret.GetNetname(),items);b.BuildConnectivity()
   if not any(connected(b,cr,p)for p in returns):raise ValueError('Actual owner return remains in a different filled island')
   if not connected(b,cp,owner):
    cs,os=mm(cp.GetPosition()),mm(owner.GetPosition());cl,ol=cp.GetParentFootprint().GetLayer(),owner.GetParentFootprint().GetLayer()
    if cl==ol:
     path=next((ps for ps in paths(cs,os)if g.clear(ps,cp.GetNetname(),cl)),None)
     if path is None:raise ValueError('No bounded same-side local power branch')
     add_route(path,cp.GetNetname(),cl,items)
    else:
     chosen=None
     for pt in escapes(cp):
      if not g.via(pt,cp.GetNetname())or not g.clear([cs,pt],cp.GetNetname(),cl):continue
      stitch_vias=[v for v in b.GetTracks()if isinstance(v,pcbnew.PCB_VIA)and v.GetNetname()==cr.GetNetname()and math.dist(pt,mm(v.GetPosition()))<=1 and own_fill(mm(v.GetPosition()),cr.GetNetname())]
      path=next((ps for ps in paths(pt,os)if g.clear(ps,cp.GetNetname(),ol)),None)
      if not path:continue
      extra_stitch=None
      if not stitch_vias:
       extra_stitch=next((q for d in(.75,.85,.95)for dx,dy in((1,0),(-1,0),(0,1),(0,-1))for q in[(round(pt[0]+d*dx,6),round(pt[1]+d*dy,6))]if g.via(q,cr.GetNetname())and own_fill(q,cr.GetNetname())and math.dist(q,pt)>=.65),None)
       if extra_stitch is None:continue
      chosen=pt,path,extra_stitch;break
     if chosen is None:raise ValueError('No local layer transition with actual own-return stitch≤1mm')
     pt,path,extra_stitch=chosen
     if extra_stitch:add_via(extra_stitch,cr.GetNetname(),items)
     add_route([cs,pt],cp.GetNetname(),cl,items);add_route(path,cp.GetNetname(),ol,items);add_via(pt,cp.GetNetname(),items)
   if not connected(b,cp,owner)or not any(connected(b,cr,p)for p in returns):raise ValueError('Actual owning-pin loop did not close')
  except ValueError as error:
   reason=str(error)
  if reason:
   for t in items:b.Remove(t)
   g=Geometry(b);skips.append(dict(ref=row['ref'],reason=reason));continue
  ids=[t.m_Uuid.AsString()for t in items];index=len(groups);groups.append(dict(ref=row['ref'],category=row['category'],owner=row['owner'],new_UUIDs=ids,actual_owning_signal_return_pairs_connected=True,retained=True));mapping.update({u:index for u in ids})
  if len(groups)%20==0:print(dict(closed_local_loops=len(groups),remaining=len(skips)),flush=True)
 rejected=[];return_reviews=[];return_rejections=[]
 expected_added={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()if t.m_Uuid.AsString()not in old}
 for attempt in range(10):
  pcbnew.SaveBoard(str(dest),b);report=drc(dest,a.out,'routed-'+str(attempt))
  defects=new_route_defects(report,known)
  if not defects:
   # Native geometry alone does not prove the supply branch has its actual
   # adjacent return. Recheck the final filled copper, including the true
   # antipad at each supply via and an anchored own-return stitch within1mm.
   reviewed=pcbnew.LoadBoard(str(dest));reviewed.BuildConnectivity()
   exact={t.m_Uuid.AsString():t for t in reviewed.GetTracks()};bad=set();pass_reviews=[]
   for index,group in enumerate(groups):
    if not group['retained']:continue
    row=next(v for v in rows if v['ref']==group['ref'])
    supply=pin(row['ref'],row['cap_power']).GetNetname();ret=pin(row['ref'],row['cap_return']).GetNetname()
    ids=[u for u in group['new_UUIDs']if exact[u].GetNetname()==supply]
    declaration=dict(return_net=ret,reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.,reference_corridor_margin_mm=.10)
    try:pass_reviews.append(dict(ref=group['ref'],**return_corridor_check(reviewed,ids,{supply:declaration})))
    except ValueError as error:
     bad.add(index);return_rejections.append(dict(ref=group['ref'],reason=str(error)))
   for index,group in enumerate(groups):
    if not group['retained']:continue
    try:actual_receiving_return_anchors(reviewed,{'owned_loops':[group]},manifest)
    except ValueError as error:bad.add(index);return_rejections.append(dict(ref=group['ref'],reason=str(error)))
   if not bad:return_reviews=pass_reviews;break
   for index in bad:
    for t in list(b.GetTracks()):
     if t.m_Uuid.AsString()in groups[index]['new_UUIDs']:b.Remove(t)
    groups[index]['retained']=False;rejected.append(index)
   continue
  rejected_groups=set()
  for issue in defects:
   scopes={mapping[v['uuid']]for v in issue['items']if v['uuid']in mapping}
   if not scopes:raise ValueError('Native violation outside new owned-loop additions')
   rejected_groups.update(scopes)
  for index in rejected_groups:
   for t in list(b.GetTracks()):
    if t.m_Uuid.AsString()in groups[index]['new_UUIDs']:b.Remove(t)
   groups[index]['retained']=False;rejected.append(index)
 else:raise ValueError('Native repair bound exceeded')
 fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity();actual={t.m_Uuid.AsString():identity(t)for t in fresh.GetTracks()}
 actual_pads={p.m_Uuid.AsString():p for p in fresh.GetPads()}
 for group in prior_clusters:
  witness=next(iter(group));current={p.m_Uuid.AsString()for p in fresh.GetConnectivity().GetConnectedItems(actual_pads[witness])if isinstance(p,pcbnew.PAD)}|{witness}
  if not group<=current:raise ValueError('Actual previously joined source pads fragmented during refill')
 if any(actual.get(u)!=v for u,v in old.items()):raise ValueError('Retained copper changed')
 retained_ids={u for v in groups if v['retained']for u in v['new_UUIDs']}
 if set(actual)!=set(old)|retained_ids or any(actual.get(u)!=expected_added[u]for u in retained_ids):raise ValueError('Native fill reassigned or changed an actual new owned route')
 for f in fresh.GetFootprints():
  ref=f.GetReference()
  if collections.Counter(pad_template(p)for p in f.Pads())!=lands[ref]or any(p.GetNetname()!=pin_nets[ref,p.m_Uuid.AsString()]for p in f.Pads()):raise ValueError('Manufacturer lands or source pins changed')
 fresh_fps={f.GetReference():f for f in fresh.GetFootprints()}
 for group in groups:
  if not group['retained']:continue
  row=next(v for v in rows if v['ref']==group['ref'])
  fresh_pin=lambda ref,num:next(p for p in fresh_fps[ref].Pads()if p.GetNumber()==num)
  signal=fresh_pin(row['ref'],row['cap_power']);ret=fresh_pin(row['ref'],row['cap_return'])
  if not any(connected(fresh,signal,fresh_pin(v['ref'],v['pin']))for v in row['power_nodes'])or not any(connected(fresh,ret,fresh_pin(v['ref'],v['pin']))for v in row['return_nodes']):raise ValueError('Actual owning-pin pair opened during native refill '+row['ref'])
 remaining=skips+[dict(ref=v['ref'],reason=next((r['reason']for r in return_rejections if r['ref']==v['ref']),'Native DRC rejected the actual local loop; reroute still required'))for v in groups if not v['retained']]
 write(a.out/'receipt.json',dict(input_sha256={str(a.board):sha(a.board),str(a.owners):sha(a.owners),str(a.baseline_disposition):sha(a.baseline_disposition),str(Path(__file__)):sha(__file__)},board_sha256=sha(dest),eligible_local_categories=sorted(CATEGORIES),owned_loops=groups,required_remaining=remaining,native_rejected_groups=rejected,actual_filled_supply_branch_return_reviews=return_reviews,actual_return_corridor_rejections=return_rejections,native_DRC_regular=len(report['violations']),native_DRC_types=dict(collections.Counter(r['type']for r in report['violations'])),known_unresolved_native_warnings_retained=report['violations'],new_route_DRC_defects=new_route_defects(report,known),complete_board_DRC_pass=not report['violations'],ignored_checks=[],all_prior_native_source_pad_clusters_preserved=True,all_retained_native_copper_and_lands_pin_nets_preserved=True,uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),manufacturing_ready=False,power_distribution_or_physical_loop_inductance_qualified=False))
 print(dict(local_loops_retained=sum(v['retained']for v in groups),required_remaining=len(remaining),native_DRC_regular=len(report['violations']),uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False)))
if __name__=='__main__':main()
