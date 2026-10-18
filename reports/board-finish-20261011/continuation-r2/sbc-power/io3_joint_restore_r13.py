"""Restore full old IO3 contacts on current root base with coupled GND repairs.

Bound local triangle searches; allow existing actual flashed layers, no new holes.
"""
import json,hashlib,math,pickle,time,uuid
from pathlib import Path
from shapely import from_wkb,set_precision,STRtree
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
import complete_geometry_r2 as G
import zone_projection_r1 as P
import re
import io3_contact_restore_r2 as Q
import continuous_path_fast_r1 as CP
L=G.L;p=G.p;R=G.B.J.R;NET='/IO_3V3';OUT=L.OUT/'coupled-power-geometry-frozen-r13'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir();g,h,tail,binding,zones=G.model(True,True,'r7',True,True)
    fb=L.OUT.parent/'field-power/native-bound-field-base-r5';fbr=json.loads((fb/'receipt.json').read_text());assert sha(fb/'receipt.json')=='528034a2ce7ad7ae58915704bb55b0a55e7c749bb0dcacf789ade300b95f7b31';assert sha(fb/'model.pkl')==fbr['model_sha256'];fm=pickle.loads((fb/'model.pkl').read_bytes());assert fbr['native_discrete_sha256']=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';g=fm['old'];h=fm['discrete'];binding['exact_native_bound_field_model_receipt_sha256']=sha(fb/'receipt.json');binding['exact_native_bound_field_model_sha256']=sha(fb/'model.pkl')
    gr=L.OUT.parent/'field-power/logic-return-repair-r2/receipt.json';rr=json.loads(gr.read_text());assert sha(gr)=='a8ea7e711121c83b3286a7965b26b4c5b1c1a92c939bd1c008e5ee2607f0b348'
    for row in rr['rows']:
        q=row['repair'];assert q is not None;f=Path(q['geometry_file']);assert sha(f)==q['sha256'];zones.append({'uuid':q['uuid'],'label':'LOGIC-GND-repair-'+q['uuid'],'net':'/LOGIC_GND','layer':q['layer'],'shape':set_precision(from_wkb(f.read_bytes()),1e-6),'field_logic_repair_proposal':True})
    binding['field_LOGIC_GND_repair_receipt_sha256']=sha(gr);binding['field_LOGIC_GND_geometry_quantized_for_this_proposal_nm']=1
    fr=L.OUT.parent/'field-power/field-contact-repair-r2-raw/receipt.json';fq=json.loads(fr.read_text());assert sha(fr)=='d9061cb443f9ae9227e1ef00a3267d7b708c5b61615eea9078d2949a8c8bdc6b'
    for row in fq['rows']:
        q=row['repair'];assert q is not None;f=Path(q['geometry_file']);assert sha(f)==q['sha256'];zones.append({'uuid':q['uuid'],'label':'field-contact-repair-'+q['uuid'],'net':q['net_raw'],'layer':q['layer'],'shape':set_precision(from_wkb(f.read_bytes()),1e-6),'field_contact_repair_proposal':True})
    binding['field_contact_repair_receipt_sha256']=sha(fr)
    nb=L.OUT.parent/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(nb)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
    binding['exact_native_discrete_board_file']=str(nb.resolve());binding['exact_native_discrete_board_sha256']=sha(nb)
    nr=L.OUT.parent/'sbc-native-contract-r3-layer-ids/receipt.json';binding['exact_native_discrete_contract_receipt_file']=str(nr.resolve());binding['exact_native_discrete_contract_receipt_sha256']=sha(nr)
    br=L.OUT.parent/'field-power/b5-contact-repair-r3-frozen/receipt.json';breceipt=json.loads(br.read_text());assert sha(br)=='07c3582abf2363eec417110ed07552d5aef4fa48d620d1c798f1d60f4ef73ca5'
    bp=br.parent/'proposed-zones.pkl';assert sha(bp)==breceipt['proposal_sha256']
    for row in breceipt['rows']:
        q=row['repair'];f=Path(q['geometry_file']);assert sha(f)==q['sha256'];zones.append({'uuid':q['uuid'],'label':'B5-contact-repair-'+q['uuid'],'net':q['net_raw'],'layer':q['layer'],'shape':set_precision(from_wkb(f.read_bytes()),1e-6),'field_B5_repair_proposal':True})
    binding['field_B5_contact_repair_receipt_sha256']=sha(br)
    cp=L.OUT/'coupled-power-geometry-frozen-r11/routing-checkpoint.json';cr=json.loads(cp.read_text());binding['reused_constructed_IO3_checkpoint_sha256']=sha(cp)
    for q in cr['fingers']:
        f=Path(q['geometry_file']);assert sha(f)==q['sha256'];zones.append({**q,'shape':set_precision(from_wkb(f.read_bytes()),1e-6),'reused_IO3_finger':True})
    outline=unary_union(p.base.polygons(g['outline']));board_free=set_precision(outline.buffer(-.525),1e-6);binding['exact_native_outline_guard_mm']=.525
    oldcore=next(q for q in zones if q['label']=='CORE-main-In2')
    for q in zones:
        q['shape']=set_precision(q['shape'].intersection(board_free),1e-6)
        if q.get('reused_IO3_finger') and q['layer']=='In2.Cu':oldcore['shape']=set_precision(oldcore['shape'].difference(q['shape'].buffer(.175)),1e-6)
    binding['old_zone_local_clearance_aware_projection']=True;binding['final_new_zone_priority']=124
    raw_names=set(re.findall(r'\(net "([^"\n]*)"\)',nb.read_text(encoding='utf-8')));native_by_norm={}
    for raw in raw_names:
        normalized=p.norm(raw);assert normalized not in native_by_norm or native_by_norm[normalized]==raw;native_by_norm[normalized]=raw
    discrete=OUT/'exact-native-bound-model.pkl';discrete.write_bytes(pickle.dumps((g,h,binding,zones),protocol=5))
    (OUT/'exact-native-bound-model-receipt.json').write_text(json.dumps({'verdict':'HOST_RECONSTRUCTION_BOUND_TO_COMPLETE_NATIVE_DISCRETE_CONTRACT','cache_file':str(discrete.resolve()),'cache_sha256':sha(discrete),'binding':binding,'source_host_constructor':str(Path(G.__file__).resolve()),'zone_projector':str(Path(P.__file__).resolve()),'zone_projector_sha256':sha(Path(P.__file__)),'new_proposal_zone_count':len(zones),'actual_native_contract_board_sha256':sha(nb),'actual_native_contract_receipt_sha256':sha(nr),'source_model_pad_count':len(h['pads']),'source_model_track_count':len(h['tracks']),'source_model_via_count':len(h['vias']),'native_refill_current_contact_gates_open':True,'native_jobs':0,'board_written':False},indent=2)+'\n')
    candidate,cuts=P.projected(g,h,zones);print('IO3_R9_PROJECTED',binding['parent_board_sha256'],len(zones),len(cuts),flush=True);Q.NET=NET
    before,bparts,bassign=Q.groups(g,return_details=True);after,aparts,aassign=Q.groups(candidate,return_details=True);mainold=max(before,key=lambda xs:sum(not r['ref'].startswith('@') for r in xs));oldids={q['uuid'] for q in mainold};counts={i:sum(r['uuid'] in oldids for r in group) for i,group in enumerate(after)};root=max(counts,key=counts.get);detached=sorted((i for i,n in counts.items() if n and i!=root),key=lambda i:counts[i],reverse=True);joined={root};fingers=[];fail=[];attempts=[]
    (OUT/'initial-contact-partitions.json').write_text(json.dumps({'old_main_contacts':mainold,'new_main_root_group':root,'split_groups':{str(i):[q for q in after[i] if q['uuid'] in oldids] for i in detached},'full_candidate_groups':after},indent=1)+'\n');print('IO3_R9_PARTITIONS',root,[(i,counts[i]) for i in detached],flush=True)
    core=next(q['shape'] for q in zones if q['label']=='CORE-main-In2');cache={}
    def source_on(layer):return unary_union([q for q,j in zip(aparts[layer],aassign[layer]) if j in joined]+[q['shape'] for q in fingers if q['layer']==layer])
    for group in detached:
        found=None
        for layer in ('In2.Cu','In3.Cu','B.Cu','F.Cu','In1.Cu','In4.Cu'):
            source=source_on(layer);target=unary_union([q for q,j in zip(aparts[layer],aassign[layer]) if j==group]);
            if source.is_empty or target.is_empty:continue
            aa,bb=nearest_points(source,target);bound=LineString([aa,bb]).bounds
            for margin in (3.,10.,30.,90.):
                window=box(max(.526,bound[0]-margin),max(.526,bound[1]-margin),min(449.474,bound[2]+margin),min(234.474,bound[3]+margin));key=(layer,tuple(window.bounds));p.WINDOW=window
                if layer not in cache:
                    p.WINDOW=box(.526,.526,449.474,234.474)
                    route_model=candidate
                    if layer in ('In1.Cu','In4.Cu'):
                        original_zones={q['uuid'] for q in g['zones']};route_model={**candidate,'zones':[q for q in candidate['zones'] if not(q['uuid'] in original_zones and p.norm(q['net'])=='/LOGIC_GND')]}
                    cache[layer]=set_precision(R.free_layer(route_model,NET,layer,p.WINDOW,(L.stage.caps.CORE,) if layer=='In2.Cu' else (),reference_guard=None,allow_own_via_connection=True).intersection(board_free),1e-6);print('IO3_R13_GLOBAL_FREE',layer,cache[layer].area,flush=True)
                free=cache[layer].intersection(window);freeparts=p.hubs.components(free)
                if not freeparts:continue
                tree=STRtree(freeparts);shared=set(map(int,tree.query(source,predicate='intersects')))&set(map(int,tree.query(target,predicate='intersects')))
                if not shared:continue
                usable=unary_union([freeparts[i] for i in shared])
                for width in (1.25,1.,.75,.5,.35,.25,.20):
                    centre=set_precision(usable.buffer(-width/2),1e-6);options=[]
                    for part in p.hubs.components(centre):
                        a=part.intersection(source);b=part.intersection(target)
                        if a.is_empty or b.is_empty:continue
                        an,bn=nearest_points(a,b);aa2=a.intersection(an.buffer(.2)).representative_point().coords[0];bb2=b.intersection(bn.buffer(.2)).representative_point().coords[0];options.append((math.dist(aa2,bb2),part,aa2,bb2))
                    for _,part,aa2,bb2 in sorted(options,key=lambda q:q[0])[:3]:
                        print('IO3_R9_SEARCH',group,layer,margin,width,part.area,flush=True);route=CP.path(part,aa2,bb2,node_cap=500000);attempt={'group':group,'layer':layer,'margin_mm':margin,'width_mm':width,'route_verdict':route['verdict'],'triangle_count':route.get('triangle_count',route.get('continuous_polygon_triangles'))};attempts.append(attempt);print('IO3_R9_RESULT',attempt,flush=True)
                        if route['verdict']!='HOST_PATH':continue
                        sh=set_precision(LineString(route['points']).buffer(width/2).intersection(free),1e-6)
                        if sh.intersection(source).is_empty or sh.intersection(target).is_empty:continue
                        found=layer,width,route,sh;break
                    if found:break
                if found:break
            if found:break
        if not found:fail.append({'candidate_group':group,'old_contacts':[q for q in after[group] if q['uuid'] in oldids]});print('IO3_R9_UNRESOLVED',group,flush=True)
        else:
            layer,width,route,sh=found;uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-sbc-r2-IO3-coupled-r13-'+str(group)));f=OUT/('IO3-joint-restoration-'+str(group)+'.wkb');f.write_bytes(sh.wkb);fingers.append({'candidate_group':group,'old_contacts':[q for q in after[group] if q['uuid'] in oldids],'uuid':uid,'label':'IO3-joint-restoration-'+str(group),'net':NET,'layer':layer,'shape':sh,'width_mm':width,'route':route,'geometry_file':str(f.resolve()),'sha256':sha(f),'area_mm2':sh.area,'original_LOGIC_GND_fill_retreat_required':layer in ('In1.Cu','In4.Cu')});joined.add(group)
            if layer=='In2.Cu':core=set_precision(core.difference(sh.buffer(.175)),1e-6)
            print('IO3_R9_RESTORED',group,layer,width,route['length_mm'],flush=True)
        (OUT/'routing-checkpoint.json').write_text(json.dumps({'joined_groups':sorted(joined),'unresolved':fail,'attempts':attempts,'fingers':[{k:v for k,v in q.items() if k!='shape'} for q in fingers]},indent=1)+'\n')
    rows=[]
    for z in zones+fingers:
        sh=core if z['label']=='CORE-main-In2' else z['shape'];f=OUT/(z['label']+'.wkb');f.write_bytes(set_precision(sh,1e-6).wkb);rows.append({'label':z['label'],'uuid':z['uuid'],'net_raw':native_by_norm[p.norm(z['net'])],'layer':z['layer'],'geometry_file':str(f.resolve()),'sha256':sha(f),'area_mm2':sh.area,'field_return_proposal':bool(z.get('field_return_proposal')),'field_logic_repair_proposal':bool(z.get('field_logic_repair_proposal')),'field_contact_repair_proposal':bool(z.get('field_contact_repair_proposal')),'field_B5_repair_proposal':bool(z.get('field_B5_repair_proposal')),'priority':124,'clearance_mm':.15,'min_thickness_mm':.15})
    result={'verdict':'COUPLED_IO3_RESTORATION_CONSTRUCTION_ONLY' if not fail else 'COUPLED_IO3_RESTORATION_INCOMPLETE','exact_source_board_sha256':L.live.SHA,'combined_parent_binding':binding,'native_coordinate_grid_nm':1,'zones':rows,'IO3_restoration_fingers':[{k:v for k,v in q.items() if k!='shape'} for q in fingers],'IO3_unresolved_contact_groups':fail,'baseline_main_original_contacts':len(mainold),'initial_detached_contact_groups':detached,'attempts':attempts,'new_holes':0,'all_original_IO3_pad_track_barrel_and_plane_native_guards_required':True,'full_current_reference_and_native_gates_open':True,'native_jobs':0,'board_written':False};(OUT/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print('IO3_R9_RECIPE',len(fingers),len(fail),flush=True)
if __name__=='__main__':main()
