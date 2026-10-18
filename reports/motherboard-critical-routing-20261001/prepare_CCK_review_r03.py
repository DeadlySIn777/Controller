from pathlib import Path
p=Path('reports/motherboard-critical-routing-20261001/review_actual_CCK_r06_r02.py');s=p.read_text().replace("OUT=P/'actual-native-source-return-r02'","OUT=P/'actual-native-source-return-r03'")
old="checker=pieces.SourceAnchoredPiecesCheck(board,{name:row},e.read(MAP));results=[];failures=[]"
new="""literal_vias={
 plan['new_signal_UUIDs'][-2]:dict(position=[95.2,46.4],diameter_mm=.5,drill_mm=.2),
 plan['new_signal_UUIDs'][-1]:dict(position=[109.,27.],diameter_mm=.6,drill_mm=.3),
}
class LiteralMixedViaCheck(pieces.SourceAnchoredPiecesCheck):
 def via(self,signal,route_row):
  u=signal.m_Uuid.AsString()
  if u not in literal_vias:raise ValueError('A via is outside exact two-via CCK declaration')
  d=literal_vias[u]
  if signal.GetNetname()!=name or list(mm(signal.GetPosition()))!=d['position'] or abs(pcbnew.ToMM(signal.GetWidth())-d['diameter_mm'])>1e-6 or abs(pcbnew.ToMM(signal.GetDrill())-d['drill_mm'])>1e-6:raise ValueError('Literal CCK via geometry changed')
  exact=copy.deepcopy(route_row);exact.update(via_diameter_mm=d['diameter_mm'],via_drill_mm=d['drill_mm'])
  return super().via(signal,exact)
e.write(OUT/'literal-mixed-via-declaration.json',dict(source_net=name,Source_pair=plan['actual_Source_pair'],source_geometry_review_sha256=e.sha(REVIEW),source_design_sha256=e.sha('hardware/motherboard/design.json'),source_netlist_sha256=e.sha('hardware/motherboard/netlist.xml'),literal_via_geometry=literal_vias,reference_layers=row['reference_layers'],reference_corridor_margin_mm=.40,return_annulus_mm=.20,Source_ground_stitch_max_distance_mm=1.,existing_BGA_pad_via_clearance_mm=.125,frozen_single_diameter_manifest_unchanged=True,frozen_geometric_checker_unchanged=True,no_general_via_dimension_exception=True,exact_factory_2oz_process_confirmation_pending=True,manufacturing_ready=False))
checker=LiteralMixedViaCheck(board,{name:row},e.read(MAP));results=[];failures=[]"""
assert old in s;s=s.replace(old,new)
Path('reports/motherboard-critical-routing-20261001/review_actual_CCK_r06_r03.py').write_text(s)
