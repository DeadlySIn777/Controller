"""Versioned continuation with exact R47 geometry and later hard nominees."""
from pathlib import Path
HERE=Path(__file__).parent
s=(HERE/'construct_core_inner_feeds_r33.py').read_text()
def rep(a,b):
    global s
    assert s.count(a)==1,(a[:100],s.count(a));s=s.replace(a,b)
rep("OUT=L.OUT/'core-inner-feed-r33'","OUT=L.OUT/'remaining-core-feeds-r48'")
rep('import continuous_path_prepared_r2 as CP','import continuous_path_prepared_r2 as CP\nimport guarded_power_projection_r44 as GP\nP=GP')
rep('G=I.G;P=I.P;Q=I.Q;C=I.C;L=I.L;p=I.p;R=I.R;NET=I.NET;LAYERS=I.LAYERS','G=I.G;Q=I.Q;C=I.C;L=I.L;p=I.p;R=I.R;NET=I.NET;LAYERS=I.LAYERS')
a=s.index('    prior_model=Path(sys.argv[1])');b=s.index('    Q.NET=NET;groups',a)
s=s[:a]+'''    prior_model=Path(sys.argv[1]) if len(sys.argv)>1 else L.OUT/'io3-u15-logic-guarded-model-r47/model.pkl'
    g,h,binding,zones,candidate=pickle.loads(prior_model.read_bytes())
    binding['remaining_CORE_search_parent_model']={'file':str(prior_model.resolve()),'sha256':sha(prior_model)}
    for q in zones:
        if q['uuid'] in binding['restored_generated_grid_UUIDs']:
            q['shape']=set_precision(q['shape'],1e-6)
            if 'zone_outline_shape' in q:q['zone_outline_shape']=set_precision(q['zone_outline_shape'],1e-6)
    # Later proposed source objects are hard obstacles only, never source
    # graph credit or silently appended native items in this continuation.
    rootdir=L.OUT.parent/'protected24-dogbones-r7'
    excluded={'32d1ff6d-3134-5587-b14c-e0fe8f143896','61bc227f-53f6-5ca5-98d2-ed53fdf555b0','2cffa505-7280-5065-aee5-167fd8d5db6b','152342e5-2634-56f0-b6a9-0520deb780d2'}
    rd=pickle.loads((rootdir/'proposed-discrete.pkl').read_bytes());rz=[z for z in pickle.loads((rootdir/'proposed-zones.pkl').read_bytes()) if z['uuid'] not in excluded]
    regdir=field/'regulated-field-source-feeds-r41';regd=pickle.loads((regdir/'proposed-discrete.pkl').read_bytes());regz=[z for z in pickle.loads((regdir/'proposed-zones.pkl').read_bytes()) if z['uuid'] not in {'bbcf660b-c137-5ec9-a1f7-bd36f0026bbd','f29de42f-2910-514b-bb6b-e86ec01a2bd8'}]
    hard_ds={'vias':rd['vias']+regd['vias'],'tracks':rd['tracks']+regd['tracks']};search_zones=zones+rz+regz
    binding['later_foreign_proposals_hard_only']={'protected_R7_discrete_sha256':sha(rootdir/'proposed-discrete.pkl'),'protected_R7_six_planes_from_sha256':sha(rootdir/'proposed-zones.pkl'),
        'protected_R9_four_unknown_planes_not_yet_screened':sorted(excluded),'field_regulated_R41_discrete_sha256':sha(regdir/'proposed-discrete.pkl'),'field_regulated_R41_zones_sha256':sha(regdir/'proposed-zones.pkl'),
        'all_later_final_mutual_reprojection_and_source_contacts_required':True}
''' +s[b:]
rep("viahard=[s.buffer(.325) for l in LAYERS for s in p.hard_shapes(hardmodel,areas,NET,l,for_via=True)]","viahard=[s for l in LAYERS for s in p.hard_shapes(hardmodel,areas,NET,l,for_via=True)]")
rep("    for q in h['tracks']:rec[q['layer']].append", "    for q in h['tracks']+hard_ds['tracks']:rec[q['layer']].append")
rep("    for q in h['vias']:\n        pt=Point", "    for q in h['vias']+hard_ds['vias']:\n        pt=Point")
a=s.index('    fixed_via_masks=');b=s.index('    newvias=[]',a)
s=s[:a]+'''    fixed_via_cache={}
    frees={};sources={}
    base_bykind={kind:{q['uuid']:q for q in g[kind]} for kind in ('pads','tracks','vias')}
    delta_ids=GP.changed_ids(g,h)|{q['uuid'] for kind in ('vias','tracks') for q in hard_ds[kind]}
    binding['original_fill_reallocation_policy']={'all_native_parent_Cu':'exact g/h delta plus all later hard nominees is subtracted from preserved free masks; complete all-native geometry gate remains mandatory',
        'new_ordinary_via_antipads':'outward-bound explicit new main field return carves, all original fill contact obligations retained',
        'inner_spokes':'all proposed foreign planes including known protected/regulated are hard; original non-GND supply fills retained'}
    for l in ('In2.Cu','In3.Cu','In1.Cu','In4.Cu','F.Cu','B.Cu'):
        f=L.OUT/'core-inner-feed-r28'/(l+'-free.wkb');assert f.exists();frees[l]=set_precision(from_wkb(f.read_bytes()),1e-6)
        extra=[GP.bounded_buffer(q['shape'],max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025) for q in search_zones if q['layer']==l and p.norm(q['net'])!=NET]
        extra += [GP.bounded_buffer(q['shape'],gap(q['net'])+.025) for q in rec[l] if q['uuid'] in delta_ids and p.norm(q['net'])!=NET]
        extra += [GP.bounded_disk(v,max(v['drill']/2+.275,v['d']/2+gap(v['net'])+.025)) for v in h['vias']+hard_ds['vias'] if v['uuid'] in delta_ids and p.norm(v['net'])!=NET]
        frees[l]=set_precision(frees[l].difference(unary_union(extra)),1e-6)
        binding.setdefault('remaining_CORE_corrected_free_masks',[]).append({'file':str(f.resolve()),'sha256':sha(f),'later_foreign_hard_body_count':len(extra),'all_native_g_h_delta_and_later_nominees_hard':True})
        sources[l]=unary_union([s for s,j in zip(parts[l],assign[l]) if j==root]);(OUT/(l+'-free.wkb')).write_bytes(frees[l].wkb);print('CORE_INNER_FREE',l,frees[l].area,'source',sources[l].area,flush=True)
''' +s[b:]
rep('    def region(win):','    def region(win,diameter,drill):')
rep("q['shape'].buffer(.3+gap(q['net'])+.025)","GP.bounded_buffer(q['shape'],diameter/2+gap(q['net'])+.025)")
rep('smd[int(i)].buffer(.425)','GP.bounded_buffer(smd[int(i)],drill/2+.275)')
rep('drills[int(i)].buffer(.15+.275)','GP.bounded_buffer(drills[int(i)],drill/2+.275)')
rep('viahard[int(i)] for i in vh.query(win,predicate=\'intersects\')','GP.bounded_buffer(viahard[int(i)],diameter/2+.025) for i in vh.query(win.buffer(1),predicate=\'intersects\')')
rep("        obs += [fixed_via_masks[int(i)].intersection(win) for i in fixed_via_tree.query(win,predicate='intersects')]","""        if diameter not in fixed_via_cache:
            masks=[GP.bounded_buffer(q['shape'],diameter/2+max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025) for q in search_zones if p.norm(q['net'])!=NET and q['uuid'] not in carvable]
            fixed_via_cache[diameter]=(masks,STRtree(masks))
        masks,mt=fixed_via_cache[diameter]
        obs += [masks[int(i)].intersection(win) for i in mt.query(win,predicate='intersects')]""")
