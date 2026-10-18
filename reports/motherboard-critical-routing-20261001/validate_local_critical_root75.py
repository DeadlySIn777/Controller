from pathlib import Path
import sys, json, copy
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_critical_digital_wip_r05 as authority
import hardware_route_critical_digital_wip_r03 as c
import hardware_scope_anchored_reference_pieces as pieces
import hardware_route_owned_bypass_loops_wip_r03 as w
e=authority.engine
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-ordinary9-r75/motherboard-bounded-merged-candidate.kicad_pcb')
OUT=Path('reports/motherboard-critical-routing-20261001/actual-source26-root75-local-critical-r01')
DEST=OUT/'motherboard-critical-local-candidate.kicad_pcb'
MAP=Path('reports/motherboard-domains-20261001/source26-root75-critical7-r01/domain-map.json')
plan=e.read(OUT/'proposed-local-groups.json')
source=Path('reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/prototype-route-geometry-review.json')
rows=e.read(source)['nets']
if e.sha(source)!=plan['exact_critical_review_sha256']or e.sha(BASE)!=plan['base_sha256']:raise ValueError('Frozen actual source/critical review changed')
old=e.parse(BASE.read_text());new=e.parse(DEST.read_text())
def cu(t):return{e.value(e.child(n,'uuid')[1]):e.dump(n)for k in('segment','via','arc')for n in e.children(t,k)}
before,after=cu(old),cu(new)
if e.immutable_objects(old)!=e.immutable_objects(new)or any(after.get(u)!=v for u,v in before.items())or set(after)-set(before)!=set(plan['actual_added_copper_UUIDs']):raise ValueError('Actual oldCu/lands/poses/zones/ledger changed')
d=e.read(OUT/'native.json');known=w.reviewed_wip_warnings(e.read(BASE.parent/'drc.json'),e.read(BASE.parent/'baseline-disposition.json'),e.sha(BASE))
if w.new_route_defects(d,known)or d.get('ignored_checks'):raise ValueError('Actual new native error/warning or ignored check')
b=pcbnew.LoadBoard(str(DEST));b.BuildConnectivity();pop,_=e.native_source_check(b,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
selected={g['net']:rows[g['net']]for g in plan['groups']}
mapping=e.read(MAP)
if mapping['input_sha256'].get(str(DEST.resolve()))!=e.sha(DEST):raise ValueError('Actual complete current source-map binding failed')
check=pieces.SourceAnchoredPiecesCheck(b,selected,mapping);tracks={t.m_Uuid.AsString():t for t in b.GetTracks()};returnproof=[]
for u in plan['actual_added_copper_UUIDs']:
 t=tracks[u];returnproof.append(dict(uuid=u,net=t.GetNetname(),actual_own_return=check.segment(t,selected[t.GetNetname()])))
def pads(board):return{p.m_Uuid.AsString():p for f in board.GetFootprints()for p in f.Pads()}
def joined(board,ids):
 board.BuildConnectivity();p,q=[pads(board)[u]for u in ids]
 return q.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in board.GetConnectivity().GetConnectedItems(p)}
positive=[];negative=[]
for index,g in enumerate(plan['groups']):
 if not joined(b,g['SOURCE_pad_UUIDs']):raise ValueError('Actual critical SOURCE endpoints not coupled')
 positive.append(dict(net=g['net'],SOURCE_pair=g['SOURCE_pair'],joined=True))
 remove={u for later in plan['groups'][index:]for u in later['new_copper_UUIDs']}
 cut=[n for n in new if not(isinstance(n,list)and n and n[0]in('segment','via','arc')and e.value(e.child(n,'uuid')[1])in remove)]
 cp=OUT/('physical-source-cut-'+str(index+1)+'.kicad_pcb');cp.write_text(authority.dump_native_board(cut)+'\n')
 if joined(pcbnew.LoadBoard(str(cp)),g['SOURCE_pad_UUIDs']):raise ValueError('Actual critical physical route-cut negative ineffective')
 negative.append(dict(net=g['net'],actual_cut_disconnected=True,exact_removed_UUIDs=sorted(remove),physical_cut_board_sha256=e.sha(cp)))
retained=c.clusters_preserved(c.source_clusters(pcbnew.LoadBoard(str(BASE))),b)
r=dict(passed=True,scope='Two literal local critical SOURCE pair groups only; not whole clock/MOSI net completion',base_sha256=e.sha(BASE),board_sha256=e.sha(DEST),map_sha256=e.sha(MAP),exact_critical_review_sha256=e.sha(source),tool_sha256=e.sha(__file__),new_copper_UUIDs=plan['actual_added_copper_UUIDs'],actual_SOURCE_endpoint_positives=positive,actual_physical_route_cut_negatives=negative,source_population=pop,prior_SOURCE_clusters=retained,exact_oldCu_source_lands_poses_zones_retained=True,native_errors=0,all_prior_unsuppressed_native_warnings=d['violations'],no_new_native_defects=True,no_ignored_checks=True,actual_full_native_reference_proofs=returnproof,eligible_piece_audit=check.eligible_piece_audit,complete_failed_reference_piece_ledger=check.full_native_report['unanchored_components'],unchanged_source_series_and_clocktap_topology=True,signal_geometry=dict(width_mm=.35,clearance_mm=.20,own_reference_margin_mm=.40,maximal_actual_route_length_mm=8),loaded_driver_and_clocktap_timing_unqualified=True,impedance_factory_stackup_unqualified=True,whole_board_reference_qualification=False,manufacturing_ready=False)
e.write(OUT/'review.json',r);print(json.dumps(dict(passed=True,actual_complete_SOURCE_pairs=len(positive),newCu=len(returnproof),physical_cut_negatives=len(negative),native_errors=0,prior_warnings=len(d['violations']))),flush=True)
