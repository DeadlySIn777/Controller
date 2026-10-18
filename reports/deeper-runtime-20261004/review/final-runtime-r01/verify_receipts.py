"""Independent read-only checks of completed source-bound runtime receipts."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from tools.create_cnc3_qualification_fixture import runtime_sources
from controller_lab.cnc3_configuration import verify_configuration
from controller_config.setup_service import SetupService
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
results=[]
for argument in sys.argv[1:]:
 base=(ROOT/argument).resolve();r=json.loads((base/'receipt.json').read_text());o=json.loads((base/'linuxcnc.json').read_text());m=json.loads((base/'configuration/runtime.json').read_text())
 expected=set(runtime_sources());actual=set(r['source_sha256']);count=o['active_joints'];active=(1<<count)-1
 changed=[f for f,h in r['source_sha256'].items() if sha(ROOT/f)!=h]
 copy_bad=[f for f,h in r['source_sha256'].items() if sha(base/'source'/f)!=h]
 logs_bad=[x['stage'] for x in r['executions'] if sha(base/(x['stage']+'.log'))!=x['log_sha256']]
 assert r['status']=='PASS' and o['status']=='PASS'
 assert not expected-actual and not actual-expected and not changed and not copy_bad and not logs_bad
 assert o==r['observations'] and all(c['status']=='PASS' for c in o['checks'])
 verify_configuration(m,SetupService(base/'configuration/setup.json'),source_root=base/'source',expected_source_files=sorted(expected))
 verify_configuration(m,SetupService(base/'configuration/setup.json'),source_root=ROOT,expected_source_files=sorted(expected))
 before=json.loads((base/'installed-modules-before.json').read_text());after=json.loads((base/'installed-modules-after.json').read_text());assert before==after and len(before)==183
 settings=sha(base/'configuration/setup.json');fixture=sha(base.parent/f'fixtures-{count}'/'setup.json');assert settings==fixture==r['settings_sha256']==o['setup_sha256_before']==o['setup_sha256_after']
 start=o['observations']['before_motion'];move=o['observations']['during_concurrent_motion'];stop=o['observations']['after_motion'];recover=o['observations']['recovered']
 assert move['rtl-armed-mask']==move['rtl-enabled-mask']==active and all(v>0 for v in move['joint-velocity'])
 pin_deltas=[move['observed-step-rises'][i]-start['observed-step-rises'][i] for i in range(count)]
 accepted_deltas=[move['model-accepted-rises'][i]-start['model-accepted-rises'][i] for i in range(count)]
 assert all(v>=5 for v in pin_deltas) and all(v>=5 for v in accepted_deltas)
 assert all(not s['physical-authority'] and not s['production-profile-complete'] for s in o['observations'].values())
 assert not recover['armed'] and not recover['sim-permission'] and not any(recover['homed']) and recover['rtl-enabled-mask']==0
 if count==8:assert stop['observed-step-rises'][8:]==[0]*4
 assert all(x['exit_code']==0 for x in r['executions'])
 results.append({'path':argument,'status':'SCOPED_PASS','receipt_sha256':sha(base/'receipt.json'),'observation_sha256':sha(base/'linuxcnc.json'),'source_count':len(actual),'current_sources_match':True,'copied_sources_match':True,'no_selected_source_omitted':True,'execution_logs_verified':len(r['executions']),'all_observation_checks_passed':len(o['checks']),'active_joints':count,'fitted_channels':o['fitted_channels'],'simultaneous_positive_velocity':move['joint-velocity'],'observed_pin_rise_deltas':pin_deltas,'model_accepted_rise_deltas':accepted_deltas,'unused_channels_inhibited':count!=8 or stop['observed-step-rises'][8:]==[0]*4,'settings_sha256':settings,'preserved_existing_modules':len(before),'physical_authority':False,'production_profile_complete':False})
print(json.dumps({'status':'SCOPED_PASS','runs':results},indent=2))
