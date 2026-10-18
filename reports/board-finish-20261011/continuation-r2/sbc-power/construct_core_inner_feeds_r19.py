"""Concrete ordinary-via supply feeds, exact discrete geometry and local carves.

The inherited CORE_1V2 whole-outline In3 planning mask is excluded here: it is
not a native keepout. Actual CORE_1V2 copper and source zone definitions remain
unchanged obstacles. Only nine proposed field main returns can acquire explicit
new-via antipads; all other new field/IO3/GND polygons remain hard obstacles.
"""
import copy,json,pickle,math,uuid,hashlib
from pathlib import Path
from shapely import set_precision,STRtree
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
import core_inner_feed_r18 as I
import continuous_path_prepared_r1 as CP
G=I.G;P=I.P;Q=I.Q;C=I.C;L=I.L;p=I.p;R=I.R;NET=I.NET;LAYERS=I.LAYERS
OUT=L.OUT/'core-inner-feed-r23'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def write(f,v):f.write_text(json.dumps(v,indent=2)+'\n')
def main():
    assert not OUT.exists();OUT.mkdir();base=L.OUT/'core-inner-feed-r18/overlay-model.pkl';g,h,binding,zones,candidate=pickle.loads(base.read_bytes());binding['CORE_field_overlay_r18_sha256']=sha(base)
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
    frees={};sources={}
    for l in ('In2.Cu','In3.Cu','In1.Cu','In4.Cu'):
        # All original GND fills may retreat; all actual foreign supply fills
        # (including CORE1V2), all field proposals and restored IO3 stay fixed.
        cuts=[q['shape'].buffer(gap(q['net'])+.025) for q in rec[l] if p.norm(q['net'])!=NET]+[s.buffer(.275) for s in innerdrills]+[s.buffer(.025) for s in hard[l]]
        for q in candidate['zones']:
            if p.norm(q['net'])==NET or q['uuid'] in originalids and p.norm(q['net'])=='/LOGIC_GND':continue
            clear=max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025
            cuts += [s.buffer(clear) for s in p.base.polygons(q['fills'].get(l,[]))]
        frees[l]=set_precision(outline.difference(unary_union(cuts)),1e-6)
        sources[l]=unary_union([s for s,j in zip(parts[l],assign[l]) if j==root]);(OUT/(l+'-free.wkb')).write_bytes(frees[l].wkb);print('CORE_INNER_FREE',l,frees[l].area,'source',sources[l].area,flush=True)
    newvias=[];newtracks=[];newzones=[];rows=[];missing=[];joined={root}
    def region(win):
        obs=[]
        for l in LAYERS:
            for ii in trees[l].query(win.buffer(2),predicate='intersects'):
                q=rec[l][int(ii)]
                if p.norm(q['net'])!=NET:obs.append(q['shape'].buffer(.3+gap(q['net'])+.025))
        obs += [smd[int(i)].buffer(.425) for i in st.query(win.buffer(1),predicate='intersects')]
        obs += [drills[int(i)].buffer(.575) for i in dt.query(win.buffer(1),predicate='intersects')]
        obs += [viahard[int(i)] for i in vh.query(win,predicate='intersects')]
        obs += [oldforeign[int(i)] for i in oft.query(win,predicate='intersects')]
        for q in zones+newzones:
            if p.norm(q['net'])!=NET and q['uuid'] not in carvable and q['shape'].intersects(win.buffer(2)):obs.append(q['shape'].buffer(.3+max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025))
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
        disk=Point(site).buffer(.3);ann=disk.difference(Point(site).buffer(.15));options=[]
        for l in frees:
            goal=sources[l]
            if goal.is_empty:continue
            if ann.intersection(goal).area>.01:return l,None,None
            a,b=nearest_points(disk,goal);options.append((a.distance(b),l,a,b))
        for distance,l,a,b in sorted(options,key=lambda x:x[0]):
            if distance>330:continue
            for margin in (8.,25.,70.,180.):
                win=box(min(a.x,b.x)-margin,min(a.y,b.y)-margin,max(a.x,b.x)+margin,max(a.y,b.y)+margin);usable=frees[l].intersection(win)
                for width in (1.25,1.,.75,.5,.35):
                    for comp in p.hubs.components(set_precision(usable.buffer(-width/2-.01),1e-6)):
                        aa=comp.intersection(ann);bb=comp.intersection(goal)
                        if aa.is_empty or bb.is_empty:continue
                        ss,ee=nearest_points(aa,bb);start=ss.coords[0];end=ee.coords[0];print('CORE_INNER_PATH_SEARCH',site,l,width,margin,comp.area,flush=True);route=CP.path(comp,start,end,node_cap=500000)
                        if route['verdict']!='HOST_PATH':continue
                        points=[[round(x,6),round(y,6)] for x,y in route['points']];line=LineString(points);core=line.buffer(width/2)
                        if not frees[l].covers(core):continue
                        body=set_precision(line.buffer(2.).intersection(frees[l]),1e-6);body=unary_union([s for s in p.hubs.components(body) if s.intersection(core).area>0])
                        if body.intersection(ann).area<=.001 or body.intersection(goal).area<=1e-8:continue
                        return l,body,{**route,'points':points,'length_mm':line.length,'minimum_core_width_mm':width,'exact_quantized_core_free_containment':True}
        return None,None,None
    for gi in targets:
        if gi in joined:continue
        answer=None;tries=0;legalcount=0;print('CORE_INNER_ISLAND',gi,flush=True)
        options=[]
        for l in ('F.Cu','B.Cu'):
            for s,j in zip(parts[l],assign[l]):
                if j==gi:options.append((s.area,l,s))
        # Large old track pieces permit ordinary hole placement away from SMD.
        for _,outer,shape in sorted(options,reverse=True,key=lambda q:q[0])[:20]:
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
            ofree=localfree(outer,win)
            for site in points:
                tries+=1
                if not legal.covers(Point(site)):continue
                disk=Point(site).buffer(.3)
                for width in (.25,.20):
                    centre=set_precision(ofree.buffer(-width/2-.01),1e-6);route=None
                    for comp in p.hubs.components(centre):
                        aa=comp.intersection(shape);bb=comp.intersection(disk)
                        if aa.is_empty or bb.is_empty:continue
                        a,b=nearest_points(aa,bb);test=CP.path(comp,a.coords[0],b.coords[0],node_cap=180000)
                        if test['verdict']=='HOST_PATH':route=test;break
                    if route is None:continue
                    pts=[[round(x,6),round(y,6)] for x,y in route['points']];pts.append(list(site));pts=[q for i,q in enumerate(pts) if i==0 or q!=pts[i-1]]
                    stubcore=LineString(pts).buffer(width/2)
                    if not ofree.covers(stubcore):continue
                    legalcount+=1;il,body,inner=innerbridge(site)
                    if il is None:continue
                    v=C.via('CORE-island-r19-'+str(gi),sp['net'],site);ts=[C.track('CORE-island-r19-'+str(gi)+'-stub-'+str(j),sp['net'],outer,a,b,width) for j,(a,b) in enumerate(zip(pts,pts[1:]))]
                    newvias.append(v);newtracks+=ts
                    if body is not None:
                        z={'uuid':C.uid('CORE-island-r19-'+str(gi)+'-plane'),'label':'CORE-island-r19-'+str(gi)+'-plane','net':sp['net'],'layer':il,'shape':set_precision(body,1e-6),'route':inner,'clearance_mm':.15};newzones.append(z);sources[il]=unary_union([sources[il],z['shape']])
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
