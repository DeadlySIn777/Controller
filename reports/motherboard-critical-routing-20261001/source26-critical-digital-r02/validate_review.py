"""Independent XML/model validation and bounded negative controls, no source edits."""
from pathlib import Path
import copy,hashlib,json,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
SRC=ROOT/'hardware/motherboard';parts=json.loads((SRC/'design.json').read_text())['components'];tree=E.parse(SRC/'netlist.xml')
native={n.get('name'):{(p.get('ref'),p.get('pin'))for p in n.findall('node')if p.get('ref')in parts}for n in tree.findall('.//nets/net')}
pin={p:n for n,ps in native.items()for p in ps}
report=json.loads((OUT/'critical-digital-source-review.json').read_text());facts=json.loads((OUT/'primary-timing-facts.json').read_text())
def validate(r,f):
 assert r['source_design_sha256']==sha(SRC/'design.json')
 assert r['source_netlist_sha256']==sha(SRC/'netlist.xml')
 assert sha(ROOT/'reports/motherboard-ordinary-routing-20261001/source26-review-r08/ordinary-source-review.json')==r['ordinary112_sha256']
 assert r['ordinary112_unchanged']and not r['route_execution_permission']and not r['physical_timing_qualification']
 seen=set();groups={g['name']:g for g in r['groups']}
 for n,row in r['nets'].items():
  assert set(map(tuple,row['source_pins']))==native[n],n
  assert len(row['source_endpoints'])==len(native[n])
  for p in row['source_endpoints']:
   ref,pn=p['reference'],p['pin'];assert (ref,pn)in native[n]
   assert p['mpn']==parts[ref]['mpn']
   if ref.startswith('U'):
    assert p['actual_return_pins']
    assert all(pin[ref,g]==row['return_net']for g in p['actual_return_pins'])
  assert row['type']=='critical_digital'and row['impedance_width_gap_mm']is None
  assert row['current_independent_missing_joins']==row['current_source_pad_clusters']-1
  assert row['maximum_voltage_v'] in (3.3,5.0)
  seen.add(n)
 assert len(seen)==r['exact_critical_native_nets']
 for i,mcu,pins,tap in [(0,'U13001',[15,16,18],'R13057'),(1,'U13004',[11,12,14],'R13058'),(2,'U13008',[11,12,14],'R13059'),(3,'U14501',[15,16,18],'R14533')]:
  g=groups[f'IOL1_L{i}'];assert g['notes']['actual_series_ohm']==22
  assert [x['mcu_pin']for x in g['notes']['chain']]==pins
  assert parts[tap]['resistance_ohm']==0
  assert pin[tap,'1']==pin[mcu,str(pins[1])]
  count='44'if i in (0,3)else'29';assert pin[tap,'2']==pin[mcu,count]
  assert g['notes']['clock_count_tap']==tap
  assert g['return_net']=='/LOGIC_GND'
 assert f['ADS8684AIDBTR']['SDI_physical_pin']==1 and f['ADS8684AIDBTR']['SDO_physical_pin']==36
 assert pin['U14734','1']==pin['U14707','14']and pin['U14734','36']==pin['U14707','10']
 assert facts['Nexperia_74LVC125APW_118']['tpd_max_ns']==4.8
 assert f['Nexperia_74LVC125APW_118']['input_capacitance_max_pf']is None
 assert f['TI_ISO776x']['actual_AO_AI_mixed3V3_5V_max_tpd_proven']is False
 code=(ROOT/'firmware/motherboard_iol1_readonly/target.c').read_text()
 assert f['STM32G031']['actual_target']['GPIO_OSPEEDR_write_present']==('OSPEEDR' in code)
 assert f['STM32G031']['actual_target']['GPIO_OSPEEDR_write_present']
 assert f['STM32G031']['actual_target']['former_speed00_gap_source_corrected']
 assert f['conditional_budget_examples']['all_budget_examples_are_conditional_not_acceptance']
 assert f['conditional_budget_examples']['IOL1_after_two4p8ns_LVC_and_speed11_ST12ns_remaining_ns']==60-2*4.8-12
 return dict(passed=True,exact_nets=len(seen),groups=len(groups),source_pins=sum(len(native[n])for n in seen))
result=validate(report,facts);neg=[]
def reject(name,change_report=None,change_facts=None):
 r,f=copy.deepcopy(report),copy.deepcopy(facts)
 if change_report:change_report(r)
 if change_facts:change_facts(f)
 try:validate(r,f)
 except (AssertionError,KeyError):neg.append(dict(name=name,rejected=True));return
 raise AssertionError('Negative control escaped:'+name)
def group(r,name):return next(g for g in r['groups']if g['name']==name)
reject('wrong_DOA_SPI1_physical_pin',lambda r:group(r,'IOL1_L1')['notes']['chain'][0].update(mcu_pin=10))
reject('invented_IOL1_33ohm',lambda r:group(r,'IOL1_L2')['notes'].update(actual_series_ohm=33))
reject('wrong_clocktap_identity',lambda r:group(r,'IOL1_L0')['notes'].update(clock_count_tap='R13058'))
reject('wrong_ADC_SDI_SDO',change_facts=lambda f:f['ADS8684AIDBTR'].update(SDI_physical_pin=36))
reject('field_return_replaced_LOGIC',lambda r:r['nets'][pin['U14608','6']].update(return_net='/LOGIC_GND'))
reject('TI_part_substituted_for_Nexperia_buffer',lambda r:next(p for p in r['nets'][pin['U13003','5']]['source_endpoints']if p['reference']=='U13003').update(mpn='SN74LVC125APWR'))
reject('corrected_speed11_falsely_missing',change_facts=lambda f:f['STM32G031']['actual_target'].update(GPIO_OSPEEDR_write_present=False))
reject('mixed_rail_ISO_timing_falsely_guaranteed',change_facts=lambda f:f['TI_ISO776x'].update(actual_AO_AI_mixed3V3_5V_max_tpd_proven=True))
reject('automatic_critical_execution_promotion',lambda r:r.update(route_execution_permission=True))
reject('missing_full_physical_source_endpoint',lambda r:r['nets'][pin['U13001','16']]['source_pins'].pop())
receipt=dict(**result,negative_controls=neg,negative_control_count=len(neg),
 input_sha256={str(p):sha(p)for p in [SRC/'design.json',SRC/'netlist.xml',OUT/'critical-digital-source-review.json',OUT/'primary-timing-facts.json',Path(__file__)]},
 source_unchanged=True,route_execution=False,manufacturing_ready=False)
(OUT/'independent-review.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(result|dict(negative_controls=len(neg))))
