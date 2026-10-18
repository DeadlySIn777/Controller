"""Negative fixtures cut actual copper while preserving every pin/net label."""
from pathlib import Path
import pcbnew,argparse,json,hashlib
from hardware_power_entry_cell_layout import recipes
from hardware_validate_power_entry_cells_native import review
from hardware_build_assembly import parse,dump,child,value
from hardware_route_logic_return import pad_identity
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists();a.out.mkdir(parents=True);digest=sha(a.board);b=pcbnew.LoadBoard(str(a.board.resolve()));pads={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()};original={p.m_Uuid.AsString():pad_identity(p)for p in b.GetPads()};baseline=review(a.board);assert baseline['error_count']==0;cases=[]
    for e in recipes()['entries']:
        if(e['efuse'],'4')not in pads:continue
        for kind,pin in [('DRV','4'),('ILIM','10'),('UV','6')]:
            net=pads[(e['efuse'],pin)].GetNetname();tree=parse(a.board.read_text());cut=[x for x in tree if isinstance(x,list)and x and x[0]in('segment','via','arc')and child(x,'net')and value(child(x,'net')[-1])==net];assert cut,'No actual copper to cut';ids=[value(child(x,'uuid')[1])for x in cut];tree[:]=[x for x in tree if x not in cut];dest=a.out/(e['name']+'-'+kind+'-cut.kicad_pcb');dest.write_text(dump(tree)+'\n');q=pcbnew.LoadBoard(str(dest));assert original=={p.m_Uuid.AsString():pad_identity(p)for p in q.GetPads()};result=review(dest);failures=[r for r in result['pin_connectivity_errors']if r['kind']==kind and r['from_pad']==e['efuse']+'.'+pin];assert failures and all(r['net_match']and not r['actual_native_connected']for r in failures),'Disconnected Cu fixture escaped independent native proof';cases.append(dict(entry=e['name'],kind=kind,net=net,cut_copper_uuids=ids,all_pin_names_nets_poses_unchanged=True,physical_disconnection_detected=True,actual_failures=failures,candidate_sha256=sha(dest)))
    assert sha(a.board)==digest;r=dict(source_sha256=digest,source_unchanged=True,baseline_actual_pin_checks=baseline['actual_pin_checks'],baseline_errors=0,cases=cases,negative_copper_cuts=len(cases),all_detected=True,manufacturing_ready=False);(a.out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k!='cases'}))
if __name__=='__main__':main()
