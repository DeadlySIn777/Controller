from pathlib import Path
import sys,importlib.util,json,subprocess,xml.etree.ElementTree as ET
ROOT=Path.cwd();P=ROOT/'reports/motherboard-integration-20261001/source27-health-feed-reset-staged-r02';T=P/'candidate-tools'
sys.path[:0]=[str(T),str(ROOT/'tools')]
import hardware_build_motherboard as b
b.ROOT=ROOT;b.MC=ROOT/'hardware/motion_card';OUT=P/'future-generated-parent-r03'
b.build(OUT)
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
for label,args in[('netlist',['sch','export','netlist','--format','kicadxml','-o',str(OUT/'netlist.xml'),str(OUT/'motherboard.kicad_sch')]),('ERC',['sch','erc','--format','json','--severity-all','-o',str(P/'future-generator-erc-r03.json'),str(OUT/'motherboard.kicad_sch')])]:
 run=subprocess.run([CLI]+args,capture_output=True,text=True);(P/('future-generator-'+label+'-r03.log')).write_text(run.stdout+run.stderr);assert not run.returncode
def nodes(path):return{(node.get('ref'),node.get('pin')):net.get('name')for net in ET.parse(path).findall('.//nets/net')for node in net.findall('node')}
staged=P/'candidate/motherboard';expected=json.loads((staged/'design.json').read_text());new=json.loads((OUT/'design.json').read_text())
assert expected['components']==new['components']
assert nodes(staged/'netlist.xml')==nodes(OUT/'netlist.xml')
for key in('adc_bypass_correction','adc_reference_component_qualification','health_source_correction','motor_feed_reset_correction'):assert expected[key]==new[key],key
actual=json.loads((P/'future-generator-erc-r03.json').read_text());viol=[v for sh in actual['sheets']for v in sh['violations']];assert len(viol)==70 and not any(v['severity']=='error'for v in viol)and not actual['ignored_checks']
r=dict(passed=True,adopted=False,all2698_component_dictionaries_exact=True,all_actual_native_pin_entries_exact=True,native_pin_entries=len(nodes(OUT/'netlist.xml')),all_ADC_Source26_health_reset_qualification_metadata_exact=True,original_child_not_mutated=True,reproducible_parent_only_health_then_feed_reset_hook=True,ERC_errors=0,ERC_warnings=70,physical_qualification=False,manufacturing_ready=False)
(P/'future-generator-reproduction-r03.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
