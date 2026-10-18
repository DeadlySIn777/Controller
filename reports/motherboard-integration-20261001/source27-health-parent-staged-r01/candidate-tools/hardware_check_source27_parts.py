"""Exact optional MB-HEALTH-001 parent-only override checks.
Inherited original MC and child04 baselines stay immutable. This checks native
identity, loading-default metadata and the exact bounded reviewed ledger; it
never establishes physical power-ramp, timing or missing-supervisor coverage.
"""
REFS=('R2106','U11019','U11025')
PRIMARY_RECEIPT='reports/motherboard-power-entry-20261001/health-source-correction-r01/receipt.json'
PRIMARY_RECEIPT_SHA='4b9d5dfe401204cfab08b969d238481211116d15ca54333563343e271f3a35b0'
PRIMARY_REVIEW_SHA='dce3d03ccac16298ad597ccce0c5f432af7f9fdeb4b834c637254359123d32ba'
MPNS={'R2106':'CRCW06032K20FKEA','U11019':'74LVC2G14GW,125','U11025':'74LVC2G14GW,125'}
MODEL_PINS={
 'R2106':{'1':'CORE_5V','2':'MC_RAILS_OK_5V'},
 'U11019':{'1':'MC_RAILS_OK_5V','2':'LOGIC_GND','3':'MC_RAILS_OK_5V','4':'CORE_HEALTH_B_N','5':'CORE_5V','6':'CORE_HEALTH_A_N'},
 'U11025':{'1':'MOTOR_FIELD_HEALTH_A_RAW','2':'FIELD_GND','3':'MOTOR_FIELD_HEALTH_B_RAW','4':'FIELD_HEALTH_B_N','5':'FIELD_5V','6':'FIELD_HEALTH_A_N'}}
NATIVE_PINS={
 'R2106':{'1':'/mc_local_power/CORE_5V','2':'/mc_local_power/MC_RAILS_OK_5V'},
 'U11019':{'1':'/mc_local_power/MC_RAILS_OK_5V','2':'/LOGIC_GND','3':'/mc_local_power/MC_RAILS_OK_5V','4':'/motherboard_power_entry/CORE_HEALTH_B_N','5':'/mc_local_power/CORE_5V','6':'/motherboard_power_entry/CORE_HEALTH_A_N'},
 'U11025':{'1':'/motherboard_motor_power/MOTOR_FIELD_HEALTH_A_RAW','2':'/motherboard_motors/FIELD_GND','3':'/motherboard_motor_power/MOTOR_FIELD_HEALTH_B_RAW','4':'/motherboard_power_entry/FIELD_HEALTH_B_N','5':'/motherboard_power_entry/FIELD_5V','6':'/motherboard_power_entry/FIELD_HEALTH_A_N'}}

def check_source27(parts, actual, model, mapping):
 errors=[];meta=model.get('health_source_correction');ledger=mapping.get('reviewed_health_source_delta')
 present=any(parts.get(r,{}).get('component_substitution')=='MB-HEALTH-001' or parts.get(r,{}).get('mpn')==MPNS[r]for r in REFS)
 if meta is None and ledger is None and not present:return errors
 if not meta or meta.get('id')!='MB-HEALTH-001' or meta.get('physical_qualification')is not False or meta.get('pin_nets_and_population_unchanged')is not True:errors.append('Exact health source parent metadata required')
 if not ledger or ledger.get('id')!='MB-HEALTH-001' or ledger.get('references')!=list(REFS) or ledger.get('parent_only_override')is not True or ledger.get('immutable_child04_and_original_MC_baselines_retained')is not True or ledger.get('physical_qualified')is not False:errors.append('Exact parent-only health ledger required')
 if not ledger or ledger.get('frozen_primary_receipt')!=PRIMARY_RECEIPT or ledger.get('frozen_primary_receipt_sha256')!=PRIMARY_RECEIPT_SHA or ledger.get('frozen_primary_review_sha256')!=PRIMARY_REVIEW_SHA or any(ledger.get(k)is not True for k in('native_pin_nets_unchanged','manufacturer_lands_unchanged','part_count_unchanged')):errors.append('Exact frozen primary evidence and unchanged native scope required')
 rows=(meta or {}).get('exact_three_part_ledger',[])
 if [r.get('reference')for r in rows]!=list(REFS):errors.append('Exactly three health source ledger rows required')
 for r in REFS:
  p=parts.get(r,{});fp='Resistor_SMD:R_0603_1608Metric'if r=='R2106'else'Package_TO_SOT_SMD:SOT-363_SC-70-6';value='2.2k 1%'if r=='R2106'else MPNS[r];old='CRCW060347K0FKEA'if r=='R2106'else'74LVC2G04GW,125'
  if p.get('mpn')!=MPNS[r]or p.get('value')!=value or p.get('footprint')!=fp or p.get('pins')!=MODEL_PINS[r]or p.get('component_substitution')!='MB-HEALTH-001'or p.get('inherited_mpn')!=old:errors.append('Exact reviewed health part identity/lands/default required '+r)
  if r=='R2106':
   if p.get('resistance_ohm')!=2200 or p.get('initial_tolerance')!=.01 or p.get('tcr_ppm')!=100 or p.get('rated_power_w')!=.1 or p.get('working_voltage_v')!=75:errors.append('Exact health pull-up rated metadata required '+r)
  elif p.get('kind')!='LVC2G14'or p.get('inherited_kind')!='LVC2G04'or p.get('legacy_pin_contract_symbol_preserved')is not True:errors.append('Exact Schmitt parent override pin-contract metadata required '+r)
  for pin,net in NATIVE_PINS[r].items():
   if actual.get((r,pin))!=net:errors.append('Health receiver must use exact native domain/provider '+r+'.'+pin)
  row=next((x for x in rows if x.get('reference')==r),{})
  if row.get('old_mpn')!=old or row.get('new_mpn')!=MPNS[r]or row.get('pin_net_map_unchanged')!=MODEL_PINS[r]or row.get('manufacturer_land_unchanged')!=fp:errors.append('Exact health old/new source row required '+r)
 return errors
