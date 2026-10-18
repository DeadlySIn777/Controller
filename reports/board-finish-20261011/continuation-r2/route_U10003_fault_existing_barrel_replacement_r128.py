"""Replace three B fault walls by one layer between two real existing barrels."""
import hashlib,json,pickle,sys,uuid
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
import tri_route as T
NET='/motherboard_do/DOA_FLT_N_FIELD';GND='/motherboard_motors/FIELD_GND'
IDS={'bd3e65f9-fe77-4a1f-88a1-c704d85af39f','ca9b0c5d-8d6f-44b2-8bec-780b6f1b3f3f','774ec021-d81e-471e-a8c8-0ea85fa50f67'}
OUT=H/'U10003-fault-two-existing-barrel-one-layer-replacement-r128'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=1)+'\n')
def polys(s):return [q for q in ([s] if s.geom_type=='Polygon' else getattr(s,'geoms',[])) if q.geom_type=='Polygon' and not q.is_empty]
def main():
    assert not OUT.exists();OUT.mkdir();mp=H/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl';assert sha(mp)=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e'
    g,h,b,z,full=pickle.loads(mp.read_bytes());pairs=[next(v for v in h['vias'] if v['uuid']==uid) for uid in ('2938cbdd-1d38-4238-9455-504b30f06e5e','1dfba07d-0355-46e7-abf9-ae2e8d1c9843')];assert all(C.norm(v['net'])==NET and v['d']==.6 and v['drill']==.3 and len(v['flashed'])==6 for v in pairs)
    hardh={**h,'tracks':[t for t in h['tracks'] if t['uuid'] not in IDS]};records,trees=F.build({**hardh,'zones':[]});roots=pickle.loads(mp.with_name('groups.pkl').read_bytes())[GND];ground=next(xs for xs in roots if any(q['kind']=='pad' and (q['ref'],q['pin'])==('J11003','2') for q in xs));refs={l:unary_union([q['shape'] for q in ground if q['layer']==l]) for l in ('In1.Cu','In4.Cu')}
    port_disks=unary_union([Point(v['x'],v['y']).buffer(.575,quad_segs=256) for v in pairs]);reference=refs['In1.Cu'].intersection(refs['In4.Cu']).union(port_disks)
    start,end=[Point(v['x'],v['y']) for v in pairs];rows=[];answer=None
    for layer in ('In2.Cu','In3.Cu','F.Cu','In4.Cu'):
        for margin in (4.,10.,20.):
            win=box(min(start.x,end.x)-margin,min(start.y,end.y)-margin,max(start.x,end.x)+margin,max(start.y,end.y)+margin);query=win.buffer(2.)
            obstacles=[]
            for j in trees[layer].query(query,predicate='intersects'):
                q=records[layer][int(j)]
                if C.norm(q['net'])==NET:continue
                gap=(.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][NET] else .6)+.025+.000020
                obstacles.append(N.bounded_buffer(q['shape'].intersection(query),gap+.1))
            for q in z:
                if q['layer']!=layer or C.norm(q['net'])==NET or not q['shape'].intersects(query):continue
                if C.norm(q['net'])==GND and layer in ('In2.Cu','In3.Cu'):continue # explicit new same-domain return role carve must follow
                gap=(.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][NET] else .6)+.025+.000020
                obstacles.append(N.bounded_buffer(q['shape'].intersection(query),max(gap,float(q.get('clearance_mm',.15))+.025+.000020)+.1))
            for p in h['pads']:
                if C.norm(p['net'])==NET:continue
                for hole in C.poly(p.get('hole') or []):
                    if hole.intersects(query):obstacles.append(N.bounded_buffer(hole,.275+.1+.000020))
            for v in h['vias']:
                if C.norm(v['net'])!=NET and query.intersects(Point(v['x'],v['y'])):obstacles.append(N.bounded_disk(v,v['drill']/2+.275+.1+.000020))
            for area in h['rule_areas']:
                if area.get('no_tracks') and layer in area['layers']:
                    obstacles.extend(N.bounded_buffer(s,.025+.1+.000020) for s in C.poly(area['outline']) if s.intersects(query))
            # Reserve the prospective ordinary ground landing needed after the
            # exact B wall is replaced; this is a hard geometry nomination.
            obstacles.append(Point(216.05,142.9945).buffer(.25+.175+.1+.000020,quad_segs=256))
            free=win.intersection(reference).difference(unary_union(obstacles));faces=[s for s in polys(free) if s.covers(start) and s.covers(end)]
            row={'layer':layer,'window_margin_mm':margin,'common_faces':len(faces)};rows.append(row);print('R128_FACE',row,flush=True)
            for face in faces:
                try:points,_=T.route(face,tuple(start.coords[0]),tuple(end.coords[0]))
                except (ValueError,AssertionError):continue
                points=[[round(x,6),round(y,6)] for x,y in points];axis=LineString(points);body=axis.buffer(.1,quad_segs=256)
                if not face.covers(axis):continue
                # The .575mm old-barrel caps are only nominees. The full
                # literal before-source-supported aperture proof is separate.
                rawgap={l:body.difference(refs[l]).area for l in refs};outside=body.difference(port_disks);gap={l:outside.difference(refs[l]).area for l in refs}
                if any(gap.values()):continue
                tracks=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-U10003-fault-r128/'+layer+'/'+str(i))),'net':pairs[0]['net'],'layer':layer,'a':a,'b':bb,'w':.2,'prospective_not_native':True} for i,(a,bb) in enumerate(zip(points,points[1:])) if a!=bb]
                test={**full,'tracks':[t for t in full['tracks'] if t['uuid'] not in IDS]+tracks};before=F.graph(full,NET);after=F.graph(test,NET);membership={k:i for i,xs in enumerate(after) for k in F.discrete_keys(xs)};losses=[]
                for i,xs in enumerate(before):
                    keys=F.discrete_keys(xs)-{('track',u) for u in IDS};missing=[list(k) for k in keys if k not in membership];dest={membership[k] for k in keys if k in membership}
                    if missing or len(dest)>1:losses.append({'old_group':i,'missing':missing,'after_groups':sorted(dest)})
                if losses:continue
                answer={'layer':layer,'points_mm':points,'tracks':tracks,'existing_native_barrels':pairs,'new_holes':0,'minimum_width_mm':.2,'length_mm':axis.length,'fault_old_retained_discrete_relationship_losses':losses,'raw_fullbody_ground_reference_gap_mm2':rawgap,'outside_bound_old_native_barrel_cap_gap_mm2':gap,'old_cap_before_source_support_NOT_YET_QUALIFIED':True,'new_ground_landing_reserved_mm':[216.05,142.9945],'all_other_native_keepouts_and_router_217_planning_reservations':'MANDATORY_SEPARATE_AUDIT'};break
            if answer:break
        if answer:break
    d={'tracks':answer['tracks'] if answer else [],'vias':[]};(OUT/'proposed-discrete.pkl').write_bytes(pickle.dumps(d,protocol=5))
    record={'verdict':'FAULT_EXISTING_BARREL_REPLACEMENT_NOMINATED_PAIRED_RETURN_AND_ALL_GATES_OPEN' if answer else 'FINITE_EXISTING_BARREL_REPLACEMENT_SEARCH_NO_NOMINEE','parent_model_sha256':sha(mp),'removed_exact_old_track_UUIDs':sorted(IDS),'rows':rows,'repair':answer,'proposed_discrete_sha256':sha(OUT/'proposed-discrete.pkl'),'native_jobs':0,'board_written':False,'adopted':False};write(OUT/'receipt.json',record);print('R128_COMPLETE',bool(answer),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
