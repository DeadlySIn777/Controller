"""Correct the physical reference aperture without changing the exact own guard or mask checks."""
from pathlib import Path
P=Path(__file__).resolve().parent
source=(P/'nominate_R371_coupled_both_functions_F_reconnect_r392.py').read_text(encoding='utf-8')
source=source.replace("CM79-R371-coupled-both-resistor-functions-actual-F-source-reconnect-r392","CM79-R371-coupled-both-functions-F-reconnect-native-antipad-bound-r393").replace('R392','R393')
old="ref=fullref.difference(Z.bounded_buffer(sig,.525));allowed=ref if cap is None else unary_union([ref,cap]);"
new="nativeLGop=next(x for x in pose['selected_ordinary_ENC_port']['explicit_normal_native_same_domain_fill_hole_operations']if L.norm(x['raw_net'])=='/LOGIC_GND'and x['layer']=='In1.Cu'); nativeZone=next(z for z in c['zones']if z['uuid']==nativeLGop['UUID']); actualNativeRadius=.25+float(nativeZone['clearance_mm']); assert abs(actualNativeRadius+.025-nativeLGop['only_normal_native_new_via_antipad_radius_mm'])<1e-9; ref=fullref.difference(sig.buffer(actualNativeRadius,quad_segs=128)); allowed=ref if cap is None else unary_union([ref,cap]);"
assert source.count(old)==1;source=source.replace(old,new)
source=source.replace("'same_Cu_reference_free_face':face is not None}","'same_Cu_reference_free_face':face is not None,'start_in_free':free.covers(Point(*start)),'end_in_free':free.covers(Point(*end)),'actual_native_LG_antipad_radius_mm':actualNativeRadius,'same_exact_terminal_guard_radius_mm':radius if cap is not None else None,'native_LG_zone_clearance_mm':float(nativeZone['clearance_mm']),'larger_conservative_R388_old_mask_guards_retained':True}")
E=P/'exact-expanded-coupled-F-reconnect-actual-native-antipad-r393.py';assert not E.exists();E.write_text(source,encoding='utf-8');exec(compile(source,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
