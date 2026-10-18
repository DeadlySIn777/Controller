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
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'field-power'))
from inventory import sha
import contact_layout as C
import fast_contacts as F
import tri_route as T
HERE=ROOT/'field-power';OUT=ROOT/'protected24-dogbones-r7'
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'];INNER=['In1.Cu','In4.Cu','In2.Cu']
def polys(s):return [s] if s.geom_type=='Polygon' else [q for q in getattr(s,'geoms',[]) if q.geom_type=='Polygon']
def write(path,value):path.write_text(json.dumps(value,indent=1)+'\n',encoding='utf-8')
def main():
    assert not OUT.exists();OUT.mkdir();bp=HERE/'field-io3-crossing-contact-audit-r15e';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'geometry.pkl')==br['geometry_sha256'];prior=pickle.loads((bp/'geometry.pkl').read_bytes());census=ROOT/'protected24-source-census-r2';cr=json.loads((census/'receipt.json').read_bytes());assert sha(census/'groups.pkl')==cr['protected_groups_sha256'];groups=pickle.loads((census/'groups.pkl').read_bytes());rp=HERE.parent/'sbc-power/io3-field-crossings-r15';old,discrete,binding,baseplanes,g=pickle.loads((rp/'model.pkl').read_bytes());r6p=HERE/'source-rooted-local-field-returns-r6';r6=json.loads((r6p/'receipt.json').read_text());assert sha(r6p/'proposed-zones.pkl')==r6['proposal_sha256'];r6adds=pickle.loads((r6p/'proposed-zones.pkl').read_bytes());r8p=HERE/'bridged-field-ground-dogbones-r8';r8=json.loads((r8p/'receipt.json').read_bytes());assert sha(r8p/'proposed-discrete.pkl')==r8['proposed_discrete_sha256'] and sha(r8p/'proposed-zones.pkl')==r8['proposed_zones_sha256'];r8discrete=pickle.loads((r8p/'proposed-discrete.pkl').read_bytes());r8zones=pickle.loads((r8p/'proposed-zones.pkl').read_bytes());r9p=HERE/'fine-outer-field-ground-joins-r9';r9=json.loads((r9p/'receipt.json').read_bytes());assert sha(r9p/'proposed-tracks.pkl')==r9['proposal_sha256'];r9tracks=pickle.loads((r9p/'proposed-tracks.pkl').read_bytes());audit19=HERE/'repaired-local-return-audit-r19';a19=json.loads((audit19/'receipt.json').read_bytes());assert a19['verdict'].startswith('PASS_');assert sha(audit19/'geometry.pkl')=='38882eeb997cfe1836314af74532bc497704548af8c8e9b1851607c2a92fff1c' and sha(audit19/'proposed-zones.pkl')=='5a7f01028ab438998bf15955ec0903a5a6a4bee280de954a0216e427004d0dae';g=pickle.loads((audit19/'geometry.pkl').read_bytes());planes=pickle.loads((audit19/'proposed-zones.pkl').read_bytes());baseplanes=planes;original_plane_shapes={q['uuid']:q['shape'] for q in planes};carves=[];frozen_pins={str(p.resolve()):sha(p) for p in (Path(__file__),bp/'receipt.json',bp/'geometry.pkl',census/'receipt.json',census/'groups.pkl',rp/'model.pkl',r6p/'receipt.json',r6p/'proposed-zones.pkl',r8p/'receipt.json',r8p/'proposed-discrete.pkl',r8p/'proposed-zones.pkl',r9p/'receipt.json',r9p/'proposed-tracks.pkl',audit19/'receipt.json',audit19/'geometry.pkl',audit19/'proposed-zones.pkl')}
    rec,trees=F.build({**g,'zones':[]});outline=unary_union(C.poly(g['outline'])).buffer(-.526);res=json.loads((C.BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text());dru=(C.BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text();exceptions={}
    for line in dru.splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m:exceptions[m[1]]={C.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
    drills=[{'shape':s,'uuid':q['uuid'],'net':q.get('net','')} for q in g['pads'] for s in C.poly(q.get('hole') or [])]+[{'shape':Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=32),'uuid':v['uuid'],'net':v['net']} for v in g['vias']];dt=STRtree([q['shape'] for q in drills]);smd=[{'shape':unary_union(C.poly(ps)),'uuid':q['uuid']} for q in g['pads'] if q['smd'] for l,ps in q['layers'].items() if l in ['F.Cu','B.Cu']];st=STRtree([q['shape'] for q in smd]);vias=[];tracks=[];adds=[];newcu=[];rows=[];missing=[]
    for bank,net,rootref in [('FB','/motherboard_power_entry/FIELD_B_24V_PROTECTED','U11006'),('FA','/motherboard_power_entry/FIELD_A_24V_PROTECTED','U11004')]:
        gs=groups[net];ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and (q['ref'],q['pin'])==(rootref,'17') for q in xs));raw=next(q['net'] for q in gs[ri] if q['kind']=='pad' and (q['ref'],q['pin'])==(rootref,'17'));domain=g['domains_normalized'][net];connected={ri}
        owned_return='/motherboard_motors/FIELD_GND' if bank=='FA' else '/motherboard_do/FIELD_B_0V'
        def may_carve(q):return q['layer'] in INNER and C.norm(q['net'])==owned_return
        currentgroups=F.graph(g,net);currentroot=next(xs for xs in currentgroups if any(q['kind']=='pad' and (q['ref'],q['pin'])==(rootref,'17') for q in xs));sameids={q['uuid'] for q in baseplanes if C.norm(q['net'])==net};ownholes={q['uuid']:q['shape'] for q in drills if q['net']==raw};source={l:unary_union([q['shape'].difference(ownholes.get(q['uuid'],Point().buffer(0))) for q in currentroot if q['layer']==l and (q['kind']!='fill' or q['uuid'] in sameids)]) for l in INNER};foreign={l:[q for q in planes if q['layer']==l and C.norm(q['net'])!=net] for l in LAYERS};ft={l:STRtree([q['shape'] for q in foreign[l]]) for l in LAYERS}
        def gap(other):return .15 if g['domains_normalized'].get(C.norm(other))==domain else .6
        obstacles={};ot={}
        for l in INNER:
            dd=[]
            for q in rec[l]:
                if C.norm(q['net'])!=net:dd.append((q['uuid'],q['shape'].buffer(gap(q['net'])+.025)))
            for drill in drills:
                if not drill['net'] or drill['net']!=raw:dd.append((drill['uuid'],drill['shape'].buffer(.275)))
            for q in foreign[l]:
                if not may_carve(q):dd.append((q['uuid'],q['shape'].buffer(gap(q['net'])+.025)))
            for rule in g['rule_areas']:
                if rule.get('no_zones') and l in rule['layers']:
                    for sh in C.poly(rule['outline']):dd.append((rule.get('uuid',rule.get('name')),sh.buffer(.025)))
            obstacles[l]=dd;ot[l]=STRtree([q[1] for q in dd])
        cached=[]
        for l in INNER:
            if source[l].is_empty:continue
            cuts=[q[1] for q in obstacles[l]]+[q['shape'].buffer(gap(q['net'])+.025) for q in adds if q['layer']==l and C.norm(q['net'])!=net]
            legal=set_precision(outline.difference(unary_union(cuts)),1e-6)
            for width in (2.,1.,.5):
                count=0
                for part in polys(legal.buffer(-width/2-.005)):
                    reachable=part.buffer(-.00002);goal=reachable.intersection(source[l])
                    if goal.is_empty or goal.area<1e-8:continue
                    cached.append({'layer':l,'width':width,'legal':legal,'part':part,'reachable':reachable,'goal':goal});count+=1
                print(bank,l,'SOURCE_COMPONENTS',width,count,flush=True)
        def bridge(point,disk,hole):
            annulus=disk.difference(hole)
            for l,goal in source.items():
                if not goal.is_empty and annulus.intersection(goal).area>.025:return l,None,None
            candidates=[]
            for q in cached:
                if not q['reachable'].intersects(annulus):continue
                startshape=q['reachable'].intersection(annulus)
                if startshape.is_empty or startshape.area<1e-8:continue
                candidates.append((startshape.distance(q['goal']),q,startshape))
            for distance,q,startshape in sorted(candidates,key=lambda x:(-x[1]['width'],x[0])):
                l,width,legal,part,goal=q['layer'],q['width'],q['legal'],q['part'],q['goal']
                start,end=nearest_points(startshape,goal)
                if get_num_coordinates(part)>160000:
                    simple=part.buffer(-.015).simplify(.005,preserve_topology=True).intersection(part)
                    possible=[p for p in polys(simple) if p.intersects(startshape) and p.intersects(goal)]
                    if not possible:continue
                    part=max(possible,key=lambda p:p.area)
                    start,end=nearest_points(part.buffer(-.00002).intersection(startshape),part.buffer(-.00002).intersection(goal))
                try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))
                except (AssertionError,ValueError):continue
                line=LineString(points);core=line.buffer(width/2,quad_segs=32)
                if not legal.buffer(.000001).covers(core):continue
                body=set_precision(unary_union([p for p in polys(line.buffer(max(2.,width),quad_segs=32).intersection(legal)) if p.intersection(core).area>1e-9]),1e-6)
                if not legal.buffer(.000002).covers(body) or not body.buffer(.000002).covers(core):continue
                if body.intersection(annulus).area<.01 or body.intersection(source[l]).area<1e-8:continue
                return l,body,{'minimum_core_width_mm':width,'length_mm':line.length,'points_mm':points,'sheet_only_R35um60C_ohm':.00057003672*line.length/width,'search':search,'source_positive_annular_overlap_mm2':body.intersection(source[l]).area,'annulus_overlap_mm2':body.intersection(annulus).area,'source_component_cache':'Exact complete outline free component, each width eroded before matching; no false150mm endpoint cap'}
            return None,None,None
        wanted=[i for i,xs in enumerate(gs) if i not in connected and any(q['kind']=='pad' and q['pin'] for q in xs)];wanted.sort(key=lambda i:(not any(q.get('ref') in {'U11038','U11017','U11018'} for q in gs[i]),i))
        for gi in wanted:
            if gi in connected:continue
            print(bank,gi,'SEARCH_STRONG_APERTURE_DOGBONE',flush=True)
            pads=sorted([q for q in gs[gi] if q['kind']=='pad' and q['layer'] in ('F.Cu','B.Cu')],key=lambda q:-q['shape'].area);answer=None;legalvias=0;attempts=0
            for a in pads[:24]:
                print(bank,gi,'PAD',a.get('ref'),a.get('pin'),a['layer'],flush=True)
                anchor=a['shape'].representative_point();outer=a['layer']
                for dia,drill in ((.8,.4),(.6,.3),(.5,.2)):
                    for radius in (.6,.9,1.2,1.6,2.2,3.,4.,5.,6.):
                        for step in range(32):
                            xy=(round(anchor.x+radius*math.cos(math.pi*step/16),6),round(anchor.y+radius*math.sin(math.pi*step/16),6));point=Point(xy);disk=point.buffer(dia/2,quad_segs=32);hole=point.buffer(drill/2,quad_segs=32);attempts+=1
                            if not outline.covers(disk):continue
                            if any(hole.distance(smd[int(j)]['shape'])<.275-1e-7 for j in st.query(hole.buffer(.275),predicate='intersects')):continue
                            if any(hole.distance(drills[int(j)]['shape'])<.275-1e-7 for j in dt.query(hole.buffer(.275),predicate='intersects')):continue
                            if any(hole.distance(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=32))<.275-1e-7 for v in vias):continue
                            for width in (.8,.5,.25,.2):
                                stub=LineString([anchor,point]).buffer(width/2,quad_segs=32);shapes={l:disk for l in LAYERS};shapes[outer]=unary_union([disk,stub]);bad=False
                                for l,cu in shapes.items():
                                    if not outline.covers(cu):bad=True;break
                                    if any(C.norm(rec[l][int(j)]['net'])!=net and cu.distance(rec[l][int(j)]['shape'])<gap(rec[l][int(j)]['net'])+.025-1e-7 for j in trees[l].query(cu.buffer(.65),predicate='intersects')):bad=True;break
                                    if any(not may_carve(foreign[l][int(j)]) and cu.distance(foreign[l][int(j)]['shape'])<gap(foreign[l][int(j)]['net'])+.025-1e-7 for j in ft[l].query(cu.buffer(.65),predicate='intersects')):bad=True;break
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
                                uid=str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller-protected24-dogbone-r7/{bank}/{gi}/{outer}/{xy}/{dia}'));sid=str(uuid.uuid5(uuid.NAMESPACE_URL,uid+'/stub'));zid=str(uuid.uuid5(uuid.NAMESPACE_URL,uid+'/inner-bridge'));pts=[[round(anchor.x,6),round(anchor.y,6)],list(xy)];v={'uuid':uid,'net':raw,'x':xy[0],'y':xy[1],'d':dia,'drill':drill,'flashed':LAYERS,'prospective_not_native':True};t={'uuid':sid,'net':raw,'layer':outer,'a':pts[0],'b':pts[1],'w':width,'prospective_not_native':True};vias.append(v);tracks.append(t)
                                if body is not None:
                                    z={'uuid':zid,'net':raw,'layer':layer,'shape':body,'clearance_mm':.15};adds.append(z);source[layer]=unary_union([source[layer],body]);(OUT/(zid+'.wkb')).write_bytes(body.wkb)
                                for q in planes:
                                    if not may_carve(q):continue
                                    cutter=unary_union([shapes[q['layer']]]+([body] if body is not None and q['layer']==layer else [])).buffer(gap(q['net'])+.025);before=q['shape'];after=set_precision(before.difference(cutter),1e-6);removed=before.difference(after);added=after.difference(before)
                                    if removed.area<1e-9 and added.area<1e-9:continue
                                    import hashlib
                                    f=OUT/(q['uuid']+'-by-'+uid+'-removed.wkb');f.write_bytes(removed.wkb);fadd=OUT/(q['uuid']+'-by-'+uid+'-quantization-added.wkb');fadd.write_bytes(added.wkb);carves.append({'owned_new_return_uuid':q['uuid'],'positive_via_uuid':uid,'positive_bridge_uuid':zid if body is not None else None,'raw_return_net':q['net'],'layer':q['layer'],'old_shape_sha256':hashlib.sha256(before.wkb).hexdigest(),'new_shape_sha256':hashlib.sha256(after.wkb).hexdigest(),'removed_area_mm2':removed.area,'removed_file':str(f.resolve()),'removed_file_sha256':sha(f),'quantization_added_area_mm2':added.area,'quantization_added_file':str(fadd.resolve()),'quantization_added_file_sha256':sha(fadd),'clearance_buffer_mm':gap(q['net'])+.025,'exact_grid_mm':1e-6});q['shape']=after
                                for l,cu in shapes.items():newcu.append({'uuid':uid+'@'+l,'net':raw,'layer':l,'shape':set_precision(cu,1e-6)})
                                hits=[j for j,xs in enumerate(gs) if any(q['kind']!='fill' and q['layer']==outer and q['shape'].intersection(shapes[outer]).area>1e-9 for q in xs)];connected|=set(hits);vp=OUT/(uid+'.via-chunk');vp.write_text('\t(via\n\t\t(at %.6f %.6f)\n\t\t(size %.2f)\n\t\t(drill %.2f)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*xy,dia,drill,raw,uid),encoding='utf-8',newline='');sp=OUT/(sid+'.segment-chunk');sp.write_text('\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.2f)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*pts[0],*xy,width,outer,raw,sid),encoding='utf-8',newline='');answer={'bank':bank,'r5_group':gi,'physical_pads':[C.identity(q) for q in gs[gi] if q['kind']=='pad'],'raw_net':raw,'source_root':rootref+'.17','source_outer_pad':C.identity(a),'via_uuid':uid,'via_position_mm':list(xy),'via_diameter_drill_mm':[dia,drill],'prospective_all6_annuli_screened':True,'every_SMD_drilled_aperture_guard_mm':.275,'all_old_and_previous_new_drill_spacing_mm':.275,'native_flash_required':[outer,layer],'stub_uuid':sid,'stub_outer_layer':outer,'stub_points_mm':pts,'stub_width_mm':width,'stub_length_mm':anchor.distance(point),'inner_source_bridge_uuid':zid if body is not None else None,'inner_source_bridge_layer':layer,'inner_source_bridge_route':route,'physical_groups_joined':hits,'via_chunk_sha256':sha(vp),'segment_chunk_sha256':sha(sp),'complete_protected24_route_policy_A':6.5,'source_domain_full_load_a':4.584429372438923 if bank=='FA' else 4.768596828963444,'package_neck_barrel_sharing_and_all_constrictions_current_qualification':'OPEN; minimum geometry width never establishes actual6.5-A capability','actual_signed_pin_current_and_cap_transients':'OPEN; no .5A actual-current allocation or rating claim','all_current_contacts_full_mutual_native_aperture_flash_fill_gates':'OPEN','same_raw_PTH_source_plane_overlap':'Positive annulus required; same-net plated hole is not a foreign plane clearance obstacle'};print(bank,gi,'BRIDGED_DOGBONE',layer,dia,width,'bridge',None if route is None else route['length_mm'],flush=True);break
                            if answer:break
                        if answer:break
                    if answer:break
                if answer:break
            if answer:rows.append(answer)
            else:missing.append({'bank':bank,'r5_group':gi,'physical_pads':[C.identity(q) for q in gs[gi] if q['kind']=='pad'],'via_candidates':attempts,'ordinary_legal_via_and_stub_candidates':legalvias});print(bank,gi,'NO_BRIDGED_ORDINARY_DOGBONE',attempts,legalvias,flush=True)
            write(OUT/'checkpoint.json',{'rows':rows,'remaining':missing,'complete':False});(OUT/'proposed-discrete.pkl').write_bytes(pickle.dumps({'vias':vias,'tracks':tracks},protocol=5));(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(adds,protocol=5))
    for p,hsh in frozen_pins.items():
        if sha(p)!=hsh:raise ValueError('Frozen positive source input changed')
    (OUT/'owned-new-return-zone-updates.pkl').write_bytes(pickle.dumps([q for q in planes if q['shape'].wkb!=original_plane_shapes[q['uuid']].wkb],protocol=5))
    receipt={'verdict':'CONSTRUCTIVE_PROTECTED24_DOGBONES_MUTUAL_CURRENT_NATIVE_PENDING','rows':rows,'remaining':missing,'new_vias':len(vias),'new_stubs':len(tracks),'new_inner_source_bridges':len(adds),'proposed_discrete_sha256':sha(OUT/'proposed-discrete.pkl'),'proposed_zones_sha256':sha(OUT/'proposed-zones.pkl'),'r15_cache_sha256':sha(rp/'model.pkl'),'r15_receipt_sha256':sha(rp/'receipt.json'),'r6_return_receipt_sha256':sha(r6p/'receipt.json'),'native_discrete_sha256':br['native_discrete_sha256'],'only_owned_same_domain_new_inner_returns_locally_carved':True,'owned_return_carve_ledger':carves,'owned_return_zone_updates_sha256':sha(OUT/'owned-new-return-zone-updates.pkl'),'original_native_zone_outlines_and_configuration_untouched':True,'input_sha256':frozen_pins,'complete_old_CONTACTS_all_source_roots_current_native_gates':'MANDATORY_OPEN','old_cached_fill_only_endpoints':False,'board_written':False,'native_jobs':0};write(OUT/'receipt.json',receipt);print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
