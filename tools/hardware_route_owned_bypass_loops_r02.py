"""Frozen local-bypass routing with actual native reference-annulus checks.

The historical router is retained. The stronger final supply-via guard and
independent receiving-ground anchor checks reject a drilled span masquerading
as a connected reference. Dedicated precision/no-via cells stay excluded.
"""
from pathlib import Path
import hashlib,json,math,sys
import pcbnew
import hardware_route_owned_bypass_loops as prior
import hardware_check_return_corridors_r02 as strict

FROZEN_ROUTER_SHA='2cb453968b23edc567061f1806caa278ced3f57f631b4c1ad82636b32a7f29a6'
STRICT_CHECKER_SHA='3496b5598390833c3cf71fd8dade26817a28ca1a7b208bba6af80fd1a0e00682'

def actual_reference_contact(board,item,layers):
    conn=board.GetConnectivity()
    return all(item.IsOnLayer(layer) and item.FlashLayer(layer)
               and conn.IsConnectedOnLayer(item,layer)for layer in layers)

def actual_receiving_return_anchors(board,receipt,manifest):
    """Each accepted actual receiving/return pad needs its own local anchor."""
    board.BuildConnectivity();conn=board.GetConnectivity()
    fps={fp.GetReference():fp for fp in board.GetFootprints()}
    actual_vias=[t for t in board.GetTracks()if isinstance(t,pcbnew.PCB_VIA)]
    owners={row['ref']:row for row in manifest['capacitors']};reviews=[]
    layers=[pcbnew.In1_Cu,pcbnew.In4_Cu]
    for group in receipt['owned_loops']:
        if not group['retained']:continue
        row=owners[group['ref']]
        ends=[{'ref':row['ref'],'pin':row['cap_return']}]+row['return_nodes']
        for endpoint in ends:
            pad=next(p for p in fps[endpoint['ref']].Pads()if p.GetNumber()==endpoint['pin'])
            candidates=[]
            # GetConnectedItems exposes some native vias as base PCB_TRACK
            # SWIG proxies. Resolve its real UUID membership against the typed
            # board inventory rather than discarding a physically valid via.
            connected_uuids={t.m_Uuid.AsString()for t in conn.GetConnectedItems(pad)}
            for item in actual_vias:
                if item.m_Uuid.AsString()not in connected_uuids or item.GetNetname()!=pad.GetNetname():continue
                dist=math.dist(prior.mm(item.GetPosition()),prior.mm(pad.GetPosition()))
                if dist<=2 and actual_reference_contact(board,item,layers):
                    candidates.append({'uuid':item.m_Uuid.AsString(),'distance_mm':dist,
                        'reference_layers':['In1.Cu','In4.Cu'],
                        'actual_flashed_and_native_connected_reference_annuli':True})
            if not candidates:
                raise ValueError('Receiving ground lacks actual local flashed/native-connected reference anchor '+endpoint['ref']+'.'+endpoint['pin'])
            reviews.append({'capacitor':row['ref'],'actual_source_endpoint':endpoint,
                'return_net':pad.GetNetname(),'physical_reference_anchors':candidates})
    return reviews

def checked_dependencies():
    actual=hashlib.sha256(Path(prior.__file__).read_bytes()).hexdigest()
    if actual!=FROZEN_ROUTER_SHA:raise ValueError('Frozen HF owned-bypass router changed')
    checker=Path(strict.__file__)
    if hashlib.sha256(checker.read_bytes()).hexdigest()!=STRICT_CHECKER_SHA:
        raise ValueError('Reviewed actual annulus checker changed')
    return {'frozen_owned_bypass_router_sha256':actual,
            'strict_return_checker_sha256':STRICT_CHECKER_SHA}

def main():
    dependencies=checked_dependencies()
    prior.return_corridor_check=strict.return_corridor_check
    prior.main()
    out=Path(sys.argv[sys.argv.index('--out')+1]).resolve()
    owners=Path(sys.argv[sys.argv.index('--owners')+1]).resolve()
    path=out/'receipt.json';receipt=json.loads(path.read_text(encoding='utf8'))
    board=pcbnew.LoadBoard(str(out/'owned-bypass-loop-candidate.kicad_pcb'))
    try:reviews=actual_receiving_return_anchors(board,receipt,json.loads(owners.read_text(encoding='utf8')))
    except ValueError as error:
        receipt.update(passed=False,actual_reference_annuli_pass=False,
            actual_reference_annulus_rejection=str(error),manufacturing_ready=False)
        path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8');raise
    receipt.update(passed=True,router_version='r02 actual annuli wrapper',
        stronger_return_dependencies=dependencies,
        actual_receiving_return_anchor_reviews=reviews,
        actual_flashed_and_native_connected_reference_annuli_required=True,
        actual_reference_annuli_pass=True,
        tool_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in[Path(__file__),Path(strict.__file__),Path(prior.__file__)]})
    path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')

if __name__=='__main__':main()
