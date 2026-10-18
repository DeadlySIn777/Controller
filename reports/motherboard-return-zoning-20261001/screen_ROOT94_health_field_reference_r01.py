"""Source-derived field projection screen; no board or zone mutation."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import native,classify,positioned,sha,write
from hardware_bridge_owned_return_resources_r04 import ReferenceGuard
from hardware_route_selected_additive import corridor_polygon
from hardware_zone_motherboard_returns import functional_barrier
from hardware_route_logic_return import xy,mm
B=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-DI7-merged-r94/motherboard-bounded-merged-candidate.kicad_pcb')
M=Path('reports/motherboard-power-entry-20261001/health-supply-r99/health-four-local-owner-manifest-r02.json')
S=Path('hardware/motherboard')
D=Path('reports/motherboard-return-zoning-20261001/ROOT94-health-field-collar-screen-r01')
D.mkdir(exist_ok=False)
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity()
parts={r:c for r,c in json.loads((S/'design.json').read_text())['components'].items()if c.get('physical')}
nodes,nc,functions=native(S/'netlist.xml');domains,barriers,_,_=classify(parts,nodes,nc)
mapping=positioned(b,parts,nodes,nc,functions,domains,barriers)
assert not mapping['errors']
guard=ReferenceGuard(b,mapping)
cu={t.m_Uuid.AsString():t for t in b.GetTracks()}
rows=[];shapes={}
for group in json.loads(M.read_text())['actual_local_loops']:
    if group['owner']not in {'U11025','U11026'}:
        continue
    for u in group['local_positive_copper']:
        t=cu[u]
        if t.Type()==pcbnew.PCB_VIA_T:
            specs=[(pcbnew.In1_Cu,corridor_polygon(tuple(t.GetPosition()),tuple(t.GetPosition()),pcbnew.FromMM(1.1))),
                   (pcbnew.In4_Cu,corridor_polygon(tuple(t.GetPosition()),tuple(t.GetPosition()),pcbnew.FromMM(1.1)))]
        else:
            layer=pcbnew.In1_Cu if t.GetLayer()==pcbnew.F_Cu else pcbnew.In4_Cu
            specs=[(layer,corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()/2+pcbnew.FromMM(.20)))]
        for layer,poly in specs:
            conflicts=[]
            for foreign,other in guard.indices[layer].candidates(mm(t.GetStart()),mm(t.GetEnd()),1.2):
                if foreign=='/motherboard_motors/FIELD_GND':
                    continue
                hit=pcbnew.SHAPE_POLY_SET(poly);hit.BooleanIntersection(other)
                if hit.OutlineCount():
                    conflicts.append(dict(foreign=foreign,intersection_mm2=hit.Area()/1e12,exact_polygon=hit.Format(False)))
            for barrier in mapping['barriers']:
                hit=pcbnew.SHAPE_POLY_SET(poly);hit.BooleanIntersection(functional_barrier(barrier))
                if hit.OutlineCount():conflicts.append(dict(barrier=barrier['reference'],intersection_mm2=hit.Area()/1e12))
            rows.append(dict(owner=group['owner'],actual_positive_uuid=u,net=t.GetNetname(),reference=b.GetLayerName(layer),
                             proposed_exact_collar=poly.Format(False),foreign_conflicts=conflicts))
            shapes.setdefault(layer,pcbnew.SHAPE_POLY_SET()).BooleanAdd(poly)
write(D/'screen.json',dict(passed=not any(r['foreign_conflicts']for r in rows),inspection_only=True,
  board=str(B),board_sha256=sha(B),actual_field_return='/motherboard_motors/FIELD_GND',
  exact_native_positive_supply_rows=rows,source_domains_pads= [p for p in mapping['pads']if p['reference']in {'U11025','U11026','C11080','C11081'}],
  no_reference_or_supply_qualification_claim=True,source_Ground_stitch_geometry_pending=True))
print(json.dumps(dict(screened=True,rows=len(rows),conflicting=sum(bool(r['foreign_conflicts'])for r in rows))))
