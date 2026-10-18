"""Correct real DI logic/field placement; archive every affected copper piece.

The twelve existing isolators and all original 327 footprints/copper remain
fixed. Only their 108 existing local passive positions change. Dedicated DI
routes relying on the invalid side placement are removed through an exact
UUID ledger; they must be rerouted and independently validated before this
candidate can be adopted as finished routing. No source pin/net changes.
"""
from __future__ import annotations
import argparse
import collections
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import pcbnew
from hardware_map_motherboard_domains import sha,write,native
from hardware_route_logic_return import identity,xy,mm,segment_hits_box
from hardware_di_leaf_routes import leaf_branches
from hardware_reconcile_motherboard_peripheral_pcb import piece
from hardware_populate_motherboard_pcb import footprint_name
from hardware_build_assembly import parse,dump,children,child,value
from motherboard_mechanical_audit import graphic_box,body_box,overlap,grown,rect,transformed_box
from hardware_route_local_signals import GeometryIndex

ROOT=Path(__file__).resolve().parents[1]
CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
BASE_SHA='c5f109b95261d5e57a3e3eae76eb7fa368e08afee8d0a91dacc906c23640e306'
DEDICATED=re.compile(r'^/motherboard_di/DI(?:[0-9]|1[0-9]|2[0-3])_(?:IN|SENSE|FIELD|LOGIC)$')
DANGLING_DI_RETURN_VIAS={
    '033fbd24-6f49-475d-977a-23831b7b239a','145cfb05-2d4c-4774-8836-b99cfc4c0d9e',
    '40413f90-a445-428c-b662-b66ddddb1619','645d7ab9-c5bc-46a2-ac8f-03928bc3012f',
    '67e1e4c0-b6b0-4c09-9cbc-a14a48b1e275','80b22426-528a-44e0-b530-51f3d226b4bf',
    '89c8ad0d-577a-4d26-95f9-3a5a0e53a00e','d4efb95e-b179-4e24-aef3-9a09fa4ffd08',
    'e91a5581-2fe8-496e-9039-02eb8676dba7'}
DANGLING_DI_RETURN_TRACKS={
    '18bbb954-c3d9-4725-a78b-7e8f0c6e6ad4','1c915240-4115-4d90-bd2b-22b245a59e5f',
    '2530da20-cd42-4d1c-8610-efb6489d7687','311e25fc-6e05-4bc8-8d15-de9be52c1a6c',
    '5395d999-b5b5-4bca-9b34-e4863ae5ef33','ad6eb46e-56bc-4884-8014-b0511b51d439',
    'c1eed6a0-c3f3-47be-8e58-b002d0aad563','ce41c68f-91dd-4591-83a9-667246cd5f55',
    'd57a546d-9358-411d-a71a-afce8e79c0e3'}


def bounds(pad):
    b=pad.GetBoundingBox();return mm(b.GetOrigin())+mm(b.GetEnd())


def gap(a,b):
    return math.hypot(max(a[0]-b[2],b[0]-a[2],0),max(a[1]-b[3],b[1]-a[3],0))


def retained_return_clusters(board,moved):
    """Literal unrelated physical-pad cluster identity on the changed return."""
    board.BuildConnectivity();connection=board.GetConnectivity();result={}
    pads=[p for p in board.GetPads() if p.GetNetname()=='/motherboard_do/FIELD_B_0V' and p.GetParentFootprint().GetReference()not in moved]
    eligible={p.m_Uuid.AsString() for p in pads}
    for pad in pads:
        peers={i.m_Uuid.AsString() for i in connection.GetConnectedItems(pad) if i.Type()==pcbnew.PCB_PAD_T and i.m_Uuid.AsString()in eligible}
        result[pad.m_Uuid.AsString()]=sorted(peers|{pad.m_Uuid.AsString()})
    return result


