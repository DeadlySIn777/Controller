from pathlib import Path
import sys,json,copy
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import pcbnew
import hardware_route_critical_digital_wip_r05 as a
import hardware_check_return_corridors_r04 as rc
import hardware_route_owned_bypass_loops_wip_r03 as w
e=a.engine
root=e.ROOT
base=root/'reports/motherboard-pcb-integration-20261001/source26-orphan-free-adopted-r62/motherboard-source26-WIP.kicad_pcb'
folder=root/'reports/motherboard-critical-routing-20261001/actual-source26-root62-sparse-FPGA-escape-r01'
candidate=folder/'motherboard-sparse-FPGA-escape-staging.kicad_pcb'
out=e.require_new_report(root/'reports/motherboard-critical-routing-20261001/actual-source26-root62-sparse-FPGA-validation-r02')
before=e.parse(base.read_text());after=e.parse(candidate.read_text())
if e.immutable_objects(before)!=e.immutable_objects(after):raise ValueError('Native immutable mismatch')
cu=lambda tree:{e.value(e.child(t,'uuid')[1]):e.dump(t)for k in ['segment','via','arc']for t in e.children(tree,k)}
old,new=cu(before),cu(after)
delta=[dict(uuid=u,before=v,after=new.get(u))for u,v in old.items()if new.get(u)!=v]
if delta:
 e.write(out/'native-serialization-delta-rejected.json',dict(passed=False,items=delta,manufacturing_ready=False));print(json.dumps(delta[:3]));raise ValueError('Native old copper changed')
b=pcbnew.LoadBoard(str(candidate));b.BuildConnectivity();e.native_source_check(b,e.read(root/'hardware/motherboard/design.json'),root/'hardware/motherboard/netlist.xml')
review=e.read(root/'reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/critical-digital-source-review.json')
rows={n:{**review['nets'][n],'via_diameter_mm':.5,'via_drill_mm':.2}for n in ['/fpga_core/IOL1_L1_MISO','/fpga_core/IOL1_L3_MISO']}
extra={t.m_Uuid.AsString():t for t in b.GetTracks()if t.m_Uuid.AsString()not in old}
signals={u for u,t in extra.items()if t.GetNetname()in rows}
try:proof=rc.return_corridor_check(b,signals,rows)
except ValueError as exc:proof={'passed':False,'reason':str(exc)}
baseline=e.read(base.parent/'baseline-disposition.json');known=w.reviewed_wip_warnings(e.read(base.parent/'drc.json'),baseline,e.sha(base))
drc=e.read(folder/'actual-native.json');defects=w.new_route_defects(drc,known)
r=dict(passed=False,actual_package_access_return_pass=proof['passed'],actual_source_and_old_Cu_and_immutable_objects_retained=True,
 board_sha256=e.sha(base),candidate_sha256=e.sha(candidate),extra_signal_count=len(signals),extra_ground_count=len(extra)-len(signals),
 actual_return_proof=proof,actual_new_native_defects=defects,actual_native_errors=[v for v in drc['violations']if v['severity']=='error'],
 actual_all_native_warnings=[v for v in drc['violations']if v['severity']=='warning'],actual_complete_nets=False,
 candidate_adopted=False,manufacturing_ready=False)
e.write(out/'review.json',r);print(json.dumps({'return':proof['passed'],'new_defects':len(defects),'errors':len(r['actual_native_errors'])}))
