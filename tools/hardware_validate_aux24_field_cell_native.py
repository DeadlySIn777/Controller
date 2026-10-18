"""Independent native seven-part AUX24 field-cell preservation and physical cuts."""
import argparse,json,hashlib
from pathlib import Path
import pcbnew
from hardware_route_logic_return import identity,pad_identity
from hardware_populate_motherboard_pcb import footprint_name
from hardware_build_assembly import parse,children,child,value,dump

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--before',type=Path,required=True);ap.add_argument('--board',type=Path,required=True);ap.add_argument('--receipt',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True)
 frozen={str(p):sha(p)for p in[a.before,a.board,a.receipt,Path(__file__)]};r=json.loads(a.receipt.read_text());assert r['board_sha256']==sha(a.board)and not r['native_errors'];assert not r['exact_added_zones']
 moved={'U11015','R11056','R11057','R11058','C11068','C11069','C11070'};old=pcbnew.LoadBoard(str(a.before));old.BuildConnectivity();b=pcbnew.LoadBoard(str(a.board));b.BuildConnectivity();co=b.GetConnectivity();of={f.GetReference():f for f in old.GetFootprints()};nf={f.GetReference():f for f in b.GetFootprints()};assert set(of)==set(nf)
 op={p.m_Uuid.AsString():p for p in old.GetPads()};np={p.m_Uuid.AsString():p for p in b.GetPads()};assert set(op)==set(np);ps={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()if p.GetNumber()}
 for ref,f in of.items():
  q=nf[ref];assert footprint_name(f)==footprint_name(q);assert {(p.GetNumber(),p.m_Uuid.AsString(),p.GetNetname())for p in f.Pads()}=={(p.GetNumber(),p.m_Uuid.AsString(),p.GetNetname())for p in q.Pads()}
  if ref not in moved:assert {p.m_Uuid.AsString():pad_identity(p)for p in f.Pads()}=={p.m_Uuid.AsString():pad_identity(p)for p in q.Pads()}
 oldcu={t.m_Uuid.AsString():json.loads(json.dumps(identity(t)))for t in old.GetTracks()};newcu={t.m_Uuid.AsString():json.loads(json.dumps(identity(t)))for t in b.GetTracks()};retired={v['uuid']for v in r['exact_retired_private_copper']};added={v['uuid']for v in r['exact_added_copper']};assert len(retired)==4;assert set(oldcu)-set(newcu)==retired and set(newcu)-set(oldcu)==added;assert all(newcu[k]==v for k,v in oldcu.items()if k not in retired)
 for v in r['exact_retired_private_copper']:assert v['identity']==oldcu[v['uuid']];assert v['identity'][1]=='/motherboard_power_entry/AUX24_A_RTN'
 for v in r['exact_added_copper']:assert v['identity']==newcu[v['uuid']]
 prior=0;seen=set()
 for uid,p in op.items():
  if uid in seen:continue
  group={uid}|{t.m_Uuid.AsString()for t in old.GetConnectivity().GetConnectedItems(p)if t.Type()==pcbnew.PCB_PAD_T};seen|=group
  if len(group)<2:continue
  after={uid}|{t.m_Uuid.AsString()for t in co.GetConnectedItems(np[uid])if t.Type()==pcbnew.PCB_PAD_T};assert group<=after;prior+=1
 checks=[]
 for row in r['actual_local_endpoint_checks']:
  p,q=ps[row['from_ref'],row['from_pin']],ps[row['to_ref'],row['to_pin']];assert p.GetNetname()==q.GetNetname();assert q.m_Uuid.AsString()in{t.m_Uuid.AsString()for t in co.GetConnectedItems(p)};checks.append(row)
 assert ps['U11015','11'].GetNetname()!=ps['U11015','6'].GetNetname();negatives=[];alive=[]
 for owner,opn,target,tp in [('U11015','1','C11069','1'),('U11015','10','C11070','1'),('U11015','6','C11069','2'),('U11015','6','C11070','2'),('U11015','2','R11057','2'),('U11015','9','R11058','2'),('U11015','7','R11056','1'),('U11015','8','C11068','1'),('U11015','11','R11056','2')]:
  n=pcbnew.LoadBoard(str(a.board));tracks={t.m_Uuid.AsString():t for t in n.GetTracks()};pmap={(f.GetReference(),p.GetNumber()):p for f in n.GetFootprints()for p in f.Pads()if p.GetNumber()};p,q=pmap[owner,opn],pmap[target,tp];net=p.GetNetname();ids=[uid for uid in added if tracks[uid].GetNetname()==net];assert ids
  alive.append((n,tracks,pmap))
  for uid in ids:n.Remove(tracks[uid])
  n.BuildConnectivity();nc=n.GetConnectivity();alive[-1]+=(nc,);assert p.GetNetname()==q.GetNetname();assert q.m_Uuid.AsString()not in{t.m_Uuid.AsString()for t in nc.GetConnectedItems(p)},('Physical cut failed',owner,opn,target,tp)
  negatives.append(dict(owner=owner,owner_pin=opn,target=target,target_pin=tp,net=net,removed_new_copper=sorted(ids),labels_unchanged=True,actual_source_disconnected=True))
 def zones(path):
  return {value(child(z,'uuid')[1]):dump([v for v in z if not(isinstance(v,list)and v[0]in['filled_polygon','fill_segments'])])for z in children(parse(path.read_text()),'zone')}
 assert zones(a.before)==zones(a.board);assert a.before.with_suffix('.kicad_dru').read_bytes()==a.board.with_suffix('.kicad_dru').read_bytes();vias=[t for t in b.GetTracks()if t.m_Uuid.AsString()in added and isinstance(t,pcbnew.PCB_VIA)];assert all(pcbnew.ToMM(v.GetWidth(pcbnew.F_Cu))==.5 and pcbnew.ToMM(v.GetDrill())==.2 and v.GetIsFree()for v in vias)
 result=dict(input_hashes=frozen,board_sha256=sha(a.board),exact_moved_parts=sorted(moved),exact_retired_private_copper=sorted(retired),added_copper=len(added),added_zones=0,actual_prior_source_clusters_preserved=prior,actual_local_endpoint_checks=checks,physical_copper_cut_negative_controls=negatives,all_unrelated_copper_pad_identities_preserved=True,source_pins_MPNs_manufacturer_lands_unchanged=True,all_new_vias_conventional_050_020=True,native_errors=0,native_uncapped_joins=co.GetUnconnectedCount(False),external_field_feeds_pending=r['external_feed_routing_pending'],physical_loaded_or_thermal_qualified=False,manufacturing_ready=False)
 assert all(sha(Path(p))==h for p,h in frozen.items());(a.out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in['input_hashes','actual_local_endpoint_checks','physical_copper_cut_negative_controls']}))
if __name__=='__main__':main()
