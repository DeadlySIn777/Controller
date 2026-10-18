"""Concrete ordinary-via supply feeds, exact discrete geometry and local carves.

The inherited CORE_1V2 whole-outline In3 planning mask is excluded here: it is
not a native keepout. Actual CORE_1V2 copper and source zone definitions remain
unchanged obstacles. Only nine proposed field main returns can acquire explicit
new-via antipads; all other new field/IO3/GND polygons remain hard obstacles.
"""
import copy,json,pickle,math,uuid,hashlib,sys
from pathlib import Path
from shapely import set_precision,STRtree,from_wkb
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
import core_inner_feed_r18 as I
import continuous_path_prepared_r1 as CP
G=I.G;P=I.P;Q=I.Q;C=I.C;L=I.L;p=I.p;R=I.R;NET=I.NET;LAYERS=I.LAYERS
OUT=L.OUT/'core-inner-feed-r28'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def write(f,v):f.write_text(json.dumps(v,indent=2)+'\n')
def main():
    assert not OUT.exists();OUT.mkdir();(OUT/'source-used.py').write_bytes(Path(__file__).read_bytes());field=I.FIELD
    prior_model=Path(sys.argv[1]) if len(sys.argv)>1 else L.OUT/'core-inner-feed-r24/model.pkl';assert prior_model.exists(),'Run r26 only after the accepted preceding geometry is frozen'
    g,h,binding,zones,candidate=pickle.loads(prior_model.read_bytes());binding['reused_CORE_r24_constructed_model_sha256']=sha(prior_model)
    field23=field/'remaining-field-ground-feeds-r23';field23receipt=field23/'receipt.json';assert sha(field23receipt)=='c7a120e6edf443c2aa6839b78d54673c6245de3a0312ce4757d9778f184fd3eb'
    field23r=json.loads(field23receipt.read_text());field23df=field23/'proposed-discrete.pkl';field23zf=field23/'proposed-zones.pkl';assert sha(field23df)==field23r['proposed_discrete_sha256'] and sha(field23zf)==field23r['proposed_zones_sha256']
    field23ds=pickle.loads(field23df.read_bytes());field23zs=pickle.loads(field23zf.read_bytes());assert len(field23ds['vias'])==2 and len(field23ds['tracks'])==6 and len(field23zs)==2
    for kind in ('vias','tracks'):
        assert not {q['uuid'] for q in h[kind]} & {q['uuid'] for q in field23ds[kind]};h[kind]+=field23ds[kind]
    assert not {q['uuid'] for q in zones} & {q['uuid'] for q in field23zs};zones+=field23zs
    binding['additional_field_R23']={'receipt_sha256':sha(field23receipt),'discrete_sha256':sha(field23df),'zones_sha256':sha(field23zf),'new_vias':2,'new_segments':6,'new_zones':2,'shape_is_actual_drill_subtracted_Cu':True,'zone_outline_shape_is_intended_native_outline':True,'all_mutual_native_and_current_gates':'OPEN'}
    candidate,_=P.projected(g,h,zones)
    prior_receipt=json.loads((prior_model.parent/'receipt.json').read_text());prior_carved={q['zone_uuid'] for q in prior_receipt['field_main_return_antipads']}
    for q in zones:
        if q['uuid'] in prior_carved or q.get('label','').startswith('CORE-island-r19-'):q['shape']=set_precision(q['shape'],1e-6)
    for q in zones:
        if q.get('old_contact_group') is not None or q.get('field_return_proposal') and q['layer']=='In2.Cu' or q.get('label')=='CORE-main-In2':q['shape']=set_precision(q['shape'],1e-6)
    Q.NET=NET;groups,parts,assign=Q.groups(candidate,return_details=True);lookup={q['uuid']:i for i,rows in enumerate(groups) for q in rows};sp=next(q for q in h['pads'] if (q['ref'],q['num'])==('R11022','2'));root=lookup[sp['uuid']];targets=[i for i,rows in enumerate(groups) if i!=root and any(not q['ref'].startswith('@') for q in rows)];targets.sort(key=lambda i:sum(not q['ref'].startswith('@') for q in groups[i]),reverse=True)
    outline=unary_union(p.base.polygons(g['outline'])).buffer(-.525);window=box(.526,.526,449.474,234.474);p.WINDOW=window;areas=L.live.reservations();domain=h['domains_normalized'][NET]
    def gap(other):return .15 if h['domains_normalized'].get(p.norm(other))==domain else .6
    # Ignore only the inherited non-native CORE1V2 outline reservation in a
    # planning copy. Retain the original actual copper, all native keepouts,
    # source reservation rules and barrier body clearances.
    hardmodel={**h,'zones':[dict(q,layers=[l for l in q['layers'] if l!='In3.Cu']) if p.norm(q['net'])=='/CORE_1V2' else q for q in h['zones']]}
    hard={l:p.hard_shapes(hardmodel,areas,NET,l) for l in LAYERS};viahard=[s.buffer(.325) for l in LAYERS for s in p.hard_shapes(hardmodel,areas,NET,l,for_via=True)]
    rec={l:[] for l in LAYERS};drills=[];innerdrills=[];smd=[]
    for q in h['pads']:
        for l,rs in q['layers'].items():
            for s in p.base.polygons(rs):
                rec[l].append({'uuid':q['uuid'],'net':q['net'],'shape':s,'kind':'pad'})
                if q['smd']:smd.append(s)
        holes=p.base.polygons(q.get('hole') or []);drills+=holes
        if p.norm(q['net'])!=NET:innerdrills+=holes
    for q in h['tracks']:rec[q['layer']].append({'uuid':q['uuid'],'net':q['net'],'shape':p.base.body(q),'kind':'track'})
    for q in h['vias']:
        pt=Point(q['x'],q['y']);hole=pt.buffer(q['drill']/2);drills.append(hole)
        if p.norm(q['net'])!=NET:innerdrills.append(hole)
        for l in q['flashed']:rec[l].append({'uuid':q['uuid'],'net':q['net'],'shape':pt.buffer(q['d']/2),'kind':'via'})
    for q in h['shapes']:
        if q['layer'] in rec:
            for s in p.base.polygons(q['poly']):rec[q['layer']].append({'uuid':q['uuid'],'net':q['net'],'shape':s,'kind':'graphic'})
    trees={l:STRtree([q['shape'] for q in rows]) for l,rows in rec.items()};dt=STRtree(drills);st=STRtree(smd);vh=STRtree(viahard)
    originalids={q['uuid'] for q in g['zones']};oldforeign=[]
    for q in candidate['zones']:
        if q['uuid'] in originalids and h['domains_normalized'].get(p.norm(q['net']))!=domain:
            oldforeign += [s.buffer(.3+max(.6,float(q['clearance_mm']))+.025) for rs in q['fills'].values() for s in p.base.polygons(rs)]
    oft=STRtree(oldforeign);carvable={q['uuid'] for q in zones if q.get('field_return_proposal')};carveledger=[]
    fixed_via_masks=[q['shape'].buffer(.3+max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025) for q in zones if p.norm(q['net'])!=NET and q['uuid'] not in carvable]
    fixed_via_tree=STRtree(fixed_via_masks)
    frees={};sources={}
    binding['original_fill_reallocation_policy']={'new_ordinary_via_antipads':'Explicit all-domain original filled-Cu retreats; original design outlines/settings unchanged; all retained physical/source contacts mandatory','short_outer_stubs':'All original fills may retreat; all foreign physical Cu, holes, native/source reservations and every new local return/IO3 polygon remain hard','inner_spokes':'Original non-GND fills remain fixed; source/cap bodies and field main proposals retained except explicitly ledgered new-via antipads'}
    for l in ('In2.Cu','In3.Cu','In1.Cu','In4.Cu','F.Cu','B.Cu'):
        f=L.OUT/'core-inner-feed-r26'/(l+'-free.wkb');assert f.exists();frees[l]=set_precision(from_wkb(f.read_bytes()),1e-6)
        binding.setdefault('reused_corrected_field_free_masks',[]).append({'file':str(f.resolve()),'sha256':sha(f),'actual_geometric_model':'r25 accepted two-feed checkpoint plus exact field R23; same physical Cu/new planes/reservations and old-fill reallocation policy'})
        sources[l]=unary_union([s for s,j in zip(parts[l],assign[l]) if j==root]);(OUT/(l+'-free.wkb')).write_bytes(frees[l].wkb);print('CORE_INNER_FREE',l,frees[l].area,'source',sources[l].area,flush=True)
    newvias=[];newtracks=[];newzones=[];rows=[];missing=[];joined={root};inner_cache={}
    def region(win):
        obs=[]
        for l in LAYERS:
            for ii in trees[l].query(win.buffer(2),predicate='intersects'):
                q=rec[l][int(ii)]
                if p.norm(q['net'])!=NET:obs.append(q['shape'].buffer(.3+gap(q['net'])+.025))
        obs += [smd[int(i)].buffer(.425) for i in st.query(win.buffer(1),predicate='intersects')]
        obs += [drills[int(i)].buffer(.575) for i in dt.query(win.buffer(1),predicate='intersects')]
        obs += [viahard[int(i)] for i in vh.query(win,predicate='intersects')]
        # Original foreign fills receive normal automatic antipads in the
        # strict P.projected ledger; physical foreign Cu still remains hard.
        obs += [fixed_via_masks[int(i)].intersection(win) for i in fixed_via_tree.query(win,predicate='intersects')]
        obs += [Point(v['x'],v['y']).buffer(.8) for v in newvias]
        return set_precision(win.intersection(outline.buffer(-.3)).difference(unary_union(obs)),1e-6)
    def localfree(layer,win):
        obs=[]
        for ii in trees[layer].query(win.buffer(2),predicate='intersects'):
            q=rec[layer][int(ii)]
            if p.norm(q['net'])!=NET:obs.append(q['shape'].buffer(gap(q['net'])+.025))
        obs += [drills[int(i)].buffer(.275) for i in dt.query(win.buffer(1),predicate='intersects')]
        obs += [s.buffer(.025) for s in hard[layer] if s.intersects(win.buffer(1))]
        for q in candidate['zones']:
            if p.norm(q['net'])==NET or q['uuid'] in originalids and p.norm(q['net'])=='/LOGIC_GND':continue
            clear=max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025
            obs += [s.buffer(clear) for s in p.base.polygons(q['fills'].get(layer,[])) if s.intersects(win.buffer(1))]
        # Main field shapes are also fixed for the outer stub; only the via
        # annulus itself has an explicitly ledgered through-stack antipad.
        return set_precision(win.intersection(outline).difference(unary_union(obs)),1e-6)
    def innerbridge(site):
        cachekey=(site,len(newzones))
        if cachekey in inner_cache:return inner_cache[cachekey]
        disk=Point(site).buffer(.3);ann=disk.difference(Point(site).buffer(.15));options=[]
        for l in ('In2.Cu','In3.Cu','In1.Cu','In4.Cu'):
            goal=sources[l]
            if goal.is_empty:continue
            if ann.intersection(goal).area>.01:
                inner_cache[cachekey]=(l,None,None);return inner_cache[cachekey]
            a,b=nearest_points(disk,goal);options.append((a.distance(b),l,a,b))
        for distance,l,a,b in sorted(options,key=lambda x:x[0]):
            if distance>330:continue
            for margin in (8.,25.,70.,180.):
                win=box(min(a.x,b.x)-margin,min(a.y,b.y)-margin,max(a.x,b.x)+margin,max(a.y,b.y)+margin);usable=frees[l].intersection(win)
                for width in (1.25,1.,.75,.5,.35):
                    for comp in p.hubs.components(set_precision(usable.buffer(-width/2-.01),1e-6)):
                        aa=comp.intersection(ann);bb=comp.intersection(goal)
                        if aa.is_empty or bb.is_empty:continue
                        aa_inside=aa.buffer(-.005);bb_inside=bb.buffer(-.005)
                        if aa_inside.is_empty or bb_inside.is_empty:continue
                        ss,ee=nearest_points(aa_inside,bb_inside);start=tuple(round(v,6) for v in ss.coords[0]);end=tuple(round(v,6) for v in ee.coords[0])
                        if not comp.covers(Point(start)) or not comp.covers(Point(end)):continue
                        print('CORE_INNER_PATH_SEARCH',site,l,width,margin,comp.area,flush=True);route=CP.path(comp,start,end,node_cap=500000)
                        if route['verdict']!='HOST_PATH':
                            print('CORE_INNER_PATH_RESULT',site,l,width,margin,route['verdict'],flush=True);continue
                        points=[[round(x,6),round(y,6)] for x,y in route['points']];line=LineString(points);core=line.buffer(width/2)
                        if not frees[l].covers(core):continue
                        body=set_precision(line.buffer(2.).intersection(frees[l]),1e-6);body=unary_union([s for s in p.hubs.components(body) if s.intersection(core).area>0])
                        if body.intersection(ann).area<=.001 or body.intersection(goal).area<=1e-8:continue
                        inner_cache[cachekey]=(l,body,{**route,'points':points,'length_mm':line.length,'minimum_core_width_mm':width,'exact_quantized_core_free_containment':True});return inner_cache[cachekey]
        inner_cache[cachekey]=(None,None,None);return inner_cache[cachekey]
    for gi in targets:
        if gi in joined:continue
        answer=None;tries=0;legalcount=0;print('CORE_INNER_ISLAND',gi,flush=True)
        options=[];inner_source=unary_union([sources[l] for l in ('In2.Cu','In3.Cu','In1.Cu','In4.Cu')])
        for l in ('F.Cu','B.Cu'):
            for s,j in zip(parts[l],assign[l]):
                if j!=gi:continue
                near=nearest_points(s,inner_source)[0];anchors=[near,s.representative_point()]+[Point(q['at']) for q in groups[gi] if not q['ref'].startswith('@')]
                for anchor in anchors:
                    clipped=s.intersection(anchor.buffer(4))
                    for c in p.hubs.components(clipped):options.append((c.distance(inner_source),l,c))
        # Large old track pieces permit ordinary hole placement away from SMD.
        for _,outer,shape in sorted(options,key=lambda q:q[0])[:20]:
            win=box(shape.bounds[0]-5,shape.bounds[1]-5,shape.bounds[2]+5,shape.bounds[3]+5);legal=region(win)
            if legal.is_empty:continue
            anchor=shape.representative_point();points=[]
            for comp in p.hubs.components(legal.buffer(-.03)):
                pt=nearest_points(anchor,comp)[1];points.append(pt.coords[0]);points.append(comp.representative_point().coords[0])
            # Bounded landing search; whole-region greedy packing is useful for
            # dense supply banks but wastes quadratic work on long thin islands.
            interior=legal.buffer(-.03)
            for radius in (.8,1.2,1.8,2.5,3.5,4.5):
                for j in range(24):
                    xy=(round(anchor.x+radius*math.cos(j*math.pi/12),6),round(anchor.y+radius*math.sin(j*math.pi/12),6))
                    if interior.covers(Point(xy)):points.append(xy)
            points=sorted({(round(x,6),round(y,6)) for x,y in points},key=lambda xy:Point(xy).distance(shape))[:48]
            ofree=frees[outer].intersection(win)
            outer_centres={width:p.hubs.components(set_precision(ofree.buffer(-width/2-.01),1e-6)) for width in (.25,.20)}
            for site in points:
                tries+=1
                if not legal.covers(Point(site)):continue
                disk=Point(site).buffer(.3)
                for width in (.25,.20):
                    route=None
                    for comp in outer_centres[width]:
                        aa=comp.intersection(shape);bb=comp.intersection(disk)
                        if aa.is_empty or bb.is_empty:continue
                        aa_inside=aa.buffer(-.005);bb_inside=bb.buffer(-.005)
                        if aa_inside.is_empty or bb_inside.is_empty:continue
                        a,b=nearest_points(aa_inside,bb_inside);start=tuple(round(v,6) for v in a.coords[0]);end=tuple(round(v,6) for v in b.coords[0])
                        if not comp.covers(Point(start)) or not comp.covers(Point(end)):continue
                        test=CP.path(comp,start,end,node_cap=180000)
                        if test['verdict']=='HOST_PATH':route=test;break
                    if route is None:continue
                    pts=[[round(x,6),round(y,6)] for x,y in route['points']];pts.append(list(site));pts=[q for i,q in enumerate(pts) if i==0 or q!=pts[i-1]]
                    stubcore=LineString(pts).buffer(width/2)
                    if not ofree.covers(stubcore):continue
                    legalcount+=1;il,body,inner=innerbridge(site)
                    if il is None:continue
                    v=C.via('CORE-island-r26-'+str(gi),sp['net'],site);ts=[C.track('CORE-island-r26-'+str(gi)+'-stub-'+str(j),sp['net'],outer,a,b,width) for j,(a,b) in enumerate(zip(pts,pts[1:]))]
                    newvias.append(v);newtracks+=ts
                    if body is not None:
                        z={'uuid':C.uid('CORE-island-r26-'+str(gi)+'-plane'),'label':'CORE-island-r26-'+str(gi)+'-plane','net':sp['net'],'layer':il,'shape':set_precision(body,1e-6),'route':inner,'clearance_mm':.15};newzones.append(z);sources[il]=unary_union([sources[il],z['shape']])
                    # Explicit nanometre antipads on the nine new main returns.
                    for z in zones:
                        if z['uuid'] not in carvable or p.norm(z['net'])==NET:continue
                        cutter=set_precision(Point(site).buffer(.3+max(gap(z['net']),float(z.get('clearance_mm',.15)))+.025),1e-6)
                        old=z['shape'];new=set_precision(set_precision(old,1e-6).difference(cutter),1e-6)
                        if old.equals(new):continue
                        f=OUT/(z['uuid']+'-via-'+str(gi)+'-old.wkb');f.write_bytes(old.wkb);nf=OUT/(z['uuid']+'-via-'+str(gi)+'-new.wkb');nf.write_bytes(new.wkb);cf=OUT/(z['uuid']+'-via-'+str(gi)+'-cutter.wkb');cf.write_bytes(cutter.wkb)
                        carveledger.append({'zone_uuid':z['uuid'],'layer':z['layer'],'net_raw':z['net'],'via_uuid':v['uuid'],'old_wkb_file':str(f.resolve()),'old_wkb_sha256':sha(f),'new_wkb_file':str(nf.resolve()),'new_wkb_sha256':sha(nf),'cutter_wkb_file':str(cf.resolve()),'cutter_wkb_sha256':sha(cf),'removed_area_mm2':old.difference(new).area,'added_quantization_area_mm2':new.difference(old).area,'operation':'set_precision(old,1e-6).difference(set_precision(circle,1e-6)); final set_precision(1e-6)'});z['shape']=new
                    joined.add(gi);answer={'group':gi,'physical_contacts':groups[gi],'via':v,'outer':outer,'stub_width_mm':width,'stub_route':{**route,'points':pts,'length_mm':LineString(pts).length},'new_track_uuids':[t['uuid'] for t in ts],'inner_layer':il,'inner_route':inner,'planning_current_and_unequal_sharing':'OPEN; one via is constructive connectivity only; no branch capacity claim'};print('CORE_INNER_JOINED',gi,site,outer,il,None if inner is None else inner['length_mm'],flush=True);break
                if answer:break
            if answer:break
        if answer:rows.append(answer)
        else:missing.append({'group':gi,'contacts':groups[gi],'via_candidates':tries,'outer_stub_legal_candidates':legalcount});print('CORE_INNER_UNRESOLVED',gi,tries,legalcount,flush=True)
        write(OUT/'checkpoint.json',{'rows':rows,'remaining':missing,'carves':carveledger,'native_jobs':0,'board_written':False});(OUT/'proposed-discrete.pkl').write_bytes(pickle.dumps({'vias':newvias,'tracks':newtracks},protocol=5));(OUT/'new-CORE-zones.pkl').write_bytes(pickle.dumps(newzones,protocol=5));(OUT/'all-zones.pkl').write_bytes(pickle.dumps(zones+newzones,protocol=5))
    hh={**h,'vias':h['vias']+newvias,'tracks':h['tracks']+newtracks};final,cuts=P.projected(g,hh,zones+newzones);Q.NET=NET;after,_,_=Q.groups(final,return_details=True);aid={q['uuid']:i for i,rs in enumerate(after) for q in rs};sr=aid[sp['uuid']];remaining=[{'group':i,'pads':[q for q in rs if not q['ref'].startswith('@')]} for i,rs in enumerate(after) if i!=sr and any(not q['ref'].startswith('@') for q in rs)]
    model=OUT/'model.pkl';model.write_bytes(pickle.dumps((g,hh,binding,zones+newzones,final),protocol=5));write(OUT/'receipt.json',{'verdict':'CONSTRUCTED_CORE_INNER_FEEDS_JOINT_CONTACT_CURRENT_NATIVE_PENDING','binding':binding,'model_sha256':sha(model),'source':'R11022.2','rows':rows,'remaining':remaining,'constructed_failures':missing,'field_main_return_antipads':carveledger,'excluded_non_native_planning_mask':'CORE1V2 entire original In3 zone-outline mask only; actual original CORE1V2 Cu and native outline/settings retained','new_vias':len(newvias),'new_segments':len(newtracks),'new_CORE_zones':len(newzones),'old_fill_retreats':cuts,'native_jobs':0,'board_written':False,'full_current_return_and_retained_contacts_gate':'OPEN'});print('CORE_INNER_COMPLETE',len(rows),len(remaining),flush=True)
if __name__=='__main__':main()
