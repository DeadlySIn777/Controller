"""Add position-derived reference-plane polygons without replacing old copper.

Run with KiCad Python. This bounded prototype adds In1/In4 return polygons,
package barrier rule areas and exclusions beneath foreign domains. It retains
all old native objects, including zone definitions; their generated fills may
acquire necessary holes. No power-current capacity, finished stackup, safety
rating or complete signal routing follows from a plane-fill DRC result.
"""
from __future__ import annotations
import argparse
import collections
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import pcbnew

from hardware_build_assembly import parse,dump,children,child,value
from hardware_map_motherboard_domains import ROOT,SEEDS,RAW_RETURNS,sha,write
from hardware_route_selected_additive import immutable_objects,zone_definitions
from hardware_route_logic_return import identity

CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
RAW_POWER={'/motherboard_comms/RS485_ISO_3V3_RAW':'/motherboard_comms/RS485_ISO_RETURN_RAW',
           '/motherboard_comms/CAN_ISO_5V_RAW':'/motherboard_comms/CAN_ISO_RETURN_RAW'}


def polygon(points):
    out=pcbnew.SHAPE_POLY_SET();out.NewOutline()
    for x,y in points:out.Append(pcbnew.FromMM(x),pcbnew.FromMM(y))
    return out


def rectangle(bounds,margin=0):
    a,b,c,d=bounds
    return polygon([(a-margin,b-margin),(c+margin,b-margin),(c+margin,d+margin),(a-margin,d+margin)])


def duplicate(poly):
    out=pcbnew.SHAPE_POLY_SET();out.Append(poly);return out


def inflation(poly,margin):
    out=duplicate(poly)
    out.Inflate(pcbnew.FromMM(margin),pcbnew.CORNER_STRATEGY_CHAMFER_ALL_CORNERS,pcbnew.FromMM(.01))
    return out


def return_net(pad):
    domain=pad['domain'];net=pad['net']
    if domain not in SEEDS or domain=='CHASSIS':return None
    if net in RAW_RETURNS:return net
    if net in RAW_POWER:return RAW_POWER[net]
    return SEEDS[domain]


def reference_envelopes(mapping):
    groups=collections.defaultdict(list)
    for pad in mapping['pads']:
        net=return_net(pad)
        if net:groups[pad['reference'],net].append(pad)
    result=[]
    for (ref,net),pads in groups.items():
        result.append(dict(reference=ref,net=net,pins=sorted({p['pin'] for p in pads}),
            bounds=[min(p['copper_aabb_mm'][0] for p in pads),min(p['copper_aabb_mm'][1] for p in pads),
                    max(p['copper_aabb_mm'][2] for p in pads),max(p['copper_aabb_mm'][3] for p in pads)]))
    return result


def build_polygons(mapping):
    """Local same-reference islands plus a continuous remaining logic region.

    Multiple local field outlines remain explicit until legal spanning return
    corridors are added and native connectivity proves them joined. The
    current function cannot silently claim such fragments are continuous.
    """
    seed=collections.defaultdict(pcbnew.SHAPE_POLY_SET)
    for row in reference_envelopes(mapping):seed[row['net']].Append(rectangle(row['bounds'],.6))
    for poly in seed.values():poly.Simplify()
    barriers=pcbnew.SHAPE_POLY_SET()
    for row in mapping['barriers']:barriers.Append(polygon(row['polygon_mm']))
    barriers.Simplify()
    ungrounded=pcbnew.SHAPE_POLY_SET()
    for row in mapping['reference_seed_envelopes']:
        if row['domain'].startswith(('SUB:','CONTACT:')) or row['domain']=='CHASSIS':
            ungrounded.Append(rectangle(row['copper_aabb_mm'],.3))
    ungrounded.Simplify()
    all_foreign=pcbnew.SHAPE_POLY_SET()
    for name,poly in seed.items():
        if name!='/LOGIC_GND':all_foreign.Append(poly)
    all_foreign.Simplify()
    regions={}
    for name,poly in seed.items():
        if name=='/LOGIC_GND':continue
        obstacles=duplicate(barriers);obstacles.Append(ungrounded)
        for other,region in seed.items():
            if other!=name:obstacles.Append(inflation(region,.25))
        obstacles.Simplify();candidate=duplicate(poly);candidate.BooleanSubtract(obstacles)
        regions[name]=candidate
    logic=rectangle([.5,.5,459.5,339.5])
    exclusions=inflation(all_foreign,.25);exclusions.Append(barriers);exclusions.Append(ungrounded);exclusions.Simplify()
    logic.BooleanSubtract(exclusions);regions['/LOGIC_GND']=logic
    # Foreign-only pour exclusions on the former power/surface plane layers
    # retain old definitions yet prevent old logic/IO3/core fill beneath fields.
    old_layer_exclusions=inflation(all_foreign,.25);old_layer_exclusions.Append(ungrounded);old_layer_exclusions.Simplify()
    return regions,barriers,ungrounded,old_layer_exclusions


