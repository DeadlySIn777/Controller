"""Independent physical entry-feed checks and route-cut negative controls."""
import argparse,hashlib,json,collections
from pathlib import Path
import pcbnew
from hardware_route_logic_return import identity,pad_identity
from hardware_populate_motherboard_pcb import footprint_name
from hardware_build_assembly import children,child,value,parse
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--before',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--route-receipts',type=Path,nargs='+',required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True);frozen={str(p):sha(p)for p in [a.board,a.before,*a.route_receipts]};frozen[str(Path(__file__))]=sha(Path(__file__));routes={}
 for path in a.route_receipts:
  for r in json.loads(path.read_text())['routes']:
   if not r.get('already_connected_before'):assert r['name']not in routes;routes[r['name']]=r
 assert len(routes)==9,routes.keys()
 b=pcbnew.LoadBoard(str(a.board));b.BuildConnectivity();co=b.GetConnectivity();ps={p.m_Uuid.AsString():p for p in b.GetPads()};native=[];negative=[];retained_negative_boards=[]
 for name,r in routes.items():
  p,q=ps[r['from_pad_uuid']],ps[r['to_pad_uuid']];assert p.GetNetname()==q.GetNetname()==r['net'];assert q.m_Uuid.AsString()in{t.m_Uuid.AsString()for t in co.GetConnectedItems(p)},name;native.append(dict(name=name,from_pad=p.m_Uuid.AsString(),to_pad=q.m_Uuid.AsString(),net=r['net']))
  n=pcbnew.LoadBoard(str(a.board));new={t.m_Uuid.AsString():t for t in n.GetTracks()};np={p.m_Uuid.AsString():p for p in n.GetPads()};retained_negative_boards.append((n,new,np));assert set(r['added_uuids'])<=set(new)
  for uid in r['added_uuids']:n.Remove(new[uid])
  n.BuildConnectivity();nc=n.GetConnectivity();retained_negative_boards[-1]+=(nc,);assert np[p.m_Uuid.AsString()].GetNetname()==np[q.m_Uuid.AsString()].GetNetname()==r['net'];reachable={t.m_Uuid.AsString()for t in nc.GetConnectedItems(np[p.m_Uuid.AsString()])};assert q.m_Uuid.AsString()not in reachable,'Physical route removal did not break '+name
  negative.append(dict(name=name,removed_actual_copper=len(r['added_uuids']),pin_net_labels_unchanged=True,source_to_target_physically_disconnected=True))
 old=pcbnew.LoadBoard(str(a.before));old.BuildConnectivity();bf={f.GetReference():f for f in old.GetFootprints()};df={f.GetReference():f for f in b.GetFootprints()};assert bf.keys()==df.keys();oldcu={t.m_Uuid.AsString():identity(t)for t in old.GetTracks()};newcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};removed=set(oldcu)-set(newcu);assert removed=={'7a3bb22d-b7b2-431e-a97d-9e288621d9fa'};assert oldcu[next(iter(removed))][1]=='/motherboard_power_entry/C_RAW';assert all(oldcu[k]==newcu[k]for k in oldcu if k not in removed)
 for ref,f in bf.items():
  d=df[ref];assert footprint_name(f)==footprint_name(d);assert {(p.GetNumber(),p.m_Uuid.AsString(),p.GetNetname())for p in f.Pads()}=={(p.GetNumber(),p.m_Uuid.AsString(),p.GetNetname())for p in d.Pads()}
  if ref!='F11001':assert {p.m_Uuid.AsString():pad_identity(p)for p in f.Pads()}=={p.m_Uuid.AsString():pad_identity(p)for p in d.Pads()}
 oldtree=parse(a.before.read_text());newtree=parse(a.board.read_text());oz={value(child(z,'uuid')[1])for z in children(oldtree,'zone')};nz={value(child(z,'uuid')[1])for z in children(newtree,'zone')};assert oz<=nz
 scope=dict(electrical_source_unchanged=True,reviewed_scope_reason='Manufacturer-land-reconciled source26 prerequisite; exact CORE fuse service move and actual current entry delivery for all three independently fused entries; old pin2-only bridge retired, all unrelated actual copper and pad identities preserved',reviewed_footprint_references=['F11001'],reviewed_copper_delta_UUIDs=sorted(removed|(set(newcu)-set(oldcu))),reviewed_added_zone_UUIDs=sorted(nz-oz))
 (a.out/'bounded-scope.json').write_text(json.dumps(scope,indent=2)+'\n');result=dict(input_hashes=frozen,board_sha256=sha(a.board),manufacturer_geometry_before_required=True,source26_required_before_parent_merge=True,actual_entry_endpoint_checks=native,physical_route_cut_negative_controls=negative,exact_removed_copper={k:oldcu[k]for k in removed},added_copper=len(set(newcu)-set(oldcu)),new_RAW_transition_zones=len(nz-oz),all_other_part_pad_copper_preserved=True,uncapped_joins=co.GetUnconnectedCount(False),ampacity_delivery_qualified=False)
 assert all(sha(Path(p))==h for p,h in frozen.items());(a.out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['input_hashes','actual_entry_endpoint_checks','physical_route_cut_negative_controls','exact_removed_copper']}))
if __name__=='__main__':main()
