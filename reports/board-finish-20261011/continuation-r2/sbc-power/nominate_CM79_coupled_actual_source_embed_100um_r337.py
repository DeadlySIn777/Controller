"""Preserve R336 near-tangent evidence; require actual source-Cu embedding."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent.parent
p=H/'sbc-power/CM79-exact-R333-q4f-q053-only-local-coupled-In2-corridor-nominations-r336/exact-expanded-coupled-local-nomination.py'
assert hashlib.sha256((p.parent/'receipt.json').read_bytes()).hexdigest()=='570c6f7aa3d1fe5f562153a85f3ecce00055b4c9db50adfeb7ede8ce304e34be'
s=p.read_text(encoding='utf-8').replace('corridor-nominations-r336','corridor-nominations-source-embed100um-r337').replace('R336_ROUTE','R337_ROUTE').replace('R336_COMPLETE','R337_COMPLETE').replace('R336_FRESH_CORE5_SOURCE','R337_BOUND_BEFORE_CORE5_SOURCE').replace('R336_FRESH_CM_SOURCE','R337_BOUND_BEFORE_CM_SOURCE')
needle='available=face.intersection(buf(target,.624995)).buffer(-.000005)'
assert s.count(needle)==1
s=s.replace(needle,'available=face.intersection(zero(target.buffer(-.10))).buffer(-.000005)')
s=s.replace("'source_Cu_finite_overlap_mm2':tap.area", "'source_Cu_finite_overlap_mm2':tap.area,'endpoint_embedded_in_actual_source_Cu':target.covers(Point(path[-1])),'actual_source_endpoint_boundary_distance_mm':Point(path[-1]).distance(target.boundary),'required_actual_source_embed_depth_mm':.10")
s=s.replace("'full_new_track_width_mm':1.25", "'full_new_track_width_mm':1.25,'required_actual_source_endpoint_embed_depth_mm':.10,'near_tangent_R336_source_contact_not_qualified':True")
s=s.replace("if tap.is_empty or tap.area<=0 or contact.is_empty or contact.area<=0:continue", "if tap.is_empty or tap.area<=0 or contact.is_empty or contact.area<=0 or not target.covers(Point(path[-1]))or Point(path[-1]).distance(target.boundary)<.10:continue")
exec(compile(s,str(__file__),'exec'))
