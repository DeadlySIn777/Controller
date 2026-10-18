"""Copied test validators need the real source root, not the report directory."""
from pathlib import Path
root=Path.cwd();p=root/'reports/motherboard-integration-20261001/source27-health-feed-reset-staged-r02'
for filename in('test_motherboard_integration.py','test_motherboard_adc_source_adoption.py'):
 path=p/'candidate-tests'/filename;text=path.read_text()
 marker='validation=importlib.util.module_from_spec(spec);spec.loader.exec_module(validation)\n'
 assert text.count(marker)==1
 text=text.replace(marker,marker+"# Report-local copied validators retain actual source/FPGA paths explicitly.\nvalidation.ROOT=ROOT\nvalidation.OUT=Path(os.environ.get('CONTROLLER_MOTHERBOARD_TEST_SOURCE',ROOT/'hardware/motherboard'))\n")
 path.write_text(text)
src=root/'reports/motherboard-integration-20261001/run_source27_health_feed_future_r02.py';text=src.read_text()
text=text.replace("'future-generated-parent-r02'","'future-generated-parent-r03'").replace('future-generator-erc-r02.json','future-generator-erc-r03.json').replace("'-r02.log'","'-r03.log'").replace('future-generator-reproduction-r02.json','future-generator-reproduction-r03.json')
(src.parent/'run_source27_health_feed_future_r03.py').write_text(text)
