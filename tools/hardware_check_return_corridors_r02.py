"""Geometric return guards plus actual flashed/native-connected annuli.

Preserves the frozen geometric checker. A drilled span alone cannot credit a
return stitch on an inner reference layer, even if a same-net name is present.
"""
import hashlib
from pathlib import Path
import pcbnew
import hardware_check_return_corridors as prior
FROZEN_GEOMETRIC_CHECKER_SHA='ae44bbaf5ba31fb4bbe0f1bf7f532f5a07ef5f6546ca82523b760a27379c1aa7'

class ActualAnnulusReturnCheck(prior.ReturnCheck):
    def via(self,signal,row):
        audit=super().via(signal,row)
        exact={prior.uid(v):v for v in self.vias}
        layers=[self.board.GetLayerID(n)for n in audit['intended_reference_layers']]
        qualified=[]
        for candidate in audit['return_stitches']:
            stitch=exact[candidate['uuid']]
            if all(stitch.IsOnLayer(layer)and stitch.FlashLayer(layer)
                   and self.board.GetConnectivity().IsConnectedOnLayer(stitch,layer)for layer in layers):
                qualified.append({**candidate,'actual_flashed_and_native_connected_reference_layers':audit['intended_reference_layers']})
        if not qualified:
            raise ValueError('Same-domain return stitch lacks an actual flashed/native-connected reference annulus')
        audit={**audit,'return_stitches':qualified,'physical_reference_annuli_required':True}
        self.audits[prior.uid(signal)]=audit
        return audit

def return_corridor_check(board,added,rows):
    if hashlib.sha256(Path(prior.__file__).read_bytes()).hexdigest()!=FROZEN_GEOMETRIC_CHECKER_SHA:
        raise ValueError('Frozen geometric return checker changed')
    checker=ActualAnnulusReturnCheck(board,rows);items=[];exact={prior.uid(t):t for t in board.GetTracks()}
    if not set(added)<=set(exact):raise ValueError('Declared added copper UUID absent')
    for ident in sorted(added):
        t=exact[ident]
        if t.GetNetname()not in rows:raise ValueError('Actual new signal lacks exact source/return manifest')
        row=rows[t.GetNetname()]
        items.append(checker.via(t,row)if isinstance(t,pcbnew.PCB_VIA)else checker.segment(t,row))
    return dict(passed=True,new_copper_items_checked=len(items),items=items,
        actual_signal_via_reference_audits=list(checker.audits.values()),
        exact_same_net_antipad_exceptions_only=True,real_numbered_source_pad_anchor_required=True,
        actual_flashed_and_native_connected_reference_annuli_required=True,
        physical_signal_integrity_qualified=False,measured_return_impedance=False,no_source_or_PCB_mutation=True)
