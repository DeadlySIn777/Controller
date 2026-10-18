"""Same R318 direct whole-body support tests, exact disjoint broad phase only."""
from pathlib import Path
import hashlib
p=Path(__file__).with_name('screen_CM79_exact_native_plane_antipads_supported_old_Cu_r318.py')
s=p.read_text(encoding='utf-8')
s=s.replace("'sbc-power/CM79-exact-native-LG-plane-antipad-supported-old-B-and-F-anchor-screen-r318'", "'sbc-power/CM79-native-local-antipad-direct-old-body-disjoint-screen-r320'")
s=s.replace("bodyrows=[];dom=h['domains_normalized'];LG=dom['/LOGIC_GND']", "bodyrows=[];omitted=[];dom=h['domains_normalized'];LG=dom['/LOGIC_GND'];max_native_LG_local=max(float(z['clearance_mm'])for z in c['zones']if z['net']=='/LOGIC_GND');maxradius=max(.375,.25+max(max_native_LG_local,.15)+.025);halo=zero(unary_union([Z.bounded_buffer(Point(rr['power']['x'],rr['power']['y']),maxradius+.000000003)for pp in pairs.values()for rr in pp])).envelope;(O/'conservative-all-candidate-native-antipad-envelope.wkb').write_bytes(halo.wkb)")
s=s.replace("body=zero(L.body(t));support=body.intersection(bank['B.Cu'])", "body=zero(L.body(t));\n  if not body.envelope.intersects(halo):omitted.append({'old_track_UUID':t['uuid'],'whole_old_body_envelope_disjoint_from_every_conservative_native_antipad_halo':True});continue\n  support=body.intersection(bank['B.Cu'])")
s=s.replace("put(O/'exact-actual-source-plane-local-antipad-authority.json',planes)", "put(O/'exact-actual-source-plane-local-antipad-authority.json',planes);put(O/'exact-full-body-disjoint-broad-phase-ledger.json',{'frozen_parent_script_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'halo_envelope_sha256':sha(O/'conservative-all-candidate-native-antipad-envelope.wkb'),'max_native_LG_local_mm':max_native_LG_local,'max_actual_native_antipad_radius_mm':maxradius,'unchanged_full_old_body_direct_BEFORE_reference_intersection':True,'all_omitted_old_B_bodies':omitted})")
s=s.replace('R318_COMPLETE','R320_COMPLETE')
s=s.replace("started=time.monotonic();assert not O.exists();O.mkdir();", "started=time.monotonic();assert not O.exists();O.mkdir();(O/'exact-expanded-screen.py').write_text(s,encoding='utf-8');")
exec(compile(s,str(p),'exec'))
