"""Negative native fixtures cut real copper while retaining pin net labels."""
from pathlib import Path
import argparse,hashlib,json,subprocess,shutil
import pcbnew
from hardware_build_assembly import parse,dump,child,value
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--route-receipt',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True);digest=sha(a.board);rr=json.loads(a.route_receipt.read_text());b=pcbnew.LoadBoard(str(a.board.resolve()));ps={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()};results=[]
    for kind,up in [('compact_SENSE_RSENSE_CIN',[16,11]),('compact_IN_RSENSE',[15,10])]:
        remove={r['uuid']for r in rr['exact_added_copper']if r['kind']==kind};assert remove;tree=parse(a.board.read_text());tree[:]=[x for x in tree if not(isinstance(x,list)and x and x[0]in('segment','via','arc')and value(child(x,'uuid')[1])in remove)];dest=a.out/(kind+'-copper-cut-negative.kicad_pcb');dest.write_text(dump(tree)+'\n');q=pcbnew.LoadBoard(str(dest));q.BuildConnectivity();qp={(f.GetReference(),p.GetNumber()):p for f in q.GetFootprints()for p in f.Pads()};rows=[]
        for n in range(12):
            u=f'U{6035+n//2}';rs=f'R{6052+3*n}';icp=str(up[n%2]);rsp='1'if 'SENSE_'in kind else'2';first,last=qp[(u,icp)],qp[(rs,rsp)];reach={v.m_Uuid.AsString()for v in q.GetConnectivity().GetConnectedItems(first)};connected=last.m_Uuid.AsString()in reach;equal=first.GetNetname()==last.GetNetname();assert equal and first.GetNetname()==ps[(u,icp)].GetNetname();rows.append(dict(channel=n,ic_pad=u+'.'+icp,resistor_pad=rs+'.'+rsp,native_assigned_nets_equal_and_unchanged=equal,actual_connected=connected,negative_control_detected=not connected))
        assert all(r['negative_control_detected']for r in rows)
        results.append(dict(kind=kind,removed_exact_copper=sorted(remove),checks=rows,all_twelve_real_copper_cuts_detected=True,fixture_sha256=sha(dest)))
    assert sha(a.board)==digest;result=dict(source_sha256=digest,source_unchanged=True,negative_controls=results,physical_connectivity_not_name_matching_proven=True,physical_measurement_claim=False);(a.out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(all24_negative_controls_detected=True,source_unchanged=True)))
if __name__=='__main__':main()
