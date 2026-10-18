"""Exact eight-conductor-row LED power classification; no reference exemption."""
import sys,json,math,copy
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
from hardware_map_motherboard_domains import sha,write
from hardware_validate_motherboard_power_entry import inhibit_screen

root=Path('reports/motherboard-return-zoning-20261001')
screen=root/'motor-bank-A-r83-field-collar-screen-r03/screen.json'
logic=root/'motor-bank-A-r83-source-collar-screen-r02/screen.json'
design=Path('hardware/motherboard/design.json')
prior=Path('reports/motherboard-power-entry-20260930/core7a-r04/validation.json')
health=Path('reports/motherboard-power-entry-20261001/health-supply-r99/receipt.json')
out=root/'motor-bank-A-eight-LED-power-classification-r01'
if out.exists():raise ValueError('Fresh immutable report required')
out.mkdir()
field=json.loads(screen.read_text())['rows'];controls=json.loads(logic.read_text())['rows']
parts=json.loads(design.read_text())['components'];condition=inhibit_screen()
roles={'R11071.2_to_U11027.1','U11027.2_to_U11028.1','FIELD_LED_A_actual_sink_from_escape',
       'FIELD_LED_A_actual_sink_to_escape','FIELD_LED_A_actual_sink','FIELD_LED_A_actual_source'}
# FIELD_LED_A_actual_source is split into the actual F/B/F supply portions.
expected_nets={'/motherboard_power_entry/FIELD_HEALTH_A_LED_A',
 '/motherboard_power_entry/FIELD_HEALTH_A_LED_MID',
 '/motherboard_power_entry/FIELD_HEALTH_A_LED_K','/motherboard_power_entry/FIELD_5V'}
def exact(rows,logicrows):
 if len(rows)!=8 or len(logicrows)!=18:raise ValueError('Exact eight power rows and18 control rows required')
 if {r['role']for r in rows}!=roles or {r['net']for r in rows}!=expected_nets:raise ValueError('Other function cannot acquire power classification')
 if any(not r['actual_copper_UUIDs']or len(r['literal_points_mm'])<2 for r in rows):raise ValueError('Actual native conductors required')
 if any(not r['net'].startswith('/motherboard_power_entry/')for r in rows):raise ValueError('Foreign path is not part of the selected LED loop')
 if any(r['net']in expected_nets for r in logicrows):raise ValueError('Power/control classifications overlap')
exact(field,controls)
negatives=[]
for name,mutate in [
 ('logic_Q_in_power_rows',lambda f,c:f[0].update(net='/motherboard_power_entry/MOTOR_ON_A')),
 ('unknown_power_row',lambda f,c:f[0].update(role='spindle_power')),
 ('missing_actual_UUID',lambda f,c:f[0].update(actual_copper_UUIDs=[])),
 ('dropped_LOGIC_control',lambda f,c:c.pop()),
 ('added_power_row',lambda f,c:f.append(copy.deepcopy(f[0]))),
]:
 f,c=copy.deepcopy(field),copy.deepcopy(controls);mutate(f,c)
 try:exact(f,c)
 except ValueError as e:negatives.append(dict(name=name,rejected=True,reason=str(e)))
 else:raise ValueError('Classification mutation accepted '+name)
# Relative copper-loss screen only. It uses exact literal routed path lengths,
# the requested70um outer copper/63um conditional minimum, a5% etch-width
# allowance, and the same copper85C resistivity assumption as prior motor work.
# Supplier thickness/etch, actual temperature and loaded rails remain unproven.
rho=1.724e-8*(1+.00393*65)
loss=[]
for row in field:
 length=sum(math.dist(a,b)for a,b in zip(row['literal_points_mm'],row['literal_points_mm'][1:]))
 width=row['width_mm']*.95
 resistance=rho*(length/1000)/((width/1000)*63e-6)
 loss.append(dict(role=row['role'],layer=row['layer'],length_mm=length,nominal_width_mm=row['width_mm'],conditional_min_width_mm=width,resistance_ohm_at85c_conditional=resistance))
r_total=sum(r['resistance_ohm_at85c_conditional']for r in loss)
hi=condition['series_led_current_a'][1];drop=hi*r_total
lower_with_drop=(4.8-2*1.8-.55-drop)/(120*(1+.013))
classification=[dict(r,classification='low_current_LED_POWER',signal_reference_qualification_credit=False,
 require_actual_Source_receiving_sink_and_return_continuity=True)for r in field]
write(out/'classification.json',dict(passed=True,scope='Exact existing field5-to-two-photorelay-LED-to-open-drain field-return current loop only',
 input_sha256={str(p):sha(p)for p in(screen,logic,design,prior,health,Path(__file__),Path('tools/hardware_validate_motherboard_power_entry.py'))},
 native_source_parts={r:parts[r]for r in('R11071','U11027','U11028','U11026','U11025')},
 exact_power_rows=classification,exact_retained_logic_control_rows=controls,
 approved_classification='Parent accepted the exact eight power-row classification; no clocks/data/STEP/precision row is removed from strict reference scope',
 signal_reference_guard_for_all18_logic_controls=dict(reference_margin_mm=.4,actual_Source_ground_stitch_required=True),
 conditional_inherited_LED_and_default_screen=condition,
 conditional_copper_loss=dict(evidence='Relative arithmetic, not measured/manufacturer guaranteed power capacity',rho_ohm_m_at85c=rho,
 copper_nominal_outer_um=70,conditional_min_outer_um=63,conditional_etch_width_ratio=.95,rows=loss,total_series_copper_ohm=r_total,
 conditional_max_copper_drop_v=drop,conditional_current_min_after_copper_drop_a=lower_with_drop,
 LED_trigger_max_a_at25c_only=.003,conditional25c_trigger_margin_a=lower_with_drop-.003,
 R11071_conditional_max_power_w=hi*hi*120*(1+.013),R11071_purchased_rated_power_w=parts['R11071']['rated_power_w'],
 whole_board_voltage_delivery_or_temperature_qualification=False),
 native_continuity_proof_required='The frozen motor83 endpoint proof and health-supply99 physical20-endpoint/four-bypass-cut proof remain separate exact prerequisites; classification does not supply missing copper',
 default_and_fault_obligations='No automatic restart; actual valid-health rails and receiving gate logic required; loaded dual-contact turnoff/partial supply ramps and20ms whole-board timing require physical validation',
 excluded_LED_reference_zones='No new field reference pockets are required or credited for these eight POWER rows',
 meaningful_classification_mutations=negatives,manufacturing_ready=False,physical20ms_proof=False))
print('classified eight actual power rows;18 strict control rows preserved;5 negative mutations rejected',flush=True)
