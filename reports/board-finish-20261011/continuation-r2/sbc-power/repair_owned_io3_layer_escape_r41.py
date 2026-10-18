"""One ordinary IO3 escape closes the owned CM crossing without clock edits."""
import copy,json,pickle,hashlib,sys,math
from pathlib import Path
from shapely import set_precision,STRtree
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
import core_inner_feed_r18 as I
import continuous_path_prepared_r2 as CP
L=I.L;p=I.p;P=I.P;Q=I.Q;C=I.C;G=I.G;R=I.R;LAYERS=I.LAYERS
OUT=L.OUT/'owned-io3-layer-escape-repair-r41';NET='/IO_3V3'
REMOVE={'f40d2eaf-c69c-5163-bf36-1b97a3063419','b1e24199-3f81-528d-bf44-77fe8c8eb9a9'}
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir();prior=L.OUT/'actual-core-cross-layer-source-bridge-r38/model.pkl'
    g,h,binding,zones,_=pickle.loads(prior.read_bytes());h=copy.deepcopy(h)
    ledger=L.OUT/'owned-io3-cm-crossing-repair-r39/owned-existing-Cu-removal-ledger.json';lr=json.loads(ledger.read_text())
    assert {q['uuid'] for q in lr['rows']}==REMOVE
    assert all(next(t for t in h['tracks'] if t['uuid']==q['uuid'])==q['geometry'] for q in lr['rows'])
    h['tracks']=[q for q in h['tracks'] if q['uuid'] not in REMOVE]
    candidate,_=P.projected(g,h,zones);Q.NET=NET;groups,parts,assign=Q.groups(candidate,return_details=True)
    ids={q['uuid']:i for i,rr in enumerate(groups) for q in rr};sp=next(q for q in h['pads'] if (q['ref'],q['num'])==('R18001','2'));tp=next(q for q in h['pads'] if (q['ref'],q['num'])==('R11049','1'));root=ids[sp['uuid']];target=ids[tp['uuid']];assert root!=target
    targetshape=unary_union([s for s,j in zip(parts['F.Cu'],assign['F.Cu']) if j==target]);anchor=Point(125.061390,164.319402)
    goals={layer:unary_union([s for s,j in zip(parts[layer],assign[layer]) if j==root]) for layer in LAYERS}
    outline=unary_union(p.base.polygons(g['outline'])).buffer(-.525);p.WINDOW=box(.526,.526,449.474,234.474);areas=L.live.reservations()
    hardmodel={**h,'zones':[dict(q,layers=[l for l in q['layers'] if l!='In3.Cu']) if p.norm(q['net'])=='/CORE_1V2' else q for q in h['zones']]}
    hard=[s for layer in LAYERS for s in p.hard_shapes(hardmodel,areas,NET,layer,for_via=True)]
    rec=[];drills=[];smd=[];ownholes=[]
    for q in h['pads']:
        for layer,rs in q['layers'].items():
            for s in p.base.polygons(rs):
                if p.norm(q['net'])!=NET:rec.append({'uuid':q['uuid'],'net':q['net'],'layer':layer,'shape':s})
                if q['smd']:smd.append(s)
        holes=p.base.polygons(q.get('hole') or []);drills+=holes
        if p.norm(q['net'])==NET:ownholes+=holes
    for t in h['tracks']:
        if p.norm(t['net'])!=NET:rec.append({'uuid':t['uuid'],'net':t['net'],'layer':t['layer'],'shape':p.base.body(t)})
    for v in h['vias']:
        point=Point(v['x'],v['y']);hole=point.buffer(v['drill']/2);drills.append(hole)
        if p.norm(v['net'])==NET:ownholes.append(hole)
        else:
            for layer in v['flashed']:rec.append({'uuid':v['uuid'],'net':v['net'],'layer':layer,'shape':point.buffer(v['d']/2)})
    for q in h['shapes']:
        if q['layer'] in LAYERS and p.norm(q['net'])!=NET:
            for s in p.base.polygons(q['poly']):rec.append({'uuid':q['uuid'],'net':q['net'],'layer':q['layer'],'shape':s})
    rt=STRtree([q['shape'] for q in rec]);dt=STRtree(drills);st=STRtree(smd);ht=STRtree(hard);oh=unary_union(ownholes)
    goals={l:s.difference(oh) for l,s in goals.items()}
    carvable={q['uuid'] for q in zones if q.get('label')=='CORE-main-In2' or q.get('field_return_proposal')}
    originalids={q['uuid'] for q in h['zones']};answer=None
    for margin in (4.,8.,16.):
        win=box(anchor.x-margin,anchor.y-margin,anchor.x+margin,anchor.y+margin)
        for diameter,drill in ((.5,.2),(.6,.3)):
            obs=[rec[int(i)]['shape'].buffer(diameter/2+G.gap(h,NET,rec[int(i)]['net'])+.025) for i in rt.query(win.buffer(2),predicate='intersects')]
            obs += [drills[int(i)].buffer(drill/2+.275) for i in dt.query(win.buffer(1),predicate='intersects')]
            obs += [smd[int(i)].buffer(drill/2+.275) for i in st.query(win.buffer(1),predicate='intersects')]
            obs += [hard[int(i)].buffer(diameter/2+.025) for i in ht.query(win.buffer(1),predicate='intersects')]
            obs += [z['shape'].buffer(diameter/2+max(G.gap(h,NET,z['net']),float(z.get('clearance_mm',.15)))+.025) for z in zones if p.norm(z['net'])!=NET and z['uuid'] not in carvable and z['shape'].intersects(win.buffer(2))]
            legal=set_precision(win.intersection(outline).difference(unary_union(obs)),1e-6)
            if legal.is_empty:continue
            repour=tuple({p.norm(q['net']) for q in h['zones']});ofree=R.free_layer(h,NET,'F.Cu',win,repour,reference_guard=None,allow_own_via_connection=True)
            outerextra=[z['shape'].buffer(max(G.gap(h,NET,z['net']),float(z.get('clearance_mm',.15)))+.025) for z in zones if z['layer']=='F.Cu' and p.norm(z['net'])!=NET and z['shape'].intersects(win.buffer(2))]
            ofree=set_precision(ofree.difference(unary_union(outerextra)),1e-6);centres=p.hubs.components(set_precision(ofree.buffer(-.11),1e-6))
            sites=[]
            for c in p.hubs.components(legal.buffer(-.02)):
                sites += [c.representative_point().coords[0],nearest_points(anchor,c)[1].coords[0]]
            for radius in (.7,1.,1.5,2.,3.,4.,6.,8.):
                for j in range(32):
                    xy=(round(anchor.x+radius*math.cos(j*math.pi/16),6),round(anchor.y+radius*math.sin(j*math.pi/16),6))
                    if legal.buffer(-.01).covers(Point(xy)):sites.append(xy)
            for xy in sorted({tuple(round(v,6) for v in xy) for xy in sites},key=lambda xy:Point(xy).distance(targetshape))[:96]:
                point=Point(xy);ann=point.buffer(diameter/2).difference(point.buffer(drill/2));outer_route=None
                for comp in centres:
                    aa=comp.intersection(targetshape).buffer(-.005);bb=comp.intersection(ann).buffer(-.005)
                    if aa.is_empty or bb.is_empty:continue
                    a,b=nearest_points(aa,bb);start=tuple(round(v,6) for v in a.coords[0]);end=tuple(round(v,6) for v in b.coords[0])
                    test=CP.path(comp,start,end,node_cap=180000)
                    if test['verdict']!='HOST_PATH':continue
                    points=[[round(x,6),round(y,6)] for x,y in test['points']]+[list(xy)];points=[a for j,a in enumerate(points) if j==0 or a!=points[j-1]]
                    if ofree.covers(LineString(points).buffer(.1)):outer_route={**test,'points':points,'length_mm':LineString(points).length};break
                if outer_route is None:continue
                for layer in ('In3.Cu','In2.Cu','In1.Cu','In4.Cu'):
                    goal=goals[layer]
                    if ann.intersection(goal).area>.005:answer={'site':xy,'diameter':diameter,'drill':drill,'outer_route':outer_route,'inner_layer':layer,'inner_route':None,'inner_shape':None};break
                    # Bounded inner scene contains all actual foreign Cu plus
                    # every new plane; own via antipad does not grant an exit
                    # through a surrounding CORE plane.
                    near=nearest_points(point,goal)[1];iw=box(min(point.x,near.x)-12,min(point.y,near.y)-12,max(point.x,near.x)+12,max(point.y,near.y)+12)
                    blockers=[q['shape'].buffer(G.gap(h,NET,q['net'])+.025) for q in rec if q['layer']==layer and q['shape'].intersects(iw.buffer(2))]
                    blockers += [s.buffer(.275) for s in drills if s.intersects(iw.buffer(1)) and not s.intersects(point.buffer(drill/2))]
                    blockers += [s.buffer(.025) for s in p.hard_shapes(hardmodel,areas,NET,layer) if s.intersects(iw.buffer(1))]
                    for z in candidate['zones']:
                        if p.norm(z['net'])==NET or z['uuid'] in originalids and p.norm(z['net'])=='/LOGIC_GND':continue
                        clear=max(G.gap(h,NET,z['net']),float(z.get('clearance_mm',.15)))+.025
                        blockers += [s.buffer(clear) for s in p.base.polygons(z['fills'].get(layer,[])) if s.intersects(iw.buffer(1))]
                    free=set_precision(iw.intersection(outline).difference(unary_union(blockers)),1e-6)
                    for comp in p.hubs.components(set_precision(free.buffer(-.11),1e-6)):
                        aa=comp.intersection(ann).buffer(-.005);bb=comp.intersection(goal).buffer(-.005)
                        if aa.is_empty or bb.is_empty:continue
                        a,b=nearest_points(aa,bb);start=tuple(round(v,6) for v in a.coords[0]);end=tuple(round(v,6) for v in b.coords[0])
                        test=CP.path(comp,start,end,node_cap=500000)
                        if test['verdict']!='HOST_PATH':continue
                        points=[[round(x,6),round(y,6)] for x,y in test['points']];line=LineString(points)
                        if not free.covers(line.buffer(.1)):continue
                        intended=set_precision(line.buffer(.5).intersection(free),1e-6);physical=set_precision(intended.difference(oh).difference(point.buffer(drill/2)),1e-6)
                        if physical.intersection(ann).area<=.005 or physical.intersection(goal).area<=.001:continue
                        answer={'site':xy,'diameter':diameter,'drill':drill,'outer_route':outer_route,'inner_layer':layer,'inner_route':{**test,'points':points,'length_mm':line.length,'minimum_core_width_mm':.2},'inner_shape':physical,'intended':intended};break
                    if answer:break
                if answer:break
            if answer:break
        if answer:break
    assert answer is not None,'No ordinary contained IO3 escape; no original/source/clock edits made'
    via=C.via('IO3-CM-owned-escape-r41',sp['net'],answer['site']);via.update(d=answer['diameter'],drill=answer['drill'])
    tracks=[C.track('IO3-CM-owned-escape-r41-stub-'+str(i),sp['net'],'F.Cu',a,b,.2) for i,(a,b) in enumerate(zip(answer['outer_route']['points'],answer['outer_route']['points'][1:]))]
    addedzones=[]
    if answer['inner_shape'] is not None:addedzones=[{'uuid':C.uid('IO3-CM-owned-escape-r41-inner'),'label':'IO3-CM-owned-escape-r41-inner','net':sp['net'],'layer':answer['inner_layer'],'shape':answer['inner_shape'],'zone_outline_shape':answer['intended'],'clearance_mm':.15,'route':answer['inner_route']}]
    carves=[]
    for z in zones:
        if z['uuid'] not in carvable or p.norm(z['net'])==NET:continue
        cutter=set_precision(Point(answer['site']).buffer(max(via['drill']/2+.275,via['d']/2+max(G.gap(h,NET,z['net']),float(z.get('clearance_mm',.15)))+.025)),1e-6)
        old=z['shape'];new=set_precision(set_precision(old,1e-6).difference(cutter),1e-6)
        if old.equals(new):continue
        paths={}
        for key,shape in (('old',old),('new',new),('cutter',cutter)):
            f=OUT/(z['uuid']+'-'+key+'.wkb');f.write_bytes(shape.wkb);paths[key+'_wkb_file']=str(f.resolve());paths[key+'_wkb_sha256']=sha(f)
        carves.append({'zone_uuid':z['uuid'],'layer':z['layer'],'net_raw':z['net'],**paths,'removed_area_mm2':old.difference(new).area,'added_quantization_area_mm2':new.difference(old).area});z['shape']=new
    h['vias'].append(via);h['tracks']+=tracks;zones+=addedzones
    binding.setdefault('existing_native_owned_Cu_removal_recipes',[]).append({'file':str(ledger.resolve()),'sha256':sha(ledger)})
    clean={k:v for k,v in answer.items() if k not in ('inner_shape','intended')}
    binding.update({'IO3_CM_ordinary_escape':{'via':via,'route':clean,'owned_new_plane_antipads':carves,'exact_clock_unchanged':lr['exact_retained_CM_clock_uuid'],'required_native_postfill_flash':['F.Cu',answer['inner_layer']]}})
    known=set(binding['restored_generated_grid_UUIDs'])|{q['zone_uuid'] for q in carves}|{q['uuid'] for q in addedzones};binding['restored_generated_grid_UUIDs']=sorted(known)
    for z in zones:
        if z['uuid'] in known:z['shape']=set_precision(z['shape'],1e-6)
    final,cuts=P.projected(g,h,zones);Q.NET=NET;after,_,_=Q.groups(final,return_details=True);ids={q['uuid']:i for i,rr in enumerate(after) for q in rr};assert ids[tp['uuid']]==ids[sp['uuid']]
    model=OUT/'model.pkl';model.write_bytes(pickle.dumps((g,h,binding,zones,final),protocol=5))
    (OUT/'proposed-discrete.pkl').write_bytes(pickle.dumps({'vias':[via],'tracks':tracks},protocol=5));(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(addedzones,protocol=5))
    receipt={'verdict':'PASS_OWNED_IO3_ORDINARY_ESCAPE_TO_ACTUAL_SOURCE_CLOCK_UNCHANGED_FULL_CONTACT_NATIVE_PENDING','model_sha256':sha(model),'parent_model_sha256':sha(prior),'binding':binding,'via':via,'new_tracks':tracks,'new_zone_shapes':len(addedzones),'route':clean,'owned_new_plane_antipads':carves,'old_owned_Cu_removal_ledger_file':str(ledger.resolve()),'old_owned_Cu_removal_ledger_sha256':sha(ledger),'old_fill_retreats':cuts,'full_original_foreign_contacts_current_native':'OPEN','native_jobs':0,'board_written':False}
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('IO3_CM_ORDINARY_ESCAPE_SOURCE_PASS',sha(model),via,clean,flush=True)
if __name__=='__main__':main()
