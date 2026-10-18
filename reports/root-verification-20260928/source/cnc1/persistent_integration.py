"""Actual LinuxCNC/RTL persistent configuration acceptance; no physical transport."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import time
import traceback


def main():
    parser=argparse.ArgumentParser();parser.add_argument('-ini');args=parser.parse_args()
    from controller_config.runtime import PROFILE, LinuxCNCRTLAdapter, RuntimeConfigurationService
    from controller_config.persistent_runtime import PersistentRuntimeService
    from controller_config.model import ConfigurationError
    if os.environ.get('CNC1_ALLOW_RTL_SIMULATION')!='1' or Path(args.ini).resolve()!=PROFILE.resolve() or os.environ.get('CNC1_ALLOW_VOLATILE_CONFIG'):
        raise SystemExit('Dedicated persistent RTL simulation required')
    import linuxcnc,hal
    observer=hal.component('cnc1_persistent_observer');observer.ready()
    stat=linuxcnc.stat();command=linuxcnc.command()
    scenario=os.environ['CNC1_PERSISTENCE_SCENARIO'];directory=Path(os.environ['CNC1_PERSISTENCE_DIRECTORY'])
    report={'schema':1,'run_id':os.environ['CNC1_RUN_ID'],'scenario':scenario,'utc':datetime.now(timezone.utc).isoformat(),
            'profile_sha256':os.environ['CNC1_PROFILE_SHA256'],'physical_hardware':False,'success':False,'checks':[],'trace':[]}
    started=time.monotonic()
    def get(name):return hal.get_value('cnc1.'+name)
    def sample():
        stat.poll()
        row={'wall_seconds':time.monotonic()-started,'state':int(get('state')),'task_state':stat.task_state,
             'enabled':bool(stat.enabled),'permission':bool(get('sim-permission')),
             'locked':bool(get('config-locked')),'pending':bool(get('persistence-pending')),
             'generation':int(get('persistence-generation')),'x_scale':float(get('0.scale')),
             'x_count':float(get('0.emitted-count')),'x':stat.actual_position[0],
             'homed':list(stat.homed[:3])}
        report['trace'].append(row);return row
    def wait(test,timeout=35):
        until=time.monotonic()+timeout
        while time.monotonic()<until:
            row=sample()
            if test(row):return row
            time.sleep(.01)
        raise TimeoutError(repr(row))
    def check(name,condition,**data):
        if not condition:raise AssertionError(name+': '+repr(data))
        report['checks'].append({'name':name,'passed':True,**data});print('PASS '+name,flush=True)
    def send(function,*args):
        function(*args)
        if command.wait_complete(5)!=linuxcnc.RCS_DONE:raise RuntimeError('Command not completed')
    def cli(operation,*args,expected=0):
        result=subprocess.run(['python3','-m','controller_config.persistent_runtime','--directory',str(directory),operation,*args],text=True,capture_output=True,timeout=20)
        if result.returncode!=expected:raise RuntimeError(result.stdout+result.stderr)
        return json.loads(result.stdout)
    def reset_driver():
        hal.set_p('cnc1.reset','1');wait(lambda r:r['state']==4);hal.set_p('cnc1.reset','0');time.sleep(.03)
    def blocked_arm(label):
        send(command.state,linuxcnc.STATE_ON)
        row=wait(lambda r:r['state']==8 and not r['enabled'])
        check(label,not row['permission'] and row['locked'] and row['pending'])
        send(command.abort);send(command.state,linuxcnc.STATE_OFF);reset_driver()
        check(label+'_reset_preserves_gate',get('config-locked') and get('persistence-pending'))
    def move_one(expected):
        send(command.state,linuxcnc.STATE_ON);wait(lambda r:get('armed'))
        send(command.mode,linuxcnc.MODE_MANUAL);send(command.teleop_enable,0);command.home(-1)
        wait(lambda r:all(stat.homed[:3]) and stat.inpos)
        before=get('0.emitted-count')
        send(command.mode,linuxcnc.MODE_MDI);command.mdi('G91 G1 X1 F120')
        row=wait(lambda r:stat.interp_state==linuxcnc.INTERP_IDLE and stat.inpos and abs(r['x']-1)<.006)
        check('deliberate_homing_and_move_use_saved_scale',row['x_count']-before==expected,counts_before=before,counts_after=row['x_count'],scale=expected)
        send(command.state,linuxcnc.STATE_OFF);wait(lambda r:r['state']==4 and not r['enabled'])
    try:
        wait(lambda r:get('discovered') and stat.ini_filename and stat.joints==3)
        send(command.state,linuxcnc.STATE_ESTOP_RESET);reset_driver()
        adapter=LinuxCNCRTLAdapter();service=PersistentRuntimeService(adapter,directory)
        row=sample()
        check('default_startup_inhibits_unvalidated_scales',get('persistence-required') and row['locked'] and row['pending'] and not row['permission'] and row['x_scale']==200)
        try:RuntimeConfigurationService(adapter).recover_inhibit();raise AssertionError('Bypass accepted')
        except ConfigurationError as error:check('ordinary_recovery_cannot_bypass_persistence',error.code=='PERSISTENT_AUTHORITY_REQUIRED')
        try:adapter.transaction(3,adapter.snapshot());raise AssertionError('Compiled bypass accepted')
        except ConfigurationError as error:check('compiled_release_rejects_pending_authority',error.code=='COMPILED_GUARD_REJECTED')
        if scenario=='initialize':
            nonce=int(get('config-ack'))+1
            hal.set_p('cnc1.config-op','4');hal.set_p('cnc1.config-deadline-hi','0');hal.set_p('cnc1.config-deadline-lo','1')
            hal.set_p('cnc1.config-request',str(nonce));wait(lambda r:get('config-ack')==nonce)
            check('compiled_guard_rejects_queued_expired_request',get('config-result')==6 and get('config-locked') and get('persistence-pending'))
            missing=cli('status',expected=2)
            check('missing_new_machine_needs_explicit_init',missing['error']['code']=='PERSISTENCE_MISSING')
            blocked_arm('initial_default_cannot_arm')
            result=cli('init','--scales','250','200','200','200','200','200')['result']
            sample();check('durable_init_activates_without_enable',result['generation']==1 and get('0.scale')==250 and not stat.enabled and not any(stat.homed[:3]),result=result)
            move_one(250)
        elif scenario=='restart_interrupt':
            status=cli('status')['result']
            check('separate_launch_observes_saved250_but_remains_inhibited',status['target']['scales'][0]==250 and status['requires_reconciliation'])
            result=cli('reconcile')['result']
            sample();check('reconcile_restarts_with_saved_scale_unhomed',get('0.scale')==250 and not stat.enabled and not any(stat.homed[:3]) and result['generation']==1)
            move_one(250)
            plan=str(directory/'interrupt-plan.json')
            cli('preview','--scales','300','200','200','200','200','200','--output',plan)
            script="""import os,sys
