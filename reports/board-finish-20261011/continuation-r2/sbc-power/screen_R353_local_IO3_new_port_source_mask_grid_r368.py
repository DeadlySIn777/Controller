"""Power-port grid eligibility only; no paired return or route is asserted."""
from pathlib import Path
H=Path(__file__).resolve().parent.parent
p=H/'sbc-power/screen_R353_local_IO3_two_new_ports_existing_actual_LG_returns_r367.py'
s=p.read_text(encoding='utf-8').replace('r367','r368').replace('R367','R368')
s=s.replace("for ret in returns:\n  for angle in range(0,360,5):\n   ar=math.radians(angle);xy=(round(ret['xy'][0]+.95*math.cos(ar),6),round(ret['xy'][1]+.95*math.sin(ar),6))", "for ret in [{'xy':[118+i*.25,167.5+j*.25]}for i in range(29)for j in range(29)]:\n  for angle in (0,):\n   xy=tuple(ret['xy'])")
s=s.replace("'existing_original_J1_two_plane_return':ret,'ordinary_return_distance_mm':math.dist(xy,ret['xy'])", "'ordinary_actual_two_plane_return_pair':'OPEN_NOT_SELECTED','ordinary_return_distance_mm':None")
s=s.replace("'PASS_local_source_geometry_mask_screen':not bad", "'PASS_local_power_source_geometry_mask_screen_ONLY':not bad")
s=s.replace("'READ_ONLY_LOCAL_IO3_TWO_NEW_PORT_ELIGIBILITY_EXISTING_TRUE_LG_RETURNS'", "'READ_ONLY_LOCAL_IO3_POWER_PORT_GRID_SOURCE_AND_OLD_MASK_ELIGIBILITY_RETURN_PAIR_OPEN'")
exec(compile(s,str(__file__),'exec'))
