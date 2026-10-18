"""Join remaining native field ground groups to concrete source-rooted Cu.

Only explicitly ledgered same-domain new inner ground returns may be carved. Native Cu and other domains/SBC stay hard. No new holes or old Cu moves.
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
import sys
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'field-power'))
from inventory import sha
import contact_layout as C
import tri_route as T
HERE=Path(__file__).resolve().parent/'field-power';OUT=ROOT/'protected24-supply-constructor-r3'
def polys(s):return [s] if s.geom_type=='Polygon' else [p for p in getattr(s,'geoms',[]) if p.geom_type=='Polygon']

def main():
    assert not OUT.exists();OUT.mkdir();base=HERE/'field-io3-crossing-contact-audit-r15e';br=json.loads((base/'receipt.json').read_text());assert sha(base/'geometry.pkl')==br['geometry_sha256'];h=pickle.loads((base/'geometry.pkl').read_bytes());census=ROOT/'protected24-source-census-r2';cr=json.loads((census/'receipt.json').read_bytes());assert sha(census/'groups.pkl')==cr['protected_groups_sha256'];gg=pickle.loads((census/'groups.pkl').read_bytes());rp=HERE.parent/'sbc-power/io3-field-crossings-r15';assert sha(rp/'model.pkl')=='a57a68ab14815a34ab5a398ef2c7fc0f79e0c6b448a28a8e84ca8a21d9e80e5d';old,discrete,binding,frozen,saved=pickle.loads((rp/'model.pkl').read_bytes());r6p=HERE/'source-rooted-local-field-returns-r6';r6=json.loads((r6p/'receipt.json').read_bytes());assert sha(r6p/'proposed-zones.pkl')==r6['proposal_sha256'];r8p=HERE/'bridged-field-ground-dogbones-r8';r8=json.loads((r8p/'receipt.json').read_bytes());assert sha(r8p/'proposed-zones.pkl')==r8['proposed_zones_sha256'] and sha(r8p/'proposed-discrete.pkl')==r8['proposed_discrete_sha256'];extra=pickle.loads((r8p/'proposed-discrete.pkl').read_bytes());r9p=HERE/'fine-outer-field-ground-joins-r9';r9=json.loads((r9p/'receipt.json').read_bytes());assert sha(r9p/'proposed-tracks.pkl')==r9['proposal_sha256'];r9tracks=pickle.loads((r9p/'proposed-tracks.pkl').read_bytes());h={**h,'vias':h['vias']+extra['vias'],'tracks':h['tracks']+extra['tracks']+r9tracks};frozen=frozen+pickle.loads((r6p/'proposed-zones.pkl').read_bytes())+pickle.loads((r8p/'proposed-zones.pkl').read_bytes());outline=unary_union(C.poly(h['outline'])).buffer(-.526);rows=[];adds=[];carve_ledger=[];original_frozen={q['uuid']:q['shape'] for q in frozen};pins={str(p.resolve()):sha(p) for p in (Path(__file__),base/'receipt.json',base/'geometry.pkl',census/'receipt.json',census/'groups.pkl',rp/'model.pkl',rp/'precision-state-ledger.json',r6p/'receipt.json',r6p/'proposed-zones.pkl',r8p/'receipt.json',r8p/'proposed-discrete.pkl',r8p/'proposed-zones.pkl',r9p/'receipt.json',r9p/'proposed-tracks.pkl')}
    for bank,net,rootref in [('FB','/motherboard_power_entry/FIELD_B_24V_PROTECTED','U11006'),('FA','/motherboard_power_entry/FIELD_A_24V_PROTECTED','U11004')]:
        groups=gg[net];root=next(i for i,xs in enumerate(groups) if any(q['kind']=='pad' and (q['ref'],q['pin'])==(rootref,'17') for q in xs));raw=next(q['net'] for q in groups[root] if q['kind']=='pad' and (q['ref'],q['pin'])==(rootref,'17'));domain=h['domains_normalized'][net];owned_same={q['uuid'] for q in frozen if C.norm(q['net'])==net};targets={l:unary_union([q['shape'] for q in groups[root] if q['layer']==l and (q['kind']!='fill' or q['uuid'] in owned_same)]) for l in h['copper_layers']};connected={root};obs={};trees={};netadds=[]
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
                owned_return='/motherboard_motors/FIELD_GND' if bank=='FA' else '/motherboard_do/FIELD_B_0V'
                may_carve=q['layer'] in ('In1.Cu','In2.Cu','In4.Cu') and C.norm(q['net'])==owned_return
                if q['layer']==layer and C.norm(q['net'])!=net and not may_carve:dd.append((q['uuid'],'frozen-new-plane',q['shape'].buffer(gap(q['net'])+.025)))
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
                    for width in (4.,2.,1.,.5,.25):
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
                        body=unary_union([q for q in polys(line.buffer(max(2.,width),quad_segs=32).intersection(legal)) if q.intersection(core).area>1e-9]);body=set_precision(body,1e-6);assert legal.buffer(.000002).covers(body) and body.buffer(.000002).covers(core);assert body.intersection(src).area>1e-8 and body.intersection(dst).area>1e-8
                        hits=[]
                        for j,xs in enumerate(groups):
                            qs=[q for q in xs if q['layer']==layer and q['kind']!='fill' and q['shape'].intersection(body).area>1e-9]
                            if qs:hits.append({'group':j,'physical_contacts':[C.identity(q) for q in qs]})
                        priorhits=[q['uuid'] for q in netadds if q['layer']==layer and q['shape'].intersection(body).area>1e-9];assert gi in {q['group'] for q in hits};uid=str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller-protected24-supply-r3/{bank}/{gi}/{layer}'));file=OUT/(uid+'.wkb');file.write_bytes(body.wkb);answer={'uuid':uid,'bank':bank,'group':gi,'net_raw':raw,'layer':layer,'minimum_core_width_mm':width,'path_length_mm':line.length,'path_mm':points,'body_prospective_max_width_mm':2*max(2.,width),'area_mm2':body.area,'source_root':rootref+'.17','source_attachment_proof':'Physical source-rooted native Cu or frozen source-rooted new Cu; accepted prior repairs recursively source-rooted','prior_repair_contact_UUIDs':priorhits,'physical_contact_groups':hits,'geometry_file':str(file.resolve()),'sha256':sha(file),'search':search,'complete_protected24_route_policy_A':6.5,'full_simultaneous_domain_source_target_A':4.584429372438923 if bank=='FA' else 4.768596828963444,'geometry_only_no_current_capacity_claim':True,'target_is_not_actual_load_or_qualified_rating':True,'actual_pin_load_signed_sharing_and_cap_transients':'OPEN; preserve full normal/fault/output limits','sheet_only_R35um_60C_uniform_core_ohm':.00057003672*line.length/width,'static_native_Cu_holes_frozen_foreign_planes_and_no_zones':'PASS','new_holes':0};new={'uuid':uid,'layer':layer,'net':raw,'shape':body};
                        for q in frozen:
                            if q['layer']!=layer or layer not in ('In1.Cu','In2.Cu','In4.Cu') or C.norm(q['net'])!=('/motherboard_motors/FIELD_GND' if bank=='FA' else '/motherboard_do/FIELD_B_0V'):continue
                            before=q['shape'];after=set_precision(before.difference(body.buffer(gap(q['net'])+.025)),1e-6);removed=before.difference(after)
                            if removed.area<1e-9:continue
                            import hashlib
                            cf=OUT/(q['uuid']+'-by-'+uid+'-removed.wkb');cf.write_bytes(removed.wkb);carve_ledger.append({'owned_new_return_uuid':q['uuid'],'protected24_uuid':uid,'layer':layer,'actual_return_raw_net':q['net'],'old_shape_sha256':hashlib.sha256(before.wkb).hexdigest(),'new_shape_sha256':hashlib.sha256(after.wkb).hexdigest(),'removed_file':str(cf.resolve()),'removed_file_sha256':sha(cf),'removed_area_mm2':removed.area,'buffer_mm':gap(q['net'])+.025,'quantized_coordinate_grid_mm':1e-6});q['shape']=after
                        adds.append(new);netadds.append(new);targets[layer]=unary_union([targets[layer],body]);connected|={q['group'] for q in hits};print('accepted',bank,gi,layer,width,line.length,'physicalgroups',[q['group'] for q in hits],flush=True);break
                    if answer:break
                if answer:break
            rows.append({'bank':bank,'group':gi,'verdict':'PROTECTED24_SOURCE_ROOTED_GEOMETRY_CURRENT_NATIVE_PENDING' if answer else 'NO_FIXED_WINDOW_REPAIR','repair':answer,'attempts':attempts});(OUT/'checkpoint.json').write_text(json.dumps(rows,indent=1)+'\n')
        print(bank,'completed',len(netadds),'still_unrooted',[i for i in wanted if i not in connected],flush=True)
    for p,hsh in pins.items():
        if sha(p)!=hsh:raise ValueError('Frozen protected24 input changed')
    (OUT/'owned-new-return-zone-updates.pkl').write_bytes(pickle.dumps([q for q in frozen if q['shape'].wkb!=original_frozen[q['uuid']].wkb],protocol=5))
    (OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(adds,protocol=5));receipt={'verdict':'CONSTRUCTIVE_PROTECTED24_SUPPLY_MUTUAL_CONTACT_CURRENT_NATIVE_PENDING','rows':rows,'proposal_sha256':sha(OUT/'proposed-zones.pkl'),'native_bound_base_contact_receipt_sha256':sha(base/'receipt.json'),'preserved_full_field_recipe_sha256':sha(HERE/'full-field-zone-recipe-r2/receipt.json'),'native_discrete_sha256':br['native_discrete_sha256'],'actual_start_and_goal_Cu_positive_contact_required':True,'old_cached_fill_only_endpoint_credit':False,'all_native_discrete_copper_and_cross_domain_SBC_planes_hard_obstacles':True,'only_same_domain_owned_new_inner_ground_returns_locally_carved':True,'owned_new_return_carve_ledger':carve_ledger,'owned_new_return_zone_updates_sha256':sha(OUT/'owned-new-return-zone-updates.pkl'),'complete_retained_original_contacts_source_roots_and_field_return_capacity':'MANDATORY_OPEN','production_native_zone_outlines_configuration_and_UUIDs_changed':False,'input_sha256':pins,'r9_exact41_tracks_included_as_hard_obstacles':True,'geometry_min_core_025_not_a_qualified_supply_rating':True,'variable_body_clipped_to_exact_physical_clearance':'Wide body up to8mm is clipped around actual Cu; mesh and every constriction/package/barrel current gate remain open.','new_holes':0,'native_jobs':0,'board_written':False};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
