"""Validate actual per-side filled returns and real physical source anchors.

This checker does not treat same-named disconnected polygons as connected.
An inner-layer return component needs an actual numbered through-pad or a
through-via whose native physical cluster reaches a numbered source return
pad. It does not assert full load capacity, all SMD power-loop completion,
measured impedance or certified insulation.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pcbnew
from hardware_map_motherboard_domains import SEEDS,RAW_RETURNS,sha,write
from hardware_zone_motherboard_returns import pad_supports_reference,return_net,split_polygons
from hardware_collect_native_reference_fills import collect_native_reference_fills


def point(row):return pcbnew.VECTOR2I(*(pcbnew.FromMM(x)for x in row['position_mm']))


def physical_reference_contact(item,layer,connection):
    """A spanned drill without a flashed connected annulus is not an anchor."""
    return bool(item.IsOnLayer(layer)and item.FlashLayer(layer)
                and connection.IsConnectedOnLayer(item,layer))


def validate(board,mapping):
    board.BuildConnectivity();conn=board.GetConnectivity()
    exact={p.m_Uuid.AsString():p for f in board.GetFootprints() for p in f.Pads() if p.GetNumber()and p.IsOnCopperLayer()}
    source={p['uuid']:p for p in mapping['pads']}
    if set(exact)!=set(source):raise ValueError('Exact native copper-pad inventory differs from source map')
    if any(exact[k].GetNetname()!=v['net']for k,v in source.items()):raise ValueError('Actual source/native pad identity differs')
    for uid,row in source.items():
        pad=exact[uid]
        position=[pcbnew.ToMM(x)for x in pad.GetPosition()]
        if any(abs(a-b)>1e-6 for a,b in zip(position,row['position_mm'])):raise ValueError('Stale source-map pad pose '+uid)
        actual_layers={board.GetLayerName(i)for i in [pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.B_Cu]if pad.IsOnLayer(i)}
        if actual_layers!=set(row['copper_layers']):raise ValueError('Stale source-map pad copper side '+uid)
        if 'copper_aabb_mm'in row:
            box=pad.GetBoundingBox();actual_bounds=[pcbnew.ToMM(x)for x in [box.GetX(),box.GetY(),box.GetRight(),box.GetBottom()]]
            if any(abs(a-b)>1e-6 for a,b in zip(actual_bounds,row['copper_aabb_mm'])):raise ValueError('Stale source-map native copper land '+uid)
    fills=collect_native_reference_fills(board,set(SEEDS.values())-{'/CHASSIS'},[pcbnew.In1_Cu,pcbnew.In4_Cu])
    vias=[t for t in board.GetTracks()if isinstance(t,pcbnew.PCB_VIA)and t.GetViaType()==pcbnew.VIATYPE_THROUGH]
    via_anchors={};anchor_clusters=[]
    for v in vias:
        uid=v.m_Uuid.AsString()
        if uid in via_anchors:continue
        peers=list(conn.GetConnectedItems(v))
        anchors=[source[p.m_Uuid.AsString()]for p in peers if isinstance(p,pcbnew.PAD)
                 and p.m_Uuid.AsString()in source and p.GetNetname()==v.GetNetname()]
        exact_anchors=[dict(reference=p['reference'],pin=p['pin'],pad_uuid=p['uuid'])for p in anchors]
        cluster_id=len(anchor_clusters)
        anchor_clusters.append(dict(cluster_id=cluster_id,net=v.GetNetname(),
            exact_actual_numbered_source_pad_anchors=exact_anchors))
        # The native graph is frozen throughout this check. Every via in this
        # actual physical component has the same source-pad reachability.
        # Store the full exact source ledger once, rather than rediscovering
        # and duplicating thousands of the same peers for every ground via.
        witness=exact_anchors[:1]
        for q in [v]+[p for p in peers if isinstance(p,pcbnew.PCB_VIA)and p.GetNetname()==v.GetNetname()]:
            via_anchors[q.m_Uuid.AsString()]=dict(cluster_id=cluster_id,witness=witness)
    rows=[];failures=[]
    for (net,layer),fill in sorted(fills.items()):
        for index,piece in enumerate(split_polygons(fill)):
            direct=[p for uid,p in source.items() if p['net']==net and physical_reference_contact(exact[uid],layer,conn)
                    and piece.Contains(exact[uid].GetPosition())]
            stitches=[v for v in vias if v.GetNetname()==net and physical_reference_contact(v,layer,conn)
                      and piece.Contains(v.GetPosition())and via_anchors[v.m_Uuid.AsString()]['witness']]
            row=dict(net=net,reference_layer=board.GetLayerName(layer),filled_piece=index,
                filled_area_mm2=piece.Area()/1e12,
                actual_numbered_through_pad_anchors=[dict(reference=p['reference'],pin=p['pin'],pad_uuid=p['uuid'])for p in direct],
                actual_source_connected_through_stitch_anchors=[dict(uuid=v.m_Uuid.AsString(),position_mm=[pcbnew.ToMM(x)for x in v.GetPosition()],
                    source_pad_anchors=via_anchors[v.m_Uuid.AsString()]['witness'],
                    source_pad_anchor_witness_only=True,
                    actual_native_source_anchor_cluster_id=via_anchors[v.m_Uuid.AsString()]['cluster_id'])for v in stitches],
                passed=bool(direct or stitches))
            rows.append(row)
            if not row['passed']:failures.append(row)
    projections=[]
    for p in mapping['pads']:
        net=return_net(p)
        if not net or net in RAW_RETURNS:continue
        for name in ['In1.Cu','In4.Cu']:
            if not pad_supports_reference(p,name):continue
            layer=board.GetLayerID(name);fill=fills.get((net,layer))
            through=exact[p['uuid']].IsOnLayer(layer)
            projections.append(dict(reference=p['reference'],pin=p['pin'],pad_uuid=p['uuid'],
                reference_net=net,reference_layer=name,actual_own_reference_under_pad_center=bool(fill and fill.Contains(point(p))),
                actual_through_contact=through,
                #Through signal pads have intentional antipads; their nearby
                #return corridor is proved by the ordinary router, not this
                #pad-centre inspection.
                center_antipad_expected=through and p['net']!=net))
    return dict(passed=bool(rows)and not failures,
        scope='actual adjacent reference resource anchoring; SMD local return loops and supply delivery separately required',
        exact_source_pad_inventory_checked=len(source),filled_component_count=len(rows),
        all_filled_components_physically_source_anchored=not failures,
        filled_components=rows,unanchored_components=failures,pad_reference_projection_rows=projections,
        exact_native_source_anchor_clusters=anchor_clusters,
        all_SMD_return_pads_physically_joined_claim=False,high_current_capacity_claim=False,
        measured_impedance=False,physical_qualification=False,manufacturing_ready=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--board',type=Path,required=True)
    p.add_argument('--map',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    mapping=json.loads(a.map.read_text(encoding='utf-8'));board=pcbnew.LoadBoard(str(a.board))
    result=validate(board,mapping);result['board_sha256']=sha(a.board);result['source_map_sha256']=sha(a.map)
    write(a.out,result);print(json.dumps({k:v for k,v in result.items()if k not in ['filled_components','unanchored_components','pad_reference_projection_rows','exact_native_source_anchor_clusters']},indent=2))
    raise SystemExit(not result['passed'])


if __name__=='__main__':main()
