"""Local full1.25 CORE5 detour retains exact old pre/post anchor bodies."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'nominate_CM79_fullwidth_power_and_three_owned_stitch_reroutes_r303.py').read_text()
needle="s=s.replace('R294','R303')"
change=r'''
s=s.replace('CM79-fullwidth-CORE5-three-owned-stitch-endpoint-preserving-nomination-r303','CM79-local-fullwidth-CORE5-three-owned-stitch-endpoint-preserving-nomination-r305')
s=s.replace("anchor_start=[131.4,202.35]", "anchor_start=[120.1,202.35];local_start=[116.2,202.35];preanchor={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM79-R305-exact-unchanged-original-CORE5-preanchor')),'net':old['net'],'layer':'F.Cu','w':1.25,'a':old['a'],'b':local_start};prebody=buf(LineString([preanchor['a'],preanchor['b']]),.625);assert prebody.difference(oldbody).is_empty")
s=s.replace("ff.covers(Point(old['a']))and ff.covers(Point(anchor_start))", "ff.covers(Point(local_start))and ff.covers(Point(anchor_start))")
s=s.replace("'actual_old_A_axis_free':pf.covers(Point(old['a']))", "'exact_old_local_preanchor_entry_free':pf.covers(Point(local_start))")
s=s.replace("TR.route(faces[0],old['a'],anchor_start)", "TR.route(faces[0],local_start,anchor_start)")
s=s.replace("pt.append(anchor);powerbody=", "pt.extend([preanchor,anchor]);powerbody=")
s=s.replace("'original_native_reserved_anchor_Cu_is_exact_subset_only':True", "'original_native_pre_and_post_anchor_Cu_is_exact_subset_only':True,'local_novel_detour_original_coords_mm':[local_start,anchor_start]")
s=s.replace('R303','R305')
'''
assert s.count(needle)==1;s=s.replace(needle,needle+'\n'+change)
exec(compile(s,str(__file__),'exec'))
