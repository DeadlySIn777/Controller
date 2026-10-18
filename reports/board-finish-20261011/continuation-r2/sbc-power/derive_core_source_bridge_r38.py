from pathlib import Path
HERE=Path(__file__).parent
s=(HERE/'bridge_actual_core_source_layers_r37.py').read_text()
def rep(a,b):
    global s
    assert s.count(a)==1,(a[:80],s.count(a));s=s.replace(a,b)
s=s.replace('source-bridge-r37','source-bridge-r38').replace('barrel-r37','barrel-r38')
rep('from shapely.geometry import Point,box','from shapely.geometry import Point,box,LineString')
rep('import core_inner_feed_r18 as I','import core_inner_feed_r18 as I\nimport continuous_path_prepared_r2 as CP')
rep("carvable={q['uuid'] for q in zones if q.get('field_return_proposal')};rows=[];carves=[];newvias=[]","carvable={q['uuid'] for q in zones if q.get('field_return_proposal')};rows=[];carves=[];newvias=[];newzones=[];safe_cache={}")
needle="        assert answer is not None,('ordinary_real_cross_layer_source_site_unresolved',uid,anchor)"
rep(needle,'''        if answer is None:
            # A real barrel may be placed elsewhere on the preserved feeder,
            # then a source-connected inner bridge reaches the actual source.
            # This expands constructive choices while keeping all physical
            # native/discrete/aperture guards identical.
            from shapely import from_wkb
            for source_layer in ('In4.Cu','In1.Cu','In2.Cu','In3.Cu'):
                if source_layer==target['layer']:continue
                if source_layer not in safe_cache:
                    ff=L.OUT/'core-inner-feed-r33'/(source_layer+'-free.wkb')
                    free=set_precision(from_wkb(ff.read_bytes()),1e-6)
                    comps=p.hubs.components(set_precision(free.buffer(-.11),1e-6))
                    ct=STRtree(comps);source_ids={int(i) for i in ct.query(goals[source_layer],predicate='intersects')}
                    safe_cache[source_layer]=(free,comps,ct,source_ids)
                free,comps,ct,source_ids=safe_cache[source_layer]
                ids=source_ids & {int(i) for i in ct.query(target['shape'],predicate='intersects')}
                for ci in sorted(ids,key=lambda ci:comps[ci].intersection(target['shape']).distance(goals[source_layer])):
                    comp=comps[ci];potential=comp.intersection(target['shape']).buffer(-.005)
                    if potential.is_empty:continue
                    near=nearest_points(potential,goals[source_layer])[0]
                    anchors=[near,nearest_points(Point(anchor),potential)[1],potential.representative_point()]
                    for probe in anchors:
                        for margin in (4.,10.,25.):
                            win=box(probe.x-margin,probe.y-margin,probe.x+margin,probe.y+margin)
                            for diameter,drill in ((.6,.3),(.5,.2)):
                                legal=legal_region(win,diameter,drill);landing=legal.buffer(-.01).intersection(potential)
                                if landing.is_empty:continue
                                sites=[]
                                for ls in p.hubs.components(landing):
                                    sites += [ls.representative_point().coords[0],nearest_points(ls,goals[source_layer])[0].coords[0]]
                                for xy in sorted(sites,key=lambda xy:Point(xy).distance(goals[source_layer]))[:16]:
                                    site=tuple(round(v,6) for v in xy)
                                    if not legal.covers(Point(site)):continue
                                    ann=Point(site).buffer(diameter/2).difference(Point(site).buffer(drill/2))
                                    ta=ann.intersection(target['shape']).area
                                    if ta<=.005:continue
                                    aa=comp.intersection(ann).buffer(-.005);bb=comp.intersection(goals[source_layer]).buffer(-.005)
                                    if aa.is_empty or bb.is_empty:continue
                                    a,b=nearest_points(aa,bb);start=tuple(round(v,6) for v in a.coords[0]);end=tuple(round(v,6) for v in b.coords[0])
                                    if not comp.covers(Point(start)) or not comp.covers(Point(end)):continue
                                    print('CORE_SOURCE_BRIDGE_SEARCH',uid,site,source_layer,diameter,drill,flush=True)
                                    route=CP.path(comp,start,end,node_cap=500000)
                                    if route['verdict']!='HOST_PATH':continue
                                    points=[[round(x,6),round(y,6)] for x,y in route['points']];line=LineString(points);core=line.buffer(.1)
                                    if not free.covers(core):continue
                                    intended=set_precision(line.buffer(2).intersection(free),1e-6)
                                    intended=unary_union([ss for ss in p.hubs.components(intended) if ss.intersection(core).area>0])
                                    physical=set_precision(intended.difference(holes).difference(Point(site).buffer(drill/2)),1e-6)
                                    sa=ann.intersection(physical).area;go=physical.intersection(goals[source_layer]).area
                                    if sa<=.005 or go<=.005:continue
                                    via=C.via('CORE-real-layer-barrel-r38-'+uid,target['net'],site);via.update(d=diameter,drill=drill)
                                    z={'uuid':C.uid('CORE-real-layer-source-bridge-r38-'+uid),'label':'CORE-real-layer-source-bridge-r38-'+uid,'net':target['net'],'layer':source_layer,'shape':physical,'zone_outline_shape':intended,'clearance_mm':.15,
                                        'route':{**route,'points':points,'length_mm':line.length,'minimum_core_width_mm':.20,'exact_quantized_core_free_containment':True}}
                                    answer={'via':via,'target_layer':target['layer'],'source_layer':source_layer,'target_plane_uuid':uid,'target_annular_overlap_mm2':ta,'source_bridge_annular_overlap_mm2':sa,'actual_source_bridge_Cu_overlap_mm2':go,'new_source_bridge_uuid':z['uuid'],'route':z['route'],'required_native_postfill_flash':[target['layer'],source_layer],'strong_hole_SMD_and_drill_edge_guard_mm':.275,'all_layer_foreign_Cu_and_reservation_guard_mm':.025,'original_incorrect_goal_endpoint':anchor,'target_current_and_unequal_barrel_share':'OPEN'}
                                    newzones.append(z);break
                                if answer:break
                            if answer:break
                        if answer:break
                    if answer:break
                if answer:break
        assert answer is not None,('ordinary_real_cross_layer_source_site_and_bridge_unresolved',uid,anchor)''')
rep("assert len(newvias)==2;h['vias']+=newvias","assert len(newvias)==2;h['vias']+=newvias;zones+=newzones")
rep("known=set(binding['restored_generated_grid_UUIDs'])|{q['zone_uuid'] for q in carves}","known=set(binding['restored_generated_grid_UUIDs'])|{q['zone_uuid'] for q in carves}|{q['uuid'] for q in newzones}")
rep("'new_zone_shapes':0","'new_zone_shapes':len(newzones)")
(HERE/'bridge_actual_core_source_layers_r38.py').write_text(s);compile(s,'r38','exec');print('R38_DERIVED_SYNTAX_PASS')