def leaf_after_return_via_removal(board,via_ids,original_ids):
    tracks=[t for t in board.GetTracks() if t.GetNetname()=='/motherboard_do/FIELD_B_0V']
    vias={t.m_Uuid.AsString():t for t in tracks if isinstance(t,pcbnew.PCB_VIA)}
    edges={t.m_Uuid.AsString():((t.GetStart().x,t.GetStart().y,t.GetLayer()),(t.GetEnd().x,t.GetEnd().y,t.GetLayer())) for t in tracks if not isinstance(t,pcbnew.PCB_VIA)}
    vertices={v for e in edges.values() for v in e};anchors=set();protected=set(original_ids)
    pads=[p for p in board.GetPads() if p.GetNetname()=='/motherboard_do/FIELD_B_0V']
    for v in vertices:
        point=pcbnew.VECTOR2I(v[0],v[1])
        if any(p.IsOnLayer(v[2]) and p.HitTest(point) for p in pads):anchors.add(v)
        if any(uid not in via_ids and v[:2]==tuple(t.GetPosition()) for uid,t in vias.items()):anchors.add(v)
    for t in tracks:
        if isinstance(t,pcbnew.PCB_VIA):continue
        if any(p.IsOnLayer(t.GetLayer()) and not p.HitTest(t.GetStart()) and not p.HitTest(t.GetEnd()) and
               segment_hits_box(mm(t.GetStart()),mm(t.GetEnd()),bounds(p),pcbnew.ToMM(t.GetWidth())/2) for p in pads):protected.add(t.m_Uuid.AsString())
    starts={v for v in vertices if v[:2]in {tuple(vias[uid].GetPosition()) for uid in via_ids}}
    return leaf_branches(edges,starts,anchors,protected)


def targets():
    moves={}
    for index in range(12):
        for slot in range(2):
            channel=2*index+slot;sign=-1 if slot==0 else 1
            moves[f'R{8001+channel}']=(f'U{8001+index}',12.5,sign*4.2,180.,'external RTHR pad separated >=4 mm from device/CIN/RSENSE')
            moves[f'R{8101+channel}']=(f'U{8001+index}',5.35,sign*1.5,0.,'RSENSE remains on the physical field side')
            moves[f'C{8001+channel}']=(f'U{8001+index}',5.8,sign*3.8,0.,'CIN remains on the physical field side')
            moves[f'R{8201+channel}']=(f'U{8001+index}',-5.7,.2 if slot==0 else 2.5,180.,'output bias remains on the physical logic side')
        moves[f'C{8101+index}']=(f'U{8001+index}',-5.3,-1.5875,180.,'logic bypass <=2 mm from the actual VCC pad')
        moves[f'U{8001+index}']=(f'U{8001+index}',0,0,0.,'complete real DI pair relocated to keep its logic and field circuits separated from unrelated occupied cells')
    return moves


