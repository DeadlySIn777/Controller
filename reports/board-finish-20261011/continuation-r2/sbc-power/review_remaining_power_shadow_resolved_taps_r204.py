"""Resolve three literal generic tap nominations from exact current source."""
from pathlib import Path
import ast,hashlib,json
P=Path(__file__).resolve().parent
wrapper=(P/'review_remaining_power_shadow_quiet_boundaries_r203.py').read_text();tail="exec(compile(s,str(old),'exec'))";assert wrapper.endswith(tail+'\n')
ns={'__file__':str(Path(__file__).resolve())};exec(compile(wrapper[:-len(tail+'\n')],str(P/'review_remaining_power_shadow_quiet_boundaries_r203.py'),'exec'),ns)
s=ns['s'].replace('remaining84-power-shadow-quiet-boundary-review-r203','remaining84-power-shadow-source-resolved-tap-review-r204').replace('R203_COMPLETE','R204_COMPLETE')
needle="   comp=parts[ref];row.update({'role':role,"
replacement="""   comp=parts[ref]
   if (ref,row['pin']) in {('R17163','1'),('R17165','1')}:
    expected='/motherboard_status/RGB_NETWORK_R_K' if ref=='R17163' else '/motherboard_status/RGB_NETWORK_G_K'
    assert raw=='/mc_local_power{slash}CORE_5V' and othernets==[expected] and atom(comp,'value')=='10000R1%'
    fields={atom(f,'name'):f[2] if len(f)>2 else '' for f in children(child(comp,'fields') or [],'field')};assert fields['MPN']=='CRCW060310K0FKEA'
    assert any(atom(q,'ref').startswith('D') for q in children(nets[expected],'node')),'Exact opposite net must retain actual LED endpoint'
    role='PDN_LED_CURRENT_LIMIT_RESISTOR_SUPPLY_FEED_EXACT_SOURCE'
   elif (ref,row['pin'])==('R18001','2'):
    assert raw=='/IO_3V3' and othernets==['/mc_local_power/IO_3V3_REG_LOCAL'] and atom(comp,'value')=='15mohm 1% 50ppm 1W'
    fields={atom(f,'name'):f[2] if len(f)>2 else '' for f in children(child(comp,'fields') or [],'field')};assert fields['MPN']=='KRL2012E-C-R015-F-T5'
    role='PDN_IO3_POST_RESERVOIR_SERIES_DAMPING_SOURCE_TERMINAL_EXACT_SOURCE_NO_BYPASS'
   row.update({'role':role,"""
assert needle in s;s=s.replace(needle,replacement)
s=s.replace("'same_rail20_and_other84_raw_legacy_losses_retained':True,","'same_rail20_and_other84_raw_legacy_losses_retained':True,'literal_three_resistor_tap_roles_resolved_from_exact_MPN_value_opposite_net_and_LED_endpoint':True,'any_VOS_feedback_divider_Kelvin_or_analog_signal_shadow_still_hard':True,")
ast.parse(s)
(P/'power-tap-source-role-resolution-r204-derivation.json').write_text(json.dumps({'R203_script_sha256':hashlib.sha256((P/'review_remaining_power_shadow_quiet_boundaries_r203.py').read_bytes()).hexdigest(),'exact_resolved_refs':['R17163.1','R17165.1','R18001.2'],'no_netwide_quiet_rule_or_tracewidth_inference':True,'legacy_raw_area_loss_results_preserved':True,'derived_source_sha256':hashlib.sha256(s.encode()).hexdigest()},indent=1)+'\n')
exec(compile(s,str(P/'review_remaining_power_shadow_source_types_r202.py'),'exec'))
