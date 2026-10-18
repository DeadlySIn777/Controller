"""Separate exact critical-digital prototype route executor.

This reuses frozen additive identity/DSN/SES/native-return primitives. It never
changes the ordinary112 validator or source review. Critical rows require their
own frozen source and prototype geometry reviews, exact board/plane binding and
explicit numeric conductor rules. Physical GPIO/clock/EMC timing stays unproved.
"""
from pathlib import Path
import json,sys
import hardware_route_selected_additive_r03 as strict
import hardware_check_return_corridors_r03 as fast

prior=strict.prior
original_transform_dsn=prior.transform_dsn
SOURCE_REVIEW=Path('reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/critical-digital-source-review.json')
GEOMETRY_REVIEW=Path('reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/prototype-route-geometry-review.json')
ORDINARY=Path('reports/motherboard-ordinary-routing-20261001/source26-review-r08/ordinary-source-review.json')
SOURCE_REVIEW_SHA='e7eef53c41f9a3c9db037ac36b9f368ae74cc4f0086333e3607482f07509547c'
GEOMETRY_REVIEW_SHA='eab1219c0f444a85142121b255c5cf8e3f7998bc94b51a60f82787a79c8027db'
CLASSES={
 'IOL1_point_to_point_clocked_lane','asynchronous_supervised_reset',
 'compute_FPGA_host_SPI','FPGA_configuration','reference_oscillator_clock',
 'reset_configuration_qualification','isolated_analog_host_SPI',
 'isolated_ADC_DAC_SPI','isolated_SPI_MISO_gated_return',
 'isolated_power_qualified_analog_reset_enable','asynchronous_permission_and_strobe',
 'isolated_smart_output_host_SPI','isolated_smart_output_field_SPI','isolated_hard_permission'}

def check_row(name,row,review,geometry,board_nets,layers,nodes):
 if name not in board_nets or name not in review['nets'] or name not in geometry['nets']:
  raise ValueError('Critical net absent or lacks exact source/geometry review: '+name)
 if name in prior.read(prior.ROOT/ORDINARY)['nets']:
  raise ValueError('Critical executor does not own ordinary112 net: '+name)
 expected=geometry['nets'][name]
 if row!=expected:raise ValueError('Critical row differs from frozen geometry: '+name)
 source=review['nets'][name]
 for field in ('source_pins','source_endpoints','return_net','type','signal_class','maximum_voltage_v'):
  if row[field]!=source[field]:raise ValueError('Source/pin/domain changed:'+name+'/'+field)
 if row['type']!='critical_digital' or row['signal_class']not in CLASSES:
  raise ValueError('Explicit reviewed critical digital class required:'+name)
 if row['maximum_voltage_v']not in (3.3,5.0):raise ValueError('Unreviewed signal voltage:'+name)
 if not .15<=row.get('width_mm',0)<=.45 or not .15<=row.get('clearance_mm',0)<=.25:
  raise ValueError('Reviewed prototype conductor dimensions required:'+name)
 if not row.get('prototype_geometry_authorized') or row.get('operating_profile_qualified')is not False:
  raise ValueError('Separate prototype geometry vs loaded timing evidence required:'+name)
 if row.get('impedance_factory_qualified')is not False:
  raise ValueError('No unquoted factory impedance guarantee:'+name)
 if not row.get('layers')or set(row['reference_layers'])!=set(row['layers']):
  raise ValueError('Every signal layer needs its exact adjacent own reference:'+name)
 for side,ref in row['reference_layers'].items():
  if side not in layers or ref not in layers or abs(layers.index(side)-layers.index(ref))!=1:
   raise ValueError('Non-adjacent reference:'+name)
  if side not in ('F.Cu','B.Cu')or ref!=({'F.Cu':'In1.Cu','B.Cu':'In4.Cu'}[side]):
   raise ValueError('Unreviewed side/reference mapping:'+name)
 if row['return_net']not in board_nets or not .2<=row['reference_corridor_margin_mm']<=.6:
  raise ValueError('Real own return and bounded corridor required:'+name)
 if sorted(map(tuple,row['source_pins']))!=sorted(nodes.get(name,[])):
  raise ValueError('Complete actual native source inventory required:'+name)
 for p in row['source_endpoints']:
  if not p.get('mpn')or ('function'not in p)or(p['reference'].startswith('U')and (not p.get('actual_return_pins')or not p['function'])):
   raise ValueError('Active source endpoint lacks exact part/pin/return:'+name)
 if row['allow_vias']not in (False,True):raise ValueError('Via decision is explicit:'+name)
 if row['allow_vias']and(row['via_diameter_mm']!=.6 or row['via_drill_mm']!=.3 or not 0<row['return_stitch_distance_mm']<=1):
  raise ValueError('Exact reviewed through-via/return-stitch geometry required:'+name)
 if row.get('allow_unreferenced_escape')or row.get('allow_isolation_barrier_crossing'):
  raise ValueError('No blanket package or isolation exception:'+name)