def place_groups(board,fps,move,out):
    """Choose full clear cells against actual and reserved native geometry."""
    proposal_path=ROOT/'reports/motherboard-mechanical-20260930/r24f-complete-mate-proposal-r05/review.json'
    power_path=ROOT/'reports/motherboard-power-entry-20260930/layout-r09/full-board-fit-r01/power-groups-geometry-candidate.kicad_pcb'
    power_receipt=power_path.with_name('placement-receipt.json')
    bypass_path=ROOT/'reports/motherboard-bypass-owners-20260930/local-placement-r01/motherboard-local-capacitors-candidate.kicad_pcb'
    proposal=json.loads(proposal_path.read_text());assert proposal['pass']
    power=pcbnew.LoadBoard(str(power_path));power_fps={f.GetReference():f for f in power.GetFootprints()}
    power_refs={r for g in json.loads(power_receipt.read_text())['groups'] for r in g['refs']}
    bypass=pcbnew.LoadBoard(str(bypass_path));bypass_fps={f.GetReference():f for f in bypass.GetFootprints()}
    obstacles=GeometryIndex()
    for ref,fp in fps.items():
        if ref in move:continue
        future=power_fps[ref] if ref in power_refs else bypass_fps[ref]
        box=graphic_box(future,pcbnew.F_CrtYd)or body_box(future)[0]
        obstacles.add((ref,box),box)
    for ref,row in proposal['actual40_ports_mutually_checked'].items():
        for key,box in row['envelopes_mm'].items():obstacles.add((ref+':'+key,box),box)
    for ref,local in [('J15001',[-3,-30,37,25]),('J16001',[-1.27,-1.565,24.13,61.3])]:
        box=transformed_box(fps[ref],local);obstacles.add((ref+':MODULE',box),box)
    for ref in [f'H{22001+i}' for i in range(6)]:
        x,y=mm(fps[ref].GetPosition());box=[x-4.25,y-4.25,x+4.25,y+4.25];obstacles.add((ref+':WASHER',box),box)
    copper=GeometryIndex()
    for t in board.GetTracks():
        if DEDICATED.fullmatch(t.GetNetname()):continue
        box=rect(t.GetBoundingBox());copper.add(t,box)
    selected=[];absolute={};old_centers={f'U{8001+i}':mm(fps[f'U{8001+i}'].GetPosition()) for i in range(12)}
    for index in range(12):
        owner=f'U{8001+index}';refs=[r for r,v in move.items() if v[0]==owner]
        for ref in refs:
            _,dx,dy,angle,_=move[ref];fps[ref].SetPosition(xy((dx,dy)));fps[ref].SetOrientationDegrees(angle)
        boxes=[graphic_box(fps[r],pcbnew.F_CrtYd)or body_box(fps[r])[0] for r in refs]
        local=[min(b[0] for b in boxes)-.3,min(b[1] for b in boxes)-.3,max(b[2] for b in boxes)+.3,max(b[3] for b in boxes)+.3]
        candidates=sorted((math.dist((x,y),old_centers[owner]),x,y) for x in range(10,443,2) for y in range(106,321,2))
        picked=None
        for _,x,y in candidates:
            box=[local[0]+x,local[1]+y,local[2]+x,local[3]+y]
            if not(.8<box[0] and .8<box[1] and box[2]<459.2 and box[3]<339.2):continue
            if any(overlap(grown(box,.25),other) for _,other in obstacles.candidates(box[:2],box[2:],.25)):continue
            # Empty projected copper cells give uninterrupted own references
            # rather than placing a field receiver over unrelated return paths.
            if any(overlap(grown(box,.25),rect(t.GetBoundingBox())) for t in copper.candidates(box[:2],box[2:],.25)):continue
            picked=(x,y,box);break
        if picked is None:raise ValueError('No complete electrically separated DI cell found for '+owner)
        x,y,box=picked;obstacles.add((owner+':DI_CELL',box),box)
        for ref in refs:
            _,dx,dy,angle,_=move[ref];absolute[ref]=(x+dx,y+dy,angle)
            fps[ref].SetPosition(xy((x+dx,y+dy)))
        selected.append(dict(owner=owner,center_mm=[x,y],reserved_cell_polygon_mm=[[box[0],box[1]],[box[2],box[1]],[box[2],box[3]],[box[0],box[3]]],references=refs))
    return absolute,selected,{str(f.relative_to(ROOT)):sha(f) for f in [proposal_path,power_path,power_receipt,bypass_path]}


