"""Remove unused inner annuli from newly added conventional logic vias only.

Original 673-item routed copper is preserved exactly. New through barrels and
their connected-layer annuli remain; this is KiCad's normal unused-layer
padstack operation. Refill and check native DRC and uncapped connectivity.
Manufacturing drill compensation/inner clearances still require qualification.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import pcbnew
from hardware_route_logic_return import identity, pad_identity

ROOT=Path(__file__).resolve().parents[1]
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--board',type=Path,required=True);p.add_argument('--original',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    source=a.board.resolve();original=a.original.resolve();out=a.out.resolve()
    if out.exists() or out.is_relative_to(ROOT/'hardware'):raise ValueError('Use new immutable report directory')
    inputs={str(f):sha(f) for f in (source,original,source.with_suffix('.kicad_pro'),source.with_suffix('.kicad_dru'))}
    b=pcbnew.LoadBoard(str(source));first=pcbnew.LoadBoard(str(original))
    old={t.m_Uuid.AsString():identity(t) for t in first.GetTracks()}
    if len(old)!=673:raise ValueError('Require the original integrated673-item copper baseline')
    before={t.m_Uuid.AsString():identity(t) for t in b.GetTracks()}
    if any(before.get(i)!=v for i,v in old.items()):raise ValueError('Original copper missing or changed before this operation')
    old_pads={(q.GetParentFootprint().GetReference(),q.GetNumber()):pad_identity(q) for q in b.GetPads()}
    modified=[]
    for t in b.GetTracks():
        if isinstance(t,pcbnew.PCB_VIA) and t.m_Uuid.AsString() not in old:
            prior=t.GetRemoveUnconnected();t.SetRemoveUnconnected(True)
            modified.append({'uuid':t.m_Uuid.AsString(),'net':t.GetNetname(),'prior_remove_unconnected':prior,
                             'remove_unconnected':t.GetRemoveUnconnected(),
                             'native_padstack_mode':int(t.Padstack().UnconnectedLayerMode())})
    # The inherited default 0.25mm hole clearance plus 0.25mm minimum
    # fill thickness cuts off a power via inside the 0.8mm lattice. PCBWay
    # publishes >=8mil inner-hole isolation for normal six-layer processing.
    # 0.205mm exceeds8mil; a0.175mm plane neck exceeds its4mil inner trace
    # floor. These are explicit provisional dimensional rules, not exclusions.
    for z in b.Zones():
        if z.GetLayer() in (pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu):
            z.SetMinThickness(pcbnew.FromMM(.175))
    pcbnew.ZONE_FILLER(b).Fill(b.Zones());out.mkdir(parents=True);dest=out/'logic-via-padstacks-candidate.kicad_pcb'
    pcbnew.SaveBoard(str(dest),b)
    dest.with_suffix('.kicad_pro').write_bytes(source.with_suffix('.kicad_pro').read_bytes())
    rules=source.with_suffix('.kicad_dru').read_text(encoding='utf-8')
    rules+='\n# PCBWay six-layer normal-process inner-hole isolation >=8mil.\n(rule "Six-layer inner drill to copper separation"\n  (layer inner)\n  (constraint hole_clearance (min 0.205mm)))\n'
    dest.with_suffix('.kicad_dru').write_text(rules,encoding='utf-8')
    for path in source.parent.glob('*.pretty'):shutil.copytree(path,out/path.name)
    for name in ('3dmodels','fp-lib-table'):
        f=source.parent/name
        if f.is_dir():shutil.copytree(f,out/name)
        elif f.is_file():shutil.copyfile(f,out/name)
    # Native refill loads the candidate's real project/custom rules; pcbnew's
    # bare in-memory filler does not initialise that complete rule engine.
    report=out/'native-drc.json';cmd=[str(CLI),'pcb','drc','--format','json','--all-track-errors','--severity-all','--refill-zones','--save-board','-o',str(report),str(dest)]
    run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (out/'native-drc.txt').write_text(run.stdout+run.stderr,encoding='utf-8')
    if run.returncode:raise RuntimeError('Native DRC command failed')
    data=json.loads(report.read_text(encoding='utf-8'))
    reopened=pcbnew.LoadBoard(str(dest));reopened.BuildConnectivity()
    after={t.m_Uuid.AsString():identity(t) for t in reopened.GetTracks()}
    if before!=after:raise ValueError('Copper geometry/net/UUID changed')
    if old_pads!={(q.GetParentFootprint().GetReference(),q.GetNumber()):pad_identity(q) for q in reopened.GetPads()}:raise ValueError('Source pad geometry/net changed')
    if any(sha(Path(f))!=h for f,h in inputs.items()):raise ValueError('Input changed during operation')
    receipt={'source_hashes':inputs,'board_sha256':sha(dest),'original673_copper_geometry_and_net_preserved':True,
      'all_track_via_geometry_and_nets_preserved':True,'native_drc_violations':len(data['violations']),
      'native_drc_ignored_checks':data.get('ignored_checks',[]),'modified_new_via_padstacks':len(modified),'padstack_changes':modified,
      'actual_filled_zones':len(reopened.Zones()),'uncapped_unconnected_edges':reopened.GetConnectivity().GetUnconnectedCount(False),
      'inner_hole_clearance_rule_mm':.205,'inner_plane_minimum_thickness_mm':.175,
      'process_reference':{'url':'https://www.pcbway.com/capabilities.html','retrieved_date':'2026-09-30',
        'basis':'Advanced-capability table: six-layer normal inner hole-to-copper >=8mil;35um inner width >=4mil. No vendor process/stackup approval.'},
      'manufacturing_ready':False,'scope':'Only new conventional logic vias remove unused inner annuli. Original copper and all source pad geometry remain. Manufacturing process and full-board completion remain open.'}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('source_hashes','padstack_changes')}))
    if data['violations'] or data.get('ignored_checks'):raise SystemExit(1)

if __name__=='__main__':main()
