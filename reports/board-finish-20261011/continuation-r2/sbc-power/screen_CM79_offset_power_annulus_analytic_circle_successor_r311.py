"""Same finite offset screen, conservative analytic circle distances, no gain."""
from pathlib import Path
import hashlib
p=Path(__file__).with_name('screen_CM79_offset_power_annulus_fullwidth_ordinary_pairs_r310.py')
s=p.read_text(encoding='utf-8')
s=s.replace("'sbc-power/CM79-offset-power-annulus-fullwidth-ordinary-pair-screen-r310'","'sbc-power/CM79-offset-power-annulus-fullwidth-ordinary-pair-analytic-screen-r311'")
s=s.replace("disk=pt.buffer(.25,quad_segs=128)","disk=set_precision(Z.bounded_buffer(pt,.25),0)")
s=s.replace("disk.distance(sh)<gap(net,n)+.025003","pt.distance(sh)-.25<gap(net,n)+.025003")
s=s.replace("'gap':disk.distance(sh)","'gap':pt.distance(sh)-.25")
s=s.replace("disk.distance(sh)<.025003","pt.distance(sh)-.25<.025003")
s=s.replace("disk.distance(mid)<.175003","pt.distance(mid)-.25<.175003")
s=s.replace("R310_SIDE","R311_SIDE").replace("R310_COMPLETE","R311_COMPLETE")
s=s.replace("started=time.monotonic();assert not O.exists();O.mkdir();", "started=time.monotonic();assert not O.exists();O.mkdir();put(O/'exact-successor-scope.json',{'parent_script_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'analytic_point_to_actual_Cu_distance_minus_full_Cu_radius_mm':.25,'same_finite_grid':True,'no_clearance_or_source_obstacle_relaxed':True});(O/'exact-expanded-screen.py').write_text(s,encoding='utf-8');")
exec(compile(s,str(p),'exec'))
