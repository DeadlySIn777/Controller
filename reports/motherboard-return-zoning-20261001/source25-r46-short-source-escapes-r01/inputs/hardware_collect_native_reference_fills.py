"""Union actual native filled polygons once per exact return net/layer.

This reads retained native metal only. It never fills an outline, borrows a
different net or side, invents connectivity, or modifies the native board.
"""
import pcbnew


def collect_native_reference_fills(board,return_nets,layers):
    result={}
    for zone in board.Zones():
        if zone.GetIsRuleArea()or zone.GetNetname()not in return_nets:continue
        for layer in layers:
            if zone.HasFilledPolysForLayer(layer):
                actual=zone.GetFilledPolysList(layer)
                if actual.Area():result.setdefault((zone.GetNetname(),layer),pcbnew.SHAPE_POLY_SET()).Append(actual)
    for poly in result.values():poly.Simplify()
    return result
