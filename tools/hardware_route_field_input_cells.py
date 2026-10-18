"""Route only exact reviewed same-side ISO1212 local SENSE/IN cells.

No new vias, external input lines, substrate copper, power, sources, footprint
poses or existing conductors may change. Actual native source-owned FGND
qualification precedes routing; native DRC, source clusters, exact own filled
corridors and uncapped independent connectivity decide acceptance.
"""
import argparse,collections,json,math,shutil,subprocess,sys
from pathlib import Path
import pcbnew
from hardware_populate_motherboard_pcb import sha,write,pad_template
from hardware_route_logic_return import identity,mm,xy
from hardware_route_local_signals import paths
from hardware_route_owned_bypass_loops_wip_r03 import Geometry,reviewed_wip_warnings,new_route_defects
from hardware_check_return_corridors_r04 import dependencies
from hardware_check_return_corridors import covered
from hardware_route_selected_additive import corridor_polygon
from hardware_anchor_owned_cmos_returns import source_clusters
from hardware_route_critical_digital_wip_r03 import clusters_preserved
from hardware_review_field_input_cells import review,ROOT
from hardware_scope_anchored_reference_pieces import verify_receipt,SourceAnchoredPiecesCheck
from hardware_route_selected_additive_r02 import native_source_check
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')

