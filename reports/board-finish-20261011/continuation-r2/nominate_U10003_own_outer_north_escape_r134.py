"""Test own pin9 outward/north escape while preserving every native keepout.

Only its own conservative expanded courtyard planner masks are locally opened;
the via Cu must remain outside the literal actual courtyard plus25um, and all
foreign Cu, pads, holes, isolation/native reservations remain hard. No old fault
copper is removed and this is a nominee, never source/native acceptance.
"""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'nominate_R214_ground_normal_native_antipads_r119.py';wrapper=source.read_text()
needle="exec(compile(code,str(source),'exec'))";assert wrapper.count(needle)==1
extra="""code=code.replace("OUT=H/'R214-ground-normal-native-antipad-nominees-r119'","OUT=H/'U10003-own-outer-north-ground-escape-nominees-r134'")
needle="targets=[('U10003','9','4021795d-90df-4df0-a1b4-13cdcbdd91ac',.026),('U11025','2','d64c464d-de71-4c7e-9d98-b870e2ad977f',.001)]";assert code.count(needle)==1
code=code.replace(needle,"targets=[('U10003','9','4021795d-90df-4df0-a1b4-13cdcbdd91ac',.026)]")
needle="corridor=box(pad['x']+.55,pad['y']-.21,pad['x']+2.5,pad['y']+.21)";assert code.count(needle)==1
code=code.replace(needle,"corridor=box(pad['x']+.55,pad['y']-2.5,pad['x']+2.5,pad['y']+.21)")
needle="            found=[s for s in ownhard if any(s.equals(c) for c in courts)];";assert code.count(needle)==1
code=code.replace(needle,"            own_literal_courtyard=unary_union([s for rs in foot['courtyard'].values() for s in C.poly(rs)]);actual_own_via_courtyard_mask=N.bounded_buffer(own_literal_courtyard,.25+.025+.000020);scoped_viahard=[s.difference(corridor) if any(s.equals(c) for c in courts) else s for s in viahard];print('R134_LITERAL_COURTYARD',own_literal_courtyard.bounds,flush=True)\\n"+needle)
needle="viaobs.extend(N.bounded_buffer(s,.25+.025+.000020) for s in viahard if s.intersects(query))";assert code.count(needle)==1
code=code.replace(needle,"viaobs.extend(N.bounded_buffer(s,.25+.025+.000020) for s in scoped_viahard if s.intersects(query));viaobs.append(actual_own_via_courtyard_mask)")
needle="'own_only_planning_escape_corridor_bounds':list(corridor.bounds) if corridor is not None else None";assert code.count(needle)==1
code=code.replace(needle,needle+",'ordinary_via_Cu_outside_literal_own_courtyard_plus25um':True,'only_own_conservative_courtyard_expansion_locally_opened':True,'actual_native_isolation_keepouts_other_footprints_pads_domains_and_all_holes_unchanged':True")
"""
wrapper=wrapper.replace(needle,extra+needle)
exec(compile(wrapper,str(source),'exec'))
