"""Read-only exact combined-board proof of the frozen ADS1115 bypass delta."""
import argparse, json
from pathlib import Path
import sys
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import identity,pad_identity,mm
from hardware_populate_motherboard_pcb import pad_template
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck
from hardware_validate_return_bridge_sources import review

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for field in ('board','map','drc','out'):ap.add_argument('--'+field,type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists():raise ValueError('Fresh immutable output required')
    folder=Path('reports/motherboard-return-zoning-20261001/source26-r74-C19042-coupled-source-cell-r05')
    donor=folder/'motherboard-C19042-source-cell-candidate.kicad_pcb'
    freeze=json.loads((folder/'closure-freeze-r06.json').read_text())
    if sha(donor)!=freeze['board_sha256']:raise ValueError('Frozen native donor changed')
    for name,h in freeze['proof_sha256'].items():
        if sha(Path(name))!=h:raise ValueError('Frozen ADC proof changed: '+name)
    frozen={str(p):sha(p)for p in(a.board,a.map,a.drc,Path(__file__),donor,folder/'closure-freeze-r06.json')}
    board=pcbnew.LoadBoard(str(a.board));board.BuildConnectivity()
    original=pcbnew.LoadBoard(str(donor))
    mapping=json.loads(a.map.read_text());native=json.loads(a.drc.read_text())
    map_board_hash=mapping.get('actual_board_sha256',mapping.get('input_sha256',{}).get(str(a.board.resolve())))
    if map_board_hash!=sha(a.board):raise ValueError('Map does not bind exact current native board')
    if any(v['severity']=='error'for v in native['violations'])or native.get('ignored_checks'):
        raise ValueError('Combined native errors/ignored checks remain')
    generation=json.loads((folder/'generation.json').read_text())
    now={t.m_Uuid.AsString():t for t in board.GetTracks()};old={t.m_Uuid.AsString():t for t in original.GetTracks()}
    exactids=generation['new_Cu']+generation['exact_old_copper_endpoint_or_pose_changes']
    if len(generation['new_Cu'])!=7 or len(generation['exact_old_copper_endpoint_or_pose_changes'])!=3:
        raise ValueError('Exact frozen seven-plus-three delta differs')
    for ident in exactids:
        if ident not in now or identity(now[ident])!=identity(old[ident]):raise ValueError('Actual ADC delta changed: '+ident)
    fps={f.GetReference():f for f in board.GetFootprints()};donorfps={f.GetReference():f for f in original.GetFootprints()}
    cap=fps['C19042'];expected=donorfps['C19042']
    if cap.GetLayer()!=pcbnew.F_Cu or mm(cap.GetPosition())!=(125.75,172.25)or cap.GetOrientationDegrees()!=0:
        raise ValueError('Actual C19042 reviewed pose differs')
    if str(cap.GetFPID())!=str(expected.GetFPID())or sorted(pad_template(p)for p in cap.Pads())!=sorted(pad_template(p)for p in expected.Pads()):
        raise ValueError('Actual manufacturer C19042 lands differ')
    pads={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in board.GetPads()}
    for pin in('1','2'):
        q=pads['C19042',pin];p=next(p for p in expected.Pads()if p.GetNumber()==pin)
        if pad_identity(q)!=pad_identity(p):raise ValueError('C19042 native Source pin identity differs')
    conn=board.GetConnectivity();pairs=[]
    for c,i in((('C19042','1'),('U19026','8')),(('C19042','2'),('U19026','3'))):
        if pads[i].m_Uuid.AsString()not in{t.m_Uuid.AsString()for t in conn.GetConnectedItems(pads[c])}:
            raise ValueError('Actual ADC owning Source pair disconnected')
        pairs.append(dict(capacitor=list(c),owner=list(i),actual_native_Source_pair_connected=True))
    power='/motherboard_do/DOB_FIELD_3V3';ground='/motherboard_do/FIELD_B_0V'
    groundvias=[now[u]for u in generation['new_Cu']if now[u].Type()==pcbnew.PCB_VIA_T]
    if len(groundvias)!=1 or groundvias[0].GetNetname()!=ground or not physical_reference_contact(groundvias[0],pcbnew.In1_Cu,conn):
        raise ValueError('Actual ADC Ground annulus lacks own native connected In1')
    groups=[dict(net=n,new_copper_UUIDs=[u for u in generation['new_Cu']if now[u].GetNetname()==n])for n in(power,ground)]
    Sourceproof=review(board,groups,mapping['pads'])
    declaration=dict(return_net=ground,reference_layers={'F.Cu':'In1.Cu'},allow_vias=False,reference_corridor_margin_mm=.4)
    checker=NativeCollectedAnnulusCheck(board,{power:declaration})
    strict=[checker.segment(now[u],declaration)for u in groups[0]['new_copper_UUIDs']]
    cuts=json.loads((folder/'physical-controls-r02/review.json').read_text())
    if not cuts['passed']or cuts['board_sha256']!=freeze['board_sha256']or len(cuts['actual_native_negative_controls'])!=3:
        raise ValueError('Frozen actual native cuts missing')
    for path,h in frozen.items():
        if sha(Path(path))!=h:raise ValueError('Read-only input changed')
    write(a.out,dict(passed=True,board_sha256=sha(a.board),input_sha256=frozen,
      exact_cap_pose_and_manufacturer_lands_preserved=True,exact7new_and3changed_native_Cu_checked=exactids,
      actual_ADC_native_Source_pairs=pairs,actual_Ground_In1_flashed_native_connected_annulus=True,
      every_new_Cu_numbered_Source_proof=Sourceproof,strict_point40_direct_F_supply_reference_reviews=strict,
      no_supply_vias=True,three_frozen_actual_native_cuts_preserved_sha256=sha(folder/'physical-controls-r02/review.json'),
      native_errors=0,ignored_checks=[],no_source_or_PCB_mutation=True,manufacturing_ready=False))
    print('Exact combined C19042 SOURCE/native/ref proof passed',flush=True)

if __name__=='__main__':main()
