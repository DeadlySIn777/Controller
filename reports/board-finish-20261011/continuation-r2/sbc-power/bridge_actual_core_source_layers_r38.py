"""Give two preserved feeder endpoints real ordinary cross-layer barrels.

All previous Cu is retained. No source contact is credited across layers
without an explicit legal ordinary via and actual target/source annular Cu.
"""
import copy,json,pickle,hashlib,math
from pathlib import Path
from shapely import set_precision,STRtree
from shapely.geometry import Point,box,LineString
from shapely.ops import unary_union,nearest_points
import core_inner_feed_r18 as I
import continuous_path_prepared_r2 as CP
L=I.L;p=I.p;P=I.P;Q=I.Q;C=I.C;G=I.G;NET=I.NET;LAYERS=I.LAYERS
OUT=L.OUT/'actual-core-cross-layer-source-bridge-r38'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir();prior=L.OUT/'five-core-and-b5-checkpoint-r32/model.pkl'
    assert sha(prior)=='8bd79b8233520e02aaf4c4c4988076ec45543d3639d75f20e2cdc0156307678b'
    g,h,binding,zones,_=pickle.loads(prior.read_bytes());h=copy.deepcopy(h)
    audit=L.OUT/'five-core-attachment-diagnostic-r34';ar=json.loads((audit/'receipt.json').read_text());assert ar['model_sha256']==sha(prior)
    cache=pickle.loads((audit/'groups.pkl').read_bytes());parts=cache['parts'];assign=cache['assign'];root=ar['source_group']
    outline=unary_union(p.base.polygons(g['outline'])).buffer(-.525);p.WINDOW=box(.526,.526,449.474,234.474)
    areas=L.live.reservations();domain=h['domains_normalized'][NET]
    def gap(n):return G.gap(h,NET,n)
    hardmodel={**h,'zones':[dict(q,layers=[l for l in q['layers'] if l!='In3.Cu']) if p.norm(q['net'])=='/CORE_1V2' else q for q in h['zones']]}
    hard=[s for l in LAYERS for s in p.hard_shapes(hardmodel,areas,NET,l,for_via=True)]
    rec=[];smd=[];drills=[];ownholes=[]
    for q in h['pads']:
        for layer,rs in q['layers'].items():
            for s in p.base.polygons(rs):
                if p.norm(q['net'])!=NET:rec.append({'uuid':q['uuid'],'net':q['net'],'layer':layer,'shape':s})
                if q['smd']:smd.append(s)
        hh=p.base.polygons(q.get('hole') or []);drills+=hh
        if p.norm(q['net'])==NET:ownholes+=hh
    for t in h['tracks']:
        if p.norm(t['net'])!=NET:rec.append({'uuid':t['uuid'],'net':t['net'],'layer':t['layer'],'shape':p.base.body(t)})
    for v in h['vias']:
        pt=Point(v['x'],v['y']);hole=pt.buffer(v['drill']/2);drills.append(hole)
        if p.norm(v['net'])==NET:ownholes.append(hole)
        else:
            for layer in v['flashed']:rec.append({'uuid':v['uuid'],'net':v['net'],'layer':layer,'shape':pt.buffer(v['d']/2)})
    for q in h['shapes']:
        if q['layer'] in LAYERS and p.norm(q['net'])!=NET:
            for s in p.base.polygons(q['poly']):rec.append({'uuid':q['uuid'],'net':q['net'],'layer':q['layer'],'shape':s})
    tree=STRtree([q['shape'] for q in rec]);st=STRtree(smd);dt=STRtree(drills);ht=STRtree(hard);holes=unary_union(ownholes)
    goals={layer:unary_union([s for s,j in zip(parts[layer],assign[layer]) if j==root]).difference(holes) for layer in LAYERS}
    carvable={q['uuid'] for q in zones if q.get('field_return_proposal')};rows=[];carves=[];newvias=[];newzones=[];safe_cache={}
    def legal_region(win,diameter,drill):
        obs=[rec[int(i)]['shape'].buffer(diameter/2+gap(rec[int(i)]['net'])+.025) for i in tree.query(win.buffer(2),predicate='intersects')]
        obs += [smd[int(i)].buffer(drill/2+.275) for i in st.query(win.buffer(1),predicate='intersects')]
        obs += [drills[int(i)].buffer(drill/2+.275) for i in dt.query(win.buffer(1),predicate='intersects')]
        obs += [hard[int(i)].buffer(diameter/2+.025) for i in ht.query(win.buffer(1),predicate='intersects')]
        obs += [z['shape'].buffer(diameter/2+max(gap(z['net']),float(z.get('clearance_mm',.15)))+.025) for z in zones if p.norm(z['net'])!=NET and z['uuid'] not in carvable and z['shape'].intersects(win.buffer(2))]
        obs += [Point(v['x'],v['y']).buffer(v['drill']/2+drill/2+.275) for v in newvias]
        return set_precision(win.intersection(outline).difference(unary_union(obs)),1e-6)
    for row in ar['rows']:
        if row['all_target_pads_source_connected']:continue
        uid=row['attached_proposed_inner_planes'][0]['uuid'];target=next(q for q in zones if q['uuid']==uid);anchor=next(q['xy'] for q in row['endpoints'] if q['name']=='inner_end');answer=None
        for source_layer in ('In4.Cu','In1.Cu','In2.Cu','In3.Cu'):
            if source_layer==target['layer']:continue
            both=target['shape'].intersection(goals[source_layer])
            if both.is_empty:continue
            for margin in (4.,10.,25.):
                win=box(anchor[0]-margin,anchor[1]-margin,anchor[0]+margin,anchor[1]+margin)
                for diameter,drill in ((.6,.3),(.5,.2)):
                    legal=legal_region(win,diameter,drill);landing=legal.buffer(-.01).intersection(both.buffer(-.005))
                    if landing.is_empty:continue
                    candidates=[]
                    for s in p.hubs.components(landing):
                        candidates += [s.representative_point().coords[0],nearest_points(Point(anchor),s.buffer(-.005))[1].coords[0]] if not s.buffer(-.005).is_empty else [s.representative_point().coords[0]]
                    for xy in sorted(candidates,key=lambda xy:Point(xy).distance(Point(anchor))):
                        site=tuple(round(v,6) for v in xy)
                        if not legal.covers(Point(site)):continue
                        ann=Point(site).buffer(diameter/2).difference(Point(site).buffer(drill/2))
                        ta=ann.intersection(target['shape']).area;sa=ann.intersection(goals[source_layer]).area
                        if ta<=.005 or sa<=.005:continue
                        via=C.via('CORE-real-layer-barrel-r38-'+uid,target['net'],site);via.update(d=diameter,drill=drill)
                        answer={'via':via,'target_layer':target['layer'],'source_layer':source_layer,'target_plane_uuid':uid,'target_annular_overlap_mm2':ta,'actual_source_annular_overlap_mm2':sa,'required_native_postfill_flash':[target['layer'],source_layer],'strong_hole_SMD_and_drill_edge_guard_mm':.275,'all_layer_foreign_Cu_and_reservation_guard_mm':.025,'original_incorrect_goal_endpoint':anchor,'target_current_and_unequal_barrel_share':'OPEN'};break
                    if answer:break
                if answer:break
            if answer:break
        if answer is None:
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
        assert answer is not None,('ordinary_real_cross_layer_source_site_and_bridge_unresolved',uid,anchor)
        via=answer['via'];site=(via['x'],via['y']);newvias.append(via)
        for z in zones:
            if z['uuid'] not in carvable or p.norm(z['net'])==NET:continue
            cutter=set_precision(Point(site).buffer(max(via['drill']/2+.275,via['d']/2+max(gap(z['net']),float(z.get('clearance_mm',.15)))+.025)),1e-6)
            old=z['shape'];new=set_precision(set_precision(old,1e-6).difference(cutter),1e-6)
            if old.equals(new):continue
            base=OUT/(z['uuid']+'-'+via['uuid']);paths={}
            for key,shape in (('old',old),('new',new),('cutter',cutter)):
                f=base.with_name(base.name+'-'+key+'.wkb');f.write_bytes(shape.wkb);paths[key+'_wkb_file']=str(f.resolve());paths[key+'_wkb_sha256']=sha(f)
            carves.append({'zone_uuid':z['uuid'],'layer':z['layer'],'net_raw':z['net'],'via_uuid':via['uuid'],**paths,
                'removed_area_mm2':old.difference(new).area,'added_quantization_area_mm2':new.difference(old).area,
                'operation':'set_precision(old,1e-6).difference(set_precision(circle,1e-6)); final set_precision(1e-6)'});z['shape']=new
        rows.append(answer);(OUT/'checkpoint.json').write_text(json.dumps({'rows':rows,'carves':carves},indent=2)+'\n')
        (OUT/'proposed-vias.pkl').write_bytes(pickle.dumps(newvias,protocol=5));print('CORE_REAL_LAYER_SOURCE_BARREL',uid,via['uuid'],site,via['d'],via['drill'],answer['target_layer'],answer['source_layer'],flush=True)
    assert len(newvias)==2;h['vias']+=newvias;zones+=newzones
    known=set(binding['restored_generated_grid_UUIDs'])|{q['zone_uuid'] for q in carves}|{q['uuid'] for q in newzones}
    for q in zones:
        if q['uuid'] in known:q['shape']=set_precision(q['shape'],1e-6)
    candidate,cuts=P.projected(g,h,zones);Q.NET=NET;after,aparts,aassign=Q.groups(candidate,return_details=True)
    ids={q['uuid']:i for i,rr in enumerate(after) for q in rr};sp=next(q for q in h['pads'] if (q['ref'],q['num'])==('R11022','2'));sr=ids[sp['uuid']]
    checks=[]
    for r in ar['rows']:
        pp=[{**q,'final_group':ids[q['uuid']],'source_connected':ids[q['uuid']]==sr} for q in r['target_physical_pads']]
        checks.append({'via_uuid':r['via']['uuid'],'pads':pp,'all_target_pads_source_connected':all(q['source_connected'] for q in pp)})
    assert all(q['all_target_pads_source_connected'] for q in checks),'Every preserved feeder must pass actual full source graph'
    binding.update({'five_CORE_attachment_diagnostic_receipt_sha256':sha(audit/'receipt.json'),'actual_cross_layer_source_barrel_rows':rows,
        'actual_cross_layer_source_field_antipad_carves':carves,'all_five_preserved_target_groups_source_connected_host':True,
        'restored_generated_grid_UUIDs':sorted(known),'scoped_planner_fix':'chosen layer must reload its own source goal; real barrels explicitly bridge the two preserved wrong-layer endpoints'})
    model=OUT/'model.pkl';model.write_bytes(pickle.dumps((g,h,binding,zones,candidate),protocol=5))
    (OUT/'groups.pkl').write_bytes(pickle.dumps({'groups':after,'parts':aparts,'assign':aassign},protocol=5))
    receipt={'verdict':'PASS_FIVE_PRESERVED_CORE_TARGETS_AFTER_REAL_SOURCE_BARRELS_FULL_CONTACT_CURRENT_NATIVE_PENDING','model_sha256':sha(model),
        'parent_model_sha256':sha(prior),'binding':binding,'rows':rows,'field_main_return_antipads':carves,'five_feed_target_checks':checks,
        'remaining_CORE_named_groups':[{'group':i,'pads':[q for q in rr if not q['ref'].startswith('@')]} for i,rr in enumerate(after) if i!=sr and any(not q['ref'].startswith('@') for q in rr)],
        'old_fill_retreats':cuts,'new_vias':2,'new_segments':0,'new_zone_shapes':len(newzones),'all_original_contact_foreign_mutual_current_native_gates':'OPEN','native_jobs':0,'board_written':False}
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('CORE_REAL_LAYER_BARRELS_SOURCE_PASS',sha(model),len(receipt['remaining_CORE_named_groups']),flush=True)
if __name__=='__main__':main()
