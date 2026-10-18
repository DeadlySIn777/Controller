from pathlib import Path
import copy,hashlib,json,sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from hardware_build_assembly import parse,dump,children,child,value
from hardware_apply_motherboard_io3_window import apply_io3_monitor_window,ROOT,OUT,REPORT,SCOPES
from hardware_validate_motherboard_io3_window import review,nodes

@pytest.fixture(params=['mc','motor'])
def source(request):
 scope=request.param;folder,stem=('motherboard_io3_upgrade','motherboard_io3_upgrade') if scope=='mc' else ('motherboard_motor_power','motherboard_motor_power')
 src=ROOT/'hardware'/folder
 return scope,parse((src/(stem+'.kicad_sch')).read_text()),json.loads((src/'design.json').read_text())

def test_bounded_transform_does_not_mutate_original(source):
 scope,t,m=source;before=(dump(t),copy.deepcopy(m));a,b,r=apply_io3_monitor_window(t,m,scope)
 assert before==(dump(t),m)
 assert review(b,scope,baseline=m)['consistency_pass']
 assert r['user_contract_changed'] is False
 assert len(b['components'])==len(m['components'])+len(SCOPES[scope])

def test_double_transform_rejected(source):
 scope,t,m=source;a,b,_=apply_io3_monitor_window(t,m,scope)
 with pytest.raises(ValueError):apply_io3_monitor_window(a,b,scope)

@pytest.mark.parametrize('mutation',[
 lambda p,u,o,s:p[u].update(mpn='PLT0603Z5362LST1'),
 lambda p,u,o,s:p[s]['pins'].update({'2':'IO_3V3'}),
 lambda p,u,o,s:p[o]['pins'].update({'1':'IO_3V3'}),
 lambda p,u,o,s:p[s].update(resistance_ohm=0),
 lambda p,u,o,s:p[u].update(initial_tolerance=.01),
 lambda p,u,o,s:p[s].update(tcr_ppm=100),
])
def test_incorrect_hardware_rejected(source,mutation):
 scope,t,m=source;a,b,_=apply_io3_monitor_window(t,m,scope);u,o,s=SCOPES[scope][0];mutation(b['components'],u,o,s)
 assert not review(b,scope,baseline=m)['consistency_pass']

def test_unrelated_monitor_reset_or_delay_source_change_rejected(source):
 scope,t,m=source;a,b,_=apply_io3_monitor_window(t,m,scope);ref='U2005' if scope=='mc' else 'U9001'
 b['components'][ref]['pins']['12']='WRONG_RESET'
 assert any('Unbounded retained mutation' in e for e in review(b,scope,baseline=m)['errors'])

def test_all_native_endpoints_match_and_erc_is_clean(source):
 scope,t,m=source;native=nodes(OUT/scope/'netlist.xml');actual=json.loads((OUT/scope/'design.json').read_text());result=review(actual,scope,baseline=m,native=native)
 assert result['consistency_pass']
 erc=json.loads((REPORT/(scope+'-erc.json')).read_text())
 assert sum(len(s['violations']) for s in erc['sheets'])==0
 assert erc.get('ignored_checks',[])==[]
 u,o,s=SCOPES[scope][0];native[(o,'1')]='IO_3V3'
 assert not review(actual,scope,baseline=m,native=native)['consistency_pass']

def test_static_trip_guard_is_inside_actual_fpga_oscillator_intersection(source):
 scope,t,m=source;a,b,_=apply_io3_monitor_window(t,m,scope);r=review(b,scope,baseline=m);s=r['screening']
 assert 3.14<s['uv_trip_v'][0]<s['uv_trip_v'][1]<3.21
 assert 3.38<s['ov_trip_v'][0]<s['ov_trip_v'][1]<3.465
 assert .0427<s['distribution_noise_margin_low_v']<.0428
 assert .0374<s['distribution_noise_margin_high_v']<.0375
 assert not r['physical_qualification']
 assert not s['default_health_reset_wdt_delay_changed']
