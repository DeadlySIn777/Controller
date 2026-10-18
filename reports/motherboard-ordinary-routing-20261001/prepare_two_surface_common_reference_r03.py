"""Try already-declared F/In2 signal layers without touching power pours."""
from pathlib import Path
p=Path(__file__).parent;s=(p/'route_root81_two_surface_r02.py').read_text()
s=s.replace('two-surface routing trial','F/In2 common-reference routing trial')
s=s.replace("((pcbnew.F_Cu,pcbnew.In1_Cu),(pcbnew.B_Cu,pcbnew.In4_Cu))","((pcbnew.F_Cu,pcbnew.In1_Cu),(pcbnew.In2_Cu,pcbnew.In1_Cu))")
s=s.replace('for l in(pcbnew.In1_Cu,pcbnew.In4_Cu)','for l in(pcbnew.In1_Cu,)')
s=s.replace('clear(line,name,pcbnew.B_Cu)','clear(line,name,pcbnew.In2_Cu)')
s=s.replace('(s,t,pcbnew.B_Cu)','(s,t,pcbnew.In2_Cu)')
s=s.replace('add_segment(s,t,name,pcbnew.B_Cu)','add_segment(s,t,name,pcbnew.In2_Cu)')
anchor='full_fills=fills;added=[];groups=[];blocked=[]'
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"""
# Actual retained IO_3V3 and CORE_1V2 filled copper is an obstacle. Signal
# cuts cannot claim that re-pouring preserves a power-delivery cross-section.
power_fills={l:pcbnew.SHAPE_POLY_SET()for l in(pcbnew.In2_Cu,pcbnew.In3_Cu)}
for z in b.Zones():
    if not z.GetIsRuleArea()and z.GetLayer()in power_fills:
        power_fills[z.GetLayer()].BooleanAdd(z.GetFilledPolysList(z.GetLayer()))
for poly in power_fills.values():poly.Simplify()
""")
anchor='        if not covered(corridor_polygon(tuple(xy(a)),tuple(xy(z)),pcbnew.FromMM(width/2+.10)),fills[layer]):return False'
assert s.count(anchor)==1
s=s.replace(anchor,"""        if layer in power_fills:
            hit=corridor_polygon(tuple(xy(a)),tuple(xy(z)),pcbnew.FromMM(width/2+clearance))
            hit.BooleanIntersection(power_fills[layer])
            if hit.OutlineCount():return False
"""+anchor)
anchor='    for index in geo.tracks.values():';assert s.count(anchor)==1
s=s.replace(anchor,"""    for power_poly in power_fills.values():
        hit=circle(tuple(xy(pt)),pcbnew.FromMM(radius+.205));hit.BooleanIntersection(power_poly)
        if hit.OutlineCount():return False
"""+anchor)
s=s.replace('motherboard-ordinary-two-surface-candidate.kicad_pcb','motherboard-ordinary-common-In1-candidate.kicad_pcb')
s=s.replace('exact_native_fill_subset_clipping_search_only=True,','actual_signal_layers=["F.Cu","In2.Cu"],actual_common_reference="In1.Cu",retained_inner_power_pours_preserved_as_obstacles=True,exact_native_fill_subset_clipping_search_only=True,')
(p/'route_root81_common_reference_r03.py').write_text(s);compile(s,str(p/'route_root81_common_reference_r03.py'),'exec')
