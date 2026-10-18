"""Exact one-pair trial; IO3 topology/receiving-feed proof is mandatory next."""
from pathlib import Path
p=Path(__file__).parent;s=(p/'route_root81_common_reference_r03.py').read_text()
s=s.replace('power_fills={l:pcbnew.SHAPE_POLY_SET()for l in(pcbnew.In2_Cu,pcbnew.In3_Cu)}','power_fills={l:pcbnew.SHAPE_POLY_SET()for l in(pcbnew.In3_Cu,)}')
s=s.replace('# Actual retained IO_3V3 and CORE_1V2 filled copper is an obstacle. Signal\n# cuts cannot claim that re-pouring preserves a power-delivery cross-section.','# CORE_1V2 remains an absolute filled-copper obstacle. The bounded IO3\n# hole/slot must separately pass exact post-refill topology/feed screening.\n# No candidate is eligible from this search alone.')
needle="        if length<=25:jobs.append((length,name,p,q))";assert s.count(needle)==1
s=s.replace(needle,"""        pair={p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),q.GetParentFootprint().GetReference()+'.'+q.GetNumber()}
        if pair=={'U17003.6','U17004.5'}:
            assert name=='/motherboard_status/OBS8_INVERTED'
            jobs.append((length,name,p,q))""")
s=s.replace('retained_inner_power_pours_preserved_as_obstacles=True','CORE1V2_preserved_as_actual_native_obstacle=True,IO3_1mm_backbone_and22_receiving_feed_preservation_pending=True')
s=s.replace('motherboard-ordinary-common-In1-candidate.kicad_pcb','motherboard-OBS8-common-In1-candidate.kicad_pcb')
(p/'route_root81_one_pair_io3_screen_r04.py').write_text(s);compile(s,str(p/'route_root81_one_pair_io3_screen_r04.py'),'exec')
