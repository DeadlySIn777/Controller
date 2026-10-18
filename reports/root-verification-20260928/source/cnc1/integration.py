"""Test orchestrator only. The cyclic servo path is the compiled HAL module."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
import traceback
import subprocess


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('-ini'); args=parser.parse_args()
    profile=Path(__file__).parent/'profiles/sim/controller.ini'
    if os.environ.get('CNC1_ALLOW_RTL_SIMULATION')!='1' or Path(args.ini).resolve()!=profile.resolve():
        raise SystemExit('Explicit dedicated RTL simulation profile required')
    import hal
    import linuxcnc
    observer=hal.component('cnc1_test_observer'); observer.ready()
    stat=linuxcnc.stat()
    deadline=time.monotonic()+10
    while True:
        stat.poll()
        if stat.ini_filename and Path(stat.ini_filename).resolve()!=profile.resolve():
            raise SystemExit('Foreign profile: '+stat.ini_filename)
        if stat.ini_filename and stat.joints==3 and stat.axis_mask==7: break
        if time.monotonic()>deadline: raise SystemExit('Simulation status was not initialized')
        time.sleep(.02)
    command=linuxcnc.command(); errors=linuxcnc.error_channel()
    started=time.monotonic()
    report={'schema':1,'run_id':os.environ.get('CNC1_RUN_ID'),'utc':datetime.now(timezone.utc).isoformat(),
            'real_linuxcnc':True,'actual_rtl':'Verilator cnc_endpoint ENABLE_DISCOVERY=1',
            'physical_hardware':False,'success':False,'checks':[],'trace':[]}
    phase='start'
    def get(name): return hal.get_value('cnc1.'+name)
    def sample():
        stat.poll()
        row={'wall_seconds':round(time.monotonic()-started,6),'sim_seconds':get('sim-seconds'),
             'phase':phase,'xyz':list(stat.actual_position[:3]),
             'counts':[get(f'{i}.emitted-count') for i in range(3)],
             'state':get('state'),'fault':get('fault-code'),'enabled':bool(stat.enabled),
             'task_state':stat.task_state,'interpreter_state':stat.interp_state,
             'rtl_permission':bool(get('sim-permission')),'sequence':get('sequence'),
             'encoder':[get(f'encoder.{i}.count') for i in range(2)]}
        report['trace'].append(row)
        return row
    def wait_for(test,timeout=45):
        until=time.monotonic()+timeout
        while time.monotonic()<until:
            row=sample()
            if test(row): return row
            time.sleep(0.01)
        raise TimeoutError(phase+': '+repr(row))
    def check(name,condition,**data):
        if not condition: raise AssertionError(name+': '+repr(data))
        report['checks'].append({'name':name,'passed':True,**data}); print('PASS '+name,flush=True)
    def send(function,*arguments):
        function(*arguments)
        if command.wait_complete(5)!=linuxcnc.RCS_DONE: raise RuntimeError('LinuxCNC command completion failed')
    def mdi(line):
        send(command.mode,linuxcnc.MODE_MDI); command.mdi(line)
    try:
        wait_for(lambda r:get('discovered'))
        capabilities={k:get(k) for k in ('step-channels','encoder-channels','frequency-channels','features','core-hz')}
        check('discovery_from_actual_RTL',capabilities=={'step-channels':6,'encoder-channels':2,'frequency-channels':0,'features':31,'core-hz':50000000},capabilities=capabilities)
        check('discovery_cannot_arm',not get('sim-permission') and not get('armed'))
        hal.set_p('cnc1.reset','1'); wait_for(lambda r:r['state']==4); hal.set_p('cnc1.reset','0')
        send(command.state,linuxcnc.STATE_ESTOP_RESET); send(command.state,linuxcnc.STATE_ON)
        wait_for(lambda r:get('armed'))
        send(command.mode,linuxcnc.MODE_MANUAL); send(command.teleop_enable,0); command.home(-1)
        wait_for(lambda r:all(stat.homed[:3]) and stat.inpos)
        check('LinuxCNC_homed_over_RTL_feedback',all(stat.homed[:3]))
        phase='coordinated_positive_negative'
        mdi('G21 G90 G1 X2 Y-1 Z0.5 F600')
        row=wait_for(lambda r:stat.interp_state==linuxcnc.INTERP_IDLE and stat.inpos and all(abs(a-b)<0.006 for a,b in zip(r['xyz'],(2,-1,.5))))
        check('actual_LinuxCNC_command_reached_RTL_and_returned',row['counts']==[400,-200,100],counts=row['counts'],xyz=row['xyz'])
        phase='reversal'
        mdi('G1 X-1 Y1 Z-0.5 F600')
        row=wait_for(lambda r:stat.interp_state==linuxcnc.INTERP_IDLE and stat.inpos and all(abs(a-b)<0.006 for a,b in zip(r['xyz'],(-1,1,-.5))))
        check('actual_RTL_direction_reversal_feedback',row['counts']==[-200,200,-100],counts=row['counts'])
        phase='spindle_feedback'
        hal.set_p('cnc1.sim-spindle','1'); hal.set_p('cnc1.sim-spindle-edge-ticks','10000')
        first=sample(); wait_for(lambda r:r['sim_seconds']-first['sim_seconds']>.02)
        slow=sample(); hal.set_p('cnc1.sim-spindle-edge-ticks','2500')
        wait_for(lambda r:r['sim_seconds']-slow['sim_seconds']>.02)
        fast=sample()
        slow_rate=(slow['encoder'][0]-first['encoder'][0])/(slow['sim_seconds']-first['sim_seconds'])
        fast_rate=(fast['encoder'][0]-slow['encoder'][0])/(fast['sim_seconds']-slow['sim_seconds'])
        check('varying_ABZ_traverses_RTL_and_HAL',fast_rate>slow_rate*2 and fast['encoder'][1]<0 and int(get('encoder-flags'))&3==3,slow_counts_per_sim_second=slow_rate,fast_counts_per_sim_second=fast_rate)
        check('encoder_scaling',abs(get('encoder.0.position')-get('encoder.0.count')/400)<.1)
        phase='link_loss_during_motion'
        mdi('G1 X15 F300')
        wait_for(lambda r:r['xyz'][0]>0)
        hal.set_p('cnc1.sim-inject','1')
        row=wait_for(lambda r:r['fault']!=0 and not r['enabled'] and not r['rtl_permission'])
        check('link_loss_fault_stops_actual_LinuxCNC',not row['enabled'] and not row['rtl_permission'] and row['xyz'][0]<15,xyz=row['xyz'],driver_fault=row['fault'])
        phase='link_return'
        hal.set_p('cnc1.sim-inject','0'); initial=sample(); time.sleep(.2); row=sample()
        check('link_return_cannot_restart',not row['enabled'] and not row['rtl_permission'] and row['state']==8)
        error_messages=[]
        while True:
            item=errors.poll()
            if item is None: break
            error_messages.append(list(item))
        check('LinuxCNC_reports_amplifier_fault',any('amplifier' in str(item).lower() for item in error_messages),errors=error_messages)
        phase='explicit_stopped_recovery'
        hal.set_p('cnc1.reset','1'); wait_for(lambda r:r['state']==4); hal.set_p('cnc1.reset','0')
        check('reset_recovers_communication_without_enabling',not get('sim-permission') and not stat.enabled)
        # Service calls below use actual LinuxCNC state and observed HAL caps.
        # They neither consult nor mutate the disconnected profile/file fixtures.
        from controller_config.runtime import LinuxCNCRTLAdapter, RuntimeConfigurationService
        from controller_config.model import ConfigurationError
        runtime=RuntimeConfigurationService(LinuxCNCRTLAdapter())
        phase='runtime_configuration'
        send(command.abort)
        send(command.state,linuxcnc.STATE_OFF)
        wait_for(lambda r:not stat.enabled and stat.task_state in (linuxcnc.STATE_OFF,linuxcnc.STATE_ESTOP_RESET) and stat.interp_state==linuxcnc.INTERP_IDLE)
        snap=runtime.snapshot()
        check('runtime_service_observes_RTL_caps',snap['capabilities']['step_channels']==6 and snap['capabilities']['joint_max_velocity']==[10.,10.,10.,None,None,None],snapshot=snap)
        cli=subprocess.run(['python3','-m','controller_config.runtime','snapshot'],text=True,capture_output=True,timeout=10)
        cli_response=json.loads(cli.stdout)
        check('runtime_CLI_uses_shared_live_service',cli.returncode==0 and cli_response['ok'] and cli_response['result']['session']==snap['session'])
        try:
            hal.set_p('cnc1.0.scale','300')
            raise AssertionError('Active scale pin accepted an external write')
        except RuntimeError:
            check('active_scale_is_read_only',get('0.scale')==200)
        unsupported=[200.]*6; unsupported[3]=250
        try:
            runtime.preview(unsupported)
            raise AssertionError('Unmapped hardware channel accepted')
        except ConfigurationError as exc:
            check('unmapped_discovered_channel_not_fake_joint',exc.code=='UNMAPPED_CHANNEL')
        high=[200.]*6; high[0]=20000
        try:
            runtime.preview(high)
            raise AssertionError('Excessive pulse demand accepted')
        except ConfigurationError as exc:
            check('runtime_scale_respects_discovered_rate',exc.code=='PULSE_RATE_LIMIT')
        stale=runtime.preview([250,200,200,200,200,200])
        send(command.state,linuxcnc.STATE_ON); wait_for(lambda r:get('armed'))
        try:
            runtime.apply(stale)
            raise AssertionError('Enabled configuration accepted')
        except ConfigurationError as exc:
            check('actual_enabled_runtime_rejects_apply',exc.code=='RUNTIME_UNSAFE')
        try:
            runtime.adapter.transaction(1,runtime.snapshot())
            raise AssertionError('Compiled enabled guard accepted')
        except ConfigurationError as exc:
            check('compiled_guard_independently_rejects_enabled',exc.code=='COMPILED_GUARD_REJECTED' and not get('config-locked'))
        send(command.state,linuxcnc.STATE_OFF); wait_for(lambda r:r['state']==4 and not r['enabled'])
        try:
            runtime.apply(stale)
            raise AssertionError('Old epoch preview accepted')
        except ConfigurationError as exc:
            check('actual_enable_cycle_invalidates_preview',exc.code=='RUNTIME_STALE')
        plan=runtime.preview([250,200,200,200,200,200])
        before=sample()
        applied=runtime.apply(plan)
        after=sample()
        check('stopped_runtime_scale_commit_unhomes_without_motion',get('0.scale')==250 and not stat.enabled and not any(stat.homed[:3]) and not get('sim-permission') and before['counts']==after['counts'],result=applied,counts_before=before['counts'],counts_after=after['counts'])
        try:
            runtime.apply(plan)
            raise AssertionError('Committed preview replay accepted')
        except ConfigurationError as exc:
            check('runtime_revision_rejects_replay',exc.code=='RUNTIME_STALE')
        hal.set_p('cnc1.0.config-scale','300'); time.sleep(.05)
        check('staging_cannot_modify_active_scale',get('0.scale')==250 and get('config-revision')==1)
        running_plan=runtime.preview([300,200,200,200,200,200])
        send(command.state,linuxcnc.STATE_ON); wait_for(lambda r:get('armed'))
        send(command.mode,linuxcnc.MODE_MANUAL); send(command.teleop_enable,0); command.home(-1)
        wait_for(lambda r:all(stat.homed[:3]) and stat.inpos)
        count_before=get('0.emitted-count')
        mdi('G91 G1 X1 F60')
        wait_for(lambda r:r['xyz'][0]>.2 and not stat.inpos)
        try:
            runtime.apply(running_plan)
            raise AssertionError('Executing motion allowed configuration')
        except ConfigurationError as exc:
            check('actual_moving_runtime_rejects_apply',exc.code=='RUNTIME_UNSAFE')
        row=wait_for(lambda r:stat.interp_state==linuxcnc.INTERP_IDLE and stat.inpos and abs(r['xyz'][0]-1)<.006)
        check('deliberate_rehome_and_move_use_new_scale',row['counts'][0]-count_before==250,counts_before=count_before,counts_after=row['counts'][0],xyz=row['xyz'])
        send(command.state,linuxcnc.STATE_OFF); wait_for(lambda r:r['state']==4 and not r['enabled'])
        phase='runtime_reversal'
        plan_path='/tmp/cnc1-reverse-'+report['run_id']+'.json'
        cli=subprocess.run(['python3','-m','controller_config.runtime','preview','--scales','200','200','200','200','200','200','--output',plan_path],text=True,capture_output=True,timeout=10)
        if cli.returncode: raise RuntimeError(cli.stdout+cli.stderr)
        cli=subprocess.run(['python3','-m','controller_config.runtime','apply',plan_path],text=True,capture_output=True,timeout=15)
        if cli.returncode: raise RuntimeError(cli.stdout+cli.stderr)
        reversed_change=json.loads(cli.stdout)['result']
        sample()
        check('scale_change_reversible_with_new_stopped_preview',get('0.scale')==200 and get('config-revision')==2 and not stat.enabled and not any(stat.homed[:3]),result=reversed_change)
        runtime.adapter.transaction(1,runtime.snapshot())
        cli=subprocess.run(['python3','-m','controller_config.runtime','recover-inhibit'],text=True,capture_output=True,timeout=15)
        recovery=json.loads(cli.stdout)
        check('interrupted_transaction_inhibit_requires_explicit_recovery',cli.returncode==0 and recovery['result']['inhibit_released'] and not get('config-locked') and not get('sim-permission'),result=recovery['result'])
        report['success']=True
    except Exception as exc:
        report['error']=str(exc); report['traceback']=traceback.format_exc(); print(report['traceback'],flush=True)
    finally:
        command.abort(); command.state(linuxcnc.STATE_OFF)
        report['wall_seconds']=time.monotonic()-started
        report['simulated_seconds']=get('sim-seconds')
        directory=Path(__file__).parent/'evidence'; directory.mkdir(exist_ok=True)
        (directory/'linuxcnc.json').write_text(json.dumps(report,indent=2)+'\n')
    return 0 if report['success'] else 1

if __name__=='__main__': raise SystemExit(main())
