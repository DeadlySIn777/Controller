"""Connect 34 exact low-current CMOS/supervisor ground pins to local own fill.

Only actual native GND/VSS/EP power-input pins of listed devices are eligible.
No signal, regulator, high-current switch, Kelvin, analog reference, module
socket, capacitor, or motor-bank head is selected. Source, placements, prior
tracks, zones, and every pad assignment remain unchanged. Adjacent reference
contact is proved in actual native copper. This is not global ground or HF
loop qualification. Physical short-to-ground current qualification is pending.
"""
import argparse,json,math,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
import pcbnew
from hardware_build_ordinary_route_manifest import native
from hardware_populate_motherboard_pcb import sha,write,pad_template
from hardware_route_owned_bypass_loops_wip_r03 import Geometry,reviewed_wip_warnings,new_route_defects
from hardware_route_logic_return import identity,xy,mm,segment_hits_box,segment_distance
from hardware_route_critical_digital_wip_r03 import source_clusters,clusters_preserved
from hardware_route_selected_additive_r02 import native_source_check
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_index_literal_reference_coverage import LiteralReferenceCoverage
from hardware_check_return_corridors import covered,circle
from hardware_stitch_owned_return_planes import definitions
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
ROLES={
 'receiving STEP/DIR idle low','FPGA-domain static default while forward buffer disabled',
 'defined-low boundary/output','outgoing STEP/DIR/TX idle-low',
 'FPGA/qualified-gate defined idle; overrides weak pull',
 'absent qualification defaults unavailable/inhibited, not a cached healthy state',
 'alarm logic output weak bias; not brownout guarantee','OPI rearm unconfigured default low',
 'output_bias','fixed permission command receiving default LOW',
 'missing isolated transfer reads bad; no intermediate-power claim',
 'LOW default includes unused-user FPGA weak pull-up; receiving leakage to qualify',
 'logic fail-off/default bias','local EN defaults OFF','local power-good absent default low',
 'receiving isolated health output bias; VCCO partial state remains unqualified',
 'idleclockLOW','MCU reset/unprogrammed defaults analog enable requests LOW',
 'frontend receiver LOW default','below0.6V supervisor output undefined held LOW by real bias',
 'powered open-input/zero-VCC bias; partial power not guaranteed',
 'missing isolated-domain observation reads not-good; real monitor is separately required',
 'physical gate unpowered Ioff bias low','probe LOW when frontend unpowered/highZ',
 'module receiver LOW default','module input default LOW while return buffer disabled',
 'health raw power-loss bias, not intermediate-voltage guarantee',
 'missing controller/permission defaults OFF','inactive AI command LOW',
 'frontend communication LOW default','inactive host clock LOW',
 'unconfigured FPGA MISO defaults LOW','inactive host command LOW',
 'inactive AI clock LOW','rearm input idleLOW','missing/unprogrammed host link default',
 'module-domain inactive input; no IO rail to unpowered compute',
 'unprogrammed/high-Z MCU response LOW; invalid frame remains invalid',
 'raw module communication LOW default','actual transceiver DE off default',
 'UART DE absent/unprogrammed LOW','zero-VCC Ioff output bias','defined common-stem bias',
 'missing chain reads invalid marker','permission receiver absent default low',
 'missing isolated field-supply health monitor is not healthy',
 'Absent compute defined LOW; frame freshness decides availability',
 'shared SPI2 inactive return bias; AI frontend must gate its SDO by separate CS',
 'host gate zero-source bias','LED driver input default LOW',
 'missing module/supervisor enable request defaults LOW'}

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for k in('board','map','out'):ap.add_argument('--'+k,type=Path,required=True)
 a=ap.parse_args();assert not a.out.exists()
 src=ROOT/'hardware/motherboard';model=json.loads((src/'design.json').read_text());mapping=json.loads(a.map.read_text())
 assert not mapping['errors']and mapping['source_physical_population_complete']
 nodes,nets,functions=native(model,src/'netlist.xml');domain={p['net']:p['domain']for p in mapping['pads']}
 selected=[{'reference': 'U13002', 'pin': '2', 'MPN': 'TPS3808G33DBVR', 'exact_source_role': 'actual3.07V IO rail supervisor; CT open fixed20msnominal reset release', 'native_function': {'num': '2', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U13005', 'pin': '2', 'MPN': 'TPS3808G33DBVR', 'exact_source_role': 'actual3.07V IO rail supervisor; CT open fixed20msnominal reset release', 'native_function': {'num': '2', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U13009', 'pin': '2', 'MPN': 'TPS3808G33DBVR', 'exact_source_role': 'actual3.07V IO rail supervisor; CT open fixed20msnominal reset release', 'native_function': {'num': '2', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U13011', 'pin': '3', 'MPN': 'SN74LVC1G17DBVR', 'exact_source_role': 'actual MCU reset to fail-off frontend; avoids NRST10kUP/RESET10kDOWN divider', 'native_function': {'num': '3', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U14007', 'pin': '7', 'MPN': 'SN74LVC14APWR', 'exact_source_role': 'six protected active-LOW contacts translated to active-HIGH status', 'native_function': {'num': '7', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U14014', 'pin': '7', 'MPN': 'SN74LVC14APWR', 'exact_source_role': 'six protected active-LOW contacts translated to active-HIGH status', 'native_function': {'num': '7', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U14017', 'pin': '3', 'MPN': 'SN74LVC1G17DBVR', 'exact_source_role': 'Schmitt restore slow request/configuration input before non-Schmitt AND', 'native_function': {'num': '3', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U14019', 'pin': '4', 'MPN': 'SN74LVC2G08DCUR', 'exact_source_role': 'XF enable=configurationdone AND qualifiedregion AND configuredrequest AND actual modulepresence', 'native_function': {'num': '4', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U14030', 'pin': '7', 'MPN': 'SN74LVC14APWR', 'exact_source_role': 'active-LOW fault/isolatedgood converted to active-HIGH status;unusedinputs grounded', 'native_function': {'num': '7', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U14032', 'pin': '8', 'MPN': 'SN74LV165APWR', 'exact_source_role': 'read-only parallel-in register;bank0 Hfirst', 'native_function': {'num': '8', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U14033', 'pin': '8', 'MPN': 'SN74LV165APWR', 'exact_source_role': 'read-only parallel-in register;bank1 Hfirst', 'native_function': {'num': '8', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U14034', 'pin': '8', 'MPN': 'SN74LV165APWR', 'exact_source_role': 'read-only parallel-in register;bank2 Hfirst', 'native_function': {'num': '8', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U14502', 'pin': '2', 'MPN': 'TPS3808G33DBVR', 'exact_source_role': '3.07V rail reset; fixed open-CT20ms nominal release', 'native_function': {'num': '2', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U14805', 'pin': '7', 'MPN': '74LVC125APW,118', 'exact_source_role': 'actual Nexperia Ioff protection into power-cycled controller: three forward SPI paths and one reverse INT path; Ioff output faces always-on host pull-up', 'native_function': {'num': '7', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U14809', 'pin': '3', 'MPN': 'SN74LVC1G125DBVR', 'exact_source_role': 'Ioff receiver into power-cycled controller; input tolerant5.5V while supply OFF', 'native_function': {'num': '3', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U14810', 'pin': '3', 'MPN': 'SN74LVC1G32DBVR', 'exact_source_role': 'real standby HIGH until controller rail ready and GPIO0/XSTBY deliberately configured LOW', 'native_function': {'num': '3', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U15001', 'pin': '2', 'MPN': 'TPS3808G33DBVR', 'exact_source_role': 'actual module3V3 supervision;3.07V threshold20msnominal release; no OS identity/ready inference', 'native_function': {'num': '2', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U15007', 'pin': '3', 'MPN': 'SN74LVC1G125DBVR', 'exact_source_role': 'Ioff-rated module to FPGA host link; source33R damping; no wired parallel driver', 'native_function': {'num': '3', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U15040', 'pin': '3', 'MPN': 'SN74LVC1G125DBVR', 'exact_source_role': 'return buffer powered only by the actual module-own auxiliary rail; Ioff protects missing module', 'native_function': {'num': '3', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U17004', 'pin': '7', 'MPN': '74LVC07APW,118', 'exact_source_role': '5V open-drain sink with explicit powered-HIGH and unpowered leakage bounds', 'native_function': {'num': '7', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U17007', 'pin': '7', 'MPN': 'SN74AHCT04PWR', 'exact_source_role': 'TTL receive buffer, no motion/DI authority', 'native_function': {'num': '7', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U17015', 'pin': '7', 'MPN': '74LVC07APW,118', 'exact_source_role': 'hardware RED override and independent WDT fault sink; LOW GOOD -> fault ON', 'native_function': {'num': '7', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U19020', 'pin': '3', 'MPN': 'SN74LVC1G06DBVR', 'exact_source_role': 'validHIGH good sinks active-HIGH fault input; receiving MCU10k pullup retained', 'native_function': {'num': '3', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U19022', 'pin': '3', 'MPN': 'SN74LVC1G06DBVR', 'exact_source_role': 'validHIGH good sinks active-HIGH fault input; receiving MCU10k pullup retained', 'native_function': {'num': '3', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U19023', 'pin': '3', 'MPN': 'SN74LVC1G06DBVR', 'exact_source_role': 'validHIGH good sinks active-HIGH fault input; receiving MCU10k pullup retained', 'native_function': {'num': '3', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U19024', 'pin': '3', 'MPN': 'SN74LVC1G06DBVR', 'exact_source_role': 'validHIGH good sinks active-HIGH fault input; receiving MCU10k pullup retained', 'native_function': {'num': '3', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U4003', 'pin': '4', 'MPN': 'SN74LVC2G08DCUR', 'exact_source_role': 'motion raw inhibit and asynchronous clear', 'native_function': {'num': '4', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U4008', 'pin': '2', 'MPN': 'SN74LVC1G11DBVR', 'exact_source_role': 'final output permission', 'native_function': {'num': '2', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U4009', 'pin': '4', 'MPN': 'SN74LVC2G08DCUR', 'exact_source_role': 'output watchdog and safety-output request gate', 'native_function': {'num': '4', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U4012', 'pin': '4', 'MPN': 'SN74LVC2G74DCUR', 'exact_source_role': 'sticky accepted general-output interruption', 'native_function': {'num': '4', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U4014', 'pin': '4', 'MPN': 'SN74LVC2G74DCUR', 'exact_source_role': 'M sticky actual-SET1-qualified watchdog falling-edge trip', 'native_function': {'num': '4', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U4019', 'pin': '4', 'MPN': 'SN74LVC2G08DCUR', 'exact_source_role': 'power-reset and explicit trip-record asynchronous clear', 'native_function': {'num': '4', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U6041', 'pin': '2', 'MPN': 'LTC6994IS6-2#TRPBF', 'exact_source_role': 'bank A both-edge digital permission qualifier; NDIV1/POL0', 'native_function': {'num': '2', 'name': 'GND', 'type': 'power_in'}}, {'reference': 'U6052', 'pin': '3', 'MPN': '74AHCT1G17GVH', 'exact_source_role': 'TTL Schmitt permission level restoration into 5V digital qualifier', 'native_function': {'num': '3', 'name': 'GND', 'type': 'power_in'}}]
 for row in selected:
  assert nodes[row['reference'],row['pin']]=='/LOGIC_GND'
  assert functions[row['reference']][row['pin']]==row['native_function']
  assert model['components'][row['reference']]['mpn']==row['MPN']
 assert selected
 frozen={str(p.resolve()):sha(p)for p in(a.board,a.map,src/'design.json',src/'netlist.xml',Path(__file__),ROOT/'tools/hardware_index_literal_reference_coverage.py')}
 base_native=json.loads((a.board.parent/'drc.json').read_text());known=reviewed_wip_warnings(base_native,json.loads((a.board.parent/'baseline-disposition.json').read_text()),sha(a.board))
 b=pcbnew.LoadBoard(str(a.board));b.BuildConnectivity();native_source_check(b,model,src/'netlist.xml')
 old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};oldpads={p.m_Uuid.AsString():(p.GetNumber(),p.GetNetname(),tuple(p.GetPosition()),pad_template(p))for p in b.GetPads()};oldzones=definitions(a.board);prior=source_clusters(b)
 ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()};physical={p['uuid']:p for p in mapping['pads']}
 for p in b.GetPads():
  if p.GetNumber()and p.IsOnCopperLayer():
   row=physical[p.m_Uuid.AsString()];assert row['net']==p.GetNetname()and all(abs(x-y)<1e-6 for x,y in zip(row['position_mm'],mm(p.GetPosition())))
 fills=collect_native_reference_fills(b,{'/LOGIC_GND'},[pcbnew.In1_Cu,pcbnew.In4_Cu]);geometry=Geometry(b)
 index=LiteralReferenceCoverage(b,{'/LOGIC_GND'},[pcbnew.In1_Cu,pcbnew.In4_Cu])
 foreign=[p for p in mapping['pads']if p['domain']not in('LOGIC','NC')]
 foreign_cu=[t for t in b.GetTracks()if domain.get(t.GetNetname(),'LOGIC')not in('LOGIC','NC')]
 def physical_clear(s,e,side):
  # A plated barrel crosses the full board; retain all foreign-pad projection
  # spacing even when the other pad lives on the opposite outer layer.
  if any(segment_hits_box(e,e,p['copper_aabb_mm'],.85)or(b.GetLayerName(side)in p['copper_layers']and segment_hits_box(s,e,p['copper_aabb_mm'],.75))for p in foreign):return False
  for t in foreign_cu:
   width=pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)if isinstance(t,pcbnew.PCB_VIA)else t.GetWidth())
   if segment_distance(e,e,mm(t.GetStart()),mm(t.GetEnd()))<.85+width/2-1e-6:return False
   if t.IsOnLayer(side)and segment_distance(s,e,mm(t.GetStart()),mm(t.GetEnd()))<.75+width/2-1e-6:return False
  return True
 groups=[];already=[];blocked=[];alive=[]
 for row in selected:
  p=ps[row['reference'],row['pin']];assert p.GetNetname()=='/LOGIC_GND'
  side=p.GetParentFootprint().GetLayer();assert side in(pcbnew.F_Cu,pcbnew.B_Cu)
  adjacent=pcbnew.In1_Cu if side==pcbnew.F_Cu else pcbnew.In4_Cu;s=mm(p.GetPosition())
  b.BuildConnectivity();co=b.GetConnectivity()
  actual_vias={v.m_Uuid.AsString():v for v in b.GetTracks()if isinstance(v,pcbnew.PCB_VIA)}
  anchors=[actual_vias[t.m_Uuid.AsString()]for t in co.GetConnectedItems(p)if t.Type()==pcbnew.PCB_VIA_T and physical_reference_contact(actual_vias[t.m_Uuid.AsString()],adjacent,co)]
  if anchors:already.append(dict(**row,actual_existing_connected_via_UUIDs=[anchors[0].m_Uuid.AsString()],actual_existing_connected_via_count=len(anchors)));continue
  chosen=None
  for distance in(.7,.85,1.,1.2,1.5,1.8,2.):
   for angle in range(24):
    e=(round(s[0]+distance*math.cos(angle*math.pi/12),6),round(s[1]+distance*math.sin(angle*math.pi/12),6))
    if geometry.via(e,'/LOGIC_GND')and geometry.clear([s,e],'/LOGIC_GND',side,.3)and physical_clear(s,e,side)and index.candidate_covered(circle(tuple(xy(e)),pcbnew.FromMM(.26)),'/LOGIC_GND',adjacent):chosen=e;break
   if chosen:break
  if not chosen:blocked.append(row);continue
  t=pcbnew.PCB_TRACK(b);t.SetNet(p.GetNet());t.SetLayer(side);t.SetWidth(pcbnew.FromMM(.3));t.SetStart(p.GetPosition());t.SetEnd(xy(chosen));b.Add(t);geometry.add(t)
  v=pcbnew.PCB_VIA(b);v.SetNet(p.GetNet());v.SetPosition(xy(chosen));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetRemoveUnconnected(False);v.SetIsFree(True);b.Add(v);geometry.add(v);alive.extend([t,v])
  groups.append(dict(**row,source_pad_uuid=p.m_Uuid.AsString(),adjacent_layer=b.GetLayerName(adjacent),via_uuid=v.m_Uuid.AsString(),new_UUIDs=[t.m_Uuid.AsString(),v.m_Uuid.AsString()],length_mm=math.dist(s,chosen),retained=True))
 a.out.mkdir(parents=True);dest=a.out/'exact-CMOS-ground-candidate.kicad_pcb'
 for ext in('.kicad_pro','.kicad_dru'):shutil.copyfile(a.board.with_suffix(ext),dest.with_suffix(ext))
 for p in a.board.parent.iterdir():
  if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,a.out/p.name)
  elif p.name=='fp-lib-table':shutil.copyfile(p,a.out/p.name)
 planned={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};owners={uid:i for i,g in enumerate(groups)for uid in g['new_UUIDs']}
 write(a.out/'generation.json',dict(input_sha256=frozen,selected_source_rows=selected,groups=groups,already_source_connected=already,blocked_required=blocked));print(dict(selected=len(selected),new_groups=len(groups),already=len(already),blocked=len(blocked)),flush=True)
 for attempt in range(8):
  pcbnew.SaveBoard(str(dest),b);path=a.out/('native-'+str(attempt)+'.json');run=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(path),str(dest)],capture_output=True,text=True);(a.out/('native-'+str(attempt)+'.txt')).write_text(run.stdout+run.stderr);assert run.returncode==0
  report=json.loads(path.read_text());bad=set()
  for issue in new_route_defects(report,known):
   indices={owners[item['uuid']]for item in issue['items']if item['uuid']in owners}
   if not indices:raise ValueError('New native defect outside new return branches')
   bad|=indices
  if not bad:break
  for i in bad:
   for t in list(b.GetTracks()):
    if t.m_Uuid.AsString()in groups[i]['new_UUIDs']:b.Remove(t)
   groups[i]['retained']=False
 else:raise ValueError('Native repair bound exceeded')
 actual=pcbnew.LoadBoard(str(dest));actual.BuildConnectivity();current={t.m_Uuid.AsString():t for t in actual.GetTracks()};kept={uid for g in groups if g['retained']for uid in g['new_UUIDs']}
 assert set(current)==set(old)|kept and all(identity(current[u])==v for u,v in old.items())and all(identity(current[u])==planned[u]for u in kept)
 assert oldpads=={p.m_Uuid.AsString():(p.GetNumber(),p.GetNetname(),tuple(p.GetPosition()),pad_template(p))for p in actual.GetPads()}and oldzones==definitions(dest)
 clusters=clusters_preserved(prior,actual);native_source_check(actual,model,src/'netlist.xml');finalfills=collect_native_reference_fills(actual,{'/LOGIC_GND'},[pcbnew.In1_Cu,pcbnew.In4_Cu]);co=actual.GetConnectivity()
 for g in groups:
  if not g['retained']:continue
  v=current[g['via_uuid']];layer=actual.GetLayerID(g['adjacent_layer'])
  assert g['source_pad_uuid']in{i.m_Uuid.AsString()for i in co.GetConnectedItems(v)}and physical_reference_contact(v,layer,co)and covered(circle(tuple(v.GetPosition()),pcbnew.FromMM(.26)),finalfills['/LOGIC_GND',layer])
 assert all(sha(Path(p))==h for p,h in frozen.items())
 write(a.out/'bounded-scope.json',dict(electrical_source_unchanged=True,reviewed_scope_reason=__doc__,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(kept),reviewed_added_zone_UUIDs=[]))
 write(a.out/'receipt.json',dict(passed=True,input_sha256=frozen,board_sha256=sha(dest),source_review=selected,actual_return_groups=groups,already_connected=already,required_blocked=blocked,prior_SOURCE_clusters=clusters,new_ground_Cu=len(kept),native_errors=0,remaining_native_warnings=report['violations'],ignored_checks=[],uncapped_missing_joins=co.GetUnconnectedCount(False),global_ground_distribution_or_current_capacity_qualified=False,manufacturing_ready=False))
 print(dict(passed=True,retained_groups=sum(g['retained']for g in groups),new_Cu=len(kept),missing_joins=co.GetUnconnectedCount(False)),flush=True)
if __name__=='__main__':main()
