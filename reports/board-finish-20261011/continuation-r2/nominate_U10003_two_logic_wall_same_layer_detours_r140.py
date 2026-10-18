"""Coupled wall detours reserve one ordinary FG via; all sources remain literal."""
import hashlib,json,pickle,re,sys,uuid
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
import tri_route as T
OUT=H/'U10003-two-logic-wall-source-referenced-detour-nominees-r140'
IDS={'eeb33c09-9494-4734-b174-e3c3ceffd73b','8f7ea41c-9cfd-4c25-a376-00657f6105ed'}
SITE=(215.4,142.05);GND='/LOGIC_GND';FG='/motherboard_motors/FIELD_GND'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def polys(s):return [q for q in ([s] if s.geom_type=='Polygon' else getattr(s,'geoms',[])) if q.geom_type=='Polygon' and not q.is_empty]
def main():
    assert not OUT.exists();OUT.mkdir();mp=H/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl';assert sha(mp)=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e'
    g,h,b,z,full=pickle.loads(mp.read_bytes());groups=pickle.loads(mp.with_name('groups.pkl').read_bytes())
    root=next(xs for xs in groups[GND] if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11001','2')for q in xs));refs={l:unary_union([q['shape']for q in root if q['layer']==l and q['kind']=='fill'])for l in ('In1.Cu','In4.Cu')}
    hard={**full,'tracks':[t for t in full['tracks']if t['uuid']not in IDS]};records,trees=F.build(hard)
    reserved=C.BASE/'recovery-composite/c06/alternate-r07';areas=json.loads((reserved/'reserved-r07.json').read_bytes())['keepouts'];dru=(reserved/'reserve/board.kicad_dru').read_text();exceptions={}
    for line in dru.splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)" \(constraint disallow track via\)\)',line.strip())
        if m:exceptions[m[1]]={C.norm(n)for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
    attempts=[];routes=[]
    for uid in sorted(IDS):
        old=next(t for t in h['tracks']if t['uuid']==uid);net=C.norm(old['net']);layer=old['layer'];ref_layer='In1.Cu'if layer=='F.Cu'else'In4.Cu';ref=refs[ref_layer]
        start,end=map(Point,(old['a'],old['b']));before_body=C.body(old);oldgap=before_body.difference(ref)
        print('R140_OLD_REFERENCE',uid,ref_layer,oldgap.area,oldgap.is_empty,flush=True)
        chosen=None
        for margin in (3.,7.,15.):
            win=box(min(start.x,end.x)-margin,min(start.y,end.y)-margin,max(start.x,end.x)+margin,max(start.y,end.y)+margin);query=win.buffer(2.);obs=[]
            for j in trees[layer].query(query,predicate='intersects'):
                q=records[layer][int(j)]
                if C.norm(q['net'])==net:continue
                gap=(.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][net]else .6)+.025+.000020
                obs.append(N.bounded_buffer(q['shape'].intersection(query),gap+.1+.000020))
            for p in h['pads']:
                for sh in C.poly(p.get('hole')or[]):
                    if sh.intersects(query):obs.append(N.bounded_buffer(sh,.275+.1+.000020))
            for v in h['vias']:
                if query.covers(Point(v['x'],v['y'])):obs.append(N.bounded_disk(v,v['drill']/2+.275+.1+.000020))
            for a in h['rule_areas']:
                if a.get('no_tracks')and layer in a['layers']:obs.extend(N.bounded_buffer(s,.025+.1+.000020)for s in C.poly(a['outline'])if s.intersects(query))
            for a in areas:
                if net not in exceptions.get(a['name'],set())and layer in a['layers']:obs.extend(N.bounded_buffer(s,.025+.1+.000020)for s in C.poly(a['outline'])if s.intersects(query))
            obs.append(Point(SITE).buffer(.25+.625+.1+.000020,quad_segs=256))
            free=win.intersection(ref.buffer(-.1-.000020,quad_segs=256)).difference(unary_union(obs))
            faces=[s for s in polys(free)if s.covers(start)and s.covers(end)]
            row={'wall_UUID':uid,'layer':layer,'actual_source_reference_layer':ref_layer,'margin_mm':margin,'common_faces':len(faces),'start_in_reference':ref.covers(start),'end_in_reference':ref.covers(end),'old_full_body_gap_mm2':oldgap.area};attempts.append(row);print('R140_FACE',json.dumps(row),flush=True)
            for face in faces:
                line=LineString([start,end])
                if face.covers(line):points=list(line.coords)
                else:
                    try:points,_=T.route(face,tuple(start.coords[0]),tuple(end.coords[0]))
                    except(ValueError,AssertionError):continue
                points=[[round(x,6),round(y,6)]for x,y in points];axis=LineString(points);body=axis.buffer(.1,quad_segs=256)
                if not face.covers(axis)or not body.difference(ref).is_empty:continue
                new=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-U10003-two-logic-wall-r140/'+uid+'/'+str(i))),'net':old['net'],'layer':layer,'a':a,'b':bb,'w':.2,'prospective_not_native':True}for i,(a,bb)in enumerate(zip(points,points[1:]))if a!=bb]
                chosen={'old':old,'tracks':new,'length_mm':axis.length,'new_full_body_reference_gap_empty':True,'new_full_body_WKB_sha256':hashlib.sha256(body.wkb).hexdigest()};routes.append(chosen);break
            if chosen:break
    d={'tracks':[t for r in routes for t in r['tracks']],'vias':[]};(OUT/'proposed-discrete.pkl').write_bytes(pickle.dumps(d,protocol=5))
    receipt={'verdict':'TWO_WALL_DETOUR_NOMINEES_INDEPENDENT_GROUND_CONTACT_CLEARANCE_REFILL_OPEN'if len(routes)==2 else'FINITE_TRUE_SOURCE_REFERENCED_LOGIC_WALL_DETOUR_INCOMPLETE','parent_model_sha256':sha(mp),'reserved_ordinary_ground_site_mm':SITE,'bound_old_wall_UUIDs':sorted(IDS),'source_ROOT':'J11001.2','attempts':attempts,'routes':routes,'proposed_discrete_sha256':sha(OUT/'proposed-discrete.pkl'),'native_jobs':0,'board_written':False,'adopted':False}
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print('R140_COMPLETE',len(routes),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
