"""Strict existing-annulus ground bridge restoration after protected antipads."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import hashlib,json,pickle,sys,uuid
from pathlib import Path
from shapely import set_precision,get_num_coordinates
from shapely.geometry import Point,LineString
from shapely.strtree import STRtree
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'field-power'));sys.path.insert(0,str(H/'sbc-power'))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
from guarded_declared_settings_projection_r58 import bounded_buffer,bounded_disk
import tri_route as T
OUT=H/'protected-field-return-restoration-r3';LAYERS=('In4.Cu','In2.Cu','In3.Cu','In1.Cu')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def polys(s):return [s] if s.geom_type=='Polygon' else [q for q in getattr(s,'geoms',[]) if q.geom_type=='Polygon']
def write(p,v):Path(p).write_text(json.dumps(v,indent=1)+'\n',encoding='utf-8')
def main():
    assert len(sys.argv)==2,'latest protected model.pkl'
    mp=Path(sys.argv[1]).resolve();assert mp.is_relative_to(H)
    receipt=json.loads(mp.with_name('receipt.json').read_bytes());assert sha(mp)==receipt['model_sha256']
    assert not OUT.exists();OUT.mkdir();old,h,binding,zones,current=pickle.loads(mp.read_bytes())
    zones,initial_guards=N.normalize_owned_via_guards(h,zones);current,initial_fill_retreats=N.projected(old,h,zones)
    rec,_=F.build({**h,'zones':[]});outline=unary_union(C.poly(h['outline'])).buffer(-.526);vias={v['uuid']:v for v in h['vias']};adds=[];rows=[];attempted=[]
    for net,rootref in [('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005')]:
        groups=F.graph(current,net);ri=next(i for i,xs in enumerate(groups) if any(q['kind']=='pad' and (q['ref'],q['pin'])==(rootref,'2') for q in xs));raw=next(q['net'] for q in groups[ri] if q['kind']=='pad');domain=h['domains_normalized'][net]
        holes=unary_union([s for p in h['pads'] if p['net']==raw for s in C.poly(p.get('hole') or [])]+[Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64) for v in h['vias'] if v['net']==raw])
        def gap(other):return .15 if h['domains_normalized'][C.norm(other)]==domain else .6
        legal={};cached={};cachedtrees={}
        for layer in LAYERS:
            obs=[bounded_buffer(q['shape'],max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025) for q in rec[layer] if q['net']!=raw]+[bounded_buffer(q['shape'],max(gap(q['net']),float(q.get('clearance_mm',.15)))+.025) for q in zones if q['layer']==layer and q['net']!=raw]
            obs += [bounded_buffer(s,.275) for p in h['pads'] if p['net']!=raw for s in C.poly(p.get('hole') or [])]+[bounded_disk(v,v['drill']/2+.275) for v in h['vias'] if v['net']!=raw]
            obs += [bounded_buffer(s,.025) for rule in h['rule_areas'] if rule.get('no_zones') and layer in rule['layers'] for s in C.poly(rule['outline'])]
            legal[layer]=set_precision(outline.difference(unary_union(obs)),1e-6);print('RETURN_LEGAL',net,layer,get_num_coordinates(legal[layer]),flush=True)
            for width in (1.,.5,.35,.25):cached[layer,width]=polys(legal[layer].buffer(-width/2-.005));cachedtrees[layer,width]=STRtree(cached[layer,width])
        targets=[{q['uuid'] for q in xs if q['kind']=='pad' and q['pin']} for i,xs in enumerate(groups) if i!=ri and any(q['kind']=='pad' and q['pin'] for q in xs)]
        for target in targets:
            groups=F.graph(current,net);root=next(xs for xs in groups if any(q['kind']=='pad' and (q['ref'],q['pin'])==(rootref,'2') for q in xs));rootpads={q['uuid'] for q in root if q['kind']=='pad'}
            if target<=rootpads:continue
            cluster=next(xs for xs in groups if any(q['kind']=='pad' and q['uuid'] in target for q in xs));source={l:unary_union([q['shape'] for q in root if q['layer']==l]).difference(holes) for l in LAYERS};options=[]
            for q in cluster:
                if q['kind']!='via' or q['layer'] not in LAYERS:continue
                v=vias[q['uuid']];ann=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=32).difference(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64));layer=q['layer']
                for width in (1.,.5,.35,.25):
                    for component_index in cachedtrees[layer,width].query(ann,predicate="intersects"):
                        part=cached[layer,width][int(component_index)]
                        inner=part.buffer(-.00002);aa=inner.intersection(ann);bb=inner.intersection(source[layer])
                        if aa.area>1e-8 and bb.area>1e-8:options.append((aa.distance(bb),layer,width,v['uuid'],part,aa,bb))
            answer=None
            for distance,layer,width,vid,part,aa,bb in sorted(options,key=lambda q:(q[0],-q[2])):
                if get_num_coordinates(part)>160000:
                    simple=part.buffer(-.015).simplify(.005,preserve_topology=True).intersection(part);pieces=[p for p in polys(simple) if p.intersects(aa) and p.intersects(bb)]
                    if not pieces:continue
                    part=max(pieces,key=lambda p:p.area);aa=part.buffer(-.00002).intersection(aa);bb=part.buffer(-.00002).intersection(bb)
                    if aa.area<=1e-8 or bb.area<=1e-8:continue
                start,end=nearest_points(aa,bb)
                chord=LineString([start,end])
                if part.covers(chord):points=list(chord.coords);search={'method':'exact_covered_nearest_chord'}
                else:
                    try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))
                    except (AssertionError,ValueError):continue
                points=[[round(x,6),round(y,6)] for x,y in points]
                if len(set(map(tuple,points)))<2:continue
                line=LineString(points);core=line.buffer(width/2,quad_segs=32)
                if not legal[layer].buffer(.000001).covers(core):continue
                nativeoutline=set_precision(unary_union([p for p in polys(line.buffer(max(.6,width),quad_segs=32).intersection(legal[layer])) if p.intersection(core).area>1e-9]),1e-6);physical=set_precision(nativeoutline.difference(holes),1e-6)
                v=vias[vid];ann=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=32).difference(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64))
                if physical.intersection(ann).area<.01 or physical.intersection(source[layer]).area<.01:continue
                uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-protected-return-r1/'+net+'/'+vid+'/'+layer+'/'+str(len(adds))));z={'uuid':uid,'net':raw,'layer':layer,'shape':physical,'zone_outline_shape':nativeoutline,'clearance_mm':.15,'physical_Cu_drill_subtracted':True,'label':'Protected supply return restoration'}
                guarded,via_guards=N.normalize_owned_via_guards(h,zones+adds+[z]);z=next(q for q in guarded if q['uuid']==uid);trial,cuts=N.projected(old,h,guarded);gs=F.graph(trial,net);tr=next(xs for xs in gs if any(q['kind']=='pad' and (q['ref'],q['pin'])==(rootref,'2') for q in xs));joined={q['uuid'] for q in tr if q['kind']=='pad'}
                record={'target_pad_UUIDs':sorted(target),'landing_via':vid,'layer':layer,'length_mm':line.length,'minimum_core_width_mm':width,'points_mm':points,'source_overlap_mm2':physical.intersection(source[layer]).area,'target_annular_overlap_mm2':physical.intersection(ann).area,'all_target_pads_source_joined_after_full_projection':target<=joined,'all_preexisting_root_pads_retained':rootpads<=joined,'shape_uuid':uid,'search':search,'new_outward_via_guards':via_guards};attempted.append(record)
                if not target<=joined or not rootpads<=joined:continue
                adds.append(z);current=trial;answer=record;print('RETURN_ROOTED',net,vid,layer,line.length,width,flush=True);break
            rows.append({'net':net,'target_pad_UUIDs':sorted(target),'eligible_routes':len(options),'repair':answer});write(OUT/'checkpoint.json',{'rows':rows,'attempted':attempted,'complete':False});(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(adds,protocol=5))
        print('RETURN_BANK_COMPLETE',net,flush=True)
    model=OUT/'model.pkl';model.write_bytes(pickle.dumps((old,h,binding,zones+adds,current),protocol=5));(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(adds,protocol=5))
    write(OUT/'receipt.json',{'verdict':'EXISTING_ANNULUS_RETURN_RESTORATION_MUTUAL_NATIVE_CURRENT_PENDING','baseline_model_sha256':sha(mp),'model_sha256':sha(model),'proposed_zones_sha256':sha(OUT/'proposed-zones.pkl'),'new_zone_shapes':len(adds),'new_holes':0,'old_Cu_deleted':0,'old_native_zone_outlines_changed':0,'rows':rows,'attempted_actual_source_projection_gates':attempted,'full_mutual_retained_contacts_source_current_native_flashes_refill_and_DRC':'OPEN','initial_outward_owned_via_guards':initial_guards,'initial_old_fill_retreats':initial_fill_retreats,'script_sha256':sha(Path(__file__)),'finite_construction_search_not_no_path_proof':True,'current_width_barrel_thermal_mesh_qualification':'OPEN','board_written':False,'native_jobs':0,'adopted':False});print('RETURN_REPAIR_FROZEN',sha(model),len(adds),flush=True)
if __name__=='__main__':main()
