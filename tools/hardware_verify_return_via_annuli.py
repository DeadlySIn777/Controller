"""Independent native flash/layer connection checks on exact return stitches."""
import argparse,json
from pathlib import Path
import pcbnew
from hardware_populate_motherboard_pcb import sha,write

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('board','receipt','out'):p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args()
 if a.out.exists():raise ValueError('Fresh native evidence required')
 receipt=json.loads(a.receipt.read_text());expected=receipt['board_sha256']
 if sha(a.board)!=expected:raise ValueError('Actual frozen return board differs')
 b=pcbnew.LoadBoard(str(a.board.resolve()));b.BuildConnectivity();conn=b.GetConnectivity()
 vias={t.m_Uuid.AsString():t for t in b.GetTracks()if isinstance(t,pcbnew.PCB_VIA)}
 pads={p.m_Uuid.AsString():p for p in b.GetPads()};rows=[]
 for group in receipt['actual_owned_return_groups']:
  if not group['retained']:continue
  v=vias[group['via_uuid']];pad=pads[group['source_pad_uuid']];layer=b.GetLayerID(group['adjacent_layer'])
  anchors={p.m_Uuid.AsString()for p in conn.GetConnectedItems(v)if isinstance(p,pcbnew.PAD)}
  same=pad.GetNetname()==v.GetNetname()==group['return_net']
  flashed=bool(v.FlashLayer(layer));connected=bool(conn.IsConnectedOnLayer(v,layer))
  rows.append(dict(via_uuid=group['via_uuid'],source_pad_uuid=group['source_pad_uuid'],reference_layer=group['adjacent_layer'],actual_numbered_source_anchor=group['source_pad_uuid']in anchors,exact_own_net=same,actual_annulus_flashed=flashed,actual_native_layer_connection=connected,passed=bool(same and flashed and connected and group['source_pad_uuid']in anchors)))
 result=dict(passed=all(r['passed']for r in rows)and bool(rows),board_sha256=sha(a.board),receipt_sha256=sha(a.receipt),tool_sha256=sha(Path(__file__)),actual_native_checked=len(rows),failed_rows=[r for r in rows if not r['passed']],rows=rows,manufacturing_ready=False,global_return_ampacity_or_physical_measurements_qualified=False)
 write(a.out,result);print(json.dumps({k:v for k,v in result.items()if k not in ['rows','failed_rows']}));print(json.dumps(result['failed_rows'][:3]));raise SystemExit(not result['passed'])

if __name__=='__main__':main()
