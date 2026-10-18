"""Exact three-part health-source correction, copied native trees/model only.
The original MC and frozen power-entry source remain read-only. No pin/net,
footprint, pose, population, permission polarity or firmware authority change.
"""
from __future__ import annotations
import copy,hashlib,json
from pathlib import Path
from hardware_build_assembly import child,children,value,q,ref_property
OLD_INVERTER='74LVC2G04GW,125'
NEW_INVERTER='74LVC2G14GW,125'
OLD_PULLUP='CRCW060347K0FKEA'
NEW_PULLUP='CRCW06032K20FKEA'
CORRECTION='MB-HEALTH-001'
INVERTER_FUNCTIONS={'1':'1A','2':'GND','3':'2A','4':'2Y','5':'VCC','6':'1Y'}
REF_BLOCK={'R2106':'mc_local_power','U11019':'motherboard_power_entry','U11025':'motherboard_power_entry'}
def _symbol(tree,ref):
 found=[s for s in children(tree,'symbol')if value(ref_property(s)[2])==ref]
 if len(found)!=1:raise ValueError('Exactly one native '+ref+' required')
 return found[0]
def apply_health_source(trees,model):
 t,m=copy.deepcopy(trees),copy.deepcopy(model);parts=m['components'];ledger=[]
 for ref,block in REF_BLOCK.items():
  p=parts[ref];s=_symbol(t[block],ref);old=OLD_PULLUP if ref=='R2106'else OLD_INVERTER;new=NEW_PULLUP if ref=='R2106'else NEW_INVERTER
  if p.get('mpn')!=old or p.get('component_substitution')==CORRECTION:raise ValueError('Unexpected original health part '+ref)
  if ref=='R2106':
   if p['pins']!={'1':'CORE_5V','2':'MC_RAILS_OK_5V'}or p['footprint']!='Resistor_SMD:R_0603_1608Metric':raise ValueError('Unreviewed health pullup endpoints/lands')
   newvalue='2.2k 1%';p.update(resistance_ohm=2200,initial_tolerance=.01,tcr_ppm=100,rated_power_w=.1,working_voltage_v=75)
  else:
   expected={'U11019':{'1':'MC_RAILS_OK_5V','2':'LOGIC_GND','3':'MC_RAILS_OK_5V','4':'CORE_HEALTH_B_N','5':'CORE_5V','6':'CORE_HEALTH_A_N'},'U11025':{'1':'MOTOR_FIELD_HEALTH_A_RAW','2':'FIELD_GND','3':'MOTOR_FIELD_HEALTH_B_RAW','4':'FIELD_HEALTH_B_N','5':'FIELD_5V','6':'FIELD_HEALTH_A_N'}}[ref]
   if p['footprint']!='Package_TO_SOT_SMD:SOT-363_SC-70-6' or p['pins']!=expected:raise ValueError('Unreviewed inverter domain/lands')
   lib=value(child(s,'lib_id')[1]);defs=[d for d in children(child(t[block],'lib_symbols'),'symbol')if value(d[1])==lib]
   if len(defs)!=1:raise ValueError('Exactly one embedded pin contract required')
   functions={value(child(pin,'number')[1]):value(child(pin,'name')[1])for sub in children(defs[0],'symbol')for pin in children(sub,'pin')}
   if functions!=INVERTER_FUNCTIONS:raise ValueError('Manufacturer dual inverter pin map differs')
   # The existing generic rectangular pin-contract symbol is preserved. Its
   # historical internal lib ID does not select the fitted manufacturer's part.
   p.update(kind='LVC2G14',inherited_kind=p.get('kind'),legacy_pin_contract_symbol_preserved=True)
   newvalue=new
  oldvalue=p['value'];p.update(value=newvalue,mpn=new,inherited_mpn=old,component_substitution=CORRECTION,qualification='source-correction-not-physical-qualification')
  changed=[]
  for prop in children(s,'property'):
   k=value(prop[1])
   if k=='Value':prop[2]=q(newvalue);changed.append(k)
   if k=='MPN':prop[2]=q(new);changed.append(k)
  if set(changed)!={'Value','MPN'}:raise ValueError('Both exact native procurement fields required '+ref)
  ledger.append(dict(reference=ref,block=block,old_mpn=old,new_mpn=new,old_value=oldvalue,new_value=newvalue,pin_net_map_unchanged=copy.deepcopy(p['pins']),manufacturer_land_unchanged=p['footprint']))
 m['health_source_correction']={'id':CORRECTION,'exact_three_part_ledger':ledger,'physical_qualification':False,'pin_nets_and_population_unchanged':True}
 return t,m,m['health_source_correction']
def health_screen(pullup=2200,pulldowns=(100000,100000,100000,100000,470000),source_min=4.95,receiver_max=5.15,drift=.025,sink_leak=9.2e-6):
 # Initial1%+100ppm/K*150K conservative full excursion screen. Leakage bounds
 # retain manufacturer endpoint test conditions; no intermediate/ramp guarantee.
 g=sum(1/(r*(1-drift))for r in pulldowns);ru=pullup*(1+drift)
 high=(source_min/ru-sink_leak)/(1/ru+g)
 current_low=5.5/(pullup*(1-drift))+10e-6+sink_leak
 absent_pullup_high=(10e-6+sink_leak)/sum(1/(r*(1+drift))for r in pulldowns)
 return dict(high_v=high,reset_total_sink_a=current_low,reset_sink_test_max_a=.003,low_output_v_max_at_test=.15,absent_external_pullup_high_screen_v=absent_pullup_high,old04_required_high_v=.7*receiver_max,new14_threshold_screen_v=3.8,new14_threshold_screen_only=True,new14_full_intermediate_voltage_maximum_not_interpolated=True,temperature_resistor_drift_screen_fraction=drift,physical_qualification=False)
