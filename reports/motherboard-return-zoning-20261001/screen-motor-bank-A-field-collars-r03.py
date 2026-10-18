"""Read-only exact moved-source projection screen of real motor control paths."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import native,classify,positioned,sha,write
from hardware_bridge_owned_return_resources_r04 import ReferenceGuard
from hardware_zone_motherboard_returns import return_net,functional_barrier
from hardware_route_logic_return import xy
from hardware_route_selected_additive import corridor_polygon
from hardware_index_literal_reference_coverage import LiteralReferenceCoverage

folder=Path('reports/motherboard-power-entry-20261001/motor-bank-A-r83')
bp=folder/'motor-bank-A-receiving-candidate.kicad_pcb'
out=Path('reports/motherboard-return-zoning-20261001/motor-bank-A-r83-field-collar-screen-r03')
if out.exists():raise ValueError('Fresh immutable screen required')
out.mkdir()
b=pcbnew.LoadBoard(str(bp));b.BuildConnectivity()
source=Path('hardware/motherboard');model=json.loads((source/'design.json').read_text());parts={r:c for r,c in model['components'].items()if c.get('physical',c.get('role')!='schematic_boundary_not_orderable')}
nodes,nc,functions=native(source/'netlist.xml');domains,barriers,_,_=classify(parts,nodes,nc)
mapping=positioned(b,parts,nodes,nc,functions,domains,barriers)
if mapping['errors']:raise ValueError('Actual native source map mismatch')
write(out/'actual-moved-source-domain-map.json',dict(mapping,actual_board_sha256=sha(bp)))
guard=ReferenceGuard(b,mapping)
controlnets={ '/motherboard_power_entry/'+x for x in('MOTOR_FEED_REARM_A','MOTOR_FEED_ON_A','MOTOR_FEED_CLEAR_SOURCE_A','MOTOR_FEED_CLEAR_MID_A','MOTOR_FEED_CLEAR_N_A','MOTOR_TX_GATE_CONTACT_MID_A','MOTOR_FEED_PG_A') }|{'/fpga_core/OPI_REARM_M'}
controlnets={'/motherboard_power_entry/'+x for x in('FIELD_HEALTH_A_LED_A','FIELD_HEALTH_A_LED_MID','FIELD_HEALTH_A_LED_K','FIELD_5V')}
rows=[];own='/motherboard_motors/FIELD_GND';cache=LiteralReferenceCoverage(b,[own],[pcbnew.In1_Cu,pcbnew.In4_Cu])
for row in json.loads((folder/'debug.json').read_text())['routes']:
    if row['net']not in controlnets:continue
    reference=pcbnew.In1_Cu if row['layer']=='F.Cu'else pcbnew.In4_Cu
    conflicts=[];coverage=[];pieces=[]
    for a,c in zip(row['points_mm'],row['points_mm'][1:]):
        shape=corridor_polygon(tuple(xy(a)),tuple(xy(c)),pcbnew.FromMM(row['width_mm']/2+.4));pieces.append(shape)
        for foreign,other in guard.indices[reference].candidates(a,c,row['width_mm']/2+.7):
            if foreign==own:continue
            hit=pcbnew.SHAPE_POLY_SET();hit.Append(shape);hit.BooleanIntersection(other)
            if hit.Area():conflicts.append(dict(segment=[a,c],foreign_return=foreign,exact_intersection_mm2=hit.Area()/1e12))
        for barrier in mapping['barriers']:
            band=functional_barrier(barrier);hit=pcbnew.SHAPE_POLY_SET();hit.Append(shape);hit.BooleanIntersection(band)
            if hit.Area():conflicts.append(dict(segment=[a,c],actual_package_barrier=barrier['reference'],exact_intersection_mm2=hit.Area()/1e12))
        coverage.append(cache.candidate_covered(shape,own,reference))
    rows.append(dict(role=row['role'],net=row['net'],actual_copper_UUIDs=row['uuids'],layer=row['layer'],reference_layer=b.GetLayerName(reference),width_mm=row['width_mm'],literal_points_mm=row['points_mm'],reference_margin_mm=.4,actual_source_projection_conflicts=conflicts,all_current_filled_segments_prefilter=all(coverage),current_segment_prefilter=coverage,native_corridor_qualification=False))
write(out/'screen.json',dict(read_only=True,board_sha256=sha(bp),source_design_sha256=sha(source/'design.json'),rows=rows,
    actual_control_path_rows=len(rows),actual_foreign_source_conflict_rows=sum(bool(r['actual_source_projection_conflicts'])for r in rows),own_collar_candidate_rows=sum(not r['actual_source_projection_conflicts']for r in rows),all_source_anchoring_DRC_reference_and_oldclusters_still_required=True))
print('Exact control rows',len(rows),'foreign conflicts',sum(bool(r['actual_source_projection_conflicts'])for r in rows),flush=True)