from controller_config.runtime import LinuxCNCRTLAdapter
from controller_config.persistent_runtime import PersistentRuntimeService
from controller_config.service import read_json
def checkpoint(phase):
    if phase=='runtime_activated':os._exit(73)
service=PersistentRuntimeService(LinuxCNCRTLAdapter(),sys.argv[1],checkpoint=checkpoint)
service.apply(read_json(sys.argv[2]))
"""
            crash=subprocess.run(['python3','-c',script,str(directory),plan],text=True,capture_output=True,timeout=20)
            row=sample()
            check('client_process_death_after_activation_retains_gate',crash.returncode==73 and row['locked'] and row['pending'] and row['x_scale']==300 and not row['permission'] and not row['enabled'],state=row)
            check('journal_preserves_old_and_pending_generations',service.status()['committed']['generation']==1 and service.status()['pending']['generation']==2)
        elif scenario=='recover':
            status=cli('status')['result']
            check('new_launch_sees_interrupted_generation',status['pending']['generation']==2 and status['pending']['scales'][0]==300)
            result=cli('recover')['result']
            sample();check('explicit_recovery_finishes_generation_without_motion',result['generation']==2 and get('0.scale')==300 and not stat.enabled and not any(stat.homed[:3]),result=result)
            move_one(300)
        else:
            expected={'missing':'PERSISTENCE_MISSING','corrupt':'INVALID_JSON','foreign':'PERSISTENCE_IDENTITY',
                      'profile':'PERSISTENCE_IDENTITY','caps':'PERSISTENCE_IDENTITY','rollback':'PERSISTENCE_CONFLICT'}[scenario]
            error=cli('reconcile',expected=2)
            check('invalid_saved_authority_refused',error['error']['code']==expected,error=error['error'])
            blocked_arm('invalid_saved_authority_cannot_arm')
        report['success']=True
    except Exception as error:
        report['error']=str(error);report['traceback']=traceback.format_exc();print(report['traceback'],flush=True)
    finally:
        command.abort();command.state(linuxcnc.STATE_OFF)
        report['wall_seconds']=time.monotonic()-started;report['simulated_seconds']=get('sim-seconds')
        destination=Path(__file__).parent/'evidence/persistent';destination.mkdir(exist_ok=True,parents=True)
        (destination/(scenario+'.json')).write_text(json.dumps(report,indent=2)+'\n')
    return 0 if report['success'] else 1


if __name__=='__main__':raise SystemExit(main())
