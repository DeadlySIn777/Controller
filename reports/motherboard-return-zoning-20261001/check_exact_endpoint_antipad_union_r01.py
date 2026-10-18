"""Equivalent endpoint exception with one final native Boolean subtraction.

The frozen actual via geometry, annulus and numbered Source-connected stitch
checks run first. Only those exact reviewed same-net endpoint circles join
the actual filled reference for the final coverage calculation. No tolerance,
minimum-area exemption, missing Source bridge, or extra circle is accepted.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck
from hardware_check_return_corridors import circle,covered
from hardware_route_selected_additive import corridor_polygon

class ExactEndpointUnionCheck(NativeCollectedAnnulusCheck):
 def segment(self,track,row):
  if track.Type()!=pcbnew.PCB_TRACE_T:raise ValueError('Only actual declared straight signal segments are supported')
  name=self.board.GetLayerName(track.GetLayer())
  if name not in row['reference_layers']:raise ValueError('Segment reference layer is undeclared')
  if track.GetNetname()not in self.rows:raise ValueError('Actual signal net lacks frozen declaration')
  layer=self.board.GetLayerID(row['reference_layers'][name]);fill=self.reference(row['return_net'],layer)
  augmented=pcbnew.SHAPE_POLY_SET();augmented.Append(fill);exceptions=[]
  for endpoint in(tuple(track.GetStart()),tuple(track.GetEnd())):
   for via in self.vias:
    if via.GetNetname()!=track.GetNetname()or tuple(via.GetPosition())!=endpoint:continue
    # Retain the complete frozen native physical annulus/Source proof.
    audit=self.via(via,row)
    radius=pcbnew.FromMM(audit['bounded_antipad_radius_mm'][self.board.GetLayerName(layer)])
    augmented.BooleanAdd(circle(endpoint,radius));exceptions.append(via.m_Uuid.AsString())
  corridor=corridor_polygon(tuple(track.GetStart()),tuple(track.GetEnd()),track.GetWidth()/2+pcbnew.FromMM(row['reference_corridor_margin_mm']))
  if not covered(corridor,augmented):raise ValueError('Actual signal corridor crosses a foreign hole or unqualified own-reference boundary')
  return dict(uuid=track.m_Uuid.AsString(),reference_net=row['return_net'],reference_layer=self.board.GetLayerName(layer),full_geometric_projected_corridor_covered=True,explicit_endpoint_antipad_vias=exceptions,exact_equivalent_one_subtraction_algebra=True,no_radius_margin_or_Source_requirement_change=True)
