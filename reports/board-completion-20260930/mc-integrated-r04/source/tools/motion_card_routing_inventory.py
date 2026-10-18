"""Read all native physical copper clusters, independently of capped DRC output."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import pcbnew


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board',type=Path,required=True);parser.add_argument('--netlist',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True);a=parser.parse_args()
    hashes={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in (a.board,a.netlist)}
    tree=ET.parse(a.netlist);native={};nc=set()
    for net in tree.findall('.//nets/net'):
        for node in net.findall('node'):
            key=(node.attrib['ref'],node.attrib['pin']);native[key]=net.attrib['name']
            if 'no_connect' in node.attrib.get('pintype',''):nc.add(key)
    board=pcbnew.LoadBoard(str(a.board.resolve()));board.BuildConnectivity();conn=board.GetConnectivity()
    by_net={};errors=[];fitted={}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            key=(fp.GetReference(),pad.GetNumber());fitted[key]=pad
            if pad.GetNetname()!=native.get(key):errors.append('Native source/PCB net mismatch '+repr(key))
            if key not in nc:by_net.setdefault(pad.GetNetname(),[]).append(pad)
    rows=[]
    for name,pads in sorted(by_net.items()):
        groups={}
        for pad in pads:
            items=list(conn.GetConnectedItems(pad))
            ids=tuple(sorted(i.m_Uuid.AsString() for i in items if i.Type()==pcbnew.PCB_PAD_T))
            if not ids or pad.m_Uuid.AsString() not in ids:errors.append('Invalid physical source-pad cluster '+name)
            groups.setdefault(ids,[]).append(pad.GetParentFootprint().GetReference()+'.'+pad.GetNumber())
        rows.append({'net':name,'source_pad_count':len(pads),'physical_pad_clusters':len(groups),
                     'missing_cluster_joins':max(0,len(groups)-1),
                     'all_fitted_source_pads_joined':len(groups)==1,'clusters':list(groups.values())})
    orphan=[]
    for track in board.GetTracks():
        if not any(i.Type()==pcbnew.PCB_PAD_T for i in conn.GetConnectedItems(track)):
            orphan.append(track.m_Uuid.AsString())
    uncapped=conn.GetUnconnectedCount(False);cluster_total=sum(r['missing_cluster_joins'] for r in rows)
    if uncapped!=cluster_total:errors.append('Uncapped ratsnest and physical-cluster totals differ')
    if orphan:errors.append('Copper clusters without source pads exist')
    result={'board_sha256':hashes[str(a.board.resolve())],'source_hashes':hashes,'source_net_checks_pass':not errors,
        'errors':errors,'footprints':len(board.GetFootprints()),'fitted_pads':len(fitted),'track_via_items':len(board.GetTracks()),
        'declared_native_NC_pads':len(nc&set(fitted)),'nets_requiring_multiple_fitted_pads':sum(r['source_pad_count']>1 for r in rows),
        'fully_joined_multiple_pad_nets':sum(r['source_pad_count']>1 and r['all_fitted_source_pads_joined'] for r in rows),
        'incomplete_multiple_pad_nets':sum(not r['all_fitted_source_pads_joined'] for r in rows),
        'uncapped_unconnected_ratsnest_edges':uncapped,'independent_physical_cluster_missing_joins':cluster_total,
        'orphan_copper_items':orphan,'manufacturing_ready':False,
        'scope':'Fitted source pins only; missing circuits/connectors cannot be treated as NC or as completed interfaces.',
        'nets':rows}
    a.out.mkdir(parents=True,exist_ok=False)
    (a.out/'review.json').write_text(json.dumps(result,indent=2)+'\n')
    with (a.out/'nets.csv').open('w',newline='') as f:
        fields=['net','source_pad_count','physical_pad_clusters','missing_cluster_joins','all_fitted_source_pads_joined']
        writer=csv.DictWriter(f,fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h for p,h in hashes.items()):raise ValueError('Input changed during inventory')
    print(json.dumps({k:v for k,v in result.items() if k not in ('nets','source_hashes')}))
    raise SystemExit(bool(errors))


if __name__=='__main__':main()
