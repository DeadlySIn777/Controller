from pathlib import Path
import sys,json,copy,collections
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_ordinary_wip_r05 as o
import hardware_route_critical_digital_wip_r03 as c
import hardware_route_owned_bypass_loops_wip_r03 as w
e=o.engine
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-four-reference-closures-r71/motherboard-bounded-merged-candidate.kicad_pcb')
OUT=Path('reports/motherboard-ordinary-routing-20261001/actual-source26-root71-local-clipped-r02')
DEST=OUT/'motherboard-ordinary-local-candidate.kicad_pcb'
PLAN=e.read(OUT/'proposed-local-groups.json');MAN=e.read(OUT/'manifest.json')
o.INPUT_BOARD=BASE;o.frozen_review_check(MAN,Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'));o.MAPPING=e.read(e.read(OUT/'piece-eligibility.json')['source_map']['path'])
old=e.parse(BASE.read_text());new=e.parse(DEST.read_text())
def cu(tree):return{e.value(e.child(t,'uuid')[1]):e.dump(t)for k in('segment','via','arc')for t in e.children(tree,k)}
before,after=cu(old),cu(new)
if e.immutable_objects(old)!=e.immutable_objects(new)or any(after.get(k)!=v for k,v in before.items()):raise ValueError('Actual old SOURCE/lands/poses/planes/copper changed')
if set(after)-set(before)!=set(PLAN['added_copper_UUIDs']):raise ValueError('Actual route ledger differs')
d=e.read(OUT/'native.json');known=w.reviewed_wip_warnings(e.read(BASE.parent/'drc.json'),e.read(BASE.parent/'baseline-disposition.json'),e.sha(BASE))
if w.new_route_defects(d,known)or d.get('ignored_checks'):raise ValueError('Actual new native routing defect')
b=pcbnew.LoadBoard(str(DEST));b.BuildConnectivity();pop,nodes=e.native_source_check(b,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
retained=c.clusters_preserved(c.source_clusters(pcbnew.LoadBoard(str(BASE))),b)
returns=o.actual_return_check(b,set(PLAN['added_copper_UUIDs']),MAN['nets'])
positive=[];negative=[]
def ps(board):return{p.m_Uuid.AsString():p for f in board.GetFootprints()for p in f.Pads()}
def joined(board,ids):
 board.BuildConnectivity();pads=ps(board);p,q=(pads[i]for i in ids);return q.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in board.GetConnectivity().GetConnectedItems(p)}
for index,g in enumerate(PLAN['groups']):
 if not joined(b,g['source_pad_UUIDs']):raise ValueError('Actual SOURCE route endpoints are not connected')
 positive.append(dict(net=g['net'],source_pair=g['source_pair'],actual_joined=True,new_copper_UUIDs=g['new_copper_UUIDs']))
 # Remove this route and every later addition. This independently recreates
 # the prior real source-component state rather than an assumed graph edge.
 # Reconstruct each native cut from the exact serialized real board. This
 # avoids a SWIG removal/proxy-lifetime failure observed in the first trial;
 # the removed physical UUID set remains explicit and reproducible.
 remove={u for row in PLAN['groups'][index:]for u in row['new_copper_UUIDs']}
 cut_tree=[v for v in new if not(isinstance(v,list)and v and v[0]in('segment','via','arc')and e.value(e.child(v,'uuid')[1])in remove)]
 cut_path=OUT/('physical-source-cut-'+str(index+1)+'.kicad_pcb')
 cut_path.write_text(__import__('hardware_route_critical_digital_wip_r05').dump_native_board(cut_tree)+'\n')
 cut=pcbnew.LoadBoard(str(cut_path))
 if joined(cut,g['source_pad_UUIDs']):raise ValueError('Actual progressive route-cut control ineffective')
 negative.append(dict(net=g['net'],source_pair=g['source_pair'],actual_route_cut_disconnected=True,removed_exact_UUIDs=sorted(remove),actual_native_cut_board=str(cut_path),actual_native_cut_sha256=e.sha(cut_path)))
r=dict(passed=True,base_sha256=e.sha(BASE),board_sha256=e.sha(DEST),manifest_sha256=e.sha(OUT/'manifest.json'),source_design_sha256=e.sha('hardware/motherboard/design.json'),source_netlist_sha256=e.sha('hardware/motherboard/netlist.xml'),tool_sha256=e.sha(__file__),actual_complete_source_pair_groups=len(positive),added_actual_copper_items=len(PLAN['added_copper_UUIDs']),actual_SOURCE_endpoint_positive_checks=positive,actual_progressive_route_cut_negative_checks=negative,actual_native_errors=0,all_prior_unsuppressed_native_warnings=d['violations'],no_new_native_defects=True,no_ignored_checks=True,exact_old_copper_and_immutable_objects_retained=True,source_population=pop,prior_SOURCE_clusters=retained,actual_full_native_return_guard=returns,exact_local_fill_intersection_used_during_search_only=True,full_failed_reference_ledger=returns['full_failed_reference_piece_ledger'],whole_board_reference_qualification=False,whole_return_net_qualification=False,manufacturing_ready=False)
e.write(OUT/'review.json',r);print(json.dumps(dict(passed=True,actual_SOURCE_pair_groups=len(positive),newCu=len(PLAN['added_copper_UUIDs']),physical_cut_negative_checks=len(negative),native_errors=0,original_warnings=len(d['violations']))),flush=True)
