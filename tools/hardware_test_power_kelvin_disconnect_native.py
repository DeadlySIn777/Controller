"""Meaningful native negative control: remove copper, preserve assigned nets."""
from pathlib import Path
import argparse,json,hashlib,shutil
import pcbnew
from hardware_build_assembly import parse,dump,child,value
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--board',required=True,type=Path);ap.add_argument('--receipt',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args();assert not a.out.exists()and a.out.resolve().is_relative_to(ROOT/'reports');a.out.mkdir(parents=True)
    digest=sha(a.board);r=json.loads(a.receipt.read_text());assert r['board_sha256']==digest
    kinds={'shunt_Kelvin_IC_escape','shunt_Kelvin_via','separate_shunt_Kelvin','shunt_inner_pad_Kelvin_tap'};remove={x['uuid']for x in r['added_copper']if x['kind']in kinds};assert remove
    t=parse(a.board.read_text());t[:]=[x for x in t if not(isinstance(x,list)and x and x[0]in ['segment','via','arc']and value(child(x,'uuid')[1])in remove)];dest=a.out/'Kelvin-copper-removed-negative-fixture.kicad_pcb';dest.write_text(dump(t)+'\n')
    for suffix in ['.kicad_pro','.kicad_dru']:
        if a.board.with_suffix(suffix).exists():shutil.copyfile(a.board.with_suffix(suffix),dest.with_suffix(suffix))
    b=pcbnew.LoadBoard(str(dest.resolve()));b.BuildConnectivity();ps={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()};rows=[]
    for u,rr in [('U11007','R11022'),('U11008','R11030')]:
        for pin,sp in [('11','1'),('12','2')]:
            p,q=ps[(u,pin)],ps[(rr,sp)];reached={v.m_Uuid.AsString()for v in b.GetConnectivity().GetConnectedItems(p)if v.Type()==pcbnew.PCB_PAD_T};connected=q.m_Uuid.AsString()in reached;rows.append(dict(ic=u,pin=pin,shunt=rr,shunt_pin=sp,equal_assigned_native_net=p.GetNetname()==q.GetNetname(),actually_connected=connected,negative_control_detected=not connected))
    assert sha(a.board)==digest
    result=dict(source_board_sha256=digest,source_board_unchanged=True,removed_exact_new_copper_uuids=sorted(remove),checks=rows,all_four_negative_controls_detected=all(r['negative_control_detected']for r in rows),net_names_not_changed=True,physical_measurement_claim=False,fixture_board_sha256=sha(dest));(a.out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
    assert result['all_four_negative_controls_detected'],'An unintended measurement bypass remains'
if __name__=='__main__':main()