def frozen_review_check(manifest,design,netlist):
 prior.checked_dependencies()
 fast.dependencies()
 for label in ('source_review','geometry_review','plane_review'):
  e=manifest.get(label,{})
  if not e.get('path')or not e.get('sha256')or prior.sha(e['path'])!=e['sha256']:
   raise ValueError('Frozen critical evidence required:'+label)
 if Path(manifest['source_review']['path']).resolve()!= (prior.ROOT/SOURCE_REVIEW).resolve():
  raise ValueError('Only issued exact source26 critical review accepted')
 if Path(manifest['geometry_review']['path']).resolve()!= (prior.ROOT/GEOMETRY_REVIEW).resolve():
  raise ValueError('Only issued exact source26 prototype geometry review accepted')
 if manifest['source_review']['sha256']!=SOURCE_REVIEW_SHA or manifest['geometry_review']['sha256']!=GEOMETRY_REVIEW_SHA:
  raise ValueError('Issued critical source/geometry immutable hashes differ')
 r=prior.read(manifest['source_review']['path']);g=prior.read(manifest['geometry_review']['path']);p=prior.read(manifest['plane_review']['path'])
 if not r.get('passed')or r['source_design_sha256']!=prior.sha(design)or r['source_netlist_sha256']!=prior.sha(netlist):
  raise ValueError('Exact current electrical source hash binding failed')
 if not g.get('passed')or not g.get('prototype_geometry_authorized')or g['source_review_sha256']!=manifest['source_review']['sha256']:
  raise ValueError('Exact separate prototype geometry review failed')
 if g['ordinary112_sha256']!=prior.sha(prior.ROOT/ORDINARY):
  raise ValueError('Geometry review no longer preserves ordinary112')
 for name,field in [('primary-timing-facts.json','primary_timing_sha256'),('independent-review.json','supporting_independent_review_sha256')]:
  if prior.sha((prior.ROOT/GEOMETRY_REVIEW).parent/name)!=g[field]:
   raise ValueError('Critical primary/source independent evidence changed:'+name)
 if p.get('passed')is not True or p.get('board_sha256')!=manifest['board_sha256']:
  raise ValueError('Passed actual same-board plane receipt required')
 if manifest.get('ordinary112_sha256')!=prior.sha(prior.ROOT/ORDINARY):
  raise ValueError('The frozen ordinary112 evidence changed')
 if manifest.get('manufacturing_ready')is not False or manifest.get('operating_profile_qualified')is not False:
  raise ValueError('Prototype routing does not prove timing/manufacturing')
 return dict(critical_source_review_sha256=manifest['source_review']['sha256'],critical_geometry_review_sha256=manifest['geometry_review']['sha256'],plane_review_sha256=manifest['plane_review']['sha256'],critical_executor_sha256=prior.sha(Path(__file__)),**prior.checked_dependencies())

def manifest_check(manifest,board_nets,board_layers,node_inventory):
 if manifest.get('schema_version')!=3 or manifest.get('type')!='critical_digital_prototype':
  raise ValueError('Separate critical digital prototype schema required')
 r=prior.read(manifest['source_review']['path']);g=prior.read(manifest['geometry_review']['path'])
 rows=manifest.get('nets')
 if not isinstance(rows,dict)or not rows:raise ValueError('No exact selected critical nets')
 for n,row in rows.items():check_row(n,row,r,g,board_nets,board_layers,node_inventory)
 return rows

def install():
 strict.install()
 prior.manifest_check=manifest_check
 prior.frozen_review_check=frozen_review_check
 prior.return_corridor_check=fast.return_corridor_check
 # In this isolated executor process only, proposal helpers inherit the same
 # exact native fill/actual-annulus guard. Historical files stay unchanged.
 fast.strict.prior.ReturnCheck=fast.NativeCollectedAnnulusCheck
 prior.transform_dsn=transform_dsn

def transform_dsn(tree,rows):
 transformed,receipt=original_transform_dsn(tree,rows)
 network=prior.child(transformed,'network')
 for node in prior.children(network,'class'):
  old=prior.value(node[1])
  if old.startswith('Reviewed_ordinary_'):
   node[1]=prior.q(old.replace('Reviewed_ordinary_','Reviewed_critical_',1))
 receipt['selection_scope']='exact independently reviewed critical digital prototype'
 return transformed,receipt

def main():
 install();prior.main()
 out=Path(sys.argv[sys.argv.index('--out')+1]).resolve()
 target=out/('prepare.json'if sys.argv[1]=='prepare'else'receipt.json')
 r=prior.read(target)
 r.update(scope='Exact selected critical digital prototype; no ordinary112, power, precision or display/network promotion.',
  critical_executor_sha256=prior.sha(Path(__file__)),
  critical_source_review_sha256=SOURCE_REVIEW_SHA,
  prototype_geometry_review_sha256=GEOMETRY_REVIEW_SHA,
  exact_nonempty_actual_annulus_dependencies=fast.dependencies(),
  actual_reference_checker_sha256=prior.sha(Path(fast.__file__)),
  operating_profile_qualified=False,impedance_factory_qualified=False,
  manufacturing_ready=False,old_ordinary112_unchanged=True)
 prior.write(target,r)

if __name__=='__main__':main()
