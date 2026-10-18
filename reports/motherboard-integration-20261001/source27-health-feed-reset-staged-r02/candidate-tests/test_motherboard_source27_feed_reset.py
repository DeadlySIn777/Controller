"""Independent parent receiving reset/default/provider scope controls."""
from pathlib import Path
import os,sys,json,copy,importlib.util,xml.etree.ElementTree as ET
import pytest
ROOT=Path(os.environ.get('CONTROLLER_PROJECT_ROOT',Path.cwd()))
CHECKER=Path(os.environ.get('CONTROLLER_SOURCE27_FEED_CHECKER',ROOT/'tools/hardware_check_source27_feed_reset.py'))
spec=importlib.util.spec_from_file_location('parent_feed_reset_checked',CHECKER);check=importlib.util.module_from_spec(spec);spec.loader.exec_module(check);check.ROOT=ROOT
FOLDER=ROOT/'reports/motherboard-integration-20261001/source27-health-feed-reset-staged-r02/candidate/motherboard'
@pytest.fixture()
def circuit():
 m=json.loads((FOLDER/'design.json').read_text());a=json.loads((FOLDER/'assembly-map.json').read_text());t=ET.parse(FOLDER/'netlist.xml');n={(p.get('ref'),p.get('pin')):net.get('name')for net in t.findall('.//nets/net')for p in net.findall('node')};return t,m,a,n
def errors(c):return check.check_feed_reset(*c)[0]
def test_actual_native_parent_and_exact_primary_reset_pass(circuit):
 assert errors(circuit)==[];t,m,a,n=circuit;assert len(m['components'])==2698
 e,overrides,new=check.check_feed_reset(t,m,a,n);assert len(overrides)==2 and len(new)==34 and sum(v is None for v in new.values())==4
 assert a['reviewed_motor_feed_reset_delta']['physical_qualified']is False
@pytest.mark.parametrize('ref,pin,wrong',[
 ('U11035','1','MOTOR_FEED_CLEAR_N_B'),('U11037','1','MOTOR_FEED_CLEAR_N_A'),('U11035','3','MOTOR_FEED_CLEAR_N_A'),('U11035','4','LOGIC_GND'),('U11036','5','IO_3V3'),('U11036','4','MOTOR_FEED_CLEAR_FAST_N_B'),('R11082','2','FIELD_GND'),('U11032','6','MOTOR_FEED_CLEAR_N_A'),('U11024','3','MOTOR_FEED_ON_A'),('C11089','1','MOTOR5A')])
def test_model_banks_rail_reset_and_final_contact_cannot_be_tampered(circuit,ref,pin,wrong):
 circuit[1]['components'][ref]['pins'][pin]=wrong;assert errors(circuit)
@pytest.mark.parametrize('ref,field,wrong',[
 ('R11074','mpn','CRCW06031K00FKEA'),('U11035','mpn','TPS3808G01DBVR'),('U11037','footprint','Package_TO_SOT_SMD:SOT-23-5'),('R11082','resistance_ohm',10000)])
def test_exact_procurement_and_manufacturer_lands_required(circuit,ref,field,wrong):
 circuit[1]['components'][ref][field]=wrong;assert errors(circuit)
@pytest.mark.parametrize('ref',['R11082','C11090'])
def test_reset_low_default_and_owned_bypass_cannot_disappear(circuit,ref):
 del circuit[1]['components'][ref];assert errors(circuit)
def test_missing_primary_parent_override_ledger_rejected(circuit):
 del circuit[2]['reviewed_motor_feed_reset_delta'];assert errors(circuit)
@pytest.mark.parametrize('ref,pin,wrong',[
 ('U11032','6','/motherboard_power_entry/MOTOR_FEED_CLEAR_N_A'),('U11035','5','/IO_3V3'),('U11036','4','/motherboard_power_entry/MOTOR_FEED_CLEAR_FAST_N_B'),('R11082','2','/motherboard_motors/FIELD_GND')])
def test_actual_native_provider_bank_and_return_required(circuit,ref,pin,wrong):
 circuit[3][ref,pin]=wrong;assert errors(circuit)
def test_actual_native_primary_SENSE_is_not_VDD(circuit):
 circuit[0].find('.//libparts/libpart[@lib="CNC_MB_FeedReset"][@part="FEED_POR"]/pins/pin[@num="5"]').set('name','VDD');assert errors(circuit)
def test_historical_live_source26_is_readable():
 folder=ROOT/'hardware/motherboard';m=json.loads((folder/'design.json').read_text());a=json.loads((folder/'assembly-map.json').read_text());t=ET.parse(folder/'netlist.xml');n={(p.get('ref'),p.get('pin')):net.get('name')for net in t.findall('.//nets/net')for p in net.findall('node')}
 assert not check.check_feed_reset(t,m,a,n)[0]
