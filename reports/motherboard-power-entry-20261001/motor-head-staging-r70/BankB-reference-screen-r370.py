import sys,json,hashlib,collections,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,mm
R=Path('reports/motherboard-power-entry-20261001/ROOT101-bankB-minimal-cell-r350/receipt.json');B=R.parent/'motor-bank-B-receiving-candidate.kicad_pcb';O=Path('reports/motherboard-power-entry-20261001/ROOT101-bankB-reference-screen-r370');assert not O.exists();O.mkdir()
helper=Path('reports/motherboard-return-zoning-20261001/check_exact_endpoint_antipad_union_r01.py');spec=importlib.util.spec_from_file_location('exact_endpoint',helper);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
frozen={str(p):sha(p)for p in[B,R,helper,Path(__file__),Path('hardware/motherboard/design.json')]};r=json.loads(R.read_text());b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();ts={t.m_Uuid.AsString():t for t in b.GetTracks()}
short={'MOTOR_FEED_REARM_B','OPI_REARM_M','MOTOR_FEED_ON_B','MOTOR_FEED_CLEAR_SOURCE_B','MOTOR_FEED_CLEAR_MID_B','MOTOR_FEED_CLEAR_N_B','MOTOR_TX_GATE_CONTACT_MID_B','MOTOR_FEED_PG_B'}
selected={v['uuid']for v in r['exact_added_copper']if v['net'].rsplit('/',1)[-1]in short};nets={ts[u].GetNetname()for u in selected};rows={n:dict(return_net='/LOGIC_GND',reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu','In2.Cu':'In1.Cu','In3.Cu':'In4.Cu'},reference_corridor_margin_mm=.40,allow_vias=True,via_diameter_mm=.50,via_drill_mm=.20,return_stitch_distance_mm=1.0)for n in nets}
c=m.ExactEndpointUnionCheck(b,rows);checks=[]
for u in sorted(selected):
 t=ts[u]
 try:q=c.via(t,rows[t.GetNetname()])if isinstance(t,pcbnew.PCB_VIA)else c.segment(t,rows[t.GetNetname()]);checks.append(dict(uuid=u,passed=True,actual=identity(t),proof=q))
 except ValueError as e:checks.append(dict(uuid=u,passed=False,actual=identity(t),reason=str(e)))
assert all(sha(Path(p))==h for p,h in frozen.items());data=dict(board_sha256=sha(B),input_hashes=frozen,reference_requirements=rows,actual_selected_control_Cu=len(selected),passed=sum(v['passed']for v in checks),rejected=sum(not v['passed']for v in checks),checks=checks,no_source_or_native_board_mutation=True,control_reference_qualified=all(v['passed']for v in checks),physical_loaded_timing_qualified=False);(O/'screen.json').write_text(json.dumps(data,indent=2));(O/'control-path-manifest.json').write_text(json.dumps(dict(board_sha256=sha(B),reference_requirements=rows,route_roles=[x for x in r['routes']if x['net']in nets],actual_selected_Cu_UUIDs=sorted(selected)),indent=2));print('SCREEN',data['passed'],data['rejected'],flush=True)
