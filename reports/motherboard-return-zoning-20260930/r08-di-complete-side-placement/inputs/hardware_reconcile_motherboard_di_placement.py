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


def bounds(pad):
    b=pad.GetBoundingBox();return mm(b.GetOrigin())+mm(b.GetEnd())


def gap(a,b):
    return math.hypot(max(a[0]-b[2],b[0]-a[2],0),max(a[1]-b[3],b[1]-a[3],0))


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
        removed_dedicated_invalid_DI_copper_count=len(removed)-len(shared_removal),removed_shared_leaf_branch_count=len(shared_removal),
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
