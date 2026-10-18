"""Independent native preservation and actual foreign-barrel checks."""
import argparse,json,math
from pathlib import Path
import pcbnew
from hardware_route_current_delivery_native import sha
from hardware_route_logic_return import identity,pad_identity,xy,mm,distance
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--before',type=Path,required=True);ap.add_argument('--route-receipt',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True);inputs={str(p):sha(p)for p in [a.board,a.before,a.route_receipt,Path(__file__)]};r=json.loads(a.route_receipt.read_text());assert r['board_sha256']==sha(a.board)
 old=pcbnew.LoadBoard(str(a.before));old.BuildConnectivity();b=pcbnew.LoadBoard(str(a.board));b.BuildConnectivity();co=b.GetConnectivity();oldcu={t.m_Uuid.AsString():identity(t)for t in old.GetTracks()};cu={t.m_Uuid.AsString():t for t in b.GetTracks()};pads={p.m_Uuid.AsString():p for p in b.GetPads()};assert {p.m_Uuid.AsString():pad_identity(p)for p in old.GetPads()}=={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};removed=set(oldcu)-set(cu);assert removed==set(r['exact_retired_copper']);assert all(identity(cu[k])==v for k,v in oldcu.items()if k not in removed)
 count=0;seen=set()
 for p in old.GetPads():
  uid=p.m_Uuid.AsString()
  if uid in seen:continue
  group={uid}|{t.m_Uuid.AsString()for t in old.GetConnectivity().GetConnectedItems(p)if t.Type()==pcbnew.PCB_PAD_T};seen|=group
  if len(group)>1:assert group<=({uid}|{t.m_Uuid.AsString()for t in co.GetConnectedItems(pads[uid])if t.Type()==pcbnew.PCB_PAD_T});count+=1
 barrel1=(398.245074,138.401818);barrel2=(376.825,145.0);newtracks=[cu[v['uuid']]for v in r['exact_added_copper']];gap1=min(distance(barrel1,mm(t.GetStart()),mm(t.GetEnd()))-pcbnew.ToMM(t.GetWidth())/2-.25 for t in newtracks);assert gap1>=.6
 z=next(z for z in b.Zones()if z.m_Uuid.AsString()==r['exact_new_zone_uuid']);gap2=pcbnew.ToMM(z.GetFilledPolysList(pcbnew.B_Cu).Distance(xy(barrel2)))-.25;assert gap2>=.6
 negative=[]
 for name,pt in [('C6032',barrel1),('C17013',barrel2)]:
  actual_old_gap=min(distance(pt,(v[2][0]/1e6,v[2][1]/1e6),(v[3][0]/1e6,v[3][1]/1e6))-v[5]/2e6-.25 for v in r['exact_retired_copper'].values());assert actual_old_gap<0;negative.append(dict(actual_source_barrel=name,restoring_retired_copper_at_same_net_physically_shorts=True,old_actual_copper_edge_gap_mm=actual_old_gap,source_labels_unchanged=True))
 out=dict(input_hashes=inputs,board_sha256=sha(a.board),actual_nine_source_endpoint_checks=r['actual_nine_entry_endpoint_checks'],prior_native_actual_pad_clusters_preserved=count,all_source_pads_unrelated_copper_preserved=True,actual_C6032_barrel_clearance_mm=gap1,actual_C17013_barrel_clearance_mm=gap2,original_trunk_restoration_negative_controls=negative,source_contract_foreign_barrel_minimum_mm=.6,current_and_drop_screens=r['current_screen_note'],C17013_actual_minimum_total_parallel_width_mm=r['C17013_minimum_actual_total_ligament_width_mm'],prototype_current_screen_only=True,physical_current_delivery_qualified=False)
 assert all(sha(Path(p))==h for p,h in inputs.items());(a.out/'receipt.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in ['input_hashes','actual_nine_source_endpoint_checks']}))
if __name__=='__main__':main()
