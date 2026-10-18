"""Search concrete translated R17031 poses with both retained OBS and CORE paths.

This is a layout nomination; no native footprint edit or source credit is implied.
All coordinates are quantized before discrete screening and path construction.
"""
import copy,json,pickle,hashlib,math
from pathlib import Path
from shapely import set_precision,STRtree,from_wkb
from shapely.geometry import Point,LineString,box
from shapely.affinity import translate
from shapely.ops import unary_union,nearest_points
import core_inner_feed_r18 as I
import continuous_path_prepared_r2 as CP
import guarded_declared_settings_projection_r58 as GP
L=I.L;p=I.p;G=I.G;Q=I.Q;C=I.C
OUT=L.OUT/'r17031-coupled-inner-bridge-nominations-r73'
CORE='/mc_local_power{slash}CORE_5V';OBS='/motherboard_status/OBS15_A'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def write(f,v):f.write_text(json.dumps(v,indent=2)+'\n')
def main():
    assert not OUT.exists();OUT.mkdir();(OUT/'source-used.py').write_bytes(Path(__file__).read_bytes())
    mf=L.OUT/'core-pocket-outward-round-guards-r69/model.pkl';assert sha(mf)=='48ce8a3f9708402708a139c8c642a447bf07e071c4e0b9216d51d8184ba54cff'
    g,h,b,z,c=pickle.loads(mf.read_bytes());ps=[q for q in h['pads'] if q['ref']=='R17031'];assert len(ps)==2
    pc=next(q for q in ps if q['num']=='1');po=next(q for q in ps if q['num']=='2');assert pc['net']==CORE and po['net']==OBS
    fp=next(q for q in h['footprints'] if q['ref']=='R17031');oldxy=(fp['x'],fp['y']);window=box(oldxy[0]-12,oldxy[1]-12,oldxy[0]+12,oldxy[1]+12)
    # Retain latest regulated R70 bodies as hard-only proposals.
    rf=L.OUT.parent/'field-power/regulated-final-power-search-base-r70/model.pkl';assert sha(rf)=='1368cee2cc2e18bc670a2875f31c4148b6d8792bbc67e89e65289107d923b73d'
    _,rh,_,rz,_=pickle.loads(rf.read_bytes());dids={k:{q['uuid'] for q in h[k]} for k in ('vias','tracks')};hardd={k:[q for q in rh[k] if q['uuid'] not in dids[k]] for k in dids};zids={q['uuid'] for q in z};hardz=[q for q in rz if q['uuid'] not in zids]
    rec={l:[] for l in I.LAYERS};smd=[];holes=[]
    for q in h['pads']:
        if q['ref']=='R17031':continue
        for l,rs in q['layers'].items():
            for sh in p.base.polygons(rs):
                rec[l].append({'kind':'pad','uuid':q['uuid'],'net':q['net'],'shape':sh,'radius':0})
                if q['smd']:smd.append(sh)
        for sh in p.base.polygons(q.get('hole') or []):holes.append({'shape':sh,'radius':0})
    for t in h['tracks']+hardd['tracks']:rec[t['layer']].append({'kind':'track','uuid':t['uuid'],'net':t['net'],'shape':LineString([t['a'],t['b']]),'radius':t['w']/2})
    for v in h['vias']+hardd['vias']:
        pt=Point(v['x'],v['y']);holes.append({'shape':pt,'radius':v['drill']/2})
        for l in v['flashed']:rec[l].append({'kind':'via','uuid':v['uuid'],'net':v['net'],'shape':pt,'radius':v['d']/2})
    for q in h['shapes']:
        if q['layer'] in rec:
            for sh in p.base.polygons(q['poly']):rec[q['layer']].append({'kind':'graphic','uuid':q['uuid'],'net':q['net'],'shape':sh,'radius':0})
    trees={l:STRtree([q['shape'].buffer(q['radius']+.001) for q in rs]) for l,rs in rec.items()}
    nearby={l:[rec[l][int(j)] for j in trees[l].query(window.buffer(3),predicate='intersects')] for l in I.LAYERS}
    gap=lambda a,b:G.gap(h,a,b)+.025
    def foreign_masks(net,layer):
        masks=[GP.bounded_buffer(q['shape'],q['radius']+gap(net,q['net'])) for q in nearby[layer] if q['net']!=net]
        masks += [GP.bounded_buffer(q['shape'],max(G.gap(h,net,q['net']),float(q.get('clearance_mm',.15)))+.025) for q in z+hardz if q['layer']==layer and q['net']!=net and q['shape'].intersects(window.buffer(2))]
        return unary_union(masks)
    fc=window.difference(foreign_masks(CORE,'F.Cu'));fo=window.difference(foreign_masks(OBS,'F.Cu'))
    courtyard=unary_union(p.base.polygons(fp['courtyard']['F']));courtyards=[s for f in h['footprints'] if f['ref']!='R17031' for s in p.base.polygons(f.get('courtyard',{}).get('F',[])) if s.intersects(window.buffer(3))];ct=STRtree(courtyards)
    oldpc=unary_union(p.base.polygons(pc['layers']['F.Cu']));oldpo=unary_union(p.base.polygons(po['layers']['F.Cu']))
    # Exact hole-radius and all-layer annulus guards. Original plane fills
    # acquire explicit normal antipads only after a frozen nomination.
    vm=[]
    for l in I.LAYERS:
        vm += [GP.bounded_buffer(q['shape'],q['radius']+.25+gap(CORE,q['net'])) for q in nearby[l] if q['net']!=CORE]
    vm += [GP.bounded_buffer(s,.1+.275) for s in smd if s.intersects(window.buffer(2))]
    vm += [GP.bounded_buffer(q['shape'],q['radius']+.1+.275) for q in holes if q['shape'].intersects(window.buffer(2))]
    for q in z+hardz:
        if q['net']!=CORE and q['shape'].intersects(window.buffer(2)):
            vm.append(GP.bounded_buffer(q['shape'],max(.1+.275,.25+max(G.gap(h,CORE,q['net']),float(q.get('clearance_mm',.15)))+.025)))
    viafree=set_precision(window.difference(unary_union(vm)),1e-6);(OUT/'via-center-free.wkb').write_bytes(viafree.wkb)
    # Explicit component/body keepouts remain hard on every candidate.
    areas=L.live.reservations();hh={**h,'pads':[q for q in h['pads'] if q['ref']!='R17031'],'footprints':[q for q in h['footprints'] if q['ref']!='R17031']}
    hard=p.hard_shapes(hh,areas,I.NET,'F.Cu',for_via=True);vh=[s for l in I.LAYERS for s in p.hard_shapes(hh,areas,I.NET,l,for_via=True) if s.intersects(window.buffer(2))]
    viafree=set_precision(viafree.difference(unary_union([GP.bounded_buffer(s,.25+.025) for s in vh])),1e-6)
    for s in hard:fc=fc.difference(GP.bounded_buffer(s,.025));fo=fo.difference(GP.bounded_buffer(s,.025))
    obsgoal=unary_union([q['shape'].buffer(q['radius']) for q in nearby['F.Cu'] if q['net']==OBS and q['shape'].distance(Point(po['x'],po['y']))<.8])
    assert not obsgoal.is_empty
    # Full CORE graph supplies real layer-specific source regions, never a
    # proposal count or L11001 pre-shunt marker.
    Q.NET=I.NET;groups,parts,assign=Q.groups(c,return_details=True);lookup={q['uuid']:i for i,rs in enumerate(groups) for q in rs};sp=next(q for q in h['pads'] if (q['ref'],q['num'])==('R11022','2'));root=lookup[sp['uuid']];sources={l:unary_union([s for s,j in zip(parts[l],assign[l]) if j==root]) for l in I.LAYERS}
    for l,s in sources.items():(OUT/(l+'-actual-source.wkb')).write_bytes(s.wkb)
    innerfree={};safe_cache={};innercache={}
    for l in ('In1.Cu','In2.Cu','In3.Cu','In4.Cu'):
        ff=L.OUT/'remaining-core-reachable-ordinary-pockets-r64'/(l+'-free.wkb');free=set_precision(from_wkb(ff.read_bytes()),1e-6)
        extra=[GP.bounded_buffer(q['shape'],max(G.gap(h,CORE,q['net']),float(q.get('clearance_mm',.15)))+.025) for q in z+hardz if q['layer']==l and q['net']!=CORE]
        extra += [GP.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+gap(CORE,t['net'])) for t in hardd['tracks'] if t['layer']==l and t['net']!=CORE]
        extra += [GP.bounded_disk(v,max(v['drill']/2+.275,v['d']/2+gap(CORE,v['net']))) for v in hardd['vias'] if v['net']!=CORE]
        innerfree[l]=set_precision(free.difference(unary_union(extra)),1e-6)
    def bridge(site):
        if site in innercache:return innercache[site]
        disk=Point(site).buffer(.25);ann=disk.difference(Point(site).buffer(.1))
        for l in ('In1.Cu','In2.Cu','In3.Cu','In4.Cu'):
            if ann.intersection(sources[l]).area>.01:
                innercache[site]=(l,None,None);return innercache[site]
        options=[]
        for l in ('In1.Cu','In2.Cu','In3.Cu','In4.Cu'):
            if sources[l].is_empty:continue
            aa,bb=nearest_points(ann,sources[l]);options.append((aa.distance(bb),l,aa,bb))
        for distance,l,aa,bb in sorted(options):
            if distance>330:continue
            for width in (1.,.5,.35,.25,.20):
                key=(l,width)
                if key not in safe_cache:
                    cs=p.hubs.components(set_precision(innerfree[l].buffer(-width/2-.01),1e-6));tree=STRtree(cs);goals={int(j) for j in tree.query(sources[l],predicate='intersects')};safe_cache[key]=(cs,tree,goals)
                cs,tree,goals=safe_cache[key];ids={int(j) for j in tree.query(ann,predicate='intersects')}&goals
                for margin in (8.,25.,70.,180.):
                    win=box(min(aa.x,bb.x)-margin,min(aa.y,bb.y)-margin,max(aa.x,bb.x)+margin,max(aa.y,bb.y)+margin)
                    for comp in [a for j in ids for a in p.hubs.components(cs[j].intersection(win))]:
                        a=comp.intersection(ann).buffer(-.003);bp=comp.intersection(sources[l]).buffer(-.003)
                        if a.is_empty or bp.is_empty:continue
                        ss,ee=nearest_points(a,bp);start=tuple(round(v,6) for v in ss.coords[0]);end=tuple(round(v,6) for v in ee.coords[0]);print('R73_INNER_SEARCH',site,l,width,margin,flush=True)
                        route=CP.path(comp,start,end,node_cap=160000)
                        if route['verdict']!='HOST_PATH':continue
                        points=[[round(x,6),round(y,6)] for x,y in route['points']];line=LineString(points);core=line.buffer(width/2)
                        if not innerfree[l].covers(core):continue
                        body=set_precision(line.buffer(2).intersection(innerfree[l]),1e-6);body=unary_union([a for a in p.hubs.components(body) if a.intersects(core)])
                        if body.intersection(ann).area<=.001 or body.intersection(sources[l]).area<=1e-8:continue
                        innercache[site]=(l,body,{'points':points,'length_mm':line.length,'minimum_core_width_mm':width});return innercache[site]
        innercache[site]=(None,None,None);return innercache[site]
    # Search translations by displacement. Orientation and all local native
    # pad/text/courtyard geometry remain unchanged in this first pass.
    moves=sorted({(round(i*.25,6),round(j*.25,6)) for i in range(-32,33) for j in range(-32,33) if i or j},key=lambda xy:(math.hypot(*xy),xy))
    counts={'poses':0,'pad_Cu_legal':0,'courtyard_legal':0,'signal_path':0,'CORE_via_path':0};accepted=[]
    for dx,dy in moves:
        counts['poses']+=1;sc=set_precision(translate(oldpc,dx,dy),1e-6);so=set_precision(translate(oldpo,dx,dy),1e-6)
        if not fc.covers(sc) or not fo.covers(so):continue
        counts['pad_Cu_legal']+=1;cy=translate(courtyard,dx,dy)
        if any(cy.distance(courtyards[int(i)])<.025 for i in ct.query(cy.buffer(.03),predicate='intersects')):continue
        counts['courtyard_legal']+=1
        # Newly moved SMD pads must preserve hole aperture to every existing
        # drill. Both pads are checked, independent of their net spelling.
        if any(min(sc.distance(q['shape']),so.distance(q['shape']))-q['radius']<.275 for q in holes if q['shape'].intersects(cy.buffer(1))):continue
        of=set_precision(fo.difference(GP.bounded_buffer(sc,.175)).buffer(-.11),1e-6)
        ocomp=[a for a in p.hubs.components(of) if a.intersects(so) and a.intersects(obsgoal)]
        if not ocomp:continue
        for oc in ocomp:
            a,bp=nearest_points(oc.intersection(so).buffer(-.003),oc.intersection(obsgoal).buffer(-.003))
            if a.is_empty or bp.is_empty:continue
            signal=CP.path(oc,tuple(round(v,6) for v in a.coords[0]),tuple(round(v,6) for v in bp.coords[0]),node_cap=100000)
            if signal['verdict']=='HOST_PATH':break
        else:continue
        counts['signal_path']+=1;op=[[round(x,6),round(y,6)] for x,y in signal['points']];oline=LineString(op)
        cf=set_precision(fc.difference(GP.bounded_buffer(so,.175)).difference(GP.bounded_buffer(oline,.1+.175)).buffer(-.11),1e-6)
        vf=viafree.difference(GP.bounded_buffer(sc,.1+.275)).difference(GP.bounded_buffer(so,.1+.275)).difference(GP.bounded_buffer(oline,.25+.1+.175))
        for comp in [a for a in p.hubs.components(cf) if a.intersects(sc)]:
            legal=set_precision(vf.intersection(comp.buffer(.245)),1e-6)
            if legal.is_empty:continue
            sites=[]
            for lc in p.hubs.components(legal.buffer(-.002)):
                sites += [nearest_points(sc,lc)[1],lc.representative_point()]
            for pt in sorted(sites,key=lambda pt:pt.distance(sc))[:20]:
                site=tuple(round(v,6) for v in pt.coords[0]);ann=Point(site).buffer(.25).difference(Point(site).buffer(.1))
                il,innerbody,innerroute=bridge(site)
                if il is None:continue
                aa=comp.intersection(sc).buffer(-.003);bb=comp.intersection(Point(site).buffer(.25)).buffer(-.003)
                if aa.is_empty or bb.is_empty:continue
                a,bp=nearest_points(aa,bb);route=CP.path(comp,tuple(round(v,6) for v in a.coords[0]),tuple(round(v,6) for v in bp.coords[0]),node_cap=100000)
                if route['verdict']!='HOST_PATH':continue
                cp=[[round(x,6),round(y,6)] for x,y in route['points']]+[list(site)];cp=[q for i,q in enumerate(cp) if not i or q!=cp[i-1]];v=C.via('R17031-r73',CORE,site);v.update(d=.5,drill=.2)
                ts=[C.track('R17031-r73-core-'+str(i),CORE,'F.Cu',a,bp,.20) for i,(a,bp) in enumerate(zip(cp,cp[1:]))]+[C.track('R17031-r73-obs-'+str(i),OBS,'F.Cu',a,bp,.20) for i,(a,bp) in enumerate(zip(op,op[1:]))]
                counts['CORE_via_path']+=1;accepted.append({'target_FP_pose':[round(oldxy[0]+dx,6),round(oldxy[1]+dy,6),0.],'translation_mm':[dx,dy],'CORE_pad':[round(pc['x']+dx,6),round(pc['y']+dy,6)],'OBS_pad':[round(po['x']+dx,6),round(po['y']+dy,6)],'CORE_via_required_source_layer':il,'inner_bridge_route':innerroute,'inner_bridge_zone_UUID':C.uid('R17031-r73-plane') if innerbody is not None else None,'via':v,'tracks':ts,'CORE_route':cp,'OBS_route':op,'OBS_target_actual_old_shared_Cu':True});print('R73_NOMINATED',accepted[-1]['target_FP_pose'],site,il,len(ts),flush=True);
                if innerbody is not None:
                    nz={'uuid':C.uid('R17031-r73-plane'),'label':'R17031-r73-plane','net':CORE,'layer':il,'shape':set_precision(innerbody.difference(unary_union([q['shape'].buffer(q['radius']) for q in holes]+[Point(site).buffer(.1)])),1e-6),'zone_outline_shape':innerbody,'route':innerroute,'clearance_mm':.15};(OUT/'new-CORE-zones.pkl').write_bytes(pickle.dumps([nz],protocol=5))
                break
            if accepted:break
        if accepted:break
        if counts['poses']%250==0:print('R73_PROGRESS',counts,flush=True)
    write(OUT/'receipt.json',{'verdict':'CONCRETE_TWO_NET_TRANSLATION_NOMINATED_ALL_MUTUAL_NATIVE_GATES_PENDING' if accepted else 'NO_TRANSLATION_NOMINATION_WITHIN8MM_GRID','parent_model_sha256':sha(mf),'regulated_R70_hard_only_model_sha256':sha(rf),'counts':counts,'rows':accepted,'all_exact_native_pose_source_shared_contact_aperture_current_refill_DRC_gates':'OPEN','native_jobs':0,'board_written':False})
    if accepted:(OUT/'proposed-discrete.pkl').write_bytes(pickle.dumps({'vias':[accepted[0]['via']],'tracks':accepted[0]['tracks']},protocol=5))
    print('R73_COMPLETE',counts,len(accepted),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
