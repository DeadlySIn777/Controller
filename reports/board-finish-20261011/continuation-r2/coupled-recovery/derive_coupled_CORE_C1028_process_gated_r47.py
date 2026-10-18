from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'screen_coupled_CORE_duplicates_IO3_ordinary_CDONE_r46.py').read_text()
s=s.replace('ordinary-IO3-screen-r46','C1028-VIPPO-process-gated-screen-r47')
s=s.replace("iv=Point(io_old['x'],io_old['y']).buffer(3,quad_segs=128)","iv=ips.buffer(-.155004)")
s=s.replace("for p in base['pads']:\n  if p['smd']:","for p in base['pads']:\n  if p['uuid']==ip['uuid']:continue\n  if p['smd']:")
s=s.replace("outside=iv.difference(court)","outside=iv.difference(court)")
s=s.replace("reachable=iv.intersection(bcell)","reachable=iv")
s=s.replace("'B_supply_reachable':info(reachable)","'fully_contained_new_process_site_region':info(reachable)")
old="""  bsource=c['source_refs']['In4.Cu'].difference(io_cut.union(sg_cut));ballow=bsource.union(owncap).buffer(-.125004);bf=bfree.intersection(ballow);bp=next((p for p in pieces(bf) if p.covers(Point(at)) and not p.intersection(ips.buffer(-.005)).is_empty),None)
  row={'IO3_at':at,'power_B_source_route':False,'CORE_geometry_route':False,'CORE_strict_source_route':False}
  if bp is None:trials.append(row);continue
  port=bp.intersection(ips.buffer(-.005)).representative_point();port=[round(x,6) for x in port.coords[0]];bpath,bmeta=tri_route.route(bp,port,at);bpath=[[round(x,6) for x in q] for q in bpath];bbody=K.Z.bounded_buffer(LineString(bpath),.125);bgap=bbody.difference(owncap).difference(bsource)
  row.update(power_B_source_route=bgap.is_empty,power_B_path=bpath,power_B_literal_source_gap=info(bgap))
  if not bgap.is_empty:trials.append(row);continue"""
new="""  hole=K.Z.bounded_disk({'x':at[0],'y':at[1]},.15)
  ann=Point(at).buffer(.3,quad_segs=128).difference(Point(at).buffer(.15,quad_segs=128))
  padcontact=ann.intersection(ips)
  sourceann=ann.intersection(wide['IO3_source_fills']['In2.Cu'])
  row={'IO3_at':at,'power_B_source_route':True,'power_B_path':[],'added_power_stem_tracks':0,'CORE_geometry_route':False,'CORE_strict_source_route':False,'explicit_new_C1028_1_VIPPO_process_location_required':True,'finite_direct_own_pad_contact':info(padcontact),'finite_own_In2_SOURCE_annulus':info(sourceann),'own_pad_contains_drill_with_5um_export_bound':ips.buffer(-.005).covers(hole)}
  if padcontact.area<=0 or sourceann.area<=0 or not row['own_pad_contains_drill_with_5um_export_bound']:trials.append(row);continue"""
assert old in s;s=s.replace(old,new)
s=s.replace("'VIPPO_registry_changes':0", "'VIPPO_registry_changes':0,'new_prospective_process_locations':1,'new_process_location_qualification':'OPEN exact C1028.1 .60/.30 TypeVII fill planarize cap; registry remains291'")
s=s.replace('COUPLED_DUPLICATE_CORE_ORDINARY_IO3_SOURCE_CONTACT_SCREEN_POSITIVE_ALL_GRAPH_CURRENT_NATIVE_OPEN','COUPLED_DUPLICATE_CORE_C1028_PROCESS_GATED_SOURCE_CONTACT_SCREEN_POSITIVE_GRAPH_CURRENT_NATIVE_PROCESS_OPEN')
s=s.replace('COUPLED_DUPLICATE_CORE_ORDINARY_IO3_BOUNDED_SCREEN_NO_FULL_POSITIVE','COUPLED_DUPLICATE_CORE_C1028_PROCESS_GATED_BOUNDED_SCREEN_NO_FULL_POSITIVE')
s=s.replace('coupled-only-authorized-CORE-duplicates-IO3-ordinary-CDONE-screen-context.pkl','coupled-only-authorized-CORE-duplicates-C1028-new-process-ordinary-CDONE-context.pkl')
(H/'screen_coupled_CORE_C1028_process_gated_r47.generated.py').write_text(s)
