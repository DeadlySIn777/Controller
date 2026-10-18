"""Apply the exact manufacturer's connector locating-hole capability, no ignores."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
import pcbnew
from hardware_route_logic_return import identity
from hardware_reconcile_motherboard_peripheral_pcb import piece
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--board',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise ValueError('Fresh output required')
    b=pcbnew.LoadBoard(str(a.board));f=next(f for f in b.GetFootprints() if f.GetReference()=='J15006')
    if f.GetValue()!='USB4105-GF-A':raise ValueError('Exact reviewed connector changed')
    holes=[q for q in f.Pads() if q.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH]
    assert len(holes)==2 and all(tuple(q.GetDrillSize())==(650000,650000) for q in holes)
    assert sorted(tuple(q.GetFPRelativePosition()) for q in holes)==[(-2890000,-2605000),(2890000,-2605000)]
    old={t.m_Uuid.AsString():identity(t) for t in b.GetTracks()}
    pads={(fp.GetReference(),q.m_Uuid.AsString()):piece(q) for fp in b.GetFootprints() for q in fp.Pads()}
    shutil.copytree(a.board.parent,a.out);dest=a.out/a.board.name;rules=dest.with_suffix('.kicad_dru')
    text=rules.read_text();assert 'GCT USB4105 own locating' not in text
    rule='''
# Exact GCT USB4105-GF-A recommended land: own .65mm locating holes
# to adjacent own outer GND lands have nominal .1944mm copper separation.
# PCBWay published special minimum NP-hole/copper .15mm; required .18mm
# applies ONLY to these own-pad pairs. All other .25mm rules remain.
(rule "GCT USB4105 own locating hole to outer ground lands"
  (condition "A.memberOfFootprint('J15006') && B.memberOfFootprint('J15006') && ((A.Pad_Type == 'NPTH, mechanical' && A.Hole_Size_X == 0.65mm && (B.Pad_Number == 'A1' || B.Pad_Number == 'A12' || B.Pad_Number == 'B1' || B.Pad_Number == 'B12')) || (B.Pad_Type == 'NPTH, mechanical' && B.Hole_Size_X == 0.65mm && (A.Pad_Number == 'A1' || A.Pad_Number == 'A12' || A.Pad_Number == 'B1' || A.Pad_Number == 'B12')))")
  (constraint hole_clearance (min 0.18mm)))
'''
    rules.write_text(text+rule)
    run=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','--output',str(a.out/'drc-usb-rule.json'),str(dest)],capture_output=True,text=True)
    (a.out/'drc-usb-rule.txt').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError('Native custom rule/DRC execution failed')
    d=json.loads((a.out/'drc-usb-rule.json').read_text())
    assert not d.get('ignored_checks') and not d['violations'],d['violations'][:3]
    fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity()
    assert old=={t.m_Uuid.AsString():identity(t) for t in fresh.GetTracks()}
    assert pads=={(fp.GetReference(),q.m_Uuid.AsString()):piece(q) for fp in fresh.GetFootprints() for q in fp.Pads()}
    receipt=dict(board_sha256=sha(dest),rules_sha256=sha(rules),parent_board_sha256=sha(a.board),native_DRC_regular=0,
        ignored_checks=[],all_copper_and_physical_pads_preserved=True,uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),
        exact_rule=rule,primary_sources=['https://gct.co/connector/usb4105','https://www.pcbway.com/pcb_prototype/PCB_Manufacturing_tolerances.html','https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html'],
        qualification='Exact manufacturer land retained; .18mm special capability must be explicitly accepted in PCBWay fabrication DFM/quote. No physical mating or manufacturing approval claimed.',manufacturing_ready=False)
    (a.out/'usb-rule-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:receipt[k] for k in ('native_DRC_regular','uncapped_missing_joins')}))
if __name__=='__main__':main()