rep("Point(v['x'],v['y']).buffer(v['drill']/2+.15+.275) for v in newvias","GP.bounded_disk(v,v['drill']/2+drill/2+.275) for v in newvias")
rep('    def innerbridge(site):\n        cachekey=(site,len(newzones))','    def innerbridge(site,diameter,drill):\n        cachekey=(site,diameter,drill,len(newzones))')
rep('disk=Point(site).buffer(.3);ann=disk.difference(Point(site).buffer(.15));options=[]','disk=Point(site).buffer(diameter/2);ann=disk.difference(Point(site).buffer(drill/2));options=[]')
rep("        for _,outer,shape in sorted(options,key=lambda q:q[0])[:20]:\n            win=box(shape.bounds[0]-5,shape.bounds[1]-5,shape.bounds[2]+5,shape.bounds[3]+5);legal=region(win)","""        for diameter,drill,_,outer,shape in [(d,dr,dis,l,sh) for dis,l,sh in sorted(options,key=lambda q:q[0])[:20] for d,dr in ((.5,.2),(.6,.3))]:
            win=box(shape.bounds[0]-5,shape.bounds[1]-5,shape.bounds[2]+5,shape.bounds[3]+5);legal=region(win,diameter,drill)""")
rep('disk=Point(site).buffer(.3)\n                for width','disk=Point(site).buffer(diameter/2)\n                for width')
rep('il,body,inner=innerbridge(site)','il,body,inner=innerbridge(site,diameter,drill)')
rep("v=C.via('CORE-island-r33-'+str(gi),sp['net'],site);ts=", "v=C.via('CORE-island-r48-'+str(gi),sp['net'],site);v.update(d=diameter,drill=drill);ts=")
s=s.replace('CORE-island-r33-','CORE-island-r48-')
rep("z={'uuid':C.uid('CORE-island-r48-'+str(gi)+'-plane'),'label':'CORE-island-r48-'+str(gi)+'-plane','net':sp['net'],'layer':il,'shape':set_precision(body,1e-6),'route':inner,'clearance_mm':.15};newzones.append(z);sources[il]=unary_union([sources[il],z['shape']])", """allholes=unary_union(drills+[Point(vv['x'],vv['y']).buffer(vv['drill']/2) for vv in newvias])
                        physical=set_precision(body.difference(allholes),1e-6)
                        z={'uuid':C.uid('CORE-island-r48-'+str(gi)+'-plane'),'label':'CORE-island-r48-'+str(gi)+'-plane','net':sp['net'],'layer':il,'shape':physical,'zone_outline_shape':set_precision(body,1e-6),'route':inner,'clearance_mm':.15};newzones.append(z);sources[il]=unary_union([sources[il],z['shape']])""")
