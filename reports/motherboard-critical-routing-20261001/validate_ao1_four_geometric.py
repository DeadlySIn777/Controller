from pathlib import Path
import sys,json,collections
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_critical_digital_wip_r05 as a
import hardware_route_critical_digital_wip_r03 as c
import hardware_route_owned_bypass_loops_wip_r03 as w
from hardware_route_logic_return import identity
e=a.engine
base=Path('reports/motherboard-return-zoning-20261001/source26-r61-AO1-DAC-return-r04/motherboard-AO1-DAC-return-candidate.kicad_pcb');out=Path('reports/motherboard-critical-routing-20261001/actual-AO1-DAC4-geometric-native-r01');dest=out/'motherboard-AO1-four-geometric-candidate.kicad_pcb'
before=e.parse(base.read_text());after=e.parse(dest.read_text());old={e.value(e.child(t,'uuid')[1]):e.dump(t)for k in('segment','via','arc')for t in e.children(before,k)};new={e.value(e.child(t,'uuid')[1]):e.dump(t)for k in('segment','via','arc')for t in e.children(after,k)}
if e.immutable_objects(before)!=e.immutable_objects(after):raise ValueError('Old native source/lands/poses/zones changed')
if any(new.get(k)!=v for k,v in old.items()):raise ValueError('Old exact copper geometry/net changed')
d=e.read(out/'drc.json');orig_d=e.read(base.parent/'native.json');known=set(map(w.warning_key,orig_d['violations']))
if w.new_route_defects(d,known):raise ValueError('New native defect')
b=pcbnew.LoadBoard(str(dest));pop,nodes=e.native_source_check(b,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'));cl=c.clusters_preserved(c.source_clusters(pcbnew.LoadBoard(str(base))),b);b.BuildConnectivity()
rows=e.read('reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/critical-digital-source-review.json')['nets'];sources=[]
for net in('/motherboard_analog_output/AO1_DAC_RESET_N','/motherboard_analog_output/AO1_DAC_SDO','/motherboard_analog_output/AO1_DAC_CS_N','/motherboard_analog_output/AO1_DAC_SDI'):
 pads=[p for p in b.GetPads()if p.GetNetname()==net];p=pads[0];peers={x.m_Uuid.AsString()for x in b.GetConnectivity().GetConnectedItems(p)}|{p.m_Uuid.AsString()}
 if not all(q.m_Uuid.AsString()in peers for q in pads):raise ValueError('Literal actual source endpoint not joined:'+net)
 sources.append(dict(net=net,source_pins=rows[net]['source_pins'],all_real_sources_joined=True))
r=dict(board_sha256=e.sha(dest),base_sha256=e.sha(base),actual_source_design_sha256=e.sha('hardware/motherboard/design.json'),native_errors=0,actual_unsuppressed_warnings=d['violations'],no_new_native_defects=True,all_old_immutable_objects_retained=True,all_old_exact_copper_retained=True,added_copper_uuids=sorted(set(new)-set(old)),added_items=len(new)-len(old),population=pop,cluster_retention=cl,actual_source_endpoint_proof=sources,reference_qualification_pending=True,geometric_route_proposal_only=True,adoptable=False,manufacturing_ready=False)
e.write(out/'native-geometric-proof.json',r);print(json.dumps(dict(newCu=r['added_items'],complete_real_source_nets=len(sources),native_errors=0,native_warnings=len(d['violations']),reference_pending=True)))
