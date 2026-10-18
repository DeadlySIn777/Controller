"""Short ordinary outer-layer joins from bare field pins to rooted physical Cu.

The route uses existing0.15mm minimum tracks with the full0.15/0.6 clearance
and explicit25um planning margin. Fine joins are limited to15mm and are not
promoted as TVS/fault or shared high-current capacity qualification.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,uuid,re
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
from shapely import get_num_coordinates
from inventory import sha
import contact_layout as C
import fast_contacts as F
import tri_route as T
HERE=Path(__file__).resolve().parent;OUT=HERE/'fine-outer-field-ground-joins-r9'
def polys(s):return [s] if s.geom_type=='Polygon' else [q for q in getattr(s,'geoms',[]) if q.geom_type=='Polygon']
def main():
    assert not OUT.exists();OUT.mkdir();bp=HERE/'native-bound-field-contact-audit-r5';br=json.loads((bp/'receipt.json').read_text());groups=pickle.loads((bp/'groups.pkl').read_bytes());rp=HERE.parent/'sbc-power/io3-field-crossings-r15';old,discrete,binding,planes,g=pickle.loads((rp/'model.pkl').read_bytes());r6p=HERE/'source-rooted-local-field-returns-r6';r6=json.loads((r6p/'receipt.json').read_text());r6adds=pickle.loads((r6p/'proposed-zones.pkl').read_bytes());assert sha(r6p/'proposed-zones.pkl')==r6['proposal_sha256'];r8p=HERE/'bridged-field-ground-dogbones-r8';r8=json.loads((r8p/'receipt.json').read_text());assert sha(r8p/'proposed-discrete.pkl')==r8['proposed_discrete_sha256'];ds=pickle.loads((r8p/'proposed-discrete.pkl').read_bytes());assert sha(r8p/'proposed-zones.pkl')==r8['proposed_zones_sha256'];planes=planes+r6adds+pickle.loads((r8p/'proposed-zones.pkl').read_bytes());h={**g,'tracks':g['tracks']+ds['tracks'],'vias':g['vias']+ds['vias']};rec,trees=F.build({**h,'zones':[]},layers={'F.Cu','B.Cu'});outline=unary_union(C.poly(g['outline'])).buffer(-.526);res=json.loads((C.BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text());dru=(C.BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text();exceptions={}
    for line in dru.splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m:exceptions[m[1]]={C.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
    adds=[];rows=[];missing=[]
    for bank,net,rootref in [('FBG','/motherboard_do/FIELD_B_0V','J11005'),('FAG','/motherboard_motors/FIELD_GND','J11003')]:
        gs=groups[net];ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and (q['ref'],q['pin'])==(rootref,'2') for q in xs));raw=next(q['net'] for q in gs[ri] if q['kind']=='pad' and (q['ref'],q['pin'])==(rootref,'2'));dom=g['domains_normalized'][net];connected={ri}
        for row in r6['rows']:
            if row['bank']==bank and row.get('repair'):connected|={q['group'] for q in row['repair']['physical_contact_groups']}
        for row in r8['rows']:
            if row['bank']==bank:connected|=set(row['physical_groups_joined'])
        targets={l:unary_union([q['shape'] for i in connected for q in gs[i] if q['layer']==l and q['kind']!='fill']+[q['shape'] for q in rec[l] if C.norm(q['net'])==net and q['uuid'] in {t['uuid'] for k in ('tracks','vias') for t in ds[k]}]) for l in ('F.Cu','B.Cu')};obs={};ot={}
        def gap(other):return .15 if g['domains_normalized'].get(C.norm(other))==dom else .6
        for l in ('F.Cu','B.Cu'):
            shapes=[q['shape'].buffer(gap(q['net'])+.025) for q in rec[l] if C.norm(q['net'])!=net]+[q['shape'].buffer(gap(q['net'])+.025) for q in planes if q['layer']==l and C.norm(q['net'])!=net]
            for v in h['vias']:
                if C.norm(v['net'])!=net:shapes.append(Point(v['x'],v['y']).buffer(v['drill']/2+.275,quad_segs=32))
            for q in h['pads']:
                if C.norm(q['net'])!=net:shapes.extend([s.buffer(.275) for s in C.poly(q.get('hole') or [])])
            for rule in g['rule_areas']:
                if rule.get('no_tracks') and l in rule['layers']:shapes.extend([s.buffer(.025) for s in C.poly(rule['outline'])])
            for rule in res['keepouts']:
                if net not in exceptions.get(rule['name'],set()) and l in rule['layers']:shapes.extend([s.buffer(.025) for s in C.poly(rule['outline'])])
            obs[l]=shapes;ot[l]=STRtree(shapes)
        wanted=[i for i,xs in enumerate(gs) if i not in connected and any(q['kind']=='pad' and q['pin'] for q in xs)];wanted.sort(key=lambda i:(not any(q.get('ref') in {'U11017','U11038'} for q in gs[i]),i))
        for gi in wanted:
            if gi in connected:continue
            candidates=[];answer=None
            for l in ('F.Cu','B.Cu'):
                src=unary_union([q['shape'] for q in gs[gi] if q['kind']!='fill' and q['layer']==l]);dst=targets[l]
                if src.is_empty or dst.is_empty:continue
                a,b=nearest_points(src,dst)
                if a.distance(b)<=12.:candidates.append((a.distance(b),l,src,dst,a,b))
            for distance,l,src,dst,a,b in sorted(candidates,key=lambda q:q[0]):
                for margin in (2.,6.,12.):
                    win=box(min(a.x,b.x)-margin,min(a.y,b.y)-margin,max(a.x,b.x)+margin,max(a.y,b.y)+margin).intersection(outline);ii=ot[l].query(win,predicate='intersects');cuts=[obs[l][int(j)] for j in ii]+[C.body(q).buffer(gap(q['net'])+.025) for q in adds if q['layer']==l and C.norm(q['net'])!=net];legal=win.difference(unary_union(cuts))
                    for width in (.25,.20,.15):
                        options=[]
                        for part in polys(legal.buffer(-width/2-.005)):
                            pa=part.buffer(-.00002).intersection(src);pb=part.buffer(-.00002).intersection(dst)
                            if not pa.is_empty and not pb.is_empty:options.append((pa.distance(pb),part,pa,pb))
                        if not options:continue
                        _,part,pa,pb=min(options,key=lambda q:q[0]);start,end=nearest_points(pa,pb)
                        if get_num_coordinates(part)>150000:continue
                        try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))
                        except (AssertionError,ValueError):continue
                        points=[[round(x,6),round(y,6)] for x,y in points];line=LineString(points)
                        if line.length>15.:continue
                        core=line.buffer(width/2,quad_segs=32)
                        if not legal.buffer(.000001).covers(core) or core.intersection(src).area<1e-8 or core.intersection(dst).area<1e-8:continue
                        uids=[]
                        for j,(aa,bb) in enumerate(zip(points,points[1:])):
                            if aa==bb:continue
                            uid=str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller-fine-field-ground-r9/{bank}/{gi}/{l}/{j}'));t={'uuid':uid,'net':raw,'layer':l,'a':aa,'b':bb,'w':width,'prospective_not_native':True};adds.append(t);uids.append(uid);path=OUT/(uid+'.segment-chunk');path.write_text('\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.2f)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*aa,*bb,width,l,raw,uid),encoding='utf-8',newline='')
                        hits=[i for i,xs in enumerate(gs) if any(q['kind']!='fill' and q['layer']==l and q['shape'].intersection(core).area>1e-9 for q in xs)];connected|=set(hits);targets[l]=unary_union([targets[l],core]+[q['shape'] for i in hits for q in gs[i] if q['kind']!='fill' and q['layer']==l]);answer={'bank':bank,'r5_group':gi,'net_raw':raw,'layer':l,'width_mm':width,'length_mm':line.length,'points_mm':points,'segment_UUIDs':uids,'physical_groups_joined':hits,'physical_pads':[C.identity(q) for q in gs[gi] if q['kind']=='pad'],'source_root':rootref+'.2','sheet_only_R35um60C_ohm':.00057003672*line.length/width,'actual_signed_load_and_TVS_fault_capacity_gates':'OPEN','source_continuity_depends_on_full_r6_r8_mutual_gates':True,'search':search};print(bank,gi,'FINE_OUTER_JOIN',l,width,line.length,flush=True);break
                    if answer:break
                if answer:break
            if answer:rows.append(answer)
            else:missing.append({'bank':bank,'r5_group':gi,'physical_pads':[C.identity(q) for q in gs[gi] if q['kind']=='pad'],'nearest_goal_distance_mm':min([q[0] for q in candidates],default=None)});print(bank,gi,'NO_SHORT_OUTER_JOIN',flush=True)
            (OUT/'checkpoint.json').write_text(json.dumps({'rows':rows,'remaining':missing},indent=1)+'\n');(OUT/'proposed-tracks.pkl').write_bytes(pickle.dumps(adds,protocol=5))
    receipt={'verdict':'CONSTRUCTIVE_FINE_OUTER_GROUND_JOINS_MUTUAL_CURRENT_NATIVE_PENDING','rows':rows,'remaining':missing,'new_segments':len(adds),'new_holes':0,'proposal_sha256':sha(OUT/'proposed-tracks.pkl'),'r8_receipt_sha256':sha(r8p/'receipt.json'),'r6_receipt_sha256':sha(r6p/'receipt.json'),'r15_cache_sha256':sha(rp/'model.pkl'),'native_discrete_sha256':br['native_discrete_sha256'],'all_retained_discrete_shapes_and_frozen_return_shapes_unchanged':True,'native_jobs':0,'board_written':False};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
