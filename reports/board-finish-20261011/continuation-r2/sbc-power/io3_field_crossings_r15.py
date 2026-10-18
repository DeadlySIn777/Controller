"""Construct bounded In2 field-plane crossing alternatives on exact native base.

Retain all discrete copper and holes. Each changed field return is explicitly
carved, with In1/In4 left unchanged and current/contact gates still required.
"""
import pickle,json,uuid,hashlib,math
from pathlib import Path
from shapely import set_precision,STRtree
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
import complete_geometry_r2 as G
import zone_projection_r1 as P
import io3_contact_restore_r2 as Q
import continuous_path_fast_r1 as CP
L=G.L;p=G.p;R=G.B.J.R;NET='/IO_3V3';OUT=L.OUT/'io3-field-crossings-r15'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir()
    cache=L.OUT/'io3-endpoint-diagnostic-r14b/model.pkl';g,h,binding,zones,candidate,groups,parts,assign,root,unresolved=pickle.loads(cache.read_bytes());binding['r14_exact_cache_sha256']=sha(cache)
    field={q['uuid']:q for q in zones if q.get('field_return_proposal') and q['layer']=='In2.Cu'}
    assert len(field)==3
    oldsh={u:q['shape'] for u,q in field.items()};originalzoneids={q['uuid'] for q in g['zones']};board=unary_union(p.base.polygons(g['outline'])).buffer(-.525)
    joined={root};fingers=[];fail=[];attempts=[];layer='In2.Cu';window=box(.526,.526,449.474,234.474);p.WINDOW=window
    route_model={**candidate,'zones':[q for q in candidate['zones'] if q['uuid'] not in field]}
    free=set_precision(R.free_layer(route_model,NET,layer,window,(L.stage.caps.CORE,),reference_guard=None,allow_own_via_connection=True).intersection(board),1e-6)
    (OUT/'crossing-free.wkb').write_bytes(free.wkb);print('CROSSING_FREE',free.area,flush=True)
    core=next(q for q in zones if q['label']=='CORE-main-In2')
    for oldid,newid in unresolved.items():
        source=unary_union([q for q,i in zip(parts[layer],assign[layer]) if i in joined]+[q['shape'] for q in fingers]);target=unary_union([q for q,i in zip(parts[layer],assign[layer]) if i==newid]);found=None
        aa,bb=nearest_points(source,target);bd=LineString([aa,bb]).bounds
        for margin in (3.,10.,30.,90.):
            local=free.intersection(box(max(.526,bd[0]-margin),max(.526,bd[1]-margin),min(449.474,bd[2]+margin),min(234.474,bd[3]+margin)))
            components=p.hubs.components(local);tree=STRtree(components);shared=set(map(int,tree.query(source,predicate='intersects')))&set(map(int,tree.query(target,predicate='intersects')))
            if not shared:continue
            usable=unary_union([components[i] for i in shared])
            for width in (1.25,1.,.75,.5,.35,.25,.20):
                centre=set_precision(usable.buffer(-width/2),1e-6);options=[]
                for part in p.hubs.components(centre):
                    a=part.intersection(source);b=part.intersection(target)
                    if a.is_empty or b.is_empty:continue
                    an,bn=nearest_points(a,b);start=a.intersection(an.buffer(.2)).representative_point().coords[0];end=b.intersection(bn.buffer(.2)).representative_point().coords[0];options.append((math.dist(start,end),part,start,end))
                for _,part,start,end in sorted(options,key=lambda r:r[0])[:3]:
                    print('CROSSING_SEARCH',oldid,margin,width,part.area,flush=True);route=CP.path(part,start,end,node_cap=500000);attempts.append({'group':oldid,'margin':margin,'width_mm':width,'verdict':route['verdict']})
                    if route['verdict']!='HOST_PATH':continue
                    shape=set_precision(LineString(route['points']).buffer(width/2).intersection(free),1e-6)
                    if not shape.intersects(source) or not shape.intersects(target):continue
                    found=width,route,shape;break
                if found:break
            if found:break
        if found is None:fail.append(oldid);print('CROSSING_UNRESOLVED',oldid,flush=True)
        else:
            width,route,shape=found;uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-io3-field-crossing-r15-'+str(oldid)));q={'uuid':uid,'label':'IO3-r15-field-crossing-'+str(oldid),'net':NET,'layer':layer,'shape':shape,'width_mm':width,'route':route,'old_contact_group':oldid,'old_contacts':groups[newid]};fingers.append(q);joined.add(newid)
            core['shape']=set_precision(core['shape'].difference(shape.buffer(.175)),1e-6)
            for z in field.values():z['shape']=set_precision(z['shape'].difference(shape.buffer(.625)),1e-6)
            print('CROSSING_CONSTRUCTED',oldid,width,route['length_mm'],flush=True)
        (OUT/'checkpoint.json').write_text(json.dumps({'unresolved':fail,'joined':sorted(joined),'fingers':[{k:v for k,v in q.items() if k!='shape'} for q in fingers],'attempts':attempts},indent=2)+'\n')
    finalzones=zones+fingers;led=[]
    for uid,q in field.items():
        removed=oldsh[uid].difference(q['shape']);f=OUT/('field-In2-removed-'+uid+'.wkb');f.write_bytes(removed.wkb);led.append({'uuid':uid,'net':q['net'],'old_sha256':hashlib.sha256(oldsh[uid].wkb).hexdigest(),'new_sha256':hashlib.sha256(q['shape'].wkb).hexdigest(),'removed_area_mm2':removed.area,'removed_file':str(f.resolve()),'removed_file_sha256':sha(f),'bounds':removed.bounds if not removed.is_empty else None,'unchanged_In1_In4':True})
    final,cuts=P.projected(g,h,finalzones);Q.NET=NET;after,_,_=Q.groups(final,return_details=True);oldmain=json.loads((L.OUT/'coupled-power-geometry-frozen-r13/initial-contact-partitions.json').read_text())['old_main_contacts'];ids={q['uuid']:i for i,rows in enumerate(after) for q in rows};oldsplit={str(ids[q['uuid']]):[] for q in oldmain}
    for q in oldmain:oldsplit[str(ids[q['uuid']])].append(q)
    (OUT/'model.pkl').write_bytes(pickle.dumps((g,h,binding,finalzones,final),protocol=5))
    (OUT/'receipt.json').write_text(json.dumps({'verdict':'CONSTRUCTED_ALTERNATE_CONTACT_CURRENT_NATIVE_GATES_OPEN','binding':binding,'field_In2_exact_delta':led,'fingers':[{k:v for k,v in q.items() if k!='shape'} for q in fingers],'unresolved':fail,'old_main_original_contacts':len(oldmain),'old_main_final_group_sizes':{k:len(v) for k,v in oldsplit.items()},'old_main_final_groups':oldsplit,'old_zone_retreats':cuts,'new_holes':0,'native_jobs':0,'board_written':False},indent=2)+'\n')
    print('CROSSING_FINAL_OLD_IO3_GROUPS',{k:len(v) for k,v in oldsplit.items()},flush=True)
if __name__=='__main__':main()
