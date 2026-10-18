"""Construct ordinary short field-ground dogbones on the exact native discrete base.

Only an actual annulus contact with source-rooted frozen/new Cu can be a goal.
All six prospective annuli, drilled aperture, ordinary SMD holes and rule areas
are screened. These are proposals until composed contact/current/native gates.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,math,uuid,re
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
from shapely import set_precision
from inventory import sha
import contact_layout as C
import fast_contacts as F
HERE=Path(__file__).resolve().parent;OUT=HERE/'local-field-ground-dogbones-r7'
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'];INNER=['In1.Cu','In4.Cu','In2.Cu','In3.Cu']
def write(path,value):path.write_text(json.dumps(value,indent=1)+'\n',encoding='utf-8')
def main():
    assert not OUT.exists();OUT.mkdir();bp=HERE/'native-bound-field-contact-audit-r5';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'geometry.pkl')==br['geometry_sha256'];g=pickle.loads((bp/'geometry.pkl').read_bytes());groups=pickle.loads((bp/'groups.pkl').read_bytes());r6p=HERE/'source-rooted-local-field-returns-r6';r6=json.loads((r6p/'receipt.json').read_text());assert sha(r6p/'proposed-zones.pkl')==r6['proposal_sha256'];r6adds=pickle.loads((r6p/'proposed-zones.pkl').read_bytes());frozen=pickle.loads((HERE/'full-field-zone-recipe-r2/proposed-zones.pkl').read_bytes());frozenids={q['uuid'] for q in frozen};nm=pickle.loads((HERE/'native-bound-field-base-r5/model.pkl').read_bytes());planes=[q for q in nm['new_zones'] if q['uuid'] not in frozenids]+frozen+r6adds
    rec,trees=F.build({**g,'zones':[]});outline=unary_union(C.poly(g['outline'])).buffer(-.526);res=json.loads((C.BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text());dru=(C.BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text();exceptions={}
    for line in dru.splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m:exceptions[m[1]]={C.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
    drills=[{'shape':s,'uuid':q['uuid']} for q in g['pads'] for s in C.poly(q.get('hole') or [])]+[{'shape':Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=32),'uuid':v['uuid']} for v in g['vias']];dt=STRtree([q['shape'] for q in drills]);smd=[{'shape':unary_union(C.poly(ps)),'uuid':q['uuid'],'layer':l} for q in g['pads'] if q['smd'] for l,ps in q['layers'].items() if l in ['F.Cu','B.Cu']];st=STRtree([q['shape'] for q in smd]);rows=[];missing=[];vias=[];tracks=[];newcu=[]
    for bank,net,rootref in [('FBG','/motherboard_do/FIELD_B_0V','J11005'),('FAG','/motherboard_motors/FIELD_GND','J11003')]:
        gs=groups[net];ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and (q['ref'],q['pin'])==(rootref,'2') for q in xs));raw=next(q['net'] for q in gs[ri] if q['kind']=='pad' and (q['ref'],q['pin'])==(rootref,'2'));domain=g['domains_normalized'][net];connected={ri}
        for row in r6['rows']:
            if row['bank']==bank and row.get('repair'):connected|={q['group'] for q in row['repair']['physical_contact_groups']}
        sameids={q['uuid'] for q in planes if C.norm(q['net'])==net};source={l:unary_union([q['shape'] for q in gs[ri] if q['layer']==l and (q['kind']!='fill' or q['uuid'] in sameids)]+[q['shape'] for q in r6adds if q['layer']==l and C.norm(q['net'])==net]) for l in INNER};foreign={l:[q for q in planes if q['layer']==l and C.norm(q['net'])!=net] for l in LAYERS};ft={l:STRtree([q['shape'] for q in foreign[l]]) for l in LAYERS};wanted=[i for i,xs in enumerate(gs) if i not in connected and any(q['kind']=='pad' and q['pin'] for q in xs)];wanted.sort(key=lambda i:(not any(q.get('ref') in {'U11038','U11017','U11018'} for q in gs[i]),i))
        def gap(other):return .15 if g['domains_normalized'].get(C.norm(other))==domain else .6
        for gi in wanted:
            if gi in connected:continue
            pads=sorted([q for q in gs[gi] if q['kind']=='pad' and q['layer'] in ('F.Cu','B.Cu')],key=lambda q:-q['shape'].area);checked=0;reasons={};answer=None
            for a in pads[:24]:
                outer=a['layer'];anchor=a['shape'].representative_point();candidates=[]
                for l,plane in source.items():
                    if plane.is_empty:continue
                    pa,pb=nearest_points(anchor,plane);dist=pa.distance(pb)
                    if dist<=8.3:
                        for d in (.08,.18,.3,.45):
                            if dist>0:candidates.append((pb.x+d*(pb.x-anchor.x)/dist,pb.y+d*(pb.y-anchor.y)/dist))
                for radius in (.6,.9,1.2,1.6,2.2,3.,4.,5.,6.,7.,8.):
                    for step in range(32):candidates.append((anchor.x+radius*math.cos(math.pi*step/16),anchor.y+radius*math.sin(math.pi*step/16)))
                seen=set()
                for xx,yy in candidates:
                    xy=(round(xx,6),round(yy,6))
                    if xy in seen:continue
                    seen.add(xy);point=Point(xy);disk=point.buffer(.3,quad_segs=32);hole=point.buffer(.15,quad_segs=32);annulus=disk.difference(hole);plane=next((l for l in INNER if source[l].intersection(annulus).area>.025),None)
                    if plane is None:continue
                    checked+=1;why=None
                    if not outline.covers(disk):why='EDGE'
                    elif any(hole.buffer(.05).intersects(smd[int(j)]['shape']) for j in st.query(hole.buffer(.05),predicate='intersects')):why='ORDINARY_SMD_HOLE_APERTURE'
                    elif any(hole.distance(drills[int(j)]['shape'])<.275-1e-7 for j in dt.query(hole.buffer(.275),predicate='intersects')):why='DRILL_CLEARANCE'
                    if why:reasons[why]=reasons.get(why,0)+1;continue
                    for width in (.25,.2,.15):
                        if width==.15 and anchor.distance(point)>3.:continue
                        line=LineString([anchor,point]);stub=line.buffer(width/2,quad_segs=32);shapes={l:disk for l in LAYERS};shapes[outer]=unary_union([disk,stub]);bad=None
                        if not outline.covers(shapes[outer]):continue
                        for l,cu in shapes.items():
                            for j in trees[l].query(cu.buffer(.65),predicate='intersects'):
                                q=rec[l][int(j)]
                                if C.norm(q['net'])!=net and cu.distance(q['shape'])<gap(q['net'])+.025-1e-7:bad='NATIVE_DISCRETE_CU';break
                            if bad:break
                            if any(cu.distance(foreign[l][int(j)]['shape'])<gap(foreign[l][int(j)]['net'])+.025-1e-7 for j in ft[l].query(cu.buffer(.65),predicate='intersects')):bad='FROZEN_FOREIGN_NEW_PLANE';break
                            for rule in g['rule_areas']:
                                if (rule.get('no_vias') or (l==outer and rule.get('no_tracks'))) and l in rule['layers'] and any(cu.intersects(s.buffer(.025)) for s in C.poly(rule['outline'])):bad='NATIVE_KEEP_OUT';break
                            if bad:break
                            for rule in res['keepouts']:
                                if net not in exceptions.get(rule['name'],set()) and l in rule['layers'] and any(cu.intersects(s.buffer(.025)) for s in C.poly(rule['outline'])):bad='RESERVED_TRACK_VIA_KEEP_OUT';break
                            if bad:break
                            if any(q['layer']==l and C.norm(q['net'])!=net and cu.distance(q['shape'])<gap(q['net'])+.025-1e-7 for q in newcu):bad='PRIOR_NEW_CU';break
                        if bad:reasons[bad]=reasons.get(bad,0)+1;continue
                        assert stub.intersection(a['shape']).area>1e-9;uid=str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller-native-field-ground-dogbone-r7/{bank}/{gi}/{outer}/{xy}'));sid=str(uuid.uuid5(uuid.NAMESPACE_URL,uid+'/stub'));pts=[[round(anchor.x,6),round(anchor.y,6)],list(xy)];voids=[]
                        for z in g['zones']:
                            if C.norm(z['net'])==net:continue
                            for l,ps in z['fills'].items():
                                if l not in shapes:continue
                                clear=max(gap(z['net']),float(z['clearance_mm']));cut=shapes[l].buffer(clear+.025);area=unary_union(C.poly(ps)).intersection(cut).area
                                if area>1e-9:voids.append({'zone_uuid':z['uuid'],'layer':l,'net_raw':z['net'],'native_local_clearance_mm':z['clearance_mm'],'clearance_mm':clear,'prospective_removed_area_mm2':area})
                        via={'uuid':uid,'net':raw,'x':xy[0],'y':xy[1],'d':.6,'drill':.3,'flashed':LAYERS,'prospective_not_native':True};track={'uuid':sid,'net':raw,'layer':outer,'a':pts[0],'b':pts[1],'w':width,'prospective_not_native':True};vias.append(via);tracks.append(track)
                        vp=OUT/(uid+'.via-chunk');vp.write_text('\t(via\n\t\t(at %.6f %.6f)\n\t\t(size 0.6)\n\t\t(drill 0.3)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*xy,raw,uid),encoding='utf-8',newline='');sp=OUT/(sid+'.segment-chunk');sp.write_text('\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.2f)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*pts[0],*xy,width,outer,raw,sid),encoding='utf-8',newline='')
                        hits=[j for j,xs in enumerate(gs) if any(q['kind']!='fill' and q['layer']==outer and q['shape'].intersection(shapes[outer]).area>1e-9 for q in xs)];connected|=set(hits)
                        for l,cu in shapes.items():newcu.append({'uuid':uid+'@'+l,'net':raw,'layer':l,'shape':set_precision(cu,1e-6)})
                        answer={'bank':bank,'old_r5_group':gi,'physical_group_pads':[C.identity(q) for q in gs[gi] if q['kind']=='pad'],'native_source_anchor':rootref+'.2','raw_net':raw,'outer':outer,'source_plane_layer':plane,'source_pad':C.identity(a),'points_mm':pts,'stub_width_mm':width,'stub_length_mm':line.length,'via_diameter_drill_mm':[.6,.3],'via_uuid':uid,'segment_uuid':sid,'all_layer_annuli_screened':LAYERS,'actual_native_postfill_flash_required':[outer,plane],'annulus_source_Cu_contact_area_mm2':source[plane].intersection(annulus).area,'physical_groups_joined':hits,'mandatory_prospective_old_fill_voids':voids,'via_chunk_path':str(vp.resolve()),'via_chunk_sha256':sha(vp),'segment_chunk_path':str(sp.resolve()),'segment_chunk_sha256':sha(sp),'sheet_only_R35um60C_ohm':.00057003672*line.length/width,'conditional_20um_barrel60C_1p6mm_R_ohm':1.99512852e-8*.0016/(math.pi*.0003*.000020),'current_capacity_planning_stress_A':.5,'stress_is_not_actual_pin_current_or_qualified_rating':True,'source_continuity_depends_on_r6_full_mutual_gate':True,'full_current_native_fill_flash_and_retained_contact_gates':'OPEN'};print(bank,gi,'DOGBONE',plane,outer,width,line.length,flush=True);break
                    if answer:break
                if answer:break
            if answer:rows.append(answer)
            else:missing.append({'bank':bank,'old_r5_group':gi,'physical_pads':[C.identity(q) for q in gs[gi] if q['kind']=='pad'],'plane_attachment_candidates':checked,'reject_reasons':reasons});print(bank,gi,'NO_LOCAL_ORDINARY_DOGBONE',checked,reasons,flush=True)
            write(OUT/'checkpoint.json',{'rows':rows,'remaining':missing,'complete':False})
    (OUT/'proposed-discrete.pkl').write_bytes(pickle.dumps({'vias':vias,'tracks':tracks,'copper':newcu},protocol=5));receipt={'verdict':'CONSTRUCTIVE_NATIVE_BOUND_ORDINARY_GROUND_DOGBONES_MUTUAL_CURRENT_NATIVE_PENDING','rows':rows,'remaining':missing,'new_vias':len(vias),'new_segments':len(tracks),'proposed_discrete_sha256':sha(OUT/'proposed-discrete.pkl'),'exact_native_base_contact_receipt_sha256':sha(bp/'receipt.json'),'r6_return_receipt_sha256':sha(r6p/'receipt.json'),'frozen38_recipe_sha256':sha(HERE/'full-field-zone-recipe-r2/receipt.json'),'native_discrete_sha256':br['native_discrete_sha256'],'all_six_annuli_and_ordinary_SMD_hole_and_drill_keepouts_screened':True,'source_rooted_annulus_attachment_required':True,'cached_old_fill_only_attachment_credit':False,'frozen38_and_r6_shapes_unchanged':True,'board_written':False,'native_jobs':0};write(OUT/'receipt.json',receipt);print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