def spacing(board):
    fps={f.GetReference():f for f in board.GetFootprints()};rows=[]
    for index in range(12):
        iso=fps[f'U{8001+index}'];center=mm(iso.GetPosition())
        device=list(iso.Pads())
        for slot in range(2):
            channel=2*index+slot;rt=fps[f'R{8001+channel}'];rs=fps[f'R{8101+channel}'];cin=fps[f'C{8001+channel}'];rb=fps[f'R{8201+channel}']
            external=next(p for p in rt.Pads() if p.GetNumber()=='1')
            protected=device+list(rs.Pads())+list(cin.Pads())
            minimum=min((gap(bounds(external),bounds(p)),p.GetParentFootprint().GetReference(),p.GetNumber()) for p in protected)
            if minimum[0]<4:raise ValueError('RTHR external pad EMC spacing below4 mm: '+rt.GetReference())
            if any(mm(p.GetPosition())[0]<=center[0] for p in list(rs.Pads())+list(cin.Pads())):
                raise ValueError('Protected field component placed across logic side')
            if any(mm(p.GetPosition())[0]>=center[0] for p in rb.Pads()):raise ValueError('Logic bias placed across field side')
            rows.append(dict(channel=channel,isolator=iso.GetReference(),RTHR=rt.GetReference(),
                external_pad=1,minimum_RTHR_to_device_CIN_RSENSE_pad_mm=minimum[0],nearest_reference=minimum[1],nearest_pin=minimum[2],
                field_component_side_pass=True,logic_bias_side_pass=True))
        cap=fps[f'C{8101+index}'];power=next(p for p in cap.Pads() if p.GetNumber()=='1');vcc=next(p for p in iso.Pads() if p.GetNumber()=='2')
        distance=math.dist(mm(power.GetPosition()),mm(vcc.GetPosition()))
        if distance>2:raise ValueError('Actual logic bypass >2mm from VCC')
        rows.append(dict(bypass=cap.GetReference(),owner=iso.GetReference(),owner_supply_pin=2,
            actual_bypass_power_pad_distance_mm=distance,ground_return_route_qualified=False))
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--board',type=Path,required=True)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();base=a.board.resolve();source=a.source.resolve();out=a.out.resolve()
    if sha(base)!=BASE_SHA or out.exists() or not out.is_relative_to(ROOT/'reports'):raise ValueError('Exact frozen base and new report directory required')
    board=pcbnew.LoadBoard(str(base));fps={f.GetReference():f for f in board.GetFootprints()};move=targets()
    before_copper={t.m_Uuid.AsString():identity(t) for t in board.GetTracks()}
    before_pads={p.m_Uuid.AsString():piece(p) for f in board.GetFootprints() for p in f.Pads()}
    before_fps={f.GetReference():(f.m_Uuid.AsString(),tuple(f.GetPosition()),f.GetOrientationDegrees(),footprint_name(f)) for f in board.GetFootprints()}
    retained_clusters_before=retained_return_clusters(board,move)
    nodes,nc,_=native(source/'netlist.xml');removed=[]
    # Prove moved-pad leaf branches independently from whole-net connectivity:
    # the B return also joins unrelated safety circuits, which must remain.
    shared_removal=set();leaf_receipts=[]
    moved_pads=[pad for ref in move for pad in fps[ref].Pads() if not DEDICATED.fullmatch(pad.GetNetname())]
    shared_nets={p.GetNetname() for p in moved_pads}
    for net in sorted(shared_nets):
        tracks=[t for t in board.GetTracks() if t.GetNetname()==net]
        edges={t.m_Uuid.AsString():((t.GetStart().x,t.GetStart().y,t.GetLayer()),(t.GetEnd().x,t.GetEnd().y,t.GetLayer()))
            for t in tracks if not isinstance(t,pcbnew.PCB_VIA)}
        vertices={v for edge in edges.values() for v in edge};starts=set();anchors=set();protected=set()
        own_moved=[p for p in moved_pads if p.GetNetname()==net]
        unchanged=[p for f in board.GetFootprints() if f.GetReference() not in move for p in f.Pads() if p.GetNetname()==net]
        for vertex in vertices:
            pos=pcbnew.VECTOR2I(vertex[0],vertex[1]);layer=vertex[2]
            if any(p.IsOnLayer(layer) and p.HitTest(pos) for p in own_moved):starts.add(vertex)
            if any(p.IsOnLayer(layer) and p.HitTest(pos) for p in unchanged):anchors.add(vertex)
        for t in tracks:
            if isinstance(t,pcbnew.PCB_VIA):
                for vertex in vertices:
                    if vertex[:2]==(t.GetPosition().x,t.GetPosition().y):anchors.add(vertex)
                continue
            # Conservative AABB intersection protects an unchanged pad even
            # when it touches the middle of a native segment.
            a,b=mm(t.GetStart()),mm(t.GetEnd());half=pcbnew.ToMM(t.GetWidth())/2
            if any(p.IsOnLayer(t.GetLayer()) and segment_hits_box(a,b,bounds(p),half) for p in unchanged):
                protected.add(t.m_Uuid.AsString())
        removed_here,evidence=leaf_branches(edges,starts,anchors,protected)
        shared_removal.update(removed_here)
        leaf_receipts.extend(dict(net=net,**row) for row in evidence)
    original=pcbnew.LoadBoard(str(ROOT/'reports/board-completion-20260930/local-signal-routing-v2/local-signal-routes-candidate.kicad_pcb'))
    original_ids={t.m_Uuid.AsString() for t in original.GetTracks()}
    if original_ids&shared_removal:raise ValueError('Leaf proof proposed deleting original retained core copper')
    for t in list(board.GetTracks()):
        if DEDICATED.fullmatch(t.GetNetname()) or t.m_Uuid.AsString() in shared_removal:
            removed.append(dict(uuid=t.m_Uuid.AsString(),before=before_copper[t.m_Uuid.AsString()],
                reason='Dedicated DI path depended on invalid placement' if DEDICATED.fullmatch(t.GetNetname()) else 'Proven moved-passive leaf branch only; shared junction/via/unmodified-pad anchors and trunks preserved'))
    absolute,cells,reservation_hashes=place_groups(board,fps,move,out)
    ledger=[]
    for ref,(owner,dx,dy,angle,reason) in move.items():
        fp=fps[ref];old=tuple(v/1e6 for v in before_fps[ref][1]);oldangle=before_fps[ref][2]
        x,y,angle=absolute[ref];fp.SetPosition(xy((x,y)));fp.SetOrientationDegrees(angle)
        ledger.append(dict(reference=ref,owner=owner,old_position_mm=old,new_position_mm=mm(fp.GetPosition()),
            old_rotation_deg=oldangle,new_rotation_deg=angle,reason=reason,pad_piece_UUIDs=[p.m_Uuid.AsString() for p in fp.Pads()]))
    evidence=spacing(board)
    out.mkdir(parents=True);inputs=out/'inputs';inputs.mkdir()
    for file in [base,source/'design.json',source/'netlist.xml',source/'assembly-map.json',Path(__file__)]:shutil.copy2(file,inputs/file.name)
    write(out/'reserved-di-cells.json',dict(cells=cells,inputs=reservation_hashes,base_sha256=sha(base)))
    candidate=out/'motherboard-di-domain-placement-candidate.kicad_pcb'
    for suffix in ['.kicad_pro','.kicad_dru']:shutil.copy2(base.with_suffix(suffix),candidate.with_suffix(suffix))
    for file in base.parent.iterdir():
        if file.is_dir() and (file.name.endswith('.pretty') or file.name=='3dmodels'):shutil.copytree(file,out/file.name)
    shutil.copy2(base.parent/'fp-lib-table',out/'fp-lib-table')
    pcbnew.SaveBoard(str(candidate),board)
    # SWIG Remove ownership varies across KiCad builds. Delete the exact
    # reviewed native pieces from the serialized tree instead, keeping all
    # other native objects byte-structure equivalent.
    tree=parse(candidate.read_text(encoding='utf-8'));remove_ids={r['uuid'] for r in removed}
    found={value(child(t,'uuid')[1]) for t in tree[1:] if isinstance(t,list) and t and t[0] in ['segment','via'] and value(child(t,'uuid')[1]) in remove_ids}
    if found!=remove_ids:raise ValueError('Literal native copper-removal ledger did not match serialized board')
    tree=[tree[0]]+[t for t in tree[1:] if not(isinstance(t,list) and t and t[0] in ['segment','via'] and value(child(t,'uuid')[1]) in remove_ids)]
    candidate.write_text(dump(tree)+'\n',encoding='utf-8')
    cmd=[str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(out/'drc.json'),str(candidate)]
    run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace');(out/'drc-command.txt').write_text(run.stdout+'\n'+run.stderr)
    drc=json.loads((out/'drc.json').read_text());fresh=pcbnew.LoadBoard(str(candidate));fresh.BuildConnectivity()
    dangling={item['uuid'] for row in drc.get('violations',[]) if row['type']=='via_dangling' for item in row['items']}
    if dangling:
        if dangling!=DANGLING_DI_RETURN_VIAS or dangling&original_ids:raise ValueError('Unexpected/original dangling via is outside bounded DI correction')
        current_tracks={t.m_Uuid.AsString():t for t in fresh.GetTracks()}
        for uid in sorted(dangling):
            via=current_tracks[uid]
            if not isinstance(via,pcbnew.PCB_VIA) or via.GetNetname()!='/motherboard_do/FIELD_B_0V':raise ValueError('Dangling DI via changed native type/net')
            touched_layers=set()
            for layer in [pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.B_Cu]:
                shape=via.GetEffectiveShape(layer)
                if any(t.m_Uuid.AsString()!=uid and t.IsOnLayer(layer) and shape.Collide(t.GetEffectiveShape(layer),0) for t in fresh.GetTracks()):touched_layers.add(layer)
                if any(p.IsOnLayer(layer) and shape.Collide(p.GetEffectiveShape(layer),0) for p in fresh.GetPads()):touched_layers.add(layer)
            if len(touched_layers)>1:raise ValueError('DI via carries an actual inter-layer connection; cannot delete')
            removed.append(dict(uuid=uid,before=before_copper[uid],reason='Exact native DRC confirms obsolete DI return via touches at most one copper layer after its original DI load moves; no existing inter-layer connection or original327 item removed',touched_copper_layers=sorted(touched_layers)))
        tree=parse(candidate.read_text(encoding='utf-8'))
        tree=[tree[0]]+[t for t in tree[1:] if not(isinstance(t,list) and t and t[0]=='via' and value(child(t,'uuid')[1]) in dangling)]
        candidate.write_text(dump(tree)+'\n',encoding='utf-8')
        shutil.move(out/'drc.json',out/'drc-before-return-via-cleanup.json')
        run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace');(out/'drc-command-after-return-via-cleanup.txt').write_text(run.stdout+'\n'+run.stderr)
        drc=json.loads((out/'drc.json').read_text());fresh=pcbnew.LoadBoard(str(candidate));fresh.BuildConnectivity()
    orphan_tracks={item['uuid'] for row in drc.get('violations',[]) if row['type']=='track_dangling' for item in row['items']}
    retired_leaf=set()
    if orphan_tracks:
        if orphan_tracks!=DANGLING_DI_RETURN_TRACKS:raise ValueError('Unexpected dangling track outside exact DI return-via consequence')
        tracks=[t for t in fresh.GetTracks() if t.GetNetname()=='/motherboard_do/FIELD_B_0V']
        edges={t.m_Uuid.AsString():((t.GetStart().x,t.GetStart().y,t.GetLayer()),(t.GetEnd().x,t.GetEnd().y,t.GetLayer()))
            for t in tracks if not isinstance(t,pcbnew.PCB_VIA)}
        vertices={v for edge in edges.values() for v in edge};anchors=set();protected=set(original_ids)
        pads=[p for p in fresh.GetPads() if p.GetNetname()=='/motherboard_do/FIELD_B_0V']
        for vertex in vertices:
            point=pcbnew.VECTOR2I(vertex[0],vertex[1])
            if any(p.IsOnLayer(vertex[2]) and p.HitTest(point) for p in pads):anchors.add(vertex)
            if any(isinstance(t,pcbnew.PCB_VIA) and vertex[:2]==tuple(t.GetPosition()) for t in tracks):anchors.add(vertex)
        for t in tracks:
            if isinstance(t,pcbnew.PCB_VIA):continue
            # Ending at an actual pad is a valid leaf boundary: delete the
            # obsolete branch, preserve the pad. A pad touching the middle of
            # a segment is protected because native endpoints alone do not
            # represent that interior electrical junction.
            if any(p.IsOnLayer(t.GetLayer()) and
                   not p.HitTest(t.GetStart()) and not p.HitTest(t.GetEnd()) and
                   segment_hits_box(mm(t.GetStart()),mm(t.GetEnd()),bounds(p),pcbnew.ToMM(t.GetWidth())/2)
                   for p in pads):protected.add(t.m_Uuid.AsString())
        starts={v for v in vertices if v[:2] in {tuple(before_copper[uid][2]) for uid in dangling}}
        retired_leaf,proof=leaf_branches(edges,starts,anchors,protected)
        if not orphan_tracks<=retired_leaf or retired_leaf&original_ids:raise ValueError('Orphan-ground leaf proof failed or changes retained core')
        leaf_receipts.extend(dict(net='/motherboard_do/FIELD_B_0V',phase='post-via-removal',**row) for row in proof)
        for uid in sorted(retired_leaf):removed.append(dict(uuid=uid,before=before_copper[uid],reason='Proved obsolete DI return-via leaf track; walk stops at current actual pad/via/junction and never removes shared trunk or original327 copper'))
        tree=parse(candidate.read_text(encoding='utf-8'))
        tree=[tree[0]]+[t for t in tree[1:] if not(isinstance(t,list) and t and t[0]=='segment' and value(child(t,'uuid')[1]) in retired_leaf)]
        candidate.write_text(dump(tree)+'\n',encoding='utf-8')
        shutil.move(out/'drc.json',out/'drc-before-return-leaf-cleanup.json')
        run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace');(out/'drc-command-after-return-leaf-cleanup.txt').write_text(run.stdout+'\n'+run.stderr)
        drc=json.loads((out/'drc.json').read_text());fresh=pcbnew.LoadBoard(str(candidate));fresh.BuildConnectivity()
    causal_cleanup=[];all_obsolete_vias=set(dangling)
    # A removed DI leaf can expose the next unused via in a former two-layer
    # branch. Follow only causal endpoints from the exact removal ledger;
    # unrelated physical-pad cluster equality is a final independent guard.
    for pass_index in range(6):
        rows=drc.get('violations',[])
        if not rows:break
        if any(r['type']not in ['via_dangling','track_dangling'] for r in rows):raise ValueError('New non-leaf native DRC requires real correction')
        via_ids={i['uuid'] for r in rows if r['type']=='via_dangling' for i in r['items']}
        if not via_ids:raise ValueError('Dangling tracks without a proven causal via require separate circuit review')
        causal_vertices={tuple(r['before'][2]) for r in removed}|{tuple(r['before'][3]) for r in removed}
        current={t.m_Uuid.AsString():t for t in fresh.GetTracks()}
        for uid in via_ids:
            via=current[uid]
            if uid in original_ids or uid not in before_copper or not isinstance(via,pcbnew.PCB_VIA) or via.GetNetname()!='/motherboard_do/FIELD_B_0V' or tuple(via.GetPosition())not in causal_vertices:
                raise ValueError('Unrelated return via outside exact old-DI leaf chain')
            touched=set();plated_anchors=set()
            for layer in [pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.B_Cu]:
                shape=via.GetEffectiveShape(layer)
                if any(t.m_Uuid.AsString()!=uid and t.IsOnLayer(layer) and shape.Collide(t.GetEffectiveShape(layer),0) for t in fresh.GetTracks()):touched.add(layer)
                for pad in fresh.GetPads():
                    if not pad.IsOnLayer(layer)or not shape.Collide(pad.GetEffectiveShape(layer),0):continue
                    if pad.GetAttribute()==pcbnew.PAD_ATTRIB_PTH and pad.GetNetname()==via.GetNetname():
                        # A same-net PTH already connects its own copper
                        # layers. This extra overlapping via adds no unique
                        # inter-layer path; final physical clusters must be
                        # literally unchanged after it is removed.
                        plated_anchors.add(pad.GetParentFootprint().GetReference()+'.'+pad.GetNumber())
                    else:touched.add(layer)
            if len(touched)>1:raise ValueError('Causal return via still carries an inter-layer connection')
        leaves,proof=leaf_after_return_via_removal(fresh,via_ids,original_ids)
        if leaves&original_ids:raise ValueError('Causal leaf cleanup changes original327 copper')
        causal_cleanup.append(dict(pass_index=pass_index,retired_via_UUIDs=sorted(via_ids),retired_track_UUIDs=sorted(leaves),leaf_proof=proof))
        leaf_receipts.extend(dict(net='/motherboard_do/FIELD_B_0V',phase='causal-return-cleanup',**r) for r in proof)
        for uid in sorted(via_ids|leaves):removed.append(dict(uuid=uid,before=before_copper[uid],reason='Native DRC causal obsolete DI return-via/leaf chain; no original327 or unrelated joined pad clusters may change'))
        all_obsolete_vias.update(via_ids);retired_leaf.update(leaves)
        tree=parse(candidate.read_text(encoding='utf-8'));ids=via_ids|leaves
        tree=[tree[0]]+[t for t in tree[1:] if not(isinstance(t,list) and t and t[0]in ['segment','via'] and value(child(t,'uuid')[1])in ids)]
        candidate.write_text(dump(tree)+'\n',encoding='utf-8')
        shutil.move(out/'drc.json',out/f'drc-before-causal-cleanup-{pass_index}.json')
        run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace');(out/f'drc-command-after-causal-cleanup-{pass_index}.txt').write_text(run.stdout+'\n'+run.stderr)
        drc=json.loads((out/'drc.json').read_text());fresh=pcbnew.LoadBoard(str(candidate));fresh.BuildConnectivity()
    if retained_return_clusters(fresh,move)!=retained_clusters_before:raise ValueError('Unrelated actual physical return-pad clusters changed')
    after_copper={t.m_Uuid.AsString():identity(t) for t in fresh.GetTracks()}
    if set(before_copper)-set(after_copper)!={r['uuid'] for r in removed}:raise ValueError('Unexpected copper removal')
    if any(before_copper[k]!=v for k,v in after_copper.items()):raise ValueError('Unrelated retained copper changed')
    for f in fresh.GetFootprints():
        ref=f.GetReference()
        if ref not in move and before_fps[ref]!=(f.m_Uuid.AsString(),tuple(f.GetPosition()),f.GetOrientationDegrees(),footprint_name(f)):raise ValueError('Unrelated footprint moved '+ref)
        for pad in f.Pads():
            key=pad.m_Uuid.AsString();old=before_pads[key];now=piece(pad)
            if pad.GetNumber() and pad.GetNetname()!=nodes.get((ref,pad.GetNumber())):raise ValueError('Source net differs after move')
            if ref not in move and old!=now:raise ValueError('Unrelated pad piece changed')
            if ref in move:
                # Position/orientation are the only eligible changes.
                if any(old[i]!=now[i] for i in range(len(old)) if i not in [3,5]):raise ValueError('Moved pad land/net/UUID changed')
    receipt=dict(base_sha256=sha(base),board_sha256=sha(candidate),physical_parts=len(fresh.GetFootprints()),
        moved_local_passives=len(move)-12,moved_DI_isolators=12,original_327_footprints_and_copper_unchanged=True,
        unrelated_native_copper_preserved=True,all_pad_lands_nets_UUIDs_preserved=True,
        removed_dedicated_invalid_DI_copper_count=len(removed)-len(shared_removal)-len(all_obsolete_vias)-len(retired_leaf),removed_shared_leaf_branch_count=len(shared_removal)+len(retired_leaf),removed_obsolete_single_layer_return_via_count=len(all_obsolete_vias),
        causal_return_cleanup=causal_cleanup,unrelated_actual_return_pad_clusters_preserved=True,
        shared_leaf_branch_proof=leaf_receipts,removed_copper=removed,moves=ledger,
        reserved_DI_cells=cells,reserved_mechanics_and_power_inputs=reservation_hashes,
        source_unchanged=True,field_logic_side_and_primary_RTHR_spacing=evidence,
        native_DRC_regular=len(drc.get('violations',[])),native_DRC_ignored=drc.get('ignored_checks',[]),
        track_via_count=len(fresh.GetTracks()),uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),
        routing_complete=False,manufacturing_ready=False,
        remaining='Exact removed dedicated DI paths require legal rerouting against corrected own-domain reference planes; bypass ground loops require actual routing proof.')
    write(out/'receipt.json',receipt);print(json.dumps({k:v for k,v in receipt.items() if k not in ['moves','removed_copper','field_logic_side_and_primary_RTHR_spacing']},indent=2))
    raise SystemExit(bool(receipt['native_DRC_regular'] or receipt['native_DRC_ignored']))


if __name__=='__main__':main()
