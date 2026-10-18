"""Supplement every retained CORE named-pad island from the real shunt output.

Owned new F copper only. Original LOGIC fill may retreat; all frozen field and
new return copper and every discrete object remain obstacles/unchanged.
"""
import pickle,json,uuid,hashlib,math
from pathlib import Path
from shapely import set_precision,STRtree
from shapely.geometry import LineString,box
from shapely.ops import unary_union,nearest_points
import complete_geometry_r2 as G
import zone_projection_r1 as P
import io3_contact_restore_r2 as Q
import continuous_path_fast_r1 as CP
L=G.L;p=G.p;R=G.B.J.R;NET=p.norm(L.stage.caps.CORE);OUT=L.OUT/'core-retained-f-feeds-r17'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir();file=L.OUT/'io3-field-crossings-r15/model.pkl';g,h,binding,zones,candidate=pickle.loads(file.read_bytes());binding['r15_complete_IO3_contact_model_sha256']=sha(file)
    changed={q['uuid'] for q in zones if q.get('old_contact_group') is not None or q.get('field_return_proposal') and q['layer']=='In2.Cu' or q['label']=='CORE-main-In2'}
    for q in zones:
        if q['uuid'] in changed:q['shape']=set_precision(q['shape'],1e-6)
    previous=L.OUT/'core-retained-f-feeds-r16/checkpoint.json';previous_receipt=json.loads(previous.read_text());binding['reused_CORE_F_constructed_checkpoint_sha256']=sha(previous)
    for q in previous_receipt['new_feed_polygons']:
        f=Path(q['geometry_file']);assert sha(f)==q['geometry_sha256'];from shapely import from_wkb
        zones.append({**q,'shape':set_precision(from_wkb(f.read_bytes()),1e-6)})
    candidate,cuts=P.projected(g,h,zones);Q.NET=NET;groups,parts,assign=Q.groups(candidate,return_details=True);lookup={q['uuid']:i for i,rows in enumerate(groups) for q in rows};sourcepad=next(q for q in h['pads'] if q['ref']=='R11022' and q['num']=='2');root=lookup[sourcepad['uuid']];targets=[i for i,rows in enumerate(groups) if i!=root and any(not q['ref'].startswith('@') for q in rows)];targets.sort(key=lambda i:sum(not q['ref'].startswith('@') for q in groups[i]),reverse=True)
    originalids={q['uuid'] for q in g['zones']};model={**candidate,'zones':[q for q in candidate['zones'] if not(q['uuid'] in originalids and p.norm(q['net'])=='/LOGIC_GND')]};window=box(.526,.526,449.474,234.474);p.WINDOW=window;board=unary_union(p.base.polygons(g['outline'])).buffer(-.525)
    frees={}
    for layer in ('F.Cu','B.Cu'):
        free=set_precision(R.free_layer(model,NET,layer,window,reference_guard=None,allow_own_via_connection=True).intersection(board),1e-6)
        guards=[]
        for z in candidate['zones']:
            if z['uuid'] in originalids and p.norm(z['net']) not in (NET,'/LOGIC_GND'):
                clear=max(G.gap(candidate,NET,z['net']),float(z['clearance_mm']))+.025
                guards += [q.buffer(clear) for q in p.base.polygons(z['fills'].get(layer,[]))]
        free=set_precision(free.difference(unary_union(guards)),1e-6);frees[layer]=free;(OUT/('CORE-'+layer+'-native-discrete-free.wkb')).write_bytes(free.wkb);print('CORE_OUTER_FREE',layer,free.area,'source',root,'targets',targets,flush=True)
    joined={root};fingers=[];fail=[];attempts=[]
    for group in targets:
        found=None
        for layer in ('F.Cu','B.Cu'):
          free=frees[layer];source=unary_union([q for q,i in zip(parts[layer],assign[layer]) if i in joined]+[q['shape'] for q in fingers if q['layer']==layer]);target=unary_union([q for q,i in zip(parts[layer],assign[layer]) if i==group])
          if source.is_empty or target.is_empty:continue
          aa,bb=nearest_points(source,target);bd=LineString([aa,bb]).bounds
          for margin in (3.,10.,30.,90.):
            local=free.intersection(box(max(.526,bd[0]-margin),max(.526,bd[1]-margin),min(449.474,bd[2]+margin),min(234.474,bd[3]+margin)));comps=p.hubs.components(local);tree=STRtree(comps);shared=set(map(int,tree.query(source,predicate='intersects')))&set(map(int,tree.query(target,predicate='intersects')))
            if not shared:continue
            usable=unary_union([comps[i] for i in shared])
            for width in (1.25,1.,.75,.5,.35,.25,.20):
                centre=set_precision(usable.buffer(-width/2),1e-6);options=[]
                for part in p.hubs.components(centre):
                    a=part.intersection(source);b=part.intersection(target)
                    if a.is_empty or b.is_empty:continue
                    an,bn=nearest_points(a,b);start=a.intersection(an.buffer(.2)).representative_point().coords[0];end=b.intersection(bn.buffer(.2)).representative_point().coords[0];options.append((math.dist(start,end),part,start,end))
                for _,part,start,end in sorted(options,key=lambda q:q[0])[:3]:
                    print('CORE_F_SEARCH',group,margin,width,part.area,flush=True);route=CP.path(part,start,end,node_cap=500000);attempts.append({'group':group,'width_mm':width,'margin_mm':margin,'verdict':route['verdict']})
                    if route['verdict']!='HOST_PATH':continue
                    # Wider bodies are actual copper contained in the exact free
                    # model. Only the certified minimum core is credited here.
                    route_line=LineString(route['points']);core=set_precision(route_line.buffer(width/2).intersection(free),1e-6);shape=set_precision(route_line.buffer(2.).intersection(free),1e-6)
                    shape=unary_union([x for x in p.hubs.components(shape) if x.intersects(core)])
                    if shape.intersection(source).area<=1e-8 or shape.intersection(target).area<=1e-8:continue
                    found=layer,width,route,shape;break
                if found:break
            if found:break
          if found:break
        if found is None:fail.append({'group':group,'contacts':groups[group]});print('CORE_F_UNRESOLVED',group,flush=True)
        else:
            layer,width,route,shape=found;uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-core-full-retained-outer-feed-r17-'+str(group)));f=OUT/('CORE-r17-feed-'+str(group)+'.wkb');f.write_bytes(shape.wkb);q={'uuid':uid,'label':'CORE-r17-retained-outer-feed-'+str(group),'net':sourcepad['net'],'layer':layer,'shape':shape,'minimum_constructed_core_mm':width,'route':route,'old_contact_group':group,'contacts':groups[group],'geometry_file':str(f.resolve()),'geometry_sha256':sha(f),'original_LOGIC_GND_fill_retreat_required':True};fingers.append(q);joined.add(group);print('CORE_F_JOINED',group,layer,width,route['length_mm'],flush=True)
        (OUT/'checkpoint.json').write_text(json.dumps({'joined':sorted(joined),'unresolved':fail,'new_feed_polygons':[{k:v for k,v in q.items() if k!='shape'} for q in fingers],'attempts':attempts},indent=2)+'\n')
    finalzones=zones+fingers;final,cuts=P.projected(g,h,finalzones);(OUT/'model.pkl').write_bytes(pickle.dumps((g,h,binding,finalzones,final),protocol=5));Q.NET=NET;after,_,_=Q.groups(final,return_details=True);lookup={q['uuid']:i for i,rows in enumerate(after) for q in rows};sourcegroup=lookup[sourcepad['uuid']];allpads=[{'group':i,'source_connected':i==sourcegroup,**q} for i,rows in enumerate(after) for q in rows if not q['ref'].startswith('@')]
    (OUT/'receipt.json').write_text(json.dumps({'verdict':'CORE_RETAINED_F_FEED_CONSTRUCTION','binding':binding,'source_endpoint':'R11022.2','source_group':sourcegroup,'fingers':[{k:v for k,v in q.items() if k!='shape'} for q in fingers],'unresolved':fail,'all_CORE_named_pads':allpads,'old_zone_retreats':cuts,'new_holes':0,'native_jobs':0,'board_written':False,'retained_branch_currents_F_fanout_reference_drop_and_native_gates_open':True},indent=2)+'\n');print('CORE_F_COMPLETE',len(fingers),'unresolved',len(fail),'unrooted_named_pads',sum(not q['source_connected'] for q in allpads),flush=True)
if __name__=='__main__':main()
