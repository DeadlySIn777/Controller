"""Bind the separate adjacent-only proof to exact board/map/filled geometry."""
import hashlib,json
from pathlib import Path
import pcbnew
import check_same_side_bypass_r01 as prior
from hardware_route_logic_return import identity,pad_identity
from hardware_populate_motherboard_pcb import pad_template
from hardware_scope_anchored_reference_pieces import SourceAnchoredPiecesCheck

FROZEN_PRIOR_SHA = '16507fe56e46b5b281801eb2f7830d40ef9dfb94ed75f682ff21f8404fe0072d'


def board_geometry_digest(board):
    """Exact native vertex/holes and source copper geometry, without saving."""
    h=hashlib.sha256()
    def add(value):
        data=str(value).encode();h.update(len(data).to_bytes(8,'little'));h.update(data)
    add(tuple(board.GetEnabledLayers().Seq()))
    for p in sorted(board.GetPads(),key=prior.uid):
        add((prior.uid(p),p.GetParentFootprint().GetReference(),p.GetNumber(),pad_identity(p),pad_template(p),tuple(p.GetDrillSize())))
    for t in sorted(board.GetTracks(),key=prior.uid):
        add((t.Type(),identity(t)))
        if t.Type()==pcbnew.PCB_VIA_T:
            add((t.GetViaType(),t.GetLayerSet().FmtBin(),t.GetRemoveUnconnected(),t.GetIsFree(),t.FlashLayer(pcbnew.In1_Cu),t.FlashLayer(pcbnew.In4_Cu)))
    for z in sorted(board.Zones(),key=prior.uid):
        add((prior.uid(z),z.GetNetname(),z.GetLayerSet().FmtBin(),z.GetIsRuleArea(),z.GetLocalClearance(),z.GetAssignedPriority()))
        add(z.Outline().Format(False))
        for layer in board.GetEnabledLayers().Seq():
            if pcbnew.IsCopperLayer(layer) and z.IsOnLayer(layer):
                add((layer,z.HasFilledPolysForLayer(layer)))
                add(z.GetFilledPolysList(layer).Format(False))
    return h.hexdigest()


def map_digest(mapping):
    return hashlib.sha256(json.dumps(mapping,sort_keys=True,separators=(',',':')).encode()).hexdigest()


class BoundSameSideCheck(SourceAnchoredPiecesCheck):
    def __init__(self,board,rows,mapping):
        if hashlib.sha256(Path(prior.__file__).read_bytes()).hexdigest()!=FROZEN_PRIOR_SHA:
            raise ValueError('Reviewed same-side geometry/return checker changed')
        board.BuildConnectivity()
        before=board_geometry_digest(board)
        super().__init__(board,rows,mapping)
        if board_geometry_digest(board)!=before:
            raise ValueError('Actual board changed while establishing reference cache')
        self._board_digest=before;self._map_digest=map_digest(mapping)

    def assert_current(self,board,mapping):
        if self.board is not board:
            raise ValueError('Wrong-board same-side reference cache')
        if self._map_digest!=map_digest(mapping):
            raise ValueError('Stale or foreign same-side source-map cache')
        if self._board_digest!=board_geometry_digest(board):
            raise ValueError('Stale native geometry/refill in same-side reference cache')


def check_group(board,group,row,mapping,checker=None):
    if checker is None:
        fps={f.GetReference():f for f in board.GetFootprints()}
        cp=next(p for p in fps[row['ref']].Pads()if p.GetNumber()==row['cap_power'])
        cr=next(p for p in fps[row['ref']].Pads()if p.GetNumber()==row['cap_return'])
        side=cp.GetParentFootprint().GetLayer()
        if side not in(pcbnew.F_Cu,pcbnew.B_Cu):raise ValueError('Exact outer surface required')
        declaration=dict(return_net=cr.GetNetname(),reference_layers={board.GetLayerName(side):'In1.Cu'if side==pcbnew.F_Cu else'In4.Cu'},allow_vias=False,reference_corridor_margin_mm=.10)
        checker=BoundSameSideCheck(board,{cp.GetNetname():declaration},mapping)
    if type(checker)is not BoundSameSideCheck:
        raise ValueError('Exact board-bound same-side checker class required')
    checker.assert_current(board,mapping)
    result=prior.check_group(board,group,row,mapping,checker)
    checker.assert_current(board,mapping)
    return dict(**result,exact_current_board_map_and_native_fill_cache_binding=True,
                native_geometry_sha256=checker._board_digest,source_map_sha256=checker._map_digest)

surface_path=prior.surface_path
