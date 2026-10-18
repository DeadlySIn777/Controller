"""Derive a specific F/In3/B ordinary two-pair fault return constructor."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent
source=H/'construct_DI15_current_ordinary_F_In2_F_pairs_r592.py';dest=H/'construct_DOB_FLT_current_ordinary_F_In3_B_pairs_r610.py';assert not dest.exists();text=source.read_text()
replacements={
 "Fresh paired DI15 constructor":"Fresh paired DOB fault constructor",
 "Both actual native pads are bare. No DI13/native copper is removed.":"Both actual native pads are bare. All retained power and old fault Cu remain fixed.",
 "OUT=H/'DI15-current-ordinary-F-In2-F-two-pair-constructor-r592';NET='/motherboard_di/DI15_LOGIC'":"OUT=H/'DOB-FLT-current-ordinary-F-In3-B-two-pair-constructor-r610';NET='/motherboard_do/DOB_FLT_N_HOST'",
 "p['uuid']=='f5027315-3d7a-42d1-b8e2-6e07075d2842'":"p['uuid']=='687076c9-e72b-4f73-bee8-388533f33e85'",
 "p['uuid']=='b9ed640f-51d8-4121-a94d-4a29c6058751'":"p['uuid']=='fb059143-4c20-4229-84d2-a42d1497388c'",
 "win=box(115,86,136,118)":"win=box(200,52,228,92)",
 "[119.835668,89.798413]":"[218.5,84.7]",
 "[131.25,112.35]":"[210.0,60.8]",
 "native=census['native_refs']['In1.Cu'];reference=hostref.intersection(native);":"native=census['native_refs']['In1.Cu'];reference=hostref.intersection(native);reference4=unary_union([r['shape']for r in root if r['kind']=='fill'and r['layer']=='In4.Cu']).intersection(census['native_refs']['In4.Cu']);",
 "inner=free[NET,'In2.Cu'].intersection(refsafe);":"inner=free[NET,'In3.Cu'].intersection(reference4.intersection(win.buffer(1)).buffer(-.105));bb=free[NET,'B.Cu'].intersection(reference4.intersection(win.buffer(1)).buffer(-.105));",
 "fctarget=[s for s in pieces(ff)if s.covers(Point(end))]":"fctarget=[s for s in pieces(bb)if s.covers(Point(end))]",
 "retRegion=vr[LG].intersection(reference)":"retRegion=vr[LG].intersection(reference).intersection(reference4)",
 "('In2.Cu',a['signal'],z['signal'],inner),('F.Cu',z['signal'],end,ff)":"('In3.Cu',a['signal'],z['signal'],inner),('B.Cu',z['signal'],end,bb)",
 "R592_":"R610_",
 "only-NEW-DI15-three-leg-two-ordinary-pair-NOMINEE.pkl":"only-NEW-DOB-FLT-three-leg-two-ordinary-pair-NOMINEE.pkl",
 "CURRENT_DI15_":"CURRENT_DOB_FLT_",
 "actual_R590_native_original_endpoints_and_source_refs_SHA256":"actual_R590_native_J1_source_refs_only_SHA256",
 "all_original_DI13_FAULT_native_or_positive_current_power_Cu_fixed":"all_original_current_power_fault_and_peer_Cu_fixed",
 "'reference_layer':'In1.Cu','used_leg_layers':['F.Cu','In2.Cu','F.Cu']":"'reference_layers':['In1.Cu','In4.Cu'],'used_leg_layers':['F.Cu','In3.Cu','B.Cu']",
 "'real_source_connected_used_In1_returns_not_generic_plane_name_or_sameplane_waiver':True":"'real_source_connected_both_In1_In4_returns_no_generic_plane_waiver':True",
}
for old,new in replacements.items():assert old in text,old;text=text.replace(old,new)
text=text.replace("start=[sourcepad['x'],sourcepad['y']];end=[targetpad['x'],targetpad['y']];", "assert(sourcepad['ref'],str(sourcepad['num']),K.L.norm(sourcepad['net']))==('U10016','7',NET);assert(targetpad['ref'],str(targetpad['num']),K.L.norm(targetpad['net']))==('U13008','15',NET);start=[sourcepad['x'],sourcepad['y']];end=[targetpad['x'],targetpad['y']];")
text=text.replace("+.030","+.025")
old="if rr:choices.append({'signal':at,'returns':[r for r in rr if .9<=math.dist(at,r)<=1]})"
new="rr=[r for r in rr if .9<=math.dist(at,r)<=1 and all(Point(r).buffer(.225,quad_segs=128).difference(Point(r).buffer(.125,quad_segs=128)).intersection(ref).area>.005 for ref in(reference,reference4))]\n   if rr:choices.append({'signal':at,'returns':rr})"
assert old in text;text=text.replace(old,new)
dest.write_text(text);print('R610_SCRIPT',hashlib.sha256(dest.read_bytes()).hexdigest())