rep("cutter=set_precision(Point(site).buffer(.3+max(gap(z['net']),float(z.get('clearance_mm',.15)))+.025),1e-6)","cutter=GP.bounded_disk(v,max(drill/2+.275,diameter/2+max(gap(z['net']),float(z.get('clearance_mm',.15)))+.025))")
rep("z['shape']=new\n                    joined.add", "z['shape']=new\n                        if 'zone_outline_shape' in z:z['zone_outline_shape']=set_precision(set_precision(z['zone_outline_shape'],1e-6).difference(cutter),1e-6)\n                    joined.add")
rep("        write(OUT/'checkpoint.json'", "        binding['restored_generated_grid_UUIDs']=sorted(set(binding.get('restored_generated_grid_UUIDs',[]))|{q['uuid'] for q in newzones}|{q['zone_uuid'] for q in carveledger})\n        write(OUT/'checkpoint.json'")
rep("hh={**h,'vias':h['vias']+newvias,'tracks':h['tracks']+newtracks};final,cuts=P.projected(g,hh,zones+newzones)","hh={**h,'vias':h['vias']+newvias,'tracks':h['tracks']+newtracks};final,cuts=P.projected(g,hh,zones+newzones)")
# Persist each accepted branch model before further searches, without making
# accepted route-count claims equivalent to complete projected source joins.
rep("write(OUT/'checkpoint.json',{'rows':rows,'remaining':missing,'carves':carveledger,'global_safe_connectivity_prefilter':prefilter,'native_jobs':0,'board_written':False});", "write(OUT/'checkpoint.json',{'rows':rows,'remaining':missing,'carves':carveledger,'global_safe_connectivity_prefilter':prefilter,'native_jobs':0,'board_written':False});(OUT/'accepted-checkpoint-model.pkl').write_bytes(pickle.dumps((g,{**h,'vias':h['vias']+newvias,'tracks':h['tracks']+newtracks},binding,zones+newzones,None),protocol=5));")
assert 'for distance,l,a,b in sorted(options,key=lambda x:x[0]):\n            goal=sources[l]' in s
file=HERE/'construct_remaining_core_feeds_r48.py';file.write_text(s);compile(s,str(file),'exec');print('R48_VERSIONED_DERIVATION_SYNTAX_PASS')