def add_zone(board,net,poly,layer,priority,name):
    if not poly.OutlineCount():return None
    zone=pcbnew.ZONE(board);zone.SetLayer(layer);zone.SetNet(board.FindNet(net))
    zone.SetAssignedPriority(priority);zone.SetZoneName(name)
    zone.SetLocalClearance(pcbnew.FromMM(.25));zone.SetMinThickness(pcbnew.FromMM(.2))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
    zone.Outline().Append(poly);board.Add(zone);return zone


def add_keepout(board,poly,layers,name,tracks=False,vias=False):
    if not poly.OutlineCount():return None
    zone=pcbnew.ZONE(board);mask=pcbnew.LSET()
    for layer in layers:mask.AddLayer(layer)
    zone.SetLayerSet(mask);zone.SetIsRuleArea(True);zone.SetZoneName(name)
    zone.SetDoNotAllowZoneFills(True);zone.SetDoNotAllowTracks(tracks);zone.SetDoNotAllowVias(vias)
    zone.SetDoNotAllowPads(False);zone.SetDoNotAllowFootprints(False)
    zone.Outline().Append(poly);board.Add(zone);return zone


def filled_return_coverage(board,mapping):
    fills={};rows=[]
    for layer in [pcbnew.In1_Cu,pcbnew.In4_Cu]:
        for zone in board.Zones():
            if zone.GetIsRuleArea() or not zone.IsOnLayer(layer) or not zone.HasFilledPolysForLayer(layer):continue
            key=zone.GetNetname(),layer
            fills.setdefault(key,pcbnew.SHAPE_POLY_SET()).Append(zone.GetFilledPolysList(layer))
    for fill in fills.values():fill.Simplify()
    for pad in mapping['pads']:
        net=return_net(pad)
        if not net:continue
        p=pcbnew.VECTOR2I(pcbnew.FromMM(pad['position_mm'][0]),pcbnew.FromMM(pad['position_mm'][1]))
        for layer in [pcbnew.In1_Cu,pcbnew.In4_Cu]:
            actual=fills.get((net,layer))
            # Copper antipads under through-hole signal contacts are expected;
            # this report is explicit projection, not an electrical pad join.
            rows.append(dict(reference=pad['reference'],pin=pad['pin'],pad_uuid=pad['uuid'],
                reference_net=net,layer=board.GetLayerName(layer),
                projected_pad_center_has_own_reference=bool(actual and actual.Contains(p)),
                through_hole_projection_antipad_expected=len(pad['copper_layers'])>1))
    continuity=[]
    for (net,layer),fill in fills.items():
        continuity.append(dict(net=net,layer=board.GetLayerName(layer),
            filled_connected_outline_count=fill.OutlineCount(),filled_area_mm2=fill.Area()/1e12,
            single_continuous_reference=fill.OutlineCount()==1))
    return dict(pad_projection_rows=rows,filled_reference_regions=continuity,
        all_pad_projection_requirement_qualified=False,
        note='Projection only; native zone copper connectivity and legal local stitching remain distinct from this geometric necessary condition. Through-hole signal antipads cannot be interpreted as an error or as adequate return proof.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--map',type=Path,required=True);p.add_argument('--board',type=Path,required=True)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();base=a.board.resolve();out=a.out.resolve();source=a.source.resolve()
    if out.exists() or not out.is_relative_to(ROOT/'reports'):raise ValueError('New immutable report directory required')
    mapping=json.loads(a.map.read_text(encoding='utf-8'))
    if mapping['input_sha256'].get(str(base))!=sha(base):raise ValueError('Domain map does not describe this exact board')
    for name in ['design.json','netlist.xml','assembly-map.json']:
        if mapping['input_sha256'].get(str(source/name))!=sha(source/name):raise ValueError('Source hash differs '+name)
    if not mapping['source_physical_population_complete'] or mapping['errors']:raise ValueError('Source population/net mapping is incomplete')
    out.mkdir(parents=True)
    inputs=out/'inputs';inputs.mkdir()
    for file in [base,a.map.resolve(),source/'design.json',source/'netlist.xml',source/'assembly-map.json',Path(__file__)]:
        shutil.copy2(file,inputs/file.name)
    candidate=out/'motherboard-return-zones-candidate.kicad_pcb'
    for suffix in ['.kicad_pro','.kicad_dru']:
        shutil.copy2(base.with_suffix(suffix),candidate.with_suffix(suffix))
    for file in base.parent.iterdir():
        if file.is_dir() and (file.name.endswith('.pretty') or file.name=='3dmodels'):shutil.copytree(file,out/file.name)
    if (base.parent/'fp-lib-table').exists():shutil.copy2(base.parent/'fp-lib-table',out/'fp-lib-table')
    hashes={str(v):sha(v) for v in [base,a.map.resolve(),source/'design.json',source/'netlist.xml',source/'assembly-map.json',base.with_suffix('.kicad_pro'),base.with_suffix('.kicad_dru')]}
    tree=parse(base.read_text(encoding='utf-8'));before=immutable_objects(tree)
    board=pcbnew.LoadBoard(str(base));old_copper={t.m_Uuid.AsString():identity(t) for t in board.GetTracks()}
    oldzones={z.m_Uuid.AsString() for z in board.Zones()}
    regions,barriers,ungrounded,foreign=build_polygons(mapping)
    all_layers=[pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.B_Cu]
    for row in mapping['barriers']:
        add_keepout(board,polygon(row['polygon_mm']),all_layers,'ISO_BARRIER_'+row['reference'],tracks=True,vias=True)
    add_keepout(board,ungrounded,all_layers,'UNGROUNDED_CONTACT_SUB_CHASSIS_POUR_EXCLUSION')
    add_keepout(board,foreign,[pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.B_Cu],'FOREIGN_REFERENCE_OLD_PLANE_EXCLUSION')
    for net,poly in regions.items():
        for layer in [pcbnew.In1_Cu,pcbnew.In4_Cu]:
            add_zone(board,net,poly,layer,10 if net=='/LOGIC_GND' else 20,'REFERENCE_'+net.replace('/','_')+'_'+board.GetLayerName(layer))
    temporary=out/'zone-donor.kicad_pcb';pcbnew.SaveBoard(str(temporary),board)
    donor=parse(temporary.read_text(encoding='utf-8'))
    additions=[z for z in children(donor,'zone') if value(child(z,'uuid')[1]) not in oldzones]
    final=copy.deepcopy(tree);final.extend(copy.deepcopy(additions));candidate.write_text(dump(final)+'\n',encoding='utf-8')
    if immutable_objects(final)[0]!=before[0] or immutable_objects(final)[2]!=before[2]:raise ValueError('Zone addition altered old native objects')
    if any(zone_definitions(final).get(k)!=v for k,v in before[1].items()):raise ValueError('Old zone definition changed')
    cmd=[str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(out/'drc.json'),str(candidate)]
    (out/'drc-command.json').write_text(json.dumps(cmd,indent=2)+'\n')
    run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (out/'drc-command.txt').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
    drc=json.loads((out/'drc.json').read_text(encoding='utf-8'))
    board=pcbnew.LoadBoard(str(candidate));board.BuildConnectivity()
    if {t.m_Uuid.AsString():identity(t) for t in board.GetTracks()}!=old_copper:raise ValueError('Retained copper changed')
    after=immutable_objects(parse(candidate.read_text(encoding='utf-8')))
    if after[0]!=before[0] or after[2]!=before[2]:raise ValueError('Native refill changed old footprints/pad pieces/other objects')
    if any(after[1].get(k)!=v for k,v in before[1].items()):raise ValueError('Native refill changed old zone definitions')
    write(out/'reference-coverage.json',filled_return_coverage(board,mapping))
    for path,h in hashes.items():
        if sha(path)!=h:raise ValueError('Immutable input changed '+path)
    receipt=dict(input_sha256=hashes,board_sha256=sha(candidate),footprints=len(board.GetFootprints()),
        old_copper_geometry_UUIDs_preserved=True,old_zone_definitions_preserved=True,old_all_pad_pieces_preserved=True,
        track_via_count=len(board.GetTracks()),old_zone_count=len(oldzones),new_zone_rule_area_objects=len(additions),
        native_DRC_regular=len(drc.get('violations',[])),native_DRC_ignored=drc.get('ignored_checks',[]),
        uncapped_unconnected=board.GetConnectivity().GetUnconnectedCount(False),
        new_reference_plan_nets=list(regions),
        SUB_nets_accounted=44,SUB_thermal_2x2_copper_implemented=False,
        field_spanning_reference_corridors_implemented=False,
        status='native_position_derived_partial_return_prototype_not_manufacturing_ready',
        manufacturing_ready=False,physical_qualification=False)
    write(out/'receipt.json',receipt);print(json.dumps(receipt,indent=2))
    raise SystemExit(bool(receipt['native_DRC_regular'] or receipt['native_DRC_ignored']))


if __name__=='__main__':main()
