"""Test orchestrator only. The cyclic servo path is the compiled HAL module."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
import traceback


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
