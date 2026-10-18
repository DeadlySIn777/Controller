"""Read-only actual native drill/SMD land audit; no manufacturing waivers."""
from pathlib import Path
import argparse, collections, json, sys
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew as p
from hardware_populate_motherboard_pcb import sha,write
from hardware_route_local_signals import GeometryIndex
from hardware_route_logic_return import mm
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--board',type=Path,required=True)
ap.add_argument('--out',type=Path,required=True)
a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
before=sha(a.board);b=p.LoadBoard(str(a.board))
source=Path('hardware/motherboard/design.json')
parts=json.loads(source.read_text())['components']
indices={p.F_Cu:GeometryIndex(),p.B_Cu:GeometryIndex()}
lands=0
for pad in b.GetPads():
    if pad.GetAttribute()!=p.PAD_ATTRIB_SMD:continue
    for layer,paste in [(p.F_Cu,p.F_Paste),(p.B_Cu,p.B_Paste)]:
        if not(pad.IsOnLayer(layer)and pad.IsOnLayer(paste)):continue
        bb=pad.GetBoundingBox();box=tuple(p.ToMM(x)for x in [bb.GetLeft(),bb.GetTop(),bb.GetRight(),bb.GetBottom()])
        indices[layer].add((pad,box),box);lands+=1
rows=[];total=0
for via in b.GetTracks():
    if not isinstance(via,p.PCB_VIA):continue
    total+=1;pos=mm(via.GetPosition());radius=via.GetDrillValue()//2
    drill=p.SHAPE_CIRCLE(via.GetPosition(),radius)
    for layer,index in indices.items():
        if not via.IsOnLayer(layer):continue
        for pad,box in index.candidates(pos,pos,p.ToMM(radius)+.001):
            if not pad.GetEffectiveShape(layer).Collide(drill,0):continue
            ref=pad.GetParentFootprint().GetReference()
            rows.append(dict(via_uuid=via.m_Uuid.AsString(),via_net=via.GetNetname(),position_mm=list(pos),
                drill_mm=p.ToMM(via.GetDrillValue()),via_diameter_mm=p.ToMM(via.GetWidth(layer)),
                tented=via.IsTented(layer),side=b.GetLayerName(layer),reference=ref,pin=pad.GetNumber(),
                pad_uuid=pad.m_Uuid.AsString(),pad_net=pad.GetNetname(),same_net=pad.GetNetname()==via.GetNetname(),
                MPN=parts.get(ref,{}).get('mpn'),source_role=parts.get(ref,{}).get('role'),
                native_land_shape=int(pad.GetShape()),native_actual_hole_intersects_solder_land=True,
                assembly_disposition='UNRESOLVED: move/re-route hole, or obtain exact filled/capped via-in-pad fabrication and assembly qualification. Tenting alone is not acceptance.'))
assert sha(a.board)==before
write(a.out/'receipt.json',dict(audit_executed=True,board_sha256=before,source_design_sha256=sha(source),
    source_board_unchanged=True,actual_native_vias_checked=total,actual_paste_SMD_lands_checked=lands,
    intersection_count=len(rows),unique_intersecting_vias=len({r['via_uuid']for r in rows}),
    same_net_intersections=sum(r['same_net']for r in rows),foreign_net_intersections=sum(not r['same_net']for r in rows),
    counts_by_reference=dict(collections.Counter(r['reference']for r in rows)),intersections=rows,
    all_drill_SMD_assembly_dispositions_closed=not rows,manufacturing_ready=False,
    scope='Actual native circular via drill vs actual native SMD copper shape on fitted paste layers, including same-net overlap. Read-only screen; not mask/paste/thermal/stencil/assembly qualification.'))
print(json.dumps(dict(intersections=len(rows),vias=len({r['via_uuid']for r in rows}),references=dict(collections.Counter(r['reference']for r in rows)))),flush=True)