def check_literal_field_scope(planes,board,rows):
    proof=verify_receipt(planes,board,rows)
    if any(r['reference_layers']!={'F.Cu':'In1.Cu'} or r['allow_vias'] is not False for r in rows.values()):
        raise ValueError('Only declared F-side, adjacent In1, zero-new-via cells are accepted')
    return proof

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('board','source','adoption','review','planes','baseline-disposition','out'):
        ap.add_argument('--'+name,dest=name.replace('-','_'),type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists():raise ValueError('Fresh immutable output required')
    source_review=json.loads(a.review.read_text());fresh_review=review(a.source,a.adoption)
    if source_review!=fresh_review:raise ValueError('Exact48 issued field cell source review changed')
    rows=source_review['nets'];plane_scope=check_literal_field_scope(a.planes,a.board,rows);dependencies()
    frozen={str(p.resolve()):sha(p) for p in (a.board,a.review,a.planes,a.baseline_disposition,Path(__file__),ROOT/'tools/hardware_scope_anchored_reference_pieces.py',ROOT/'tools/hardware_validate_motherboard_return_planes_r02.py',ROOT/'tools/hardware_scope_critical_reference_qualification.py')}
    baseline=json.loads((a.board.parent/'drc.json').read_text())
    known=reviewed_wip_warnings(baseline,json.loads(a.baseline_disposition.read_text()),sha(a.board))
    board=pcbnew.LoadBoard(str(a.board.resolve()));board.BuildConnectivity()
    native_source_check(board,json.loads((a.source/'design.json').read_text()),a.source/'netlist.xml')
    previous_clusters=source_clusters(board);old={t.m_Uuid.AsString():identity(t) for t in board.GetTracks()}
    old_fps={f.GetReference():f for f in board.GetFootprints()}
    old_pads={p.m_Uuid.AsString():(p.GetNumber(),p.GetNetname(),tuple(p.GetPosition()),pad_template(p)) for p in board.GetPads()}
    source_mapping=json.loads(Path(plane_scope['source_map']['path']).read_text())
    initial_reference=SourceAnchoredPiecesCheck(board,rows,source_mapping)
    # Native connected-peer iteration can choose another equally real SOURCE
    # witness. Recompute every anchor and require exact piece geometry/status,
    # rather than comparing an incidental peer ordering or first-witness ID.
    piece_identity=lambda r:(r['net'],r['reference_layer'],r['filled_piece'],r['filled_area_mm2'],r['passed'])
    frozen_full=json.loads(Path(plane_scope['full_plane_review']['path']).read_text())
    if sorted(map(piece_identity,initial_reference.full_native_report['filled_components']))!=sorted(map(piece_identity,frozen_full['filled_components'])):
        raise ValueError('Frozen reference geometry/anchoring differs from actual SOURCE-connected native pieces')
    geometry=Geometry(board);groups=[];blocked=[];owners=[]
    pin=lambda ref,num:next(p for p in old_fps[ref].Pads() if p.GetNumber()==num)
    for name,row in sorted(rows.items()):
        pads=[pin(*pair) for pair in row['source_pins']]
        if any(not p.IsOnLayer(pcbnew.F_Cu) or p.GetNetname()!=name for p in pads):
            raise ValueError('Exact source-owned F-only field cell changed: '+name)
        while True:
            board.BuildConnectivity();clusters={}
            for p in pads:
                ids={q.m_Uuid.AsString() for q in board.GetConnectivity().GetConnectedItems(p) if q.Type()==pcbnew.PCB_PAD_T};ids.add(p.m_Uuid.AsString())
                clusters.setdefault(tuple(sorted(ids)),[]).append(p)
            if len(clusters)<2:break
            values=list(clusters.values());pairs=[]
            for i,left in enumerate(values):
                for right in values[i+1:]:
                    for p in left:
                        for q in right:
                            if math.dist(mm(p.GetPosition()),mm(q.GetPosition()))<=row['maximum_source_pad_route_span_mm']:
                                pairs.append((math.dist(mm(p.GetPosition()),mm(q.GetPosition())),p,q))
            chosen=None
            for _,p,q in sorted(pairs,key=lambda v:v[0]):
                for points in paths(mm(p.GetPosition()),mm(q.GetPosition())):
                    length=sum(math.dist(s,e) for s,e in zip(points,points[1:]))
                    fill=initial_reference.reference(row['return_net'],pcbnew.In1_Cu)
                    corridor_ok=all(covered(corridor_polygon(tuple(xy(s)),tuple(xy(e)),pcbnew.FromMM(row['width_mm']/2+row['reference_corridor_margin_mm'])),fill) for s,e in zip(points,points[1:]))
                    if length<=row['maximum_added_path_length_mm'] and corridor_ok and geometry.clear(points,name,pcbnew.F_Cu,width=row['width_mm']):
                        chosen=(p,q,points,length);break
                if chosen:break
            if chosen is None:blocked.append(dict(net=name,reason='No legal same-side bounded cell path; required route remains',source_clusters=len(clusters)));break
            p,q,points,length=chosen;items=[]
            for s,e in zip(points,points[1:]):
                if math.dist(s,e)<1e-7:continue
                t=pcbnew.PCB_TRACK(board);t.SetNet(p.GetNet());t.SetLayer(pcbnew.F_Cu);t.SetWidth(pcbnew.FromMM(row['width_mm']));t.SetStart(xy(s));t.SetEnd(xy(e));board.Add(t);items.append(t);geometry.add(t)
            groups.append(dict(net=name,from_source=[p.GetParentFootprint().GetReference(),p.GetNumber()],to_source=[q.GetParentFootprint().GetReference(),q.GetNumber()],new_UUIDs=[t.m_Uuid.AsString() for t in items],points_mm=points,length_mm=length,retained=True));owners.extend(items)
    a.out.mkdir(parents=True);dest=a.out/'field-local-cell-candidate.kicad_pcb'
    for suffix in ('.kicad_pro','.kicad_dru'):shutil.copyfile(a.board.with_suffix(suffix),dest.with_suffix(suffix))
    for resource in a.board.parent.iterdir():
        if resource.is_dir() and (resource.suffix=='.pretty' or resource.name=='3dmodels'):shutil.copytree(resource,a.out/resource.name)
        elif resource.name=='fp-lib-table':shutil.copyfile(resource,a.out/resource.name)
    mapping={u:i for i,g in enumerate(groups) for u in g['new_UUIDs']};rejects=[]
    for attempt in range(10):
        pcbnew.SaveBoard(str(dest),board);native=a.out/('native-'+str(attempt)+'.json')
        run=subprocess.run([str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(native),str(dest)],capture_output=True,text=True)
        (a.out/('native-'+str(attempt)+'.txt')).write_text(run.stdout+run.stderr)
        if run.returncode:raise ValueError('Actual native DRC did not execute')
        report=json.loads(native.read_text());defects=new_route_defects(report,known);bad=set()
        for error in defects:
            matches={mapping[x['uuid']] for x in error['items'] if x['uuid'] in mapping}
            if not matches:raise ValueError('New native defect outside new field-cell transaction')
            bad.update(matches)
        actual=pcbnew.LoadBoard(str(dest));checker=SourceAnchoredPiecesCheck(actual,rows,source_mapping)
        exact={t.m_Uuid.AsString():t for t in actual.GetTracks()};corridors=[]
        for i,g in enumerate(groups):
            if not g['retained'] or i in bad:continue
            try:corridors.extend(checker.segment(exact[u],rows[g['net']]) for u in g['new_UUIDs'])
            except ValueError as error:bad.add(i);rejects.append(dict(group=i,net=g['net'],reason=str(error)))
        if not bad:break
        for i in bad:
            for t in list(board.GetTracks()):
                if t.m_Uuid.AsString() in groups[i]['new_UUIDs']:board.Remove(t)
            groups[i]['retained']=False
    else:raise ValueError('Bounded native/reference repair exceeded')
    current={t.m_Uuid.AsString():identity(t) for t in actual.GetTracks()}
    added={u for g in groups if g['retained'] for u in g['new_UUIDs']}
    if set(current)!=set(old)|added or any(current.get(u)!=v for u,v in old.items()):raise ValueError('Retained/source26 native copper changed')
    if old_pads!={p.m_Uuid.AsString():(p.GetNumber(),p.GetNetname(),tuple(p.GetPosition()),pad_template(p)) for p in actual.GetPads()}:raise ValueError('Source lands/pin nets/poses changed')
    cluster_proof=clusters_preserved(previous_clusters,actual)
    inventory=a.out/'independent-connectivity'
    run=subprocess.run([sys.executable,str(ROOT/'tools/motion_card_routing_inventory.py'),'--board',str(dest),'--netlist',str(a.source/'netlist.xml'),'--source-design',str(a.source/'design.json'),'--out',str(inventory)],capture_output=True,text=True)
    (a.out/'connectivity-command.txt').write_text(run.stdout+run.stderr)
    if run.returncode:raise ValueError('Independent uncapped/SOURCE/orphan inventory failed')
    if any(sha(Path(p))!=h for p,h in frozen.items()):raise ValueError('Frozen inputs changed')
    native_source_check(actual,json.loads((a.source/'design.json').read_text()),a.source/'netlist.xml')
    result=dict(passed=True,input_sha256=frozen,board_sha256=sha(dest),groups=groups,blocked_required_routes=blocked,actual_rejected_groups=rejects,retained_groups=sum(g['retained'] for g in groups),new_signal_copper_UUIDs=sorted(added),new_vias=0,
      actual_own_filled_reference_corridors=corridors,literal_source_owned_FIELD_B_piece_eligibility=plane_scope,
      final_complete_native_reference_report=checker.full_native_report,actual_eligible_piece_audit=checker.eligible_piece_audit,
      whole_return_net_qualification=False,prior_source_cluster_proof=cluster_proof,
      native_errors=0,known_unresolved_native_warnings=report['violations'],ignored_checks=[],independent_connectivity_review_sha256=sha(inventory/'review.json'),
      actual_filter_delay_surge_or_EMC_measured=False,source_or_existing_copper_modified=False,manufacturing_ready=False)
    write(a.out/'receipt.json',result);print(dict(passed=True,new_groups=result['retained_groups'],new_Cu=len(added),missing_joins=json.loads((inventory/'review.json').read_text())['uncapped_unconnected_ratsnest_edges']))
if __name__=='__main__':main()
