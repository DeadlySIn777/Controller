from pathlib import Path
import shutil,json
ROOT=Path.cwd();P=ROOT/'reports/motherboard-integration-20261001/source27-health-feed-reset-staged-r02';T=P/'candidate-tools';OUT=P/'candidate-tests';OUT.mkdir(exist_ok=False)
old=ROOT/'reports/motherboard-integration-20261001/source27-health-parent-staged-r01/candidate-tests/test_motherboard_source27_health.py'
shutil.copy2(old,OUT/old.name)
for filename in('test_motherboard_integration.py','test_motherboard_adc_source_adoption.py'):
 text=(ROOT/'tests'/filename).read_text()
 needle="ROOT=Path(__file__).resolve().parents[1]";assert text.count(needle)==1
 text=text.replace(needle,"ROOT=Path(os.environ.get('CONTROLLER_PROJECT_ROOT',Path(__file__).resolve().parents[1]))")
 needle="ROOT/'tools/hardware_validate_motherboard.py'";assert text.count(needle)==1
 text=text.replace(needle,"Path(os.environ.get('CONTROLLER_MOTHERBOARD_VALIDATOR',ROOT/'tools/hardware_validate_motherboard.py'))")
 if filename=='test_motherboard_adc_source_adoption.py':
  needle="self.assertEqual(2688,len(self.model['components']))";assert text.count(needle)==1
  text=text.replace(needle,"self.assertEqual(2698 if self.model.get('motor_feed_reset_correction',{}).get('id')=='MB-MOTOR-FEED-POR-001' else 2688,len(self.model['components']))")
 (OUT/filename).write_text(text)
builder=T/'hardware_build_motherboard.py';text=builder.read_text();needle="print(json.dumps({'physical_parts':len(parts),'retained_mc_parts':327,";assert text.count(needle)==1
text=text.replace(needle,"print(json.dumps({'physical_parts':len(json.loads((OUT/'design.json').read_text())['components']),'retained_mc_parts':327,")
builder.write_text(text)
print(json.dumps(dict(staged_tests=True,live_tests_unchanged=True)))
