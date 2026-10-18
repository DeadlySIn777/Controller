"""Literal38 rule candidate plus aggregate-per-net guard and primary conflicts.

The candidate absolute floor is .15 only because KiCad's absolute minimum
cannot be locally overridden; the custom .20 rule remains effective everywhere
else. This writes a report copy, never changes an authoritative parent board.
"""
from pathlib import Path
import sys,json,copy,math,shutil,urllib.request,uuid
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_review_fpga_neck_rule as prior
import hardware_route_critical_digital_wip_r05 as authority
import hardware_audit_fpga_package_access as access
e=authority.engine
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-four-reference-closures-r71/motherboard-bounded-merged-candidate.kicad_pcb')
OUT=Path(sys.argv[1]);OUT.mkdir(exist_ok=False,parents=True)
review=e.read('reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/prototype-route-geometry-review.json')
b=pcbnew.LoadBoard(str(BASE));fp=next(f for f in b.GetFootprints()if f.GetReference()=='U1001')
_,nodes=e.native_source_check(b,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
names={p.GetNetname()for p in fp.Pads()if p.GetNetname()in review['nets']}
if len(names)!=38 or any(n in {'/LOGIC_GND','/CORE_1V2','/IO_3V3'}for n in names):raise ValueError('Literal reviewed critical signal scope changed')

def aggregate_guard(board):
 totals={};records=[]
 for t in board.GetTracks():
  if t.Type()!=pcbnew.PCB_TRACE_T or pcbnew.ToMM(t.GetWidth())>=.2-1e-6:continue
  net=t.GetNetname();start,end=pcbnew.ToMM(t.GetStart()),pcbnew.ToMM(t.GetEnd())
  if net not in names or t.GetLayer()!=pcbnew.F_Cu or abs(pcbnew.ToMM(t.GetWidth())-.15)>1e-6:raise ValueError('Narrow copper escaped literal F-only signal exception')
  # Whole conductor, including its half-width, lies inside the declared area.
  if any(not (92+.075<=x<=108-.075 and 36+.075<=y<=52-.075)for x,y in (start,end)):raise ValueError('Narrow neck leaves literal U1001 area')
  length=math.dist(start,end);totals[net]=totals.get(net,0)+length;records.append(dict(uuid=t.m_Uuid.AsString(),net=net,length_mm=length))
 if any(v>1+1e-6 for v in totals.values()):raise ValueError('Aggregate narrow F neck exceeds 1mm per reviewed net')
 return dict(passed=True,narrow_segments=records,aggregate_length_mm_by_net=totals,maximum_per_net_mm=1.0)

controls=[]
sample=next(n for n in sorted(names)if n=='/fpga_core/IOL1_L1_MISO')
for mode in ('healthy_aggregate','split_overlength','unreviewed_net','B_side'):
 fixture=pcbnew.BOARD()
 for n in names|{'/UNREVIEWED'}:fixture.Add(pcbnew.NETINFO_ITEM(fixture,n))
 net=sample if mode!='unreviewed_net'else'/UNREVIEWED';layer=pcbnew.B_Cu if mode=='B_side'else pcbnew.F_Cu
 access.track(fixture,net,(96,42),(96.4,42),layer,.15)
 access.track(fixture,net,(96.4,42),(96.8,42),layer,.15)
 if mode=='split_overlength':access.track(fixture,net,(96.8,42),(97.2,42),layer,.15)
 try:r=aggregate_guard(fixture);controls.append(dict(mode=mode,accepted=True,proof=r))
 except ValueError as exc:controls.append(dict(mode=mode,accepted=False,reason=str(exc)))
if not controls[0]['accepted']or any(c['accepted']for c in controls[1:]):raise ValueError('Aggregate neck positive/negative controls failed')

primary=[]
for label,url in [('pcbway-capabilities','https://www.pcbway.com/capabilities.html'),('pcbway-manufacturing-tolerances','https://www.pcbway.com/pcb_prototype/PCB_Manufacturing_tolerances.html')]:
 path=OUT/(label+'.html');path.write_bytes(urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=60).read());primary.append(dict(url=url,path=str(path),sha256=e.sha(path),retrieved='2026-10-01'))
tree=e.parse(BASE.read_text());original=copy.deepcopy(tree)
# Exact native area syntax is copied from the prior persisted actual package
# rule-zone fixture. Only its UUID is fresh. No old board object is resaved or
# normalized while constructing this bounded rule-only proposal.
zone_tree=e.parse('(zone (layer "F.Cu") (uuid "'+str(uuid.uuid4())+'") (name "'+prior.AREA+'") (hatch edge 0.5) (connect_pads (clearance 0)) (min_thickness 0.25) (keepout (tracks allowed) (vias allowed) (pads allowed) (copperpour allowed) (footprints allowed)) (placement (enabled no) (sheetname "")) (fill (thermal_gap 0.5) (thermal_bridge_width 0.5) (island_removal_mode 0)) (polygon (pts (xy 92 36) (xy 108 36) (xy 108 52) (xy 92 52))))');tree.append(zone_tree)
dest=OUT/'motherboard-literal38-neck-rule-candidate.kicad_pcb';dest.write_text(authority.dump_native_board(tree)+'\n',encoding='utf8')
project=json.loads(BASE.with_suffix('.kicad_pro').read_text());project['board']['design_settings']['rules']['min_track_width']=.15;dest.with_suffix('.kicad_pro').write_text(json.dumps(project,indent=2))
dest.with_suffix('.kicad_dru').write_text(BASE.with_suffix('.kicad_dru').read_text()+prior.proposed_rules(names))
for f in BASE.parent.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,OUT/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,OUT/f.name)
e.write(OUT/'proposal.json',dict(board_sha256=e.sha(BASE),candidate_sha256=e.sha(dest),source_design_sha256=e.sha('hardware/motherboard/design.json'),source_netlist_sha256=e.sha('hardware/motherboard/netlist.xml'),tool_sha256=e.sha(__file__),nets={n:nodes[n]for n in sorted(names)},rules_sha256=e.sha(dest.with_suffix('.kicad_dru')),absolute_floor_mm=.15,effective_general_minimum_mm=.2,neck_width_mm=.15,neck_area_mm=[92,36,108,52],F_only=True,maximum_aggregate_per_net_mm=1.0,aggregate_guard=aggregate_guard(b),aggregate_controls=controls,primary_sources=primary,
 primary_tolerances_2oz=dict(normal_trace_spacing_mm=.15,pad_trace_mm=.15,compensation_mm=.02,normal_via_ring_mm=.16),primary_capabilities_70um=dict(normal_trace_spacing_mm=[.1778,.2032],medium_trace_spacing_mm=[.1524,.1778]),
 conflicting_primary_process_tables_retained=True,exact_factory_2oz_process_confirmation_outstanding=True,existing_specific_BGA_125um_pad_via_rule_unchanged=True,reference_annulus_checker_unchanged=True,all_old_copper_retained=True,no_routes_added=True,actual_parent_changed=False,native_validation_pending=True,manufacturing_ready=False))
print(json.dumps(dict(candidate=str(dest),exact_signal_nets=len(names),aggregate_controls_passed=True,actual_parent_changed=False)),flush=True)
