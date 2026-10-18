"""Derive a versioned continuation of the preserved R28 CORE constructor."""
from pathlib import Path
HERE=Path(__file__).parent
s=(HERE/'construct_core_inner_feeds_r28.py').read_text()
def rep(a,b):
    global s
    assert s.count(a)==1,(a[:100],s.count(a));s=s.replace(a,b)
rep('import continuous_path_prepared_r1 as CP','import continuous_path_prepared_r2 as CP')
rep("OUT=L.OUT/'core-inner-feed-r28'","OUT=L.OUT/'core-inner-feed-r33'")
a=s.index("    prior_model=Path(sys.argv[1])")
b=s.index('    Q.NET=NET;groups',a)
s=s[:a]+'''    prior_model=Path(sys.argv[1]) if len(sys.argv)>1 else L.OUT/'five-core-and-b5-checkpoint-r32/model.pkl'
    assert prior_model.exists(),'Accepted five-feed + B5 checkpoint is required'
    g,h,binding,zones,candidate=pickle.loads(prior_model.read_bytes())
    assert binding['accepted_CORE_feed_count']==5
    assert binding['latest_field_R25_exact_owned_25via_108segment_comparison'] is True
    binding['reused_five_CORE_and_B5_model_file']=str(prior_model.resolve())
    binding['reused_five_CORE_and_B5_model_sha256']=sha(prior_model)
    for q in zones:
        if q['uuid'] in binding['restored_generated_grid_UUIDs']:q['shape']=set_precision(q['shape'],1e-6)
''' + s[b:]
rep("    outline=unary_union(p.base.polygons(g['outline'])).buffer(-.525)","    write(OUT/'initial-islands.json',{'source_group':root,'targets':[{'group':i,'pads':[q for q in groups[i] if not q['ref'].startswith('@')]} for i in targets],'binding':binding})\n    outline=unary_union(p.base.polygons(g['outline'])).buffer(-.525)")
rep("    for l in ('In2.Cu','In3.Cu','In1.Cu','In4.Cu','F.Cu','B.Cu'):\n        f=L.OUT/'core-inner-feed-r26'/(l+'-free.wkb');assert f.exists();frees[l]=set_precision(from_wkb(f.read_bytes()),1e-6)","""    b5=field/'b5-source-rooted-feeds-r4'
    b5ds=pickle.loads((b5/'proposed-discrete.pkl').read_bytes());b5zs=pickle.loads((b5/'proposed-zones.pkl').read_bytes())
    for l in ('In2.Cu','In3.Cu','In1.Cu','In4.Cu','F.Cu','B.Cu'):
        f=L.OUT/'core-inner-feed-r28'/(l+'-free.wkb');assert f.exists();frees[l]=set_precision(from_wkb(f.read_bytes()),1e-6)
        extra=[q['shape'].buffer(max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025) for q in b5zs if q['layer']==l]
        extra += [Point(v['x'],v['y']).buffer(max(v['drill']/2+.275,v['d']/2+gap(v['net'])+.025)) for v in b5ds['vias']]
        extra += [p.base.body(t).buffer(gap(t['net'])+.025) for t in b5ds['tracks'] if t['layer']==l]
        frees[l]=set_precision(frees[l].difference(unary_union(extra)),1e-6)""")
rep("'actual_geometric_model':'r25 accepted two-feed checkpoint plus exact field R23; same physical Cu/new planes/reservations and old-fill reallocation policy'","'actual_geometric_model':'preserved R28 free mask + exact B5 R4 obstacles; all five accepted CORE feeds/source-rooted parts retained'")
rep("obs += [drills[int(i)].buffer(.575) for i in dt.query(win.buffer(1),predicate='intersects')]","obs += [drills[int(i)].buffer(.15+.275) for i in dt.query(win.buffer(1),predicate='intersects')]")
rep("obs += [Point(v['x'],v['y']).buffer(.8) for v in newvias]","obs += [Point(v['x'],v['y']).buffer(v['drill']/2+.15+.275) for v in newvias]")
rep("    def innerbridge(site):","""    safe_cache={};goal_component_cache={};prefilter={'rejected_layer_sites':0,'tested_layer_sites':0}
    def safe_components(layer,width):
        key=(layer,width)
        if key not in safe_cache:
            comps=p.hubs.components(set_precision(frees[layer].buffer(-width/2-.01),1e-6))
            safe_cache[key]=(comps,STRtree(comps));print('CORE_SAFE_COMPONENTS',layer,width,len(comps),flush=True)
        return safe_cache[key]
    def source_safe_ids(layer,width):
        key=(layer,width,len(newzones))
        if key not in goal_component_cache:
            _,tree=safe_components(layer,width)
            goal_component_cache[key]={int(i) for i in tree.query(sources[layer],predicate='intersects')}
        return goal_component_cache[key]
    def innerbridge(site):""")
rep("            a,b=nearest_points(disk,goal);options.append((a.distance(b),l,a,b))","""            _,tree=safe_components(l,.20)
            prefilter['tested_layer_sites']+=1
            if not ({int(i) for i in tree.query(ann,predicate='intersects')} & source_safe_ids(l,.20)):
                prefilter['rejected_layer_sites']+=1;continue
            a,b=nearest_points(disk,goal);options.append((a.distance(b),l,a,b))""")
rep("win=box(min(a.x,b.x)-margin,min(a.y,b.y)-margin,max(a.x,b.x)+margin,max(a.y,b.y)+margin);usable=frees[l].intersection(win)\n                for width in (1.25,1.,.75,.5,.35):\n                    for comp in p.hubs.components(set_precision(usable.buffer(-width/2-.01),1e-6)):","""win=box(min(a.x,b.x)-margin,min(a.y,b.y)-margin,max(a.x,b.x)+margin,max(a.y,b.y)+margin)
                for width in (1.25,1.,.75,.5,.35,.25,.20):
                    allcomps,tree=safe_components(l,width)
                    ids={int(i) for i in tree.query(ann,predicate='intersects')} & source_safe_ids(l,width)
                    for comp in [c for ii in ids for c in p.hubs.components(allcomps[ii].intersection(win))]:""")
s=s.replace('CORE-island-r26-','CORE-island-r33-')
rep("write(OUT/'checkpoint.json',{'rows':rows,'remaining':missing,'carves':carveledger,'native_jobs':0,'board_written':False})","write(OUT/'checkpoint.json',{'rows':rows,'remaining':missing,'carves':carveledger,'global_safe_connectivity_prefilter':prefilter,'native_jobs':0,'board_written':False})")
rep("'source':'R11022.2','rows':rows","'source':'R11022.2','global_safe_connectivity_prefilter':prefilter,'drill_site_obstacle_rule':'actual existing hole shape buffered by new radius .15 + drill-edge guard .275; previous .575 buffer double-counted .15 existing radius','rows':rows")
(HERE/'construct_core_inner_feeds_r33.py').write_text(s)
compile(s,str(HERE/'construct_core_inner_feeds_r33.py'),'exec')
print('DERIVED_R33_SYNTAX_PASS')
