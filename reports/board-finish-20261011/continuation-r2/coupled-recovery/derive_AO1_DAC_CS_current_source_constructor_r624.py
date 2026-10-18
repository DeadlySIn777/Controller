"""Fresh AO1 DAC-CS constructor from actual COM cache and four VREF peers."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;src=H/'construct_DOB_FLT_current_ordinary_F_In3_B_pairs_r610.py';dest=H/'construct_AO1_DAC_CS_current_ordinary_F_In3_B_pairs_r624.py';assert not dest.exists();text=src.read_text();rp=H/'AO1-COM-actual-full-native-current-source-and-two-residual-port-binding-r622/receipt.json';r=json.loads(rp.read_bytes())
replacements={
 "Fresh paired DOB fault constructor":"Fresh paired AO1 DAC-CS constructor",
 "OUT=H/'DOB-FLT-current-ordinary-F-In3-B-two-pair-constructor-r610';NET='/motherboard_do/DOB_FLT_N_HOST';LG='/LOGIC_GND'":"OUT=H/'AO1-DAC-CS-current-ordinary-F-In3-B-two-pair-constructor-r624';NET='/motherboard_analog_output/AO1_DAC_CS_N';LG='/motherboard_analog_output/AO1_COM'",
 "p['uuid']=='687076c9-e72b-4f73-bee8-388533f33e85'":"p['uuid']=='5bd36a6a-0ece-4d8a-bb54-e362786d2249'",
 "p['uuid']=='fb059143-4c20-4229-84d2-a42d1497388c'":"p['uuid']=='6cc6e8f2-29a9-482e-a9b7-c53dea062394'",
 "('U10016','7',NET)":"('U14626','7',NET)",
 "('U13008','15',NET)":"('R14633','1',NET)",
 "win=box(200,52,228,92)":"win=box(368,121,389,154)",
 "[218.5,84.7]":"[374.05,127.8]",
 "[210.0,60.8]":"[381.3,145.0]",
 "R610_":"R624_",
 "only-NEW-DOB-FLT-three-leg-two-ordinary-pair-NOMINEE.pkl":"only-NEW-AO1-DAC-CS-three-leg-two-ordinary-pair-NOMINEE.pkl",
 "CURRENT_DOB_FLT_":"CURRENT_AO1_DAC_CS_",
 "actual_R590_native_J1_source_refs_only_SHA256":"actual_R622_native_and_current_AO1_COM_refs_SHA256",
}
for old,new in replacements.items():assert old in text,old;text=text.replace(old,new)
begin=text.index('gp=pin(');end=text.index('sourcefile=pin(',begin)
prefix="cp=pin(H/'AO1-COM-actual-full-native-current-source-and-two-residual-port-binding-r622/exact_actual_current_AO1_COM_source_and_ports_NOMINATION_ONLY.pkl','"+r['cached_source_port_SHA256']+"');census=pickle.loads(cp.read_bytes());reference=census['references']['In1.Cu'];reference4=census['references']['In4.Cu'];native=census['native_refs']['In1.Cu'];root=census['current_root'];"
text=text[:begin]+prefix+text[end:]
old="win=box(368,121,389,154);rec,trees=K.F.build({**h,'zones':[]});"
new="win=box(368,121,389,154);reference=reference.intersection(win.buffer(2));reference4=reference4.intersection(win.buffer(2));peertracks=[];peervias=[]\n for peer in census['VREF_four_hard_peer_items']:\n  if peer['kind']=='segment':peertracks.append({'uuid':peer['uuid'],'net':peer['net'],'layer':peer['layer'],'a':peer['a'],'b':peer['b'],'w':peer['w']})\n  else:assert peer['kind']=='via';peervias.append({'uuid':peer['uuid'],'net':peer['net'],'x':peer['at'][0],'y':peer['at'][1],'d':peer['d'],'drill':peer['drill'],'flashed':list(K.LAYERS)})\n planner_h={**h,'tracks':h['tracks']+peertracks,'vias':h['vias']+peervias};rec,trees=K.F.build({**planner_h,'zones':[]});"
assert old in text;text=text.replace(old,new)
text=text.replace("holes,ht=K.hole_context(h)","holes,ht=K.hole_context(planner_h)")
text=text.replace("for v in h['vias']","for v in planner_h['vias']")
text=text.replace("'ordinary_signal_return_window_mm':[.9,1.0]","'ordinary_signal_return_window_mm':[.9,1.0],'source_reference_root_selector':['U14619','7'],'reference_clipped_to_local_window_plus_2mm_all_used_bodies_inside':True,'VREF_four_prospective_items_HARD_only_not_reference_credit':True")
dest.write_text(text);print('R624_SCRIPT',hashlib.sha256(dest.read_bytes()).hexdigest())
