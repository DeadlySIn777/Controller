"""Join remaining native field ground groups to concrete source-rooted Cu.

All frozen38 shapes and SBC r7 proposals stay hard. No new holes or old Cu moves.
This is constructive host geometry; current sharing, transients and native fill remain gates.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,uuid
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely import set_precision,get_num_coordinates
from shapely.strtree import STRtree
from inventory import sha
import contact_layout as C
import tri_route as T
HERE=Path(__file__).resolve().parent;OUT=HERE/'source-rooted-local-field-returns-r6'
def polys(s):return [s] if s.geom_type=='Polygon' else [p for p in getattr(s,'geoms',[]) if p.geom_type=='Polygon']

def main():
    assert not OUT.exists();OUT.mkdir();base=HERE/'native-bound-field-contact-audit-r5';br=json.loads((base/'receipt.json').read_text());assert sha(base/'geometry.pkl')==br['geometry_sha256'];h=pickle.loads((base/'geometry.pkl').read_bytes());assert sha(base/'groups.pkl')==br['groups_sha256'];gg=pickle.loads((base/'groups.pkl').read_bytes());nm=pickle.loads((HERE/'native-bound-field-base-r5/model.pkl').read_bytes());owned=pickle.loads((HERE/'full-field-zone-recipe-r2/proposed-zones.pkl').read_bytes());owned_ids={q['uuid'] for q in owned};frozen=[q for q in nm['new_zones'] if q['uuid'] not in owned_ids]+owned;outline=unary_union(C.poly(h['outline'])).buffer(-.526);rows=[];adds=[]
    for bank,net,rootref in [('FBG','/motherboard_do/FIELD_B_0V','J11005'),('FAG','/motherboard_motors/FIELD_GND','J11003')]:
        groups=gg[net];root=next(i for i,xs in enumerate(groups) if any(q['kind']=='pad' and (q['ref'],q['pin'])==(rootref,'2') for q in xs));raw=next(q['net'] for q in groups[root] if q['kind']=='pad' and (q['ref'],q['pin'])==(rootref,'2'));domain=h['domains_normalized'][net];owned_same={q['uuid'] for q in frozen if C.norm(q['net'])==net};targets={l:unary_union([q['shape'] for q in groups[root] if q['layer']==l and (q['kind']!='fill' or q['uuid'] in owned_same)]) for l in h['copper_layers']};connected={root};obs={};trees={};netadds=[]
        for layer in h['copper_layers']:
            dd=[]
            def gap(other):return .15 if h['domains_normalized'].get(C.norm(other))==domain else .6
            for t in h['tracks']:
                if t['layer']==layer and C.norm(t['net'])!=net:dd.append((t['uuid'],'native-track',C.body(t).buffer(gap(t['net'])+.025)))
            for v in h['vias']:
                if C.norm(v['net'])==net:continue
                radius=v['drill']/2+.275
                if layer in v['flashed']:radius=max(radius,v['d']/2+gap(v['net'])+.025)
                dd.append((v['uuid'],'native-hole-or-annulus',Point(v['x'],v['y']).buffer(radius,quad_segs=32)))
            for pad in h['pads']:
                if C.norm(pad['net'])!=net:
                    for shape in C.poly(pad['layers'].get(layer,[])):dd.append((pad['uuid'],'native-pad',shape.buffer(gap(pad['net'])+.025)))
                    for shape in C.poly(pad.get('hole') or []):dd.append((pad['uuid'],'native-pad-hole',shape.buffer(.275)))
            for q in frozen+adds:
                if q['layer']==layer and C.norm(q['net'])!=net:dd.append((q['uuid'],'frozen-new-plane',q['shape'].buffer(gap(q['net'])+.025)))
            for area in h['rule_areas']:
                if area.get('no_zones') and layer in area['layers']:
                    for shape in C.poly(area['outline']):dd.append((area.get('uuid',area.get('name')),'native-no-zones',shape.buffer(.025)))
            obs[layer]=dd;trees[layer]=STRtree([q[2] for q in dd]);print(bank,'obstacles',layer,len(dd),flush=True)
        wanted=[i for i,xs in enumerate(groups) if i!=root and any(q['kind']=='pad' and q['pin'] for q in xs)]
        # Finish the new regulator and existing LDO grounds first.
        wanted.sort(key=lambda i:(not any(q.get('ref') in {'U11038','U11018','U11017'} for q in groups[i]),i))
        for gi in wanted:
            if gi in connected:rows.append({'bank':bank,'group':gi,'verdict':'ALREADY_JOINED_BY_PRIOR_SOURCE_ROOTED_REPAIR'});continue
            srcs={l:unary_union([q['shape'] for q in groups[gi] if q['layer']==l and q['kind']!='fill']) for l in h['copper_layers']};gaps=[];attempts=[];answer=None
            for layer,src in srcs.items():
                dst=targets[layer]
                if src.is_empty or dst.is_empty:continue
                a,b=nearest_points(src,dst);gaps.append((a.distance(b),layer,a,b))
            for distance,layer,a,b in sorted(gaps,key=lambda q:q[:2]):
                src=srcs[layer];dst=targets[layer]
                for margin in (8.,20.,45.):
                    win=box(min(a.x,b.x)-margin,min(a.y,b.y)-margin,max(a.x,b.x)+margin,max(a.y,b.y)+margin).intersection(outline);idx=trees[layer].query(win,predicate='intersects');legal=win.difference(unary_union([obs[layer][int(i)][2] for i in idx]))
                    for width in (.5,.35):
                        center=legal.buffer(-width/2-.005);parts=[]
                        for part in polys(center):
                            inside=part.buffer(-.00002);sa=inside.intersection(src);tb=inside.intersection(dst)
                            if not sa.is_empty and not tb.is_empty:parts.append((sa.distance(tb),part,sa,tb))
                        if not parts:attempts.append({'layer':layer,'margin_mm':margin,'width_mm':width,'verdict':'NO_SHARED_LEGAL_PHYSICAL_ATTACHMENT_COMPONENT'});continue
                        _,part,sa,tb=min(parts,key=lambda q:q[0]);start,end=nearest_points(sa,tb)
                        if get_num_coordinates(part)>180000:
                            simple=part.buffer(-.015).simplify(.005,preserve_topology=True).intersection(part);poss=[q for q in polys(simple) if q.intersects(sa) and q.intersects(tb)]
                            if not poss:attempts.append({'layer':layer,'margin_mm':margin,'width_mm':width,'verdict':'CONSERVATIVE_SIMPLIFICATION_LOST_ATTACHMENT'});continue
                            part=max(poss,key=lambda q:q.area);start,end=nearest_points(part.buffer(-.00002).intersection(sa),part.buffer(-.00002).intersection(tb))
                        try:points,search=T.route(part,tuple(start.coords[0]),tuple(end.coords[0]))
                        except (AssertionError,ValueError):attempts.append({'layer':layer,'margin_mm':margin,'width_mm':width,'verdict':'EXACT_ROUTE_PRECISION_REJECTED'});continue
                        line=LineString(points);core=line.buffer(width/2,quad_segs=32)
                        if not legal.buffer(.000001).covers(core):attempts.append({'layer':layer,'width_mm':width,'verdict':'EXACT_CORE_NOT_COVERED'});continue
                        body=unary_union([q for q in polys(line.buffer(.6,quad_segs=32).intersection(legal)) if q.intersection(core).area>1e-9]);body=set_precision(body,1e-6);assert legal.buffer(.000002).covers(body) and body.buffer(.000002).covers(core);assert body.intersection(src).area>1e-8 and body.intersection(dst).area>1e-8
                        hits=[]
                        for j,xs in enumerate(groups):
                            qs=[q for q in xs if q['layer']==layer and q['kind']!='fill' and q['shape'].intersection(body).area>1e-9]
                            if qs:hits.append({'group':j,'physical_contacts':[C.identity(q) for q in qs]})
                        priorhits=[q['uuid'] for q in netadds if q['layer']==layer and q['shape'].intersection(body).area>1e-9];assert gi in {q['group'] for q in hits};uid=str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller-source-rooted-local-field-r6/{bank}/{gi}/{layer}'));file=OUT/(uid+'.wkb');file.write_bytes(body.wkb);answer={'uuid':uid,'bank':bank,'group':gi,'net_raw':raw,'layer':layer,'minimum_core_width_mm':width,'path_length_mm':line.length,'path_mm':points,'body_max_width_mm':1.2,'area_mm2':body.area,'source_root':rootref+'.2','source_attachment_proof':'Physical source-rooted native Cu or frozen source-rooted new Cu; accepted prior repairs recursively source-rooted','prior_repair_contact_UUIDs':priorhits,'physical_contact_groups':hits,'geometry_file':str(file.resolve()),'sha256':sha(file),'search':search,'geometry_capacity_planning_target_A':.5,'target_is_not_actual_load_or_qualified_rating':True,'actual_pin_load_signed_sharing_and_cap_transients':'OPEN; preserve full normal/fault/output limits','sheet_only_R35um_60C_uniform_core_ohm':.00057003672*line.length/width,'static_native_Cu_holes_frozen_foreign_planes_and_no_zones':'PASS','new_holes':0};new={'uuid':uid,'layer':layer,'net':raw,'shape':body};adds.append(new);netadds.append(new);targets[layer]=unary_union([targets[layer],body]);connected|={q['group'] for q in hits};print('accepted',bank,gi,layer,width,line.length,'physicalgroups',[q['group'] for q in hits],flush=True);break
                    if answer:break
                if answer:break
            rows.append({'bank':bank,'group':gi,'verdict':'SOURCE_ROOTED_LEGAL_GEOMETRY_CURRENT_NATIVE_PENDING' if answer else 'NO_FIXED_WINDOW_REPAIR','repair':answer,'attempts':attempts});(OUT/'checkpoint.json').write_text(json.dumps(rows,indent=1)+'\n')
        print(bank,'completed',len(netadds),'still_unrooted',[i for i in wanted if i not in connected],flush=True)
    (OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(adds,protocol=5));receipt={'verdict':'CONSTRUCTIVE_LOCAL_SOURCE_ROOTED_RETURNS_MUTUAL_CONTACT_CURRENT_NATIVE_PENDING','rows':rows,'proposal_sha256':sha(OUT/'proposed-zones.pkl'),'native_bound_base_contact_receipt_sha256':sha(base/'receipt.json'),'preserved_full_field_recipe_sha256':sha(HERE/'full-field-zone-recipe-r2/receipt.json'),'native_discrete_sha256':br['native_discrete_sha256'],'actual_start_and_goal_Cu_positive_contact_required':True,'old_cached_fill_only_endpoint_credit':False,'all_frozen38_owned_shapes_and_SBC_r7_foreign_shapes_preserved':True,'new_holes':0,'native_jobs':0,'board_written':False};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
