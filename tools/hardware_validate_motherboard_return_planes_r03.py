"""Strict resource audit with positive literal native filled-metal provenance.

The previous resource audit remains frozen. Native Boolean union can emit a
nanometre-scale derived polygon that intersects none of its literal operands.
Such a computation artifact is retained in the ledger but cannot authorize a
route or become a physical copper island. A real small island still requires
the exact same physical Source anchor as every other native filled resource.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_zone_motherboard_returns import split_polygons
from hardware_validate_motherboard_return_planes_r02 import validate as frozen_validate


def positive_literal_contact(derived,literal_pieces):
    """Require positive native intersection area; never use a size tolerance."""
    for metadata,actual in literal_pieces:
        if not derived.Collide(actual):
            continue
        intersection=pcbnew.SHAPE_POLY_SET()
        intersection.Append(derived)
        intersection.BooleanIntersection(actual)
        if intersection.Area()>0:
            return dict(**metadata,actual_intersection_area_nm2=intersection.Area())
    return None


def add_literal_provenance(board,original):
    nets={r['net']for r in original['filled_components']}
    layers=[pcbnew.In1_Cu,pcbnew.In4_Cu]
    fills=collect_native_reference_fills(board,nets,layers)
    derived={k:list(split_polygons(v))for k,v in fills.items()}
    literal={}
    for zone in board.Zones():
        if zone.GetIsRuleArea()or zone.GetNetname()not in nets:
            continue
        for layer in layers:
            if not zone.IsOnLayer(layer):
                continue
            for index,piece in enumerate(split_polygons(zone.GetFilledPolysList(layer))):
                if piece.Area()<=0:
                    continue
                metadata=dict(zone_uuid=zone.m_Uuid.AsString(),literal_filled_piece=index,
                              literal_native_area_nm2=piece.Area())
                literal.setdefault((zone.GetNetname(),layer),[]).append((metadata,piece))
    rows=[];artifacts=[];unanchored=[]
    for row in original['filled_components']:
        key=(row['net'],board.GetLayerID(row['reference_layer']))
        shape=derived[key][row['filled_piece']]
        witness=positive_literal_contact(shape,literal.get(key,[]))
        current=dict(row,literal_native_positive_metal_provenance=witness)
        if witness is None:
            current.update(physical_copper_resource=False,passed=False,
                           route_coverage_or_source_anchor_authorization=False,
                           disposition='Derived Boolean polygon has zero positive-area intersection with every actual same-net/layer literal native filled operand. Computation artifact retained; physical copper unchanged.')
            artifacts.append(current)
        else:
            current['physical_copper_resource']=True
            rows.append(current)
            if not current['passed']:
                unanchored.append(current)
    result=dict(original)
    result.update(schema_version=3,scope='Positive literal native filled copper and actual adjacent Source resource anchoring; local loops/current/corridor coverage remain separately required',
                  passed=bool(rows)and not unanchored,filled_components=rows,
                  filled_component_count=len(rows),unanchored_components=unanchored,
                  all_filled_components_physically_source_anchored=bool(rows)and not unanchored,
                  derived_nonphysical_computation_artifacts=artifacts,
                  frozen_original_resource_report=original,
                  route_coverage_guard_changed=False,native_copper_modified=False,
                  source_anchor_requirement_weakened=False,manufacturing_ready=False)
    return result


def validate(board,mapping):
    return add_literal_provenance(board,frozen_validate(board,mapping))


def main():
    p=argparse.ArgumentParser();p.add_argument('--board',type=Path,required=True);p.add_argument('--map',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();b=pcbnew.LoadBoard(str(a.board));r=validate(b,json.loads(a.map.read_text()))
    r.update(board_sha256=sha(a.board),source_map_sha256=sha(a.map),analyzer_sha256=sha(Path(__file__)))
    write(a.out,r)
    print(json.dumps(dict(passed=r['passed'],physical_native_resources=r['filled_component_count'],unanchored=len(r['unanchored_components']),derived_nonphysical=len(r['derived_nonphysical_computation_artifacts']),board_sha256=r['board_sha256']),indent=2))


if __name__=='__main__':main()
