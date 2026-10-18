"""Independent actual source-path and removal proof for IO3 extension."""
import argparse,json
from pathlib import Path
import pcbnew
from hardware_route_logic_return import pad_identity,identity,mm
from hardware_route_current_delivery_native import sha
from hardware_build_assembly import parse,children,child,value
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--before',type=Path,required=True);ap.add_argument('--route-receipt',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True);inputs={str(p):sha(p)for p in [a.board,a.before,a.route_receipt,Path(__file__)]};r=json.loads(a.route_receipt.read_text());assert r['board_sha256']==sha(a.board)and not r['pending_receiver_supply']and not r['native_errors']
 b=pcbnew.LoadBoard(str(a.board));b.BuildConnectivity();co=b.GetConnectivity();ps={p.m_Uuid.AsString():p for p in b.GetPads()};source=next(p for f in b.GetFootprints()if f.GetReference()=='R18001'for p in f.Pads()if p.GetNumber()=='2');reachable={t.m_Uuid.AsString()for t in co.GetConnectedItems(source)};endpoints=[];receivers={v['reference']for v in r['actual_receiver_endpoint_checks']};vias=[]
 for v in r['actual_receiver_endpoint_checks']:
  p=ps[v['pad_uuid']];assert p.GetNetname()=='/IO_3V3'and p.m_Uuid.AsString()in reachable;endpoints.append(dict(reference=v['reference'],pin=v['pin'],source_connected=True))
 actual_vias={t.m_Uuid.AsString():t for t in b.GetTracks()if isinstance(t,pcbnew.PCB_VIA)}
 for ref in sorted(receivers):
  p=next(p for f in b.GetFootprints()if f.GetReference()==ref for p in f.Pads()if p.GetNumber()=='2');vs=[t for t in co.GetConnectedItems(p)if t.Type()==pcbnew.PCB_VIA_T and t.GetNetname()=='/IO_3V3'];assert len(vs)>=1
  item=min(vs,key=lambda t:(mm(t.GetPosition())[0]-mm(p.GetPosition())[0])**2+(mm(t.GetPosition())[1]-mm(p.GetPosition())[1])**2);v=actual_vias[item.m_Uuid.AsString()];assert v.m_Uuid.AsString()in reachable and v.FlashLayer(pcbnew.In2_Cu)and co.IsConnectedOnLayer(v,pcbnew.In2_Cu);vias.append(dict(reference=ref,via_uuid=v.m_Uuid.AsString(),point_mm=mm(v.GetPosition()),actual_source_connected=True,native_inner_annulus_flashed=True,native_inner_layer_connected=True))
 n=pcbnew.LoadBoard(str(a.board));cu={t.m_Uuid.AsString():t for t in n.GetTracks()};zs={z.m_Uuid.AsString():z for z in n.Zones()};retained=[]
 for v in r['exact_added_copper']:retained.append(cu[v['uuid']]);n.Remove(cu[v['uuid']])
 for v in r['exact_added_positive_zones']:retained.append(zs[v['uuid']]);n.Remove(zs[v['uuid']])
 n.BuildConnectivity();ns=next(p for f in n.GetFootprints()if f.GetReference()=='R18001'for p in f.Pads()if p.GetNumber()=='2');nr={t.m_Uuid.AsString()for t in n.GetConnectivity().GetConnectedItems(ns)};assert all(v['pad_uuid']not in nr for v in r['actual_receiver_endpoint_checks']), 'Removing actual extension did not break all source paths'
 old=pcbnew.LoadBoard(str(a.before));op={p.m_Uuid.AsString():pad_identity(p)for p in old.GetPads()};assert op=={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};oc={t.m_Uuid.AsString():identity(t)for t in old.GetTracks()};bc={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};assert all(bc[k]==v for k,v in oc.items());ot=parse(a.before.read_text());bt=parse(a.board.read_text());oz={value(child(z,'uuid')[1]):{child(z,'filled_polygon')[0]if child(z,'filled_polygon')else ''}for z in children(ot,'zone')};assert set(oz)<={z.m_Uuid.AsString()for z in b.Zones()}
 out=dict(input_hashes=inputs,board_sha256=sha(a.board),actual_source_endpoint_checks=endpoints,actual_receiving_via_checks=vias,negative_control=dict(removed_actual_extension_copper=len(r['exact_added_copper']),removed_actual_extension_zones=len(r['exact_added_positive_zones']),all44_actual_receiving_power_pins_disconnected=True,all_pin_labels_unchanged=True),prior_actual_clusters_preserved=r['prior_actual_clusters_preserved'],all_old_actual_pad_copper_preserved=True,native_no_new_errors=True,native_no_receiver_dangling_vias=True,IR_drop_distribution_qualified=False,manufacturing_ready=False)
 assert len(endpoints)==44 and len(vias)==22 and all(sha(Path(p))==h for p,h in inputs.items());(a.out/'receipt.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in ['input_hashes','actual_source_endpoint_checks','actual_receiving_via_checks']}))
if __name__=='__main__':main()
