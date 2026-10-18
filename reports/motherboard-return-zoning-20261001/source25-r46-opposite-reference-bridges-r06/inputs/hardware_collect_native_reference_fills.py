"""Union actual nonempty native filled polygons per exact return net/layer.

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
                # Preserve the native sequential BooleanAdd geometry exactly.
                # Empty default fill lists can be reported as present for
                # other enabled layers; repeatedly adding them needlessly
                # re-clips large contours. Append/Simplify differs at tiny
                # rounding slivers on the actual board and is not adopted.
                if actual.Area():result.setdefault((zone.GetNetname(),layer),pcbnew.SHAPE_POLY_SET()).BooleanAdd(actual)
    return result
