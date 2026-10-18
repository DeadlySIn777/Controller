"""Recover/review exact additive CMOS stitches on a native candidate.

Existing plane-isolation warnings remain explicit unresolved geometry work;
they are never suppressed or called manufacturing-ready. Incorrect new groups
are removed in their entirety; all original copper, zones and source pads stay.
"""
import argparse,collections,json,math,shutil
from pathlib import Path
import pcbnew
from hardware_build_assembly import parse,children,child,value
from hardware_anchor_owned_cmos_returns import CMOS_PREFIXES,EXCLUDED_ADC,EXCLUDED_BLOCKS,source_clusters,warning_key
from hardware_route_owned_bypass_loops import CATEGORIES,drc
from hardware_route_logic_return import identity,mm
from hardware_populate_motherboard_pcb import sha,write,pad_template
from hardware_check_return_corridors import ReturnCheck,circle,covered
from hardware_merge_bounded_pcb_delta import zone_definition
from hardware_merge_bounded_pcb_delta import without_generated_fills

def connected(b,p,q):
 # This reviewer explicitly builds once after load/refill, then only reads
 # the frozen graph. Rebuilding that unchanged graph per stitch is needless.
 return q.m_Uuid.AsString()in{v.m_Uuid.AsString()for v in b.GetConnectivity().GetConnectedItems(p)}

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for k in ('before','candidate','owners','source','out'):ap.add_argument('--'+k,type=Path,required=True)
 a=ap.parse_args()
 if a.out.exists():raise ValueError('Fresh immutable output required')
 frozen={str(p.resolve()):sha(p)for p in(a.before,a.candidate,a.owners,a.source,Path(__file__))}
 src=json.loads(a.source.read_text());owners=json.loads(a.owners.read_text())
 if owners.get('errors')or owners.get('pending')or not owners['all_owner_mappings_verified']:raise ValueError('Verified exact native owners required')
 before=pcbnew.LoadBoard(str(a.before.resolve()));before.BuildConnectivity();b=pcbnew.LoadBoard(str(a.candidate.resolve()));b.BuildConnectivity()
 # Native child wrappers do not own their BOARD. Keep every original/native
 # load alive while exact pad/track wrappers are held for review.
 board_lifetimes=[before,b]
 cu=lambda board:{t.m_Uuid.AsString():identity(t)for t in board.GetTracks()}
 pads=lambda board:{p.m_Uuid.AsString():(p.GetParentFootprint().GetReference(),p.GetNumber(),p.GetNetname(),tuple(p.GetPosition()),pad_template(p))for p in board.GetPads()}
 zones=lambda path:{value(child(z,'uuid')[1]):zone_definition(z)for z in children(parse(without_generated_fills(path.read_text())),'zone')}
 old=cu(before);candidate_cu=cu(b);added={u:v for u,v in candidate_cu.items()if u not in old};oldpads=pads(before)
 if any(candidate_cu.get(u)!=v for u,v in old.items())or pads(b)!=oldpads or zones(a.before)!=zones(a.candidate):raise ValueError('Candidate changes old native copper, source pads or zone definitions')
 groups_before=source_clusters(before);eligible={};byref={f.GetReference():f for f in b.GetFootprints()}
 for c in owners['capacitors']:
  if c['category']not in CATEGORIES:continue
  owner=c['owner'];m=src['components'][owner]
  if m['mpn']!=c['actual_owner_MPN']:raise ValueError('Actual owner MPN differs')
  if c['ref']in EXCLUDED_ADC or owner in EXCLUDED_ADC or m['source_block']in EXCLUDED_BLOCKS or not m['mpn'].startswith(CMOS_PREFIXES):continue
  for ep in [dict(ref=c['ref'],pin=c['cap_return'])]+c['return_nodes']:
   for p in byref[ep['ref']].Pads():
    if p.GetNumber()==ep['pin']and p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD:
     if p.GetNetname()!=c['actual_cap_return_net']:raise ValueError('Actual CMOS source return differs')
     eligible[p.m_Uuid.AsString()]=dict(pad=p,owner=owner,MPN=m['mpn'],capacitor=c['ref'])
 new_items={t.m_Uuid.AsString():t for t in b.GetTracks()if t.m_Uuid.AsString()in added}
 vias={u:t for u,t in new_items.items()if isinstance(t,pcbnew.PCB_VIA)};tracks={u:t for u,t in new_items.items()if isinstance(t,pcbnew.PCB_TRACK)and not isinstance(t,pcbnew.PCB_VIA)}
 groups=[];used=set();early_rejected=[]
 for u,v in vias.items():
  peers=[(tu,t)for tu,t in tracks.items()if t.GetNetname()==v.GetNetname()and tuple(t.GetEnd())==tuple(v.GetPosition())]
  if len(peers)!=1:raise ValueError('Exact one-track/one-via source stitch expected')
  tu,t=peers[0];source=[(pu,p)for pu,p in eligible.items()if p['pad'].GetNetname()==t.GetNetname()and tuple(p['pad'].GetPosition())==tuple(t.GetStart())]
  if not source:raise ValueError('New route has no verified exact native CMOS return source')
  pu,ep=source[0];p=ep['pad'];layer=p.GetParentFootprint().GetLayer();adjacent=pcbnew.In1_Cu if layer==pcbnew.F_Cu else pcbnew.In4_Cu
  if v.GetViaType()!=pcbnew.VIATYPE_THROUGH or v.GetWidth(pcbnew.F_Cu)!=pcbnew.FromMM(.5)or v.GetDrillValue()!=pcbnew.FromMM(.2)or t.GetWidth()!=pcbnew.FromMM(.2):raise ValueError('New source stitch geometry differs')
  length=math.dist(mm(t.GetStart()),mm(t.GetEnd()))
  if length>2.000001:raise ValueError('New source stitch exceeds bounded2mm')
  group=dict(reference=p.GetParentFootprint().GetReference(),pin=p.GetNumber(),source_pad_uuid=pu,return_net=p.GetNetname(),owner=ep['owner'],owner_MPN=ep['MPN'],capacitor=ep['capacitor'],adjacent_layer=b.GetLayerName(adjacent),new_copper_UUIDs=[tu,u],via_uuid=u,escape_length_mm=length,retained=True)
  if t.GetLayer()!=layer or not connected(b,p,v):
   group['retained']=False;early_rejected.append(dict(source_pad_uuid=pu,reason='Source SMD copper side/actual native pad-to-via connection differs; entire new group removed'))
  groups.append(group);used|={tu,u}
 if used!=set(added):raise ValueError('Unreviewed new native copper exists')
 a.out.mkdir(parents=True);dest=a.out/'reviewed-owned-return-stitches-candidate.kicad_pcb'
 for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(a.candidate.with_suffix(suffix),dest.with_suffix(suffix))
 for f in a.candidate.parent.iterdir():
  if f.is_dir()and(f.suffix=='.pretty'or f.name=='3dmodels'):shutil.copytree(f,a.out/f.name)
  elif f.name=='fp-lib-table':shutil.copyfile(f,a.out/f.name)
 baseline=json.loads((a.candidate.parent/'baseline.json').read_text());basekeys=collections.Counter(warning_key(v)for v in baseline['violations'])
 prior_native=a.candidate.parent/'native-0.json'
 if prior_native.is_file():
  # Prior issues may reject a new group, never accept one. Final native refill
  # still independently checks every retained object and source connection.
  byu={u:i for i,g in enumerate(groups)for u in g['new_copper_UUIDs']}
  for issue in json.loads(prior_native.read_text())['violations']:
   if issue['type']=='isolated_copper':continue
   if basekeys[warning_key(issue)]:continue
   for item in issue['items']:
    if item['uuid']in byu:groups[byu[item['uuid']]]['retained']=False
 for group in groups:
  if not group['retained']:
   for u in group['new_copper_UUIDs']:b.Remove(new_items[u])
 rejected=[]
 for attempt in range(4):
  pcbnew.SaveBoard(str(dest),b);report=drc(dest,a.out,'native-'+str(attempt));b=pcbnew.LoadBoard(str(dest));board_lifetimes.append(b);b.BuildConnectivity()
  byu={u:i for i,g in enumerate(groups)if g['retained']for u in g['new_copper_UUIDs']};counts=collections.Counter();bad=set()
  for v in report['violations']:
   key=warning_key(v);counts[key]+=1
   if v['type']=='isolated_copper'and v['severity']=='warning':continue
   if counts[key]<=basekeys[key]:continue
   touch={byu[i['uuid']]for i in v['items']if i['uuid']in byu}
   if not touch:raise ValueError('Native issue outside exact new-Cu scope '+v['type'])
   bad|=touch
  if not bad:break
  native_items={t.m_Uuid.AsString():t for t in b.GetTracks()}
  for i in bad:
   for u in groups[i]['new_copper_UUIDs']:b.Remove(native_items[u])
   groups[i]['retained']=False;rejected.append(i)
 else:raise ValueError('Bounded new-Cu rejection exceeded')
 current=cu(b);kept={u for g in groups if g['retained']for u in g['new_copper_UUIDs']}
 if set(current)!=set(old)|kept or any(current.get(u)!=v for u,v in old.items())or any(current[u]!=added[u]for u in kept)or pads(b)!=oldpads or zones(dest)!=zones(a.before):raise ValueError('Native refill changes original/new copper, source pads or zones')
 pu={p.m_Uuid.AsString():p for p in b.GetPads()};ts={t.m_Uuid.AsString():t for t in b.GetTracks()};check=ReturnCheck(b,{});proof=[]
 for g in groups:
  if not g['retained']:continue
  p=pu[g['source_pad_uuid']];via=ts[g['via_uuid']];layer=b.GetLayerID(g['adjacent_layer'])
  if not connected(b,p,via)or not covered(circle(tuple(via.GetPosition()),pcbnew.FromMM(.24)),check.reference(g['return_net'],layer)):raise ValueError('Actual owning source pad to filled adjacent reference is not closed')
  anchors=check.source_anchors(via,g['return_net'])
  if not any(v['pad_uuid']==g['source_pad_uuid']for v in anchors):raise ValueError('Actual direct source anchor missing')
  proof.append(dict(via_uuid=g['via_uuid'],source_pad_uuid=g['source_pad_uuid'],adjacent_layer=g['adjacent_layer'],actual_source_pad_anchor=True,actual_filled_reference_circle_verified=True))
 for cluster in groups_before:
  p=pu[next(iter(cluster))];new={x.m_Uuid.AsString()for x in b.GetConnectivity().GetConnectedItems(p)if isinstance(x,pcbnew.PAD)}|{p.m_Uuid.AsString()}
  if not cluster<=new:raise ValueError('Prior actual source-pad cluster fragmented')
 if any(sha(Path(p))!=h for p,h in frozen.items()):raise ValueError('Input changed during actual native review')
 isolated=[v for v in report['violations']if v['type']=='isolated_copper'];scope=dict(electrical_source_unchanged=True,reviewed_scope_reason='Exact source-owned short CMOS return stitches, actual adjacent filled-resource and numbered-source anchor proof; no original Cu/pad/zone/pose changes. All isolated fill warnings remain reported for dedicated plane cleanup.',reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(kept),reviewed_added_zone_UUIDs=[])
 write(a.out/'bounded-scope.json',scope)
 result=dict(passed=True,input_sha256=frozen,board_sha256=sha(dest),actual_owned_return_groups=groups,actual_own_source_to_adjacent_fill_proofs=proof,early_rejected_groups=early_rejected,native_rejected_group_indices=rejected,native_DRC_types=dict(collections.Counter(v['type']for v in report['violations'])),native_errors=sum(v['severity']=='error'for v in report['violations']),unresolved_isolated_fill_warnings=isolated,all_prior_source_pad_clusters_preserved=True,old_copper_source_pads_zone_definitions_preserved=True,ignored_checks=[],uncapped_missing_joins=b.GetConnectivity().GetUnconnectedCount(False),manufacturing_ready=False,global_return_ampacity_or_physical_inductance_qualified=False)
 write(a.out/'receipt.json',result);print(dict(passed=True,actual_source_owned_stitches=len(proof),native_DRC_types=result['native_DRC_types'],uncapped_missing_joins=result['uncapped_missing_joins'],board_sha256=result['board_sha256']))

if __name__=='__main__':main()
