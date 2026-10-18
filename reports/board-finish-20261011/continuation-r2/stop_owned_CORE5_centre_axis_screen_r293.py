"""Stop only this root host's invalid centre-axis screen, preserve evidence."""
import datetime,json,pickle,hashlib,psutil
from pathlib import Path
H=Path(__file__).resolve().parent;OUT=H/'CORE5-current-new-transport-full1p25-In3-real-LGIn4-screen-r291'
_,h,_,_,_=pickle.loads((H/'sbc-power/CM79-R369-one-positive-LG-nine-settings-exact-native-outline-profile-r371/model.pkl').read_bytes())
import math
pv=next(v for v in h['vias']if v['uuid']=='63677f16-9cb3-5144-a82d-69a2c7fb8b3d');gv=next(v for v in h['vias']if v['uuid'].startswith('3aace899'))
distance=math.dist((pv['x'],pv['y']),(gv['x'],gv['y']));required=.625+gv['d']/2+.15+.025005
assert distance<required
p=psutil.Process(876);created=datetime.datetime.fromtimestamp(p.create_time(),datetime.timezone.utc).isoformat();args=p.cmdline()
assert created.startswith('2026-10-12T23:32:30.948') and 'screen_CORE5_current_In3_LGIn4_transport_r291.py' in ' '.join(args) and 'launch_confined_host.py' in ' '.join(args)
record={'status':'OWNED_HOST_CENTRE_AXIS_SCREEN_STOPPED_AFTER_EXPLICIT_REPRESENTATION_BLOCKER','PID':p.pid,'create_time_UTC':created,'cmdline':args,'source_graph_and_finished_rows_preserved':True,'power_via_UUID':pv['uuid'],'paired_LG_UUID':gv['uuid'],'centre_distance_mm':distance,'full_1p25_cap_plus_LG_via_plus_guard_required_mm':required,'body_centre_axis_invalid_independent_of_target_or_source_reference':True,'replacement_uses_previously_qualified_actual_side_annular_contact':True,'only_this_ROOT_host_process_stopped':True,'native_jobs_stopped':0,'adopted':False}
rp=OUT/'owned-host-centre-axis-stop-r293.json';assert not rp.exists();rp.write_text(json.dumps(record,indent=1)+'\n',encoding='utf-8');p.terminate();p.wait(30)
print('R293_OWN_HOST_STOPPED',p.pid,flush=True)
