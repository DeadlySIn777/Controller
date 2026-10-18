"""Actual literal critical Source-pair local routing; no net-class expansion."""
from pathlib import Path
import sys, copy, json, math, shutil
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_critical_digital_wip_r05 as authority
import hardware_scope_anchored_reference_pieces as pieces
import hardware_route_owned_bypass_loops_wip_r03 as w
from hardware_search_native_local_path import find_local_pad_path
from hardware_route_logic_return import xy
e=authority.engine
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-ordinary9-r75/motherboard-bounded-merged-candidate.kicad_pcb')
MAP=Path('reports/motherboard-domains-20261001/source26-r75-r01/domain-map.json')
SOURCE=Path('reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/prototype-route-geometry-review.json')
OUT=Path(sys.argv[1]);OUT.mkdir(exist_ok=False,parents=True)
review=e.read(SOURCE)
if review['source_design_sha256']!=e.sha('hardware/motherboard/design.json')or review['source_netlist_sha256']!=e.sha('hardware/motherboard/netlist.xml'):raise ValueError('Exact source26 critical inventory changed')
rows={n:r for n,r in review['nets'].items()if r['return_net']=='/LOGIC_GND'}
b=pcbnew.LoadBoard(str(BASE));b.BuildConnectivity();e.native_source_check(b,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
checker=pieces.SourceAnchoredPiecesCheck(b,rows,e.read(MAP));fill=checker.reference('/LOGIC_GND',pcbnew.In1_Cu);g=w.Geometry(b)
pads={};groups=[];blocked=[];added=[]
for f in b.GetFootprints():
 for p in f.Pads():
  if p.GetNetname()in rows and p.IsOnLayer(pcbnew.F_Cu):pads.setdefault(p.GetNetname(),[]).append(p)
jobs=[]
for name,ps in pads.items():
 for index,p in enumerate(ps):
  for q in ps[index+1:]:
   dist=math.dist(pcbnew.ToMM(p.GetPosition()),pcbnew.ToMM(q.GetPosition()))
   if dist<=8:jobs.append((dist,name,p,q))
for span,name,p,q in sorted(jobs,key=lambda row:row[0]):
 b.BuildConnectivity()
 if q.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in b.GetConnectivity().GetConnectedItems(p)}:continue
 row=rows[name];pair=[p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),q.GetParentFootprint().GetReference()+'.'+q.GetNumber()]
 if any([pad.GetParentFootprint().GetReference(),pad.GetNumber()]not in row['source_pins']for pad in(p,q)):raise ValueError('Literal native endpoint not reviewed')
 candidate=find_local_pad_path(b,p,q,geometry=g,eligible_reference_fill=fill,width_mm=.35,clearance_mm=.20,reference_margin_mm=.40,maximum_length_mm=8,maximum_seconds=15)
 if not candidate['passed']:
  blocked.append(dict(net=name,SOURCE_pair=pair,span_mm=span,reason=candidate));print(json.dumps(dict(blocked=name,pair=pair,reason=candidate)),flush=True);continue
 ids=[]
 for a,z in zip(candidate['proposed_points_mm'],candidate['proposed_points_mm'][1:]):
  t=pcbnew.PCB_TRACK(b);t.SetStart(xy(a));t.SetEnd(xy(z));t.SetLayer(pcbnew.F_Cu);t.SetWidth(pcbnew.FromMM(.35));t.SetNet(b.FindNet(name));b.Add(t);g.add(t);added.append(t);ids.append(t.m_Uuid.AsString())
 groups.append(dict(net=name,SOURCE_pair=pair,SOURCE_pad_UUIDs=[p.m_Uuid.AsString(),q.m_Uuid.AsString()],new_copper_UUIDs=ids,route=candidate,actual_SOURCE_review=row))
 print(json.dumps(dict(routed=name,pair=pair,newCu=len(ids))),flush=True)
tree=e.parse(BASE.read_text());old=copy.deepcopy(tree)
for t in added:tree.append(['segment',['start',*[str(v)for v in pcbnew.ToMM(t.GetStart())]],['end',*[str(v)for v in pcbnew.ToMM(t.GetEnd())]],['width','.35'],['layer','"F.Cu"'],['net',e.q(t.GetNetname())],['uuid',e.q(t.m_Uuid.AsString())]])
if e.immutable_objects(tree)!=e.immutable_objects(old):raise ValueError('Actual immutable SOURCE/lands/poses/zone definitions changed')
dest=OUT/'motherboard-critical-local-candidate.kicad_pcb';dest.write_text(authority.dump_native_board(tree)+'\n')
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(BASE.with_suffix(suffix),dest.with_suffix(suffix))
for f in BASE.parent.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,OUT/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,OUT/f.name)
e.write(OUT/'proposed-local-groups.json',dict(base_sha256=e.sha(BASE),map_sha256=e.sha(MAP),exact_critical_review_sha256=e.sha(SOURCE),tool_sha256=e.sha(__file__),groups=groups,blocked=blocked,actual_added_copper_UUIDs=[t.m_Uuid.AsString()for t in added],no_ordinary_allowlist_change=True,maximum_total_path_mm=8,unchanged_geometry=dict(width_mm=.35,clearance_mm=.20,reference_margin_mm=.40),full_failed_reference_piece_ledger=checker.full_native_report['unanchored_components'],native_final_validation_pending=True,manufacturing_ready=False))
print(json.dumps(dict(actual_local_groups=len(groups),newCu=len(added),blocked=len(blocked))),flush=True)
