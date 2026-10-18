from pathlib import Path
import sys,json,copy
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_critical_digital_wip_r05 as authority
import hardware_route_critical_digital_wip_r03 as c
import hardware_scope_anchored_reference_pieces as pieces
import hardware_route_owned_bypass_loops_wip_r03 as w
e=authority.engine
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-local-CMOS-returns-adopted-r74/motherboard-source26-WIP.kicad_pcb')
OUT=Path('reports/motherboard-critical-routing-20261001/actual-AO1-SDO-root74-corridor-r04')
DEST=OUT/'motherboard-AO1-SDO-corridor-candidate.kicad_pcb'
MAP=Path('reports/motherboard-domains-20261001/source26-AO1-SDO-root74-r04/domain-map.json')
plan=e.read(OUT/'original-corridor-delta.json');retire=e.read(OUT/'new-fragment-retirement.json')
if not retire['passed']or plan['base_sha256']!=e.sha(BASE):raise ValueError('Actual bounded empty-space/reference ledger changed')
ids=set(plan['actual_added_copper_UUIDs']);name=plan['literal_source_net']
old=e.parse(BASE.read_text());new=e.parse(DEST.read_text())
def cu(t):return{e.value(e.child(n,'uuid')[1]):e.dump(n)for k in('segment','via','arc')for n in e.children(t,k)}
before,after=cu(old),cu(new)
if any(after.get(u)!=v for u,v in before.items())or set(after)-set(before)!=ids:raise ValueError('Actual oldCu/newfour ledger changed')
oldimm,newimm=e.immutable_objects(old),e.immutable_objects(new)
if oldimm[0]!=newimm[0]or oldimm[2]!=newimm[2]:raise ValueError('SOURCE/lands/poses/other objects changed')
changed={r['uuid']:r for r in plan['changed_zone_polygon_ledger']if r['action']=='polygon_only'}
removed=set()
restoration=e.read(OUT/'original-outline-restoration.json')
if not restoration['passed']or restoration['old_zone_retirements']!=0:raise ValueError('Actual original same-net outline retention failed')
oldzones,newzones=e.zone_definitions(old),e.zone_definitions(new)
if any(newzones.get(u)!=v for u,v in oldzones.items()if u not in changed):raise ValueError('Unreviewed old zone definition changed')
if set(newzones)-set(oldzones)!=set(changed)-set(oldzones)-removed:raise ValueError('New bounded zone split ledger differs')
for u,row in changed.items():
 if u in removed:continue
 if row['action']=='polygon_only':
  a,b=copy.deepcopy(e.parse(oldzones[u])),copy.deepcopy(e.parse(newzones[u]))
  for tree in(a,b):
   for p in list(e.children(tree,'polygon')):tree.remove(p)
  if e.dump(a)!=e.dump(b):raise ValueError('Actual revised zone changed rules/net/UUID beyond polygon')
d=e.read(OUT/'native.json');known=w.reviewed_wip_warnings(e.read(BASE.parent/'drc.json'),e.read(BASE.parent/'baseline-disposition.json'),e.sha(BASE))
if w.new_route_defects(d,known)or d.get('ignored_checks'):raise ValueError('Actual new native defect/ignored check')
b=pcbnew.LoadBoard(str(DEST));b.BuildConnectivity();pop,_=e.native_source_check(b,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
source=Path('reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/prototype-route-geometry-review.json');row=e.read(source)['nets'][name]
mapping=e.read(MAP)
if mapping['input_sha256'].get(str(DEST.resolve()))!=e.sha(DEST):raise ValueError('Actual current source-map binding failed')
check=pieces.SourceAnchoredPiecesCheck(b,{name:row},mapping);tracks={t.m_Uuid.AsString():t for t in b.GetTracks()};returns=[]
for u in sorted(ids):
 t=tracks[u]
 if t.GetNetname()!=name:raise ValueError('Actual four SDO segments source net changed')
 returns.append(dict(uuid=u,actual_source_owned_return=check.segment(t,row)))
def ps(board):return{(f.GetReference(),p.GetNumber()):p for f in board.GetFootprints()for p in f.Pads()}
def joined(board):
 board.BuildConnectivity();pads=ps(board);p,q=pads['U14626','3'],pads['U14623','10']
 return q.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in board.GetConnectivity().GetConnectedItems(p)}
if not joined(b):raise ValueError('Actual DAC SDO Source endpoints remain disconnected')
cut=[n for n in new if not(isinstance(n,list)and n and n[0]in('segment','via','arc')and e.value(e.child(n,'uuid')[1])in ids)]
cp=OUT/'physical-source-cut-SDO.kicad_pcb';cp.write_text(authority.dump_native_board(cut)+'\n')
if joined(pcbnew.LoadBoard(str(cp))):raise ValueError('Actual SDO physical route-cut negative ineffective')
retained=c.clusters_preserved(c.source_clusters(pcbnew.LoadBoard(str(BASE))),b)
r=dict(passed=True,scope='One actual AO1 DAC SDO Source pair/four F segments only',base_sha256=e.sha(BASE),board_sha256=e.sha(DEST),map_sha256=e.sha(MAP),tool_sha256=e.sha(__file__),source_population=pop,old_SOURCE_clusters=retained,exact_old_Cu_and_immutable_lands_source_poses_retained=True,changed_zone_polygons_exact_ledger=list(changed.values()),original_AO1_outline_retention_proof=restoration,all_original_zone_UUIDs_retained=True,new_SOURCE_empty_fragment_retirement=retire,native_errors=0,all_prior_unsuppressed_native_warnings=d['violations'],no_new_native_defects=True,no_ignored_checks=True,new_copper_UUIDs=sorted(ids),actual_SOURCE_pair=['U14626.3','U14623.10'],actual_SOURCE_pair_joined=True,persisted_actual_route_cut_negative=dict(passed=True,board_sha256=e.sha(cp),removed_UUIDs=sorted(ids)),actual_full_native_source_owned_reference_proofs=returns,eligible_piece_audit=check.eligible_piece_audit,complete_failed_reference_piece_ledger=check.full_native_report['unanchored_components'],own_return='/motherboard_analog_output/AO1_COM',reference_margin_mm=.40,no_foreign_SOURCE_reference_borrowing=True,loaded_ADC_DAC_waveform_qualification=False,whole_board_reference_qualification=False,manufacturing_ready=False)
e.write(OUT/'review.json',r);print(json.dumps(dict(passed=True,actual_SOURCE_pairs=1,newCu=4,native_errors=0,prior_warnings=len(d['violations']),actual_physical_cut_negative=True)),flush=True)
