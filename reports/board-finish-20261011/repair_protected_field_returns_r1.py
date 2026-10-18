"""Reconnect protected-antipad field-ground splits using existing annuli.

No new barrel, source edit, old copper deletion or old zone outline change.
Every proposal must pass a fresh complete projected source graph before it is
preserved. These are host candidates; native fill/current gates stay open.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import hashlib,json,pickle,sys,uuid
from pathlib import Path
from shapely import set_precision,get_num_coordinates
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'field-power'))
import contact_layout as C
import fast_contacts as F
import zone_projection_r1 as N
import tri_route as T
OUT=H/'protected-field-return-restoration-r1'
LAYERS=('In4.Cu','In2.Cu','In3.Cu','In1.Cu')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def polys(s):return [s] if s.geom_type=='Polygon' else [q for q in getattr(s,'geoms',[]) if q.geom_type=='Polygon']
def write(p,v):Path(p).write_text(json.dumps(v,indent=1)+'\n',encoding='utf-8')
def main():
    mp=H/'protected-joint-core-b5-model-r1/model.pkl';assert sha(mp)=='e5fe557e23fd3bd022c315a73b953655b256239cffb848bfe8f040e5aa5debe9'
    assert not OUT.exists();OUT.mkdir();old,h,binding,zones,current=pickle.loads(mp.read_bytes())
    # Restore the exact r15 precision state lost across WKB pickling.
    precise={q['uuid'] for q in zones if q.get('label')=='CORE-main-In2' or q.get('label','').startswith('IO3-r15-field-crossing-') or q.get('field_return_proposal') and q['layer']=='In2.Cu'}
    assert len(precise)==9
    zones=[{**q,'shape':set_precision(q['shape'],1e-6)} if q['uuid'] in precise else q for q in zones]
    current,_=N.projected(old,h,zones)
    rec,trees=F.build({**h,'zones':[]});outline=unary_union(C.poly(h['outline'])).buffer(-.526)
    vias={v['uuid']:v for v in h['vias']};adds=[];rows=[];attempted=[]
    for net,rootref in [('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005')]:
        groups=F.graph(current,net);ri=next(i for i,xs in enumerate(groups) if any(q['kind']=='pad' and (q['ref'],q['pin'])==(rootref,'2') for q in xs))
        raw=next(q['net'] for q in groups[ri] if q['kind']=='pad');domain=h['domains_normalized'][net]
        holes=unary_union([s for p in h['pads'] if p['net']==raw for s in C.poly(p.get('hole') or [])]+[Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64) for v in h['vias'] if v['net']==raw])
        def gap(other):return .15 if h['domains_normalized'][C.norm(other)]==domain else .6
        legal={};cached={}
        for layer in LAYERS:
            obstacles=[q['shape'].buffer(gap(q['net'])+.025) for q in rec[layer] if q['net']!=raw]
            obstacles += [q['shape'].buffer(gap(q['net'])+.025) for q in zones if q['layer']==layer and q['net']!=raw]
            obstacles += [s.buffer(.275) for p in h['pads'] if p['net']!=raw for s in C.poly(p.get('hole') or [])]
            obstacles += [Point(v['x'],v['y']).buffer(v['drill']/2+.275,quad_segs=32) for v in h['vias'] if v['net']!=raw]
            obstacles += [s.buffer(.025) for rule in h['rule_areas'] if rule.get('no_zones') and layer in rule['layers'] for s in C.poly(rule['outline'])]
            legal[layer]=set_precision(outline.difference(unary_union(obstacles)),1e-6)
            print('RETURN_LEGAL',net,layer,get_num_coordinates(legal[layer]),flush=True)
            for width in (1.,.5,.35,.25):cached[layer,width]=polys(legal[layer].buffer(-width/2-.005))
        targets=[{q['uuid'] for q in xs if q['kind']=='pad' and q['pin']} for i,xs in enumerate(groups) if i!=ri and any(q['kind']=='pad' and q['pin'] for q in xs)]
        # Existing named groups with signal walls may have no usable annulus;
        # retain bounded negatives, never add a fictitious plane-only contact.
        for target in targets:
            groups=F.graph(current,net);root=next(xs for xs in groups if any(q['kind']=='pad' and (q['ref'],q['pin'])==(rootref,'2') for q in xs));rootpads={q['uuid'] for q in root if q['kind']=='pad'}
            if target<=rootpads:continue
            cluster=next(xs for xs in groups if any(q['kind']=='pad' and q['uuid'] in target for q in xs))
            source={layer:unary_union([q['shape'] for q in root if q['layer']==layer]).difference(holes) for layer in LAYERS}
            options=[]
            for q in cluster:
                if q['kind']!='via' or q['layer'] not in LAYERS:continue
                v=vias[q['uuid']];ann=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=32).difference(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64));layer=q['layer']
                if source[layer].is_empty:continue
                for width in (1.,.5,.35,.25):
                    for part in cached[layer,width]:
                        inner=part.buffer(-.00002);startarea=inner.intersection(ann);goal=inner.intersection(source[layer])
                        if startarea.area>1e-8 and goal.area>1e-8:options.append((startarea.distance(goal),layer,width,v['uuid'],part,startarea,goal))
            answer=None
            for distance,layer,width,vid,part,startarea,goal in sorted(options,key=lambda q:(-q[2],q[0])):
                if get_num_coordinates(part)>160000:
                    simpler=part.buffer(-.015).simplify(.005,preserve_topology=True).intersection(part)
                    candidates=[p for p in polys(simpler) if p.intersects(startarea) and p.intersects(goal)]
                    if not candidates:continue
                    part=max(candidates,key=lambda p:p.area);startarea=part.buffer(-.00002).intersection(startarea);goal=part.buffer(-.00002).intersection(goal)
                    if startarea.area<=1e-8 or goal.area<=1e-8:continue
                start,end=nearest_points(startarea,goal)
                try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))
                except (AssertionError,ValueError):continue
                points=[[round(x,6),round(y,6)] for x,y in points]
                if len(set(map(tuple,points)))<2:continue
                line=LineString(points);core=line.buffer(width/2,quad_segs=32)
                if not legal[layer].buffer(.000001).covers(core):continue
                outline_shape=set_precision(unary_union([p for p in polys(line.buffer(max(.6,width),quad_segs=32).intersection(legal[layer])) if p.intersection(core).area>1e-9]),1e-6)
                physical=set_precision(outline_shape.difference(holes),1e-6)
                v=vias[vid];ann=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=32).difference(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64))
                if physical.intersection(ann).area<.01 or physical.intersection(source[layer]).area<.01:continue
                uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-protected-return-restoration-r1/'+net+'/'+vid+'/'+layer+'/'+str(len(adds))))
                z={'uuid':uid,'net':raw,'layer':layer,'shape':physical,'zone_outline_shape':outline_shape,'clearance_mm':.15,'physical_Cu_drill_subtracted':True,'label':'Protected supply return restoration'}
                trial,cuts=N.projected(old,h,zones+adds+[z]);trialgroups=F.graph(trial,net);trialroot=next(xs for xs in trialgroups if any(q['kind']=='pad' and (q['ref'],q['pin'])==(rootref,'2') for q in xs));joined={q['uuid'] for q in trialroot if q['kind']=='pad'}
                record={'target_pad_UUIDs':sorted(target),'existing_landing_via_UUID':vid,'actual_existing_layer':layer,'length_mm':line.length,'minimum_core_width_mm':width,'points_mm':points,'source_overlap_mm2':physical.intersection(source[layer]).area,'target_annular_overlap_mm2':physical.intersection(ann).area,'all_target_pads_source_joined_after_full_projection':target<=joined,'all_preexisting_root_pads_retained':rootpads<=joined,'shape_uuid':uid,'search':search}
                attempted.append(record)
                if not target<=joined or not rootpads<=joined:continue
                adds.append(z);current=trial;answer=record;print('RETURN_ROOTED',net,vid,layer,line.length,width,flush=True);break
            rows.append({'net':net,'target_pad_UUIDs':sorted(target),'eligible_same_layer_routes':len(options),'repair':answer})
            write(OUT/'checkpoint.json',{'rows':rows,'attempted':attempted,'complete':False})
            (OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(adds,protocol=5))
        print('RETURN_BANK_COMPLETE',net,flush=True)
    model=OUT/'model.pkl';model.write_bytes(pickle.dumps((old,h,binding,zones+adds,current),protocol=5))
    (OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(adds,protocol=5))
    write(OUT/'receipt.json',{'verdict':'CONSTRUCTED_EXISTING_ANNULUS_RETURN_RESTORATION_MUTUAL_NATIVE_CURRENT_PENDING','baseline_model_sha256':sha(mp),'model_sha256':sha(model),'proposed_zones_sha256':sha(OUT/'proposed-zones.pkl'),'new_zone_shapes':len(adds),'new_holes':0,'old_Cu_deleted':0,'old_native_zone_outlines_changed':0,'rows':rows,'attempted_actual_source_projection_gates':attempted,'native_flashes_refill_DRC_source_current_and_complete_retained_contact_gates':'OPEN','board_written':False,'native_jobs':0,'adopted':False})
    print('RETURN_REPAIR_FROZEN',sha(model),len(adds),flush=True)
if __name__=='__main__':main()
