"""Prepare a separate no-transition local trial; retain old101 loop guards."""
from pathlib import Path
import hashlib,json
p=Path(__file__).parent
parent=p/'route-strict-same-side-bypass-r05.py'
target=p/'route-adjacent-same-side-bypass-r06.py';assert not target.exists()
s=parent.read_text()
s=s.replace('import pcbnew\n','import pcbnew\nfrom check_same_side_bypass_r01 import check_group, surface_path\nfrom hardware_scope_anchored_reference_pieces import SourceAnchoredPiecesCheck\n',1)
s=s.replace("ap.add_argument('--only-refs',", "ap.add_argument('--source-map',type=Path,required=True)\n ap.add_argument('--only-refs',",1)
s=s.replace('manifest=json.loads(a.owners.read_text())','manifest=json.loads(a.owners.read_text())\n source_mapping=json.loads(a.source_map.read_text())\n if source_mapping["input_sha256"].get(str(a.board.resolve()))!=sha(a.board):raise ValueError("Exact current parent source map required")',1)
old=" def own_fill(pt,return_net):\n  return all(indexed.candidate_covered(circle(tuple(xy(pt)),pcbnew.FromMM(.24)),return_net,b.GetLayerID(layer))for layer in('In1.Cu','In4.Cu'))"
new=" def own_fill(pt,return_net,outer_layer):\n  adjacent=pcbnew.In1_Cu if outer_layer==pcbnew.F_Cu else pcbnew.In4_Cu\n  return indexed.candidate_covered(circle(tuple(xy(pt)),pcbnew.FromMM(.24)),return_net,adjacent)"
assert old in s;s=s.replace(old,new,1)
s=s.replace('own_fill(mm(v.GetPosition()),ret.GetNetname())','own_fill(mm(v.GetPosition()),ret.GetNetname(),ret.GetParentFootprint().GetLayer())')
s=s.replace('own_fill(pt,ret.GetNetname())','own_fill(pt,ret.GetNetname(),layer)')
start=s.index('    else:\n     chosen=None')
end=s.index("   if not connected(b,cp,owner)",start)
s=s[:start]+"    else:raise ValueError('Supply layer transition forbidden in this separate trial')\n"+s[end:]
needle="   if not connected(b,cp,owner)or not any(connected(b,cr,p)for p in returns):raise ValueError('Actual owning-pin loop did not close')"
extra="""
   complete=surface_path(b,cp.GetNetname(),cp.GetParentFootprint().GetLayer(),tuple(cp.GetPosition()),tuple(owner.GetPosition()),8.)
   if not {t.m_Uuid.AsString()for t in items if t.GetNetname()==cp.GetNetname()}<=set(complete['actual_surface_trace_UUIDs']):raise ValueError('New supply copper is outside the declared complete local branch')
"""
assert s.count(needle)==1;s=s.replace(needle,needle+extra,1)
s=s.replace("new_UUIDs=ids,actual_owning_signal_return_pairs_connected", "new_UUIDs=ids,complete_supply_branch_UUIDs=complete['actual_surface_trace_UUIDs'],actual_owning_signal_return_pairs_connected",1)
start=s.index("   exact={t.m_Uuid.AsString():t for t in reviewed.GetTracks()};bad=set();pass_reviews=[]")
end=s.index('   if not bad:return_reviews=pass_reviews;break',start)
replacement="""   exact={t.m_Uuid.AsString():t for t in reviewed.GetTracks()};bad=set();pass_reviews=[]
   declarations={}
   for group in groups:
    if not group['retained']:continue
    row=next(v for v in rows if v['ref']==group['ref'])
    cp=pin(row['ref'],row['cap_power']);cr=pin(row['ref'],row['cap_return']);outer=cp.GetParentFootprint().GetLayer()
    declarations[cp.GetNetname()]=dict(return_net=cr.GetNetname(),reference_layers={b.GetLayerName(outer):'In1.Cu'if outer==pcbnew.F_Cu else'In4.Cu'},allow_vias=False,reference_corridor_margin_mm=.10)
   shared=SourceAnchoredPiecesCheck(reviewed,declarations,source_mapping)
   for index,group in enumerate(groups):
    if not group['retained']:continue
    row=next(v for v in rows if v['ref']==group['ref'])
    try:pass_reviews.append(dict(ref=group['ref'],**check_group(reviewed,group,row,source_mapping,checker=shared)))
    except ValueError as error:bad.add(index);return_rejections.append(dict(ref=group['ref'],reason=str(error)))
"""
s=s[:start]+replacement+s[end:]
s=s.replace('original_both_reference_ground_anchoring_retained=True','separate_same_side_adjacent_reference_proof=True,prior_101_loop_guards_require_independent_unchanged_recheck=True')
s=s.replace("str(a.owners):sha(a.owners),", "str(a.owners):sha(a.owners),str(a.source_map):sha(a.source_map),str(Path(__file__).with_name('check_same_side_bypass_r01.py')):sha(Path(__file__).with_name('check_same_side_bypass_r01.py')),",1)
s=s.replace('This is not power distribution.', 'This separate trial admits only a complete single-surface supply branch with its actual adjacent return, exact <=8 mm supply route and <=2 mm real surface receiving-ground routes. The previously accepted101 loops must independently retain their original both-plane guards. This is not power distribution.',1)
target.write_text(s)
record=dict(prepared=True,not_run=True,parent_router_sha256=hashlib.sha256(parent.read_bytes()).hexdigest(),trial_router_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),checker_sha256=hashlib.sha256((p/'check_same_side_bypass_r01.py').read_bytes()).hexdigest(),scope='Existing reviewed77 small local capacitors only, no poses/source/oldCu/plane changes, no supply vias. Source-ground path and actual adjacent reference proof separate from old101 guards.',actual_positive_and_negative_proofs=['same-side-real-circuit-proof-r01.json','same-side-native-controls-r02.json'])
(p/'adjacent-same-side-preparation-r01.json').write_text(json.dumps(record,indent=2)+'\n')
print('Prepared separate reviewed-scope trial, not executed')
