from pathlib import Path
import sys,json,copy,importlib.util,xml.etree.ElementTree as ET,hashlib
ROOT=Path.cwd();OUT=ROOT/'reports/motherboard-integration-20261001/source27-health-parent-staged-r01';T=OUT/'candidate-tools';sys.path.insert(0,str(T));sys.path.insert(1,str(ROOT/'tools'))
import hardware_check_source27_parts as health
spec=importlib.util.spec_from_file_location('source27_parent_validation',T/'hardware_validate_motherboard.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);v.ROOT=ROOT
D=OUT/'candidate/motherboard';v.OUT=D;tree=ET.parse(D/'netlist.xml');model=json.loads((D/'design.json').read_text());mapping=json.loads((D/'assembly-map.json').read_text());baseline=v.validate(tree,model,mapping,True)
if baseline:raise ValueError(baseline)
actual=v.nodes(tree);controls=[]
def run(label,mutate,expect):
 m,a,n=copy.deepcopy(model),copy.deepcopy(mapping),copy.deepcopy(actual);mutate(m,a,n);errors=health.check_source27(m['components'],n,m,a)
 if not errors or not any(expect in s for s in errors):raise ValueError((label,errors))
 controls.append(dict(label=label,rejected=True,actual_errors=errors))
for ref in health.REFS:
 run(ref+' unreviewed MPN',lambda m,a,n,r=ref:m['components'][r].update(mpn='FAKE'), 'Exact reviewed health part')
 run(ref+' wrong land',lambda m,a,n,r=ref:m['components'][r].update(footprint='Package_TO_SOT_SMD:SOT-23-6'),'Exact reviewed health part')
 run(ref+' altered native pin',lambda m,a,n,r=ref:n.update({(r,'1'):'/UNREVIEWED_FAKE_HEALTH'}),'Health receiver must')
 run(ref+' altered model pin',lambda m,a,n,r=ref:m['components'][r]['pins'].update({'1':'WRONG_RAIL'}),'Exact reviewed health part')
run('Remove health ledger',lambda m,a,n:a.pop('reviewed_health_source_delta'),'Exact parent-only health ledger')
run('Remove health metadata',lambda m,a,n:m.pop('health_source_correction'),'Exact health source parent metadata')
run('Claim physical qualification',lambda m,a,n:m['health_source_correction'].update(physical_qualification=True),'Exact health source parent metadata')
run('Claim child baseline changed',lambda m,a,n:a['reviewed_health_source_delta'].update(parent_only_override=False),'Exact parent-only health ledger')
run('Remove one reviewed source row',lambda m,a,n:m['health_source_correction']['exact_three_part_ledger'].pop(),'Exactly three health source')
run('Larger pull-up violates default recipe',lambda m,a,n:m['components']['R2106'].update(resistance_ohm=47000),'Exact health pull-up rated metadata')
run('Field receiver wrong return',lambda m,a,n:n.update({('U11025','2'):'/LOGIC_GND'}),'Health receiver must')
run('Revert ordinary-input inverter kind',lambda m,a,n:m['components']['U11019'].update(kind='LVC2G04'),'Exact Schmitt parent override')
run('Falsify inherited MPN',lambda m,a,n:m['components']['U11025'].update(inherited_mpn='74LVC2G14GW,125'),'Exact reviewed health part')
for field in ('frozen_primary_receipt','frozen_primary_receipt_sha256','frozen_primary_review_sha256'):
 run('Wrong primary ledger '+field,lambda m,a,n,k=field:a['reviewed_health_source_delta'].update({k:'FAKE'}),'Exact frozen primary evidence')
run('False native-scope ledger',lambda m,a,n:a['reviewed_health_source_delta'].update(native_pin_nets_unchanged=False),'Exact frozen primary evidence')
# The parent checker also preserves previous five-part/ADC qualifications.
for label,key,container in [('Missing source26 ledger','reviewed_source26_qualification_delta','mapping'),('Missing ADC correction','adc_bypass_correction','model')]:
 m,a=copy.deepcopy(model),copy.deepcopy(mapping);(a if container=='mapping'else m).pop(key);errors=v.validate(tree,m,a,False)
 if not errors:raise ValueError(label+' unexpectedly accepted')
 controls.append(dict(label=label,rejected=True,actual_errors=errors))
from hardware_apply_motherboard_health_source import apply_health_source,health_screen
from hardware_build_assembly import parse
try:apply_health_source({k:parse((D/(k+'.kicad_sch')).read_text())for k in ['mc_local_power','motherboard_power_entry']},model)
except ValueError as e:controls.append(dict(label='Repeated already-correct parent override rejected',rejected=True,actual_error=str(e)))
else:raise ValueError('Frozen helper improperly accepts repeated correction')
old=ET.parse(ROOT/'hardware/motherboard/netlist.xml');om=json.loads((ROOT/'hardware/motherboard/design.json').read_text());oa=json.loads((ROOT/'hardware/motherboard/assembly-map.json').read_text())
if health.check_source27(om['components'],v.nodes(old),om,oa):raise ValueError('Historical source26 no-override case rejected')
if v.nodes(old)!=actual or len(model['components'])!=2688 or len(mapping['retained_native_pin_nets'])!=1229:raise ValueError('Native population/history changed')
result=dict(passed=True,source_stage_sha256={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()for p in[D/'design.json',D/'assembly-map.json',D/'netlist.xml',T/'hardware_validate_motherboard.py',T/'hardware_check_source27_parts.py']},full_actual_parent_validation_with_all_live_baseline_child_hashes=True,meaningful_negative_controls=controls,negative_controls_count=len(controls),old_source26_compatibility_positive=True,exact_original327_1229_native_pin_nets_preserved=True,ADC_and_source26_overlays_preserved=True,health_DC_screen=health_screen(),historical47k_DC_screen=health_screen(47000),complete_physical_ramp_and_intermediate_threshold_qualification=False,shared_files_unchanged=True,manufacturing_ready=False)
(OUT/'independent-health-validation-r02.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,meaningful_negative_controls=len(controls),old_source26=True,live_unchanged=True)),flush=True)

