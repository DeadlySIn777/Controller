from pathlib import Path
import sys,os,json
ROOT=Path.cwd();P=ROOT/'reports/motherboard-integration-20261001/source27-health-feed-reset-staged-r02';T=P/'candidate-tools'
sys.path[:0]=[str(T),str(ROOT/'tools')]
import hardware_check_source27_feed_reset as feed
feed.ROOT=ROOT
os.environ['CONTROLLER_PROJECT_ROOT']=str(ROOT)
os.environ['CONTROLLER_MOTHERBOARD_TEST_SOURCE']=str(P/'candidate/motherboard')
os.environ['CONTROLLER_SOURCE26_STAGE']=str(P/'candidate/motherboard')
os.environ['CONTROLLER_MOTHERBOARD_VALIDATOR']=str(T/'hardware_validate_motherboard.py')
os.environ['CONTROLLER_SOURCE27_CHECKER']=str(T/'hardware_check_source27_parts.py')
os.environ['CONTROLLER_SOURCE27_FEED_CHECKER']=str(T/'hardware_check_source27_feed_reset.py')
names=['test_motherboard_source27_health.py','test_motherboard_source27_feed_reset.py','test_motherboard_integration.py','test_motherboard_adc_source_adoption.py']
args=[str(P/'candidate-tests'/name)for name in names]
args+=['tests/'+name for name in ['test_motherboard_fpga_allocation.py','test_motherboard_fpga_current_annotations.py','test_motherboard_analog_input.py','test_motherboard_source26_parts.py','test_motherboard_fuse_geometry.py','test_motherboard_power_entry.py','test_motherboard_motor_power.py','test_motherboard_io3_window.py','test_motherboard_io3_upgrade.py','test_motor_feed_reset.py']]
import pytest
raise SystemExit(pytest.main(args+['-q','--import-mode=importlib']))
