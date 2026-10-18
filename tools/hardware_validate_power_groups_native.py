"""Independent uncapped local converter connectivity and source-pin audit."""
from pathlib import Path
import argparse,json,hashlib,collections
import pcbnew
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--recipes',type=Path,required=True);ap.add_argument('--owners',type=Path,required=True);ap.add_argument('--supplement',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();digest=sha(a.board)
    b=pcbnew.LoadBoard(str(a.board.resolve()));b.BuildConnectivity();c=b.GetConnectivity();fs={f.GetReference():f for f in b.GetFootprints()};ps=collections.defaultdict(list)
    for f in fs.values():
        for p in f.Pads():ps[(f.GetReference(),p.GetNumber())].append(p)
    groups=json.loads(a.recipes.read_text())['groups'];scope={r for g in groups.values()for r in g};own=json.loads(a.owners.read_text())['capacitors'];caprows=[];errors=[]
    if a.supplement:own+=json.loads(a.supplement.read_text())['capacitors']
    assert len({r['ref']for r in own})==len(own),'Duplicate owner rows'
    def keys(p):return{(q.GetParentFootprint().GetReference(),q.GetNumber())for q in c.GetConnectedItems(p)if q.Type()==pcbnew.PCB_PAD_T}
    for row in own:
        if row['ref']not in scope:continue
        rr=dict(ref=row['ref'],owner_ref=row['owner_ref'],checks=[])
        for pin,eps in row['actual_owner_endpoints'].items():
            p=ps[(row['ref'],pin)][0];reach=keys(p)
            same=[ep for ep in eps if ep['ref']in scope]
            for ep in same:
                q=ps[(ep['ref'],ep['pin'])][0]
                match=p.GetNetname()==q.GetNetname();joined=(ep['ref'],ep['pin'])in reach
                rr['checks'].append(dict(cap_pin=pin,owner_ref=ep['ref'],owner_pin=ep['pin'],exact_native_net=p.GetNetname(),net_match=match,actual_native_connected=joined))
                if not match or not joined:errors.append(row['ref']+'.'+pin+'→'+ep['ref']+'.'+ep['pin'])
        caprows.append(rr)
    kelvin=[]
    for ref,shunt in [('U11007','R11022'),('U11008','R11030')]:
        for pin,sp in [('11','1'),('12','2')]:
            p,q=ps[(ref,pin)][0],ps[(shunt,sp)][0];joined=(shunt,sp)in keys(p)
            kelvin.append(dict(ic=ref,ic_pin=pin,shunt=shunt,shunt_pin=sp,actual_native_connected=joined,net_match=p.GetNetname()==q.GetNetname()))
            if not joined or p.GetNetname()!=q.GetNetname():errors.append(ref+'.'+pin+'→'+shunt+'.'+sp)
    group_rows=[]
    for name,g in groups.items():
        nn=collections.defaultdict(list)
        for ref in g:
            for p in fs[ref].Pads():
                if p.GetNetname()and not p.GetNetname().startswith('unconnected-'):nn[p.GetNetname()].append(p)
        rows=[]
        for net,pads in nn.items():
            expected={(p.GetParentFootprint().GetReference(),p.GetNumber())for p in pads}
            seen=set();clusters=[]
            for p in pads:
                key=(p.GetParentFootprint().GetReference(),p.GetNumber())
                if key in seen:continue
                reach=keys(p)&expected;reach.add(key);seen.update(reach);clusters.append(sorted(ref+'.'+pin for ref,pin in reach))
            rows.append(dict(net=net,physical_source_pins=sorted(ref+'.'+pin for ref,pin in expected),actual_native_clusters=clusters,closed_local_net=len(clusters)==1))
        group_rows.append(dict(group=name,nets=rows,open_internal_nets=[r for r in rows if not r['closed_local_net']]))
    assert sha(a.board)==digest
    receipt=dict(board_sha256=digest,board_unchanged=True,actual_uncapped_whole_board_unconnected=b.GetConnectivity().GetUnconnectedCount(False),reviewed_group_caps=len(caprows),capacitor_pin_checks=sum(len(r['checks'])for r in caprows),capacitors=caprows,kelvin_pin_connectivity=kelvin,cap_owner_connectivity_errors=errors,groups=group_rows,external_group_feed_return_or_control_delivery_qualified=False,manufacturing_ready=False)
    a.output.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items()if k not in('capacitors','groups')}))
if __name__=='__main__':main()
