"""Independent native local motor-supply proof and nine physical cut controls."""
import argparse,json,hashlib
from pathlib import Path
import pcbnew
from hardware_route_logic_return import identity,pad_identity
from hardware_populate_motherboard_pcb import footprint_name
from hardware_build_assembly import parse,children,child,value,dump

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--before',type=Path,required=True);ap.add_argument('--board',type=Path,required=True);ap.add_argument('--receipt',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True);frozen={str(p):sha(p)for p in [a.before,a.board,a.receipt,Path(__file__)]};r=json.loads(a.receipt.read_text());assert not r['native_errors']and sha(a.board)==r['board_sha256'];old=pcbnew.LoadBoard(str(a.before));old.BuildConnectivity();b=pcbnew.LoadBoard(str(a.board));b.BuildConnectivity();co=b.GetConnectivity();of={f.GetReference():f for f in old.GetFootprints()};nf={f.GetReference():f for f in b.GetFootprints()};assert set(of)==set(nf);moved={'C11057','C11058','C11060'};oldcu={t.m_Uuid.AsString():identity(t)for t in old.GetTracks()};newcu={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};assert set(oldcu)<=set(newcu)and all(newcu[k]==v for k,v in oldcu.items());ps={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()if p.GetNumber()};prior_count=0;seen=set();newuid={p.m_Uuid.AsString():p for p in b.GetPads()}
 for ref,f in of.items():
  d=nf[ref];assert footprint_name(f)==footprint_name(d);assert {(p.GetNumber(),p.m_Uuid.AsString(),p.GetNetname())for p in f.Pads()}=={(p.GetNumber(),p.m_Uuid.AsString(),p.GetNetname())for p in d.Pads()}
  if ref not in moved:assert {p.m_Uuid.AsString():pad_identity(p)for p in f.Pads()}=={p.m_Uuid.AsString():pad_identity(p)for p in d.Pads()}
 for p in old.GetPads():
  uid=p.m_Uuid.AsString()
  if uid in seen:continue
  group={uid}|{t.m_Uuid.AsString()for t in old.GetConnectivity().GetConnectedItems(p)if t.Type()==pcbnew.PCB_PAD_T};seen|=group
  if len(group)<2:continue
  newgroup={uid}|{t.m_Uuid.AsString()for t in co.GetConnectedItems(newuid[uid])if t.Type()==pcbnew.PCB_PAD_T};assert group<=newgroup,('Old fitted pad cluster lost',uid);prior_count+=1
 checks=[]
 for row in r['actual_owner_endpoint_checks']:
  p,q=ps[row['owner'],row['owner_pin']],ps[row['capacitor'],row['capacitor_pin']];assert p.GetNetname()==q.GetNetname()==row['net'];assert q.m_Uuid.AsString()in{t.m_Uuid.AsString()for t in co.GetConnectedItems(p)};checks.append(row)
 assert len(checks)==24
 negatives=[];retained=[]
 cuts=[('U600'+str(k),'16','C600'+str(k),'1','U600'+str(k)+'_VCC16_bypass')for k in range(1,7)]+[('U11010','3','C11057','1','C11057_actual_owner_bypass_branch'),('U11010','9','C11058','1','C11058_actual_owner_bypass_branch'),('U11011','9','C11060','1','C11060_actual_owner_bypass_branch')]
 for owner,pin,cap,cp,role in cuts:
  n=pcbnew.LoadBoard(str(a.board));tracks={t.m_Uuid.AsString():t for t in n.GetTracks()};zones={z.m_Uuid.AsString():z for z in n.Zones()};np={(f.GetReference(),p.GetNumber()):p for f in n.GetFootprints()for p in f.Pads()if p.GetNumber()};prefix=owner if owner.startswith('U600')else cap;net=np[owner,pin].GetNetname();ids=[v['uuid']for v in r['new_copper']if v['role'].startswith(prefix+'_')and tracks[v['uuid']].GetNetname()==net];zids=[v['uuid']for v in r['new_zones']if v['role'].startswith(prefix+'_')and v['net']==net];assert ids;retained.append((n,tracks,np,zones))
  for uid in ids:n.Remove(tracks[uid])
  for uid in zids:n.Remove(zones[uid])
  n.BuildConnectivity();nc=n.GetConnectivity();retained[-1]+=(nc,);p,q=np[owner,pin],np[cap,cp];assert p.GetNetname()==q.GetNetname();assert q.m_Uuid.AsString()not in{t.m_Uuid.AsString()for t in nc.GetConnectedItems(p)},('Cut did not disconnect actual source',role);negatives.append(dict(owner=owner,pin=pin,capacitor=cap,actual_removed_copper=ids,actual_removed_local_positive_zones=zids,labels_unchanged=True,source_disconnected=True))
 ot,nt=parse(a.before.read_text()),parse(a.board.read_text());oz={value(child(z,'uuid')[1]):dump([v for v in z if not(isinstance(v,list)and v[0]in ['filled_polygon','fill_segments'])])for z in children(ot,'zone')};nz={value(child(z,'uuid')[1]):dump([v for v in z if not(isinstance(v,list)and v[0]in ['filled_polygon','fill_segments'])])for z in children(nt,'zone')};assert set(oz)<=set(nz)and all(nz[k]==v for k,v in oz.items());scope=dict(electrical_source_unchanged=True,reviewed_scope_reason='Six actual AM26C31 owner bypass/return cells and three source-existing TPS22990 cap physical corrections; exact source-derived field exclusions; no previous copper retired or unrelated fitted clusters changed',reviewed_footprint_references=sorted(moved),reviewed_copper_delta_UUIDs=sorted(set(newcu)-set(oldcu)),reviewed_added_zone_UUIDs=sorted(set(nz)-set(oz)));(a.out/'bounded-scope.json').write_text(json.dumps(scope,indent=2)+'\n');result=dict(input_hashes=frozen,board_sha256=sha(a.board),prior_actual_fitted_pad_clusters_preserved=prior_count,actual_owner_checks=checks,actual_copper_cut_negative_controls=negatives,added_copper=len(newcu)-len(oldcu),added_own_local_zones=len(nz)-len(oz),exact_moved_parts=sorted(moved),native_errors=0,native_uncapped_joins=co.GetUnconnectedCount(False),all_old_copper_and_source_pin_maps_preserved=True,current_delivery_or_loop_inductance_qualified=False,manufacturing_ready=False);assert all(sha(Path(p))==h for p,h in frozen.items());(a.out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['input_hashes','actual_owner_checks','actual_copper_cut_negative_controls']}))
if __name__=='__main__':main()
