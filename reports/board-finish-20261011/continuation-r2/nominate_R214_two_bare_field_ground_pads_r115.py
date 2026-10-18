"""Fresh ordinary fanout nominees on exact R214; no withdrawn old walls."""
import copy,hashlib,json,math,pickle,re,sys,uuid
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent
for directory in ('field-power','sbc-power'):sys.path.insert(0,str(H/directory))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
import tri_route as T
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
NET='/motherboard_motors/FIELD_GND'
OUT=H/'R214-two-bare-field-ground-ordinary-fanout-nominees-r115'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=1)+'\n')
def polys(s):return [q for q in ([s] if s.geom_type=='Polygon' else getattr(s,'geoms',[])) if q.geom_type=='Polygon' and not q.is_empty]
def main():
    head=H/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214';mp=head/'model.pkl'
    assert sha(mp)=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e'
    assert sha(head/'receipt.json')=='e8eaa4704155b733da2bf32b241a5dcca98d08b5d24d8e7b1ecf4e9b4df73d9e'
    assert not OUT.exists();OUT.mkdir()
    g,h,b,z,full=pickle.loads(mp.read_bytes());groups=pickle.loads((head/'groups.pkl').read_bytes())[NET]
    root=next(xs for xs in groups if any(q['kind']=='pad' and (q['ref'],q['pin'])==('J11003','2') for q in xs))
    sources={l:unary_union([q['shape'] for q in root if q['layer']==l]) for l in LAYERS}
    records,trees=F.build(full)
    domain=h['domains_normalized'][NET]
    def gap(net):return (.15 if h['domains_normalized'][C.norm(net)]==domain else .6)+.025+.000020
    holes=[s for p in h['pads'] for s in C.poly(p.get('hole') or [])]+[N.bounded_disk(v,v['drill']/2) for v in h['vias']]
    smd=[s for p in h['pads'] if p['smd'] for rs in p['layers'].values() for s in C.poly(rs)]
    ht=STRtree(holes);st=STRtree(smd)
    reserve=C.BASE/'recovery-composite/c06/alternate-r07';areas=json.loads((reserve/'reserved-r07.json').read_bytes())['keepouts'];dru=(reserve/'reserve/board.kicad_dru').read_text();exceptions={}
    for line in dru.splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m:exceptions[m[1]]={C.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
    # Use the exact existing planning-barrier inventory rather than guessing
    # a footprint exclusion. Its own outward pad escape is separately scoped.
    import core_inner_feed_r18 as I
    I.p.WINDOW=box(.526,.526,449.474,234.474)
    outline=unary_union(C.poly(h['outline'])).buffer(-.526)
    # hard_shapes expects explicit exemption sets; attach the source-authorized
    # sets from the saved router reservation rule text to those exact rows.
    for area in areas:area['exempt']=exceptions.get(area['name'],set())
    hard={l:I.p.hard_shapes(h,areas,NET,l) for l in LAYERS}
    viahard=[s for l in LAYERS for s in I.p.hard_shapes(h,areas,NET,l,for_via=True)]
    targets=[('U10003','9','4021795d-90df-4df0-a1b4-13cdcbdd91ac',.026),('U11025','2','d64c464d-de71-4c7e-9d98-b870e2ad977f',.001)]
    rows=[];new={'vias':[],'tracks':[]}
    for ref,pin,uid,current in targets:
        pad=next(p for p in h['pads'] if p['uuid']==uid);assert (pad['ref'],pad['num'])==(ref,pin) and C.norm(pad['net'])==NET
        layer=next(iter(pad['layers']));padshape=unary_union(C.poly(pad['layers'][layer]));point=Point(pad['x'],pad['y'])
        ownhard=hard[layer];corridor=None
        if ref=='U10003':
            foot=next(q for q in h['footprints'] if q['ref']==ref);courts=[s.buffer(.6) for rs in foot['courtyard'].values() for s in C.poly(rs)]
            corridor=box(pad['x']+.55,pad['y']-.21,pad['x']+2.5,pad['y']+.21)
            assert all(corridor.bounds[0]>p['x'] for p in h['pads'] if p['ref']==ref)
            found=[s for s in ownhard if any(s.equals(c) for c in courts)];assert len(found)==len(courts)>0
            ownhard=[s.difference(corridor) if any(s.equals(c) for c in courts) else s for s in ownhard]
        answer=None;attempts=[]
        for radius in (2.,5.,10.):
            win=box(point.x-radius,point.y-radius,point.x+radius,point.y+radius);query=win.buffer(2.)
            viaobs=[];trackobs=[]
            for l in LAYERS:
                for j in trees[l].query(query,predicate='intersects'):
                    q=records[l][int(j)]
                    if C.norm(q['net'])==NET:continue
                    n=gap(q['net']);viaobs.append(N.bounded_buffer(q['shape'].intersection(query),.25+n))
                    if l==layer:trackobs.append(N.bounded_buffer(q['shape'].intersection(query),n))
            for j in ht.query(query,predicate='intersects'):
                sh=holes[int(j)];viaobs.append(N.bounded_buffer(sh,.375+.000020));trackobs.append(N.bounded_buffer(sh,.275+.000020))
            for j in st.query(query,predicate='intersects'):viaobs.append(N.bounded_buffer(smd[int(j)],.375+.000020))
            viaobs.extend(N.bounded_buffer(s,.25+.025+.000020) for s in viahard if s.intersects(query))
            trackobs.extend(N.bounded_buffer(s,.025+.000020) for s in ownhard if s.intersects(query))
            for v in new['vias']:viaobs.append(N.bounded_disk(v,(v['drill']+.2)/2+.275+.000020))
            landing=win.intersection(outline.buffer(-.25)).difference(unary_union(viaobs))
            free=win.intersection(outline).difference(unary_union(trackobs)).buffer(-.1-.000020)
            faces=[s for s in polys(free) if s.intersects(padshape.buffer(-.000020))]
            options=[]
            for inner in ('In1.Cu','In4.Cu','In2.Cu','In3.Cu'):
                for face in faces:
                    for piece in polys(landing.intersection(face).intersection(N.bounded_buffer(sources[inner],.2))):
                        for p in (piece.representative_point(),nearest_points(piece,point)[0],piece.centroid):
                            if piece.covers(p):options.append((point.distance(p),inner,p,face))
            print('R115_SITE',ref,radius,'landing',landing.area,'faces',len(faces),'nominees',len(options),flush=True)
            attempts.append({'radius_mm':radius,'all6_hard_landing_area_mm2':landing.area,'outer_escape_faces':len(faces),'candidate_points':len(options)})
            for _,inner,p,face in sorted(options,key=lambda q:q[:2]):
                site=Point(round(p.x,6),round(p.y,6));ann=N.bounded_disk({'x':site.x,'y':site.y},.25).difference(N.bounded_disk({'x':site.x,'y':site.y},.1))
                if not landing.covers(site) or not face.covers(site) or ann.intersection(sources[inner]).area<.01:continue
                start=nearest_points(face.intersection(padshape.buffer(-.000020)),point)[0];line=LineString([start,site])
                if face.covers(line):points=list(line.coords)
                else:
                    try:points,_=T.route(face,tuple(start.coords[0]),tuple(site.coords[0]))
                    except (ValueError,AssertionError):continue
                points=[[round(x,6),round(y,6)] for x,y in points]
                if len(set(map(tuple,points)))<2:continue
                vid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-R214-FG-r115/'+uid+'/via/'+repr((site.x,site.y))))
                via={'uuid':vid,'net':pad['net'],'x':site.x,'y':site.y,'d':.5,'drill':.2,'flashed':LAYERS.copy(),'prospective_not_native':True}
                ts=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,vid+'/track/'+str(i))),'net':pad['net'],'a':a,'b':bb,'w':.2,'layer':layer,'prospective_not_native':True} for i,(a,bb) in enumerate(zip(points,points[1:])) if a!=bb]
                answer={'ref':ref,'pin':pin,'pad_UUID':uid,'raw_net':pad['net'],'planning_return_current_A':current,'ordinary_via':via,'tracks':ts,'actual_J3_source_layer':inner,'actual_source_annular_overlap_mm2':ann.intersection(sources[inner]).area,'all_native_filled_foreign_Cu_hard':True,'own_only_planning_escape_corridor_bounds':list(corridor.bounds) if corridor is not None else None,'length_mm':LineString(points).length,'coupled_source_contact_native_reference_fullbody_current_gates':'OPEN'}
                new['vias'].append(via);new['tracks']+=ts;break
            if answer:break
        rows.append({'ref':ref,'pin':pin,'repair_nominee':answer,'attempts':attempts});write(OUT/'checkpoint.json',rows)
    (OUT/'proposed-discrete.pkl').write_bytes(pickle.dumps(new,protocol=5))
    receipt={'verdict':'R214_ORDINARY_FIELD_GROUND_NOMINEES_ONLY_FULL_GATES_OPEN' if any(q['repair_nominee'] for q in rows) else 'R214_FINITE_HARD_NATIVE_FILL_FIELD_GROUND_SEARCH_NO_NOMINEE','parent_model_sha256':sha(mp),'parent_receipt_sha256':sha(head/'receipt.json'),'script_sha256':sha(__file__),'rows':rows,'new_vias':len(new['vias']),'new_tracks':len(new['tracks']),'discrete_sha256':sha(OUT/'proposed-discrete.pkl'),'original_Cu_deleted_or_changed':0,'new_owned_roles_edited':0,'native_jobs':0,'board_written':False,'adopted':False}
    write(OUT/'receipt.json',receipt);print('R115_COMPLETE',len(new['vias']),len(new['tracks']),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
