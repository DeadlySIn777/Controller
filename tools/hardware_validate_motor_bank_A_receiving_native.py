"""Independent native Bank A source/lands/Cu invariants and physical cut controls."""
import argparse,json,hashlib
from pathlib import Path
import pcbnew
import sys
sys.path.insert(0,str(Path('tools').resolve()))
from hardware_route_logic_return import identity,pad_identity,xy
from hardware_populate_motherboard_pcb import footprint_name,pad_template
from hardware_build_assembly import parse,children,child,value,dump

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def j(v):return json.loads(json.dumps(v))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--before',type=Path,required=True);ap.add_argument('--board',type=Path,required=True);ap.add_argument('--receipt',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True);hashes={str(p):sha(p)for p in[a.before,a.board,a.receipt,Path(__file__),Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml')]};r=json.loads(a.receipt.read_text());assert not r['native_errors']and r['board_sha256']==sha(a.board)
 old=pcbnew.LoadBoard(str(a.before));old.BuildConnectivity();b=pcbnew.LoadBoard(str(a.board));b.BuildConnectivity();co=b.GetConnectivity();of={f.GetReference():f for f in old.GetFootprints()};nf={f.GetReference():f for f in b.GetFootprints()};assert set(of)==set(nf);moved=set(r['new_poses']);assert len(moved)==23
 op={p.m_Uuid.AsString():p for p in old.GetPads()};np={p.m_Uuid.AsString():p for p in b.GetPads()};assert set(op)==set(np);oldcu={t.m_Uuid.AsString():j(identity(t))for t in old.GetTracks()};newcu={t.m_Uuid.AsString():j(identity(t))for t in b.GetTracks()};retired={v['uuid']for v in r['exact_retired_copper']};added={v['uuid']for v in r['exact_added_copper']};assert set(oldcu)-set(newcu)==retired and set(newcu)-set(oldcu)==added;assert all(newcu[k]==v for k,v in oldcu.items()if k not in retired)
 for row in r['exact_retired_copper']:assert row['identity']==oldcu[row['uuid']]
 for row in r['exact_added_copper']:assert row['identity']==newcu[row['uuid']]
 # Cache exact BEFORE source membership prior to normalizing copied old lands.
 groups=[];seen=set()
 for uid,p in op.items():
  if uid in seen:continue
  group={uid}|{t.m_Uuid.AsString()for t in old.GetConnectivity().GetConnectedItems(p)if t.Type()==pcbnew.PCB_PAD_T};seen|=group
  if len(group)>1:groups.append((uid,group))
 for uid,group in groups:
  reach={uid}|{t.m_Uuid.AsString()for t in co.GetConnectedItems(np[uid])if t.Type()==pcbnew.PCB_PAD_T};assert group<=reach,('Actual BEFORE source cluster lost',uid)
 lands=0
 for ref,f in of.items():
  q=nf[ref];assert footprint_name(f)==footprint_name(q);assert f.GetValue()==q.GetValue();assert {v.GetName():v.GetText()for v in f.GetFields()}=={v.GetName():v.GetText()for v in q.GetFields()};assert {(p.GetNumber(),p.m_Uuid.AsString(),p.GetNetname())for p in f.Pads()}=={(p.GetNumber(),p.m_Uuid.AsString(),p.GetNetname())for p in q.Pads()}
  if ref not in moved:assert {p.m_Uuid.AsString():pad_identity(p)for p in f.Pads()}=={p.m_Uuid.AsString():pad_identity(p)for p in q.Pads()}
  else:
   pose=r['new_poses'][ref]
   if f.GetLayer()!=q.GetLayer():assert ref.startswith('C');f.Flip(f.GetPosition(),False)
   f.SetPosition(xy(pose['point_mm']));f.SetOrientationDegrees(pose['angle'])
   assert {p.m_Uuid.AsString():j(pad_template(p))for p in f.Pads()}=={p.m_Uuid.AsString():j(pad_template(p))for p in q.Pads()},('Manufacturer local lands changed',ref)
   assert {p.m_Uuid.AsString():pad_identity(p)for p in f.Pads()}=={p.m_Uuid.AsString():pad_identity(p)for p in q.Pads()}
   lands+=1
 ps={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()if p.GetNumber()};checks=[]
 for row in r['actual_endpoint_checks']:
  p,q=ps[row['from_ref'],row['from_pin']],ps[row['to_ref'],row['to_pin']];assert p.GetNetname()==q.GetNetname();assert q.m_Uuid.AsString()in{t.m_Uuid.AsString()for t in co.GetConnectedItems(p)};checks.append(row)
 # Exact SOURCE circuit: neither a name nor a power flag can substitute for a pad path.
 for endpoint in [('U11010','3','C11046','1'),('U11010','4','C11046','1'),('U11010','11','C11046','1'),('U11010','6','C11046','2'),('U11032','8','C11046','1'),('U11032','5','U11010','5'),('R11042','2','C11046','2'),('U11010','7','R11043','2'),('R11043','1','R18001','2')]:
  rr,pp,ss,qq=endpoint;p,q=ps[rr,pp],ps[ss,qq];assert p.GetNetname()==q.GetNetname();assert q.m_Uuid.AsString()in{t.m_Uuid.AsString()for t in co.GetConnectedItems(p)};checks.append(dict(from_ref=rr,from_pin=pp,to_ref=ss,to_pin=qq,role='independent_source_contract'))
 def zone_defs(path):return {value(child(z,'uuid')[1]):dump([v for v in z if not(isinstance(v,list)and v[0]in ['filled_polygon','fill_segments'])])for z in children(parse(path.read_text()),'zone')}
 assert zone_defs(a.before)==zone_defs(a.board);assert a.before.with_suffix('.kicad_dru').read_bytes()==a.board.with_suffix('.kicad_dru').read_bytes()
 newvias=[v for v in b.GetTracks()if v.m_Uuid.AsString()in added and isinstance(v,pcbnew.PCB_VIA)];assert all(pcbnew.ToMM(v.GetWidth(pcbnew.F_Cu))==.5 and pcbnew.ToMM(v.GetDrill())==.2 and v.GetIsFree()and not v.GetRemoveUnconnected()for v in newvias)
 negatives=[];alive=[]
 for owner,pin,target,tp in [('U11032','5','U11010','5'),('U11031','4','U11032','1'),('U11021','4','U11027','3'),('U11027','4','U11032','6'),('U11022','4','U11028','3'),('U11022','2','U11020','6'),('R11067','1','C11088','1'),('R11071','1','C11055','1'),('U11010','9','C11058','1'),('U11032','8','C11046','1'),('C11083','2','U11032','4')]:
  n=pcbnew.LoadBoard(str(a.board));nt={v.m_Uuid.AsString():v for v in n.GetTracks()};pm={(f.GetReference(),p.GetNumber()):p for f in n.GetFootprints()for p in f.Pads()if p.GetNumber()};p,q=pm[owner,pin],pm[target,tp];net=p.GetNetname();assert net==q.GetNetname();ids=[uid for uid in added if nt[uid].GetNetname()==net];assert ids;alive.append((n,nt,pm))
  for uid in ids:n.Remove(nt[uid])
  n.BuildConnectivity();nc=n.GetConnectivity();alive[-1]+=(nc,);assert q.m_Uuid.AsString()not in{v.m_Uuid.AsString()for v in nc.GetConnectedItems(p)},('Physical cut did not disconnect SOURCE',owner,pin,target,tp)
  negatives.append(dict(owner=owner,owner_pin=pin,target=target,target_pin=tp,net=net,removed_added_copper=ids,all_labels_unchanged=True,actual_source_disconnected=True))
 scope=json.loads(a.receipt.with_name('bounded-scope.json').read_text());assert set(scope['reviewed_copper_delta_UUIDs'])==added|retired;assert set(scope['reviewed_footprint_references'])==moved and not scope['reviewed_added_zone_UUIDs']
 assert all(sha(Path(p))==h for p,h in hashes.items());out=dict(input_hashes=hashes,board_sha256=sha(a.board),all_old_source_clusters_preserved=len(groups),exact_manufacturer_lands_after_only_declared_moves=lands,all_unrelated_pad_copper_zone_definitions_unchanged=True,added_copper=len(added),retired_literal_copper=len(retired),new_conventional_vias=len(newvias),actual_source_endpoint_checks=checks,physical_cut_negative_controls=negatives,native_errors=0,native_uncapped_joins=co.GetUnconnectedCount(False),global_control_reference_current_thermal_qualification=False,manufacturing_ready=False);(a.out/'receipt.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in['input_hashes','actual_source_endpoint_checks','physical_cut_negative_controls']}),flush=True)
if __name__=='__main__':main()
