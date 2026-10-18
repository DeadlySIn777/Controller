"""Preserve the blocked old In3 branch and add an ordinary signal port instead."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'nominate_U10003_complete_relocated_fault_barrel_routes_r170.py';code=source.read_text()
code=code.replace('complete-relocated-fault-barrel-route-nomination-r170','additional-signal-port-old-In3-preserved-nomination-r171')
needle="via={**oldvia,'x':site[0]";assert code.count(needle)==1
code=code.replace(needle,"via={**oldvia,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'U10003-additional-ordinary-signal-port-r171')),'x':site[0]")
old="deletes={'9b04445f-38cf-4932-ac07-a2fa592e7b0a','ec60e344-6c18-4565-8eef-32449e4e88bd','c4e9e150-1f69-573b-bb70-d4d00441eba5','cc078be4-6bc9-5dd0-9194-ede561b48077'}"
new="deletes={'c4e9e150-1f69-573b-bb70-d4d00441eba5','cc078be4-6bc9-5dd0-9194-ede561b48077'}"
assert code.count(old)==1;code=code.replace(old,new)
old="'vias':[v for v in h['vias']if v['uuid']!=olduid]+[via]";assert code.count(old)==1;code=code.replace(old,"'vias':h['vias']+[via]")
old="endpoints=[('B.Cu',[213.65,143.549999],site),('In3.Cu',site,[212.65,144.549999]),('In2.Cu',[218.35,142.15],site)]"
new="pad=next(p for p in h['pads']if(p['ref'],p['num'])==('U10003','10'));assert C.norm(pad['net'])==NET;endpoints=[('B.Cu',[pad['x'],pad['y']],site),('In2.Cu',[218.35,142.15],site)]"
assert code.count(old)==1;code=code.replace(old,new)
code=code.replace("len({t['layer']for t in tracks})==3","len({t['layer']for t in tracks})==2")
code=code.replace("'same_UUID_existing_via_replacement':via,'exact_old_via':oldvia","'new_ordinary_signal_via':via,'exact_old_via_unchanged':oldvia")
code=code.replace('COMPLETE_THREE_LAYER_OLD_CONTACT_RESTORATION_NOMINATED_ALL_REFERENCE_SOURCE_CURRENT_NATIVE_OPEN','ADDITIONAL_ORDINARY_SIGNAL_PORT_TWO_LAYER_NOMINEE_ALL_OLD_IN3_CU_RETAINED_REFERENCE_SOURCE_CURRENT_NATIVE_OPEN')
code=code.replace('FINITE_RELOCATED_PORT_OLD_CONTACT_RESTORATION_NO_COMPLETE_NOMINEE','FINITE_ADDITIONAL_SIGNAL_PORT_TWO_LAYER_ROUTE_NO_COMPLETE_NOMINEE')
code=code.replace("'proposed_ordinary_signal_site_mm':site","'new_ordinary_signal_UUID':via['uuid'],'proposed_ordinary_signal_site_mm':site,'old_original_via_B_In3_geometry_exact_unchanged':True")
code=code.replace('U10003-relocated-fault-r170/','U10003-additional-fault-port-r171/')
code=code.replace('HOST_RELOCATION_ONLY_ALL_ORIGINAL_NATIVE_MASKS_REQUIRE_FRESH_ACTUAL_NATIVE_FILL','HOST_NEW_ORDINARY_PORT_ONLY_ACTUAL_ALL6_MASK_AND_SOURCE_ANNULI_REQUIRE_FRESH_NATIVE_FILL')
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
