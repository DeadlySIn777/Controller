"""Actual native cuts of the bounded ADC cell; candidate file remains immutable."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha, write
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck

folder = Path('reports/motherboard-return-zoning-20261001/source26-r74-C19042-coupled-source-cell-r05')
source = folder / 'motherboard-C19042-source-cell-candidate.kicad_pcb'
frozen = sha(source)
generation = json.loads((folder / 'generation.json').read_text())
power = '/motherboard_do/DOB_FIELD_3V3'
ground = '/motherboard_do/FIELD_B_0V'

def pads(board):
    return {(p.GetParentFootprint().GetReference(), p.GetNumber()): p for p in board.GetPads()}

def paired(board, a, b):
    board.BuildConnectivity()
    items = pads(board)
    return items[b].m_Uuid.AsString() in {q.m_Uuid.AsString() for q in board.GetConnectivity().GetConnectedItems(items[a])}

rows = []
held_native_boards = []
for name, targetnet, endpoints in (
    ('remove_actual_F_supply_branch', power, (('C19042','1'),('U19026','8'))),
    ('remove_actual_return_branch_and_annulus', ground, (('C19042','2'),('U19026','3'))),
):
    board = pcbnew.LoadBoard(str(source))
    held_native_boards.append(board)
    removed = []
    for item in list(board.GetTracks()):
        if item.m_Uuid.AsString() in generation['new_Cu'] and item.GetNetname() == targetnet:
            removed.append(item.m_Uuid.AsString()); board.Remove(item)
    cut_file = folder / (name + '-cut.kicad_pcb')
    if cut_file.exists(): raise ValueError('Fresh immutable control file required')
    pcbnew.SaveBoard(str(cut_file), board)
    board = pcbnew.LoadBoard(str(cut_file)); held_native_boards.append(board)
    print('Checking actual cut ' + name, flush=True)
    if not removed or paired(board, *endpoints):
        raise ValueError('Actual native physical cut did not reject: ' + name)
    rows.append(dict(name=name, passed=True, actual_removed_native_UUIDs=removed,
                     actual_source_pair_rejected=True, saved_candidate_mutated=False))

board = pcbnew.LoadBoard(str(source))
held_native_boards.append(board)
for zone in list(board.Zones()):
    if zone.m_Uuid.AsString() in generation['new_zone_UUIDs']:
        board.Remove(zone)
print('Checking actual reference-collar cut', flush=True)
pcbnew.ZONE_FILLER(board).Fill(board.Zones()); board.BuildConnectivity()
declaration = dict(return_net=ground, reference_layers={'F.Cu':'In1.Cu'},
                   allow_vias=False, reference_corridor_margin_mm=.4)
checker = NativeCollectedAnnulusCheck(board, {power:declaration})
rejected = []
for item in board.GetTracks():
    if item.m_Uuid.AsString() in generation['new_Cu'] and item.GetNetname()==power:
        try: checker.segment(item, declaration)
        except ValueError as error: rejected.append(dict(uuid=item.m_Uuid.AsString(), reason=str(error)))
if not rejected:
    raise ValueError('Missing actual own reference collar failed to reject')
rows.append(dict(name='remove_actual_own_In1_reference_collar', passed=True,
                 actual_reference_segment_rejections=rejected,
                 native_refill_performed=True, saved_candidate_mutated=False))
if sha(source)!=frozen: raise ValueError('Frozen actual cell candidate changed')
write(folder/'native-physical-controls-r01.json',dict(passed=True, board_sha256=frozen,
      actual_native_negative_controls=rows, no_source_or_saved_PCB_mutation=True,
      route_margin_or_old_guards_changed=False, manufacturing_ready=False))
print('Three actual ADC source/reference cut controls passed',flush=True)
