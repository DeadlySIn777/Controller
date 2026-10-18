"""Real ordinary field-ground vias plus explicit current-sized inner source joins.

The via need not already overlap a plane. Its attached inner polygon must be
source-rooted by a positive Cu overlap; cached isolated fills are not goals.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,math,uuid,re,sys
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
from shapely import set_precision,get_num_coordinates
from inventory import sha
import contact_layout as C
import fast_contacts as F
import tri_route as T
HERE=Path(__file__).resolve().parent;OUT=HERE/'bridged-field-ground-dogbones-r8'
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'];INNER=['In1.Cu','In4.Cu','In2.Cu']
def polys(s):return [s] if s.geom_type=='Polygon' else [q for q in getattr(s,'geoms',[]) if q.geom_type=='Polygon']
def write(path,value):path.write_text(json.dumps(value,indent=1)+'\n',encoding='utf-8')
def main():
    assert not OUT.exists();OUT.mkdir();bp=HERE/'native-bound-field-contact-audit-r5';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'geometry.pkl')==br['geometry_sha256'];prior=pickle.loads((bp/'geometry.pkl').read_bytes());groups=pickle.loads((bp/'groups.pkl').read_bytes());rp=HERE.parent/'sbc-power/io3-field-crossings-r15';old,discrete,binding,baseplanes,g=pickle.loads((rp/'model.pkl').read_bytes());r6p=HERE/'source-rooted-local-field-returns-r6';r6=json.loads((r6p/'receipt.json').read_text());assert sha(r6p/'proposed-zones.pkl')==r6['proposal_sha256'];r6adds=pickle.loads((r6p/'proposed-zones.pkl').read_bytes());planes=baseplanes+r6adds
    rec,trees=F.build({**g,'zones':[]});outline=unary_union(C.poly(g['outline'])).buffer(-.526);res=json.loads((C.BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text());dru=(C.BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text();exceptions={}
    for line in dru.splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m:exceptions[m[1]]={C.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
    drills=[{'shape':s,'uuid':q['uuid']} for q in g['pads'] for s in C.poly(q.get('hole') or [])]+[{'shape':Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=32),'uuid':v['uuid']} for v in g['vias']];dt=STRtree([q['shape'] for q in drills]);smd=[{'shape':unary_union(C.poly(ps)),'uuid':q['uuid']} for q in g['pads'] if q['smd'] for l,ps in q['layers'].items() if l in ['F.Cu','B.Cu']];st=STRtree([q['shape'] for q in smd]);vias=[];tracks=[];adds=[];newcu=[];rows=[];missing=[]
    for bank,net,rootref in [('FBG','/motherboard_do/FIELD_B_0V','J11005'),('FAG','/motherboard_motors/FIELD_GND','J11003')]:
        gs=groups[net];ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and (q['ref'],q['pin'])==(rootref,'2') for q in xs));raw=next(q['net'] for q in gs[ri] if q['kind']=='pad' and (q['ref'],q['pin'])==(rootref,'2'));domain=g['domains_normalized'][net];connected={ri}
        for row in r6['rows']:
            if row['bank']==bank and row.get('repair'):connected|={q['group'] for q in row['repair']['physical_contact_groups']}
        currentgroups=F.graph(g,net);currentroot=next(xs for xs in currentgroups if any(q['kind']=='pad' and (q['ref'],q['pin'])==(rootref,'2') for q in xs));sameids={q['uuid'] for q in baseplanes if C.norm(q['net'])==net};source={l:unary_union([q['shape'] for q in currentroot if q['layer']==l and (q['kind']!='fill' or q['uuid'] in sameids)]+[q['shape'] for q in r6adds if q['layer']==l and C.norm(q['net'])==net]) for l in INNER};foreign={l:[q for q in planes if q['layer']==l and C.norm(q['net'])!=net] for l in LAYERS};ft={l:STRtree([q['shape'] for q in foreign[l]]) for l in LAYERS}
        def gap(other):return .15 if g['domains_normalized'].get(C.norm(other))==domain else .6
        obstacles={};ot={}
        for l in INNER:
            dd=[]
            for q in rec[l]:
                if C.norm(q['net'])!=net:dd.append((q['uuid'],q['shape'].buffer(gap(q['net'])+.025)))
            for drill in drills:dd.append((drill['uuid'],drill['shape'].buffer(.275)))
            for q in foreign[l]:dd.append((q['uuid'],q['shape'].buffer(gap(q['net'])+.025)))
            for rule in g['rule_areas']:
                if rule.get('no_zones') and l in rule['layers']:
                    for sh in C.poly(rule['outline']):dd.append((rule.get('uuid',rule.get('name')),sh.buffer(.025)))
            obstacles[l]=dd;ot[l]=STRtree([q[1] for q in dd])
        def bridge(point,disk,hole):
            annulus=disk.difference(hole)
            options=[]
            for l,goal in source.items():
                if goal.is_empty:continue
                if annulus.intersection(goal).area>.025:return l,None,None
                a,b=nearest_points(disk,goal);options.append((a.distance(b),l,a,b))
            for distance,l,a,b in sorted(options,key=lambda x:x[0]):
                if distance>150:continue
                for margin in (8.,22.,45.):
                    win=box(min(a.x,b.x)-margin,min(a.y,b.y)-margin,max(a.x,b.x)+margin,max(a.y,b.y)+margin).intersection(outline);ii=ot[l].query(win,predicate='intersects');cuts=[obstacles[l][int(j)][1] for j in ii]+[q['shape'].buffer(gap(q['net'])+.025) for q in adds if q['layer']==l and C.norm(q['net'])!=net];legal=win.difference(unary_union(cuts))
                    for width in (.5,.35):
                        options=[]
                        for part in polys(legal.buffer(-width/2-.005)):
                            a0=part.buffer(-.00002).intersection(annulus);b0=part.buffer(-.00002).intersection(source[l])
                            if not a0.is_empty and not b0.is_empty:options.append((a0.distance(b0),part,a0,b0))
                        if not options:continue
                        _,part,a0,b0=min(options,key=lambda q:q[0]);start,end=nearest_points(a0,b0)
                        if get_num_coordinates(part)>160000:
                            ss=part.buffer(-.015).simplify(.005,preserve_topology=True).intersection(part);poss=[q for q in polys(ss) if q.intersects(a0) and q.intersects(b0)]
                            if not poss:continue
                            part=max(poss,key=lambda q:q.area);start,end=nearest_points(part.buffer(-.00002).intersection(a0),part.buffer(-.00002).intersection(b0))
                        try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))
                        except (AssertionError,ValueError):continue
                        line=LineString(points);core=line.buffer(width/2,quad_segs=32)
                        if not legal.buffer(.000001).covers(core):continue
                        body=set_precision(unary_union([q for q in polys(line.buffer(.6,quad_segs=32).intersection(legal)) if q.intersection(core).area>1e-9]),1e-6)
                        if not legal.buffer(.000002).covers(body) or not body.buffer(.000002).covers(core):continue
                        if body.intersection(annulus).area<.01 or body.intersection(source[l]).area<1e-8:continue
                        return l,body,{'minimum_core_width_mm':width,'length_mm':line.length,'points_mm':points,'sheet_only_R35um60C_ohm':.00057003672*line.length/width,'search':search,'source_overlap_mm2':body.intersection(source[l]).area,'annulus_overlap_mm2':body.intersection(annulus).area}
            return None,None,None
        wanted=[i for i,xs in enumerate(gs) if i not in connected and any(q['kind']=='pad' and q['pin'] for q in xs)];wanted.sort(key=lambda i:(not any(q.get('ref') in {'U11038','U11017','U11018'} for q in gs[i]),i))
        for gi in wanted:
            if gi in connected:continue
            pads=sorted([q for q in gs[gi] if q['kind']=='pad' and q['layer'] in ('F.Cu','B.Cu')],key=lambda q:-q['shape'].area);answer=None;legalvias=0;attempts=0
            for a in pads[:24]:
                anchor=a['shape'].representative_point();outer=a['layer']
                for dia,drill in ((.6,.3),(.5,.2)):
                    for radius in (.6,.9,1.2,1.6,2.2,3.,4.,5.,6.):
                        for step in range(32):
                            xy=(round(anchor.x+radius*math.cos(math.pi*step/16),6),round(anchor.y+radius*math.sin(math.pi*step/16),6));point=Point(xy);disk=point.buffer(dia/2,quad_segs=32);hole=point.buffer(drill/2,quad_segs=32);attempts+=1
                            if not outline.covers(disk):continue
                            if any(hole.buffer(.05).intersects(smd[int(j)]['shape']) for j in st.query(hole.buffer(.05),predicate='intersects')):continue
                            if any(hole.distance(drills[int(j)]['shape'])<.275-1e-7 for j in dt.query(hole.buffer(.275),predicate='intersects')):continue
                            for width in (.25,.2,.15):
                                if width==.15 and radius>3.:continue
                                stub=LineString([anchor,point]).buffer(width/2,quad_segs=32);shapes={l:disk for l in LAYERS};shapes[outer]=unary_union([disk,stub]);bad=False
                                for l,cu in shapes.items():
                                    if not outline.covers(cu):bad=True;break
                                    if any(C.norm(rec[l][int(j)]['net'])!=net and cu.distance(rec[l][int(j)]['shape'])<gap(rec[l][int(j)]['net'])+.025-1e-7 for j in trees[l].query(cu.buffer(.65),predicate='intersects')):bad=True;break
                                    if any(cu.distance(foreign[l][int(j)]['shape'])<gap(foreign[l][int(j)]['net'])+.025-1e-7 for j in ft[l].query(cu.buffer(.65),predicate='intersects')):bad=True;break
                                    for rule in g['rule_areas']:
                                        if (rule.get('no_vias') or (l==outer and rule.get('no_tracks'))) and l in rule['layers'] and any(cu.intersects(s.buffer(.025)) for s in C.poly(rule['outline'])):bad=True;break
                                    if bad:break
                                    for rule in res['keepouts']:
                                        if net not in exceptions.get(rule['name'],set()) and l in rule['layers'] and any(cu.intersects(s.buffer(.025)) for s in C.poly(rule['outline'])):bad=True;break
                                    if bad:break
                                    if any(q['layer']==l and C.norm(q['net'])!=net and cu.distance(q['shape'])<gap(q['net'])+.025-1e-7 for q in newcu):bad=True;break
                                if bad:continue
                                legalvias+=1;layer,body,route=bridge(point,disk,hole)
                                if layer is None:continue
                                uid=str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller-bridged-field-ground-r8/{bank}/{gi}/{outer}/{xy}/{dia}'));sid=str(uuid.uuid5(uuid.NAMESPACE_URL,uid+'/stub'));zid=str(uuid.uuid5(uuid.NAMESPACE_URL,uid+'/inner-bridge'));pts=[[round(anchor.x,6),round(anchor.y,6)],list(xy)];v={'uuid':uid,'net':raw,'x':xy[0],'y':xy[1],'d':dia,'drill':drill,'flashed':LAYERS,'prospective_not_native':True};t={'uuid':sid,'net':raw,'layer':outer,'a':pts[0],'b':pts[1],'w':width,'prospective_not_native':True};vias.append(v);tracks.append(t)
                                if body is not None:
                                    z={'uuid':zid,'net':raw,'layer':layer,'shape':body,'clearance_mm':.15};adds.append(z);source[layer]=unary_union([source[layer],body]);(OUT/(zid+'.wkb')).write_bytes(body.wkb)
                                for l,cu in shapes.items():newcu.append({'uuid':uid+'@'+l,'net':raw,'layer':l,'shape':set_precision(cu,1e-6)})
                                hits=[j for j,xs in enumerate(gs) if any(q['kind']!='fill' and q['layer']==outer and q['shape'].intersection(shapes[outer]).area>1e-9 for q in xs)];connected|=set(hits);vp=OUT/(uid+'.via-chunk');vp.write_text('\t(via\n\t\t(at %.6f %.6f)\n\t\t(size %.2f)\n\t\t(drill %.2f)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*xy,dia,drill,raw,uid),encoding='utf-8',newline='');sp=OUT/(sid+'.segment-chunk');sp.write_text('\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.2f)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*pts[0],*xy,width,outer,raw,sid),encoding='utf-8',newline='');answer={'bank':bank,'r5_group':gi,'physical_pads':[C.identity(q) for q in gs[gi] if q['kind']=='pad'],'raw_net':raw,'source_root':rootref+'.2','source_outer_pad':C.identity(a),'via_uuid':uid,'via_position_mm':list(xy),'via_diameter_drill_mm':[dia,drill],'prospective_all6_annuli_screened':True,'native_flash_required':[outer,layer],'stub_uuid':sid,'stub_outer_layer':outer,'stub_points_mm':pts,'stub_width_mm':width,'stub_length_mm':anchor.distance(point),'inner_source_bridge_uuid':zid if body is not None else None,'inner_source_bridge_layer':layer,'inner_source_bridge_route':route,'physical_groups_joined':hits,'via_chunk_sha256':sha(vp),'segment_chunk_sha256':sha(sp),'stress_capacity_planning_target_A':.5,'actual_signed_pin_current_and_cap_transients':'OPEN; no .5A actual-current allocation or rating claim','all_current_contacts_full_mutual_native_aperture_flash_fill_gates':'OPEN'};print(bank,gi,'BRIDGED_DOGBONE',layer,dia,width,'bridge',None if route is None else route['length_mm'],flush=True);break
                            if answer:break
                        if answer:break
                    if answer:break
                if answer:break
            if answer:rows.append(answer)
            else:missing.append({'bank':bank,'r5_group':gi,'physical_pads':[C.identity(q) for q in gs[gi] if q['kind']=='pad'],'via_candidates':attempts,'ordinary_legal_via_and_stub_candidates':legalvias});print(bank,gi,'NO_BRIDGED_ORDINARY_DOGBONE',attempts,legalvias,flush=True)
            write(OUT/'checkpoint.json',{'rows':rows,'remaining':missing,'complete':False});(OUT/'proposed-discrete.pkl').write_bytes(pickle.dumps({'vias':vias,'tracks':tracks},protocol=5));(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(adds,protocol=5))
    receipt={'verdict':'CONSTRUCTIVE_BRIDGED_FIELD_RETURNS_MUTUAL_CURRENT_NATIVE_PENDING','rows':rows,'remaining':missing,'new_vias':len(vias),'new_stubs':len(tracks),'new_inner_source_bridges':len(adds),'proposed_discrete_sha256':sha(OUT/'proposed-discrete.pkl'),'proposed_zones_sha256':sha(OUT/'proposed-zones.pkl'),'r15_cache_sha256':sha(rp/'model.pkl'),'r15_receipt_sha256':sha(rp/'receipt.json'),'r6_return_receipt_sha256':sha(r6p/'receipt.json'),'native_discrete_sha256':br['native_discrete_sha256'],'frozen38_and_r6_shapes_unchanged':True,'old_cached_fill_only_endpoints':False,'board_written':False,'native_jobs':0};write(OUT/'receipt.json',receipt);print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
