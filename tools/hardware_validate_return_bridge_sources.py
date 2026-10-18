"""Require every new return-bridge conductor to reach real native source pads.

Checking old source clusters or a same-named filled polygon is insufficient:
an omitted predecessor transfer can leave a downstream bridge orphaned while
native DRC remains clean. Each literal new item must have a real numbered,
non-NC source-pad witness on its own return net. This does not qualify global
return capacity, local loop geometry, filled reference coverage or fabrication.
"""
from __future__ import annotations
import pcbnew


def review(board, groups, source_pads):
    """Read a native board; do not alter copper or create synthetic anchors."""
    expected={p['uuid']:p for p in source_pads}
    if len(expected)!=len(source_pads):raise ValueError('Duplicate actual source-pad identity')
    actual={p.m_Uuid.AsString():p for p in board.GetPads()if p.GetNumber()and p.IsOnCopperLayer()}
    for uid,p in expected.items():
        native=actual.get(uid)
        if native is None or native.GetNetname()!=p['net']or native.GetNumber()!=p['pin']or native.GetParentFootprint().GetReference()!=p['reference']:
            raise ValueError('Exact source-pad identity/net differs: '+uid)
    board.BuildConnectivity();conn=board.GetConnectivity();items={t.m_Uuid.AsString():t for t in board.GetTracks()}
    records=[];seen=set()
    for group in groups:
        net=group['net'];ids=group['new_copper_UUIDs']
        if not ids:raise ValueError('Empty return-bridge group')
        witnesses=[]
        for uid in ids:
            if uid in seen:raise ValueError('Return-bridge conductor appears in multiple groups')
            seen.add(uid);item=items.get(uid)
            if item is None or item.GetNetname()!=net:raise ValueError('Literal new return-bridge conductor missing/wrong net: '+uid)
            pads=[]
            for peer in conn.GetConnectedItems(item):
                if not isinstance(peer,pcbnew.PAD)or not peer.GetNumber()or not peer.IsOnCopperLayer():continue
                row=expected.get(peer.m_Uuid.AsString())
                if row and not row.get('native_nc')and row['net']==net and peer.GetNetname()==net:
                    pads.append(dict(reference=row['reference'],pin=row['pin'],pad_uuid=row['uuid']))
            if not pads:raise ValueError('New return bridge is physically orphaned from actual source pads: '+uid)
            witnesses.append(dict(uuid=uid,actual_native_source_pad_witness=sorted(pads,key=lambda p:(p['reference'],p['pin'],p['pad_uuid']))[0]))
        records.append(dict(net=net,new_copper_UUIDs=list(ids),every_new_conductor_has_actual_source_pad_witness=True,witnesses=witnesses))
    return dict(passed=True,new_copper_count=len(seen),groups=records,
        actual_native_source_pad_reachability_required=True,
        same_name_plane_or_old_cluster_preservation_is_not_an_anchor=True,
        global_current_capacity_qualified=False,manufacturing_ready=False,no_source_or_PCB_mutation=True)
