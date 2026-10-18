"""Constructive .20 F DC joins around retained original Cu; no new holes."""
import sys,json,pickle,time,math,copy,uuid
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely import STRtree
P=Path(__file__).resolve().parent;H=P.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
import fast_contacts as F
import tri_route as TR
import physical_reference_losses_r3_zero_r208 as RF
K=N.K;L=N.L;sha=N.sha;NET='/LOGIC_GND'
OUT=P/'CM51-retained-CORE-no-new-hole-constructive-F-DC-source-joins-r443'
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
    started=time.monotonic();assert not OUT.exists();OUT.mkdir();d=P/'CM51-pruned-real-source-before-safe-subset-incident-terminal-handoffs-r442';assert sha(d/'receipt.json')=='77dc4017c1dc6e614ae11cf8bc562d38d6789fbacdf909ab26b7cb1dce6cf6e8';sr=json.loads((d/'receipt.json').read_bytes());pf=d/'only-source-before-connected-safe-CM-subset-no-old-edits.pkl';assert sha(pf)==sr['selected_packet_SHA256'];selected=pickle.loads(pf.read_bytes());prev=P/'CM79-R300-all-native-intents-and-local-unchanged-definition-binding-r431';rr=json.loads((prev/'receipt.json').read_bytes());cf=prev/'only-active-current-Cu-native-poses-all-native-intents-BEFORE-fill-context.pkl';assert sha(cf)==rr['packet_SHA256'];ctx=pickle.loads(cf.read_bytes());c=copy.deepcopy(ctx['current_Cu_and_local_native_pads']);mp=Path(selected['R435_minimal_patch_dependency']);assert sha(mp)==selected['R435_minimal_patch_SHA256'];minimal=pickle.loads(mp.read_bytes());c['vias']=[minimal['moved_original_via']if v['uuid']==minimal['moved_original_via']['uuid']else v for v in c['vias']]+minimal['only_new_vias']+selected['vias'];c['tracks']+=minimal['only_new_tracks']+selected['tracks'];dom=c['domains_normalized'];gap=lambda n:.15 if dom.get(L.norm(n))==dom.get(NET)else .6;region=box(105,154,140,213);roi=region.buffer(2);board=unary_union(L.poly(c['outline'])).buffer(-.625005);rec,trees=F.build(c,layers={'F.Cu'});nativeZones={z['uuid']:z for z in c['zones']};cuts=[]
    for jj in trees['F.Cu'].query(roi,predicate='intersects'):
        r=rec['F.Cu'][int(jj)]
        if L.norm(r['net'])==NET:continue
        req=max(gap(r['net']),float(nativeZones[r['uuid']].get('clearance_mm',.15))if r['kind']=='fill'and r['uuid']in nativeZones else .15)+.025005;cuts.append(r['shape'].buffer(.1+req,quad_segs=64))
    for z in ctx['all_current_native_intents']:
        if z['layer']=='F.Cu'and L.norm(z['net'])!=NET and z['shape'].intersects(roi):cuts.append(z['shape'].buffer(.1+max(gap(z['net']),z['clearance_mm'])+.025005,quad_segs=64))
    holes=[Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)for v in c['vias']]+[s for p in c['pads']for s in L.poly(p.get('hole')or[])];cuts.extend(sh.buffer(.380005,quad_segs=64)for sh in holes if sh.intersects(roi))
    for r in ctx['all_current_native_rule_areas']:
        if r['no_tracks']and'F.Cu'in r['layers']:cuts.extend(sh.buffer(.125005,quad_segs=64)for sh in L.poly(N.O.polys(r['outline']))if sh.intersects(roi))
    free=region.intersection(board).difference(unary_union(cuts));(OUT/'actual-current-Cu-intent-holes-and-selected-peers-full20-F-centre-free.wkb').write_bytes(free.wkb);faces=RF.parts(free);gs,_=N.bound_R663_before_groups({NET});source=K.root(gs[NET],'J11001','2');iv0=K.A.C.inventory((N.R157/'copy/board.kicad_pcb').read_bytes());iv1=K.A.C.inventory(Path(ctx['active_board']).read_bytes());pose=json.loads((H/'combined-R753-one-full-native-fill-cached-DRC-r299/native-full/before-native-all-FP-pad-pose.json').read_bytes());sourceShapes=[]
    for r in source:
        if r['layer']!='F.Cu'or not r['shape'].intersects(roi):continue
        if r['kind']in {'track','via'}and(r['uuid']not in iv1[3]or iv1[3][r['uuid']]!=iv0[3][r['uuid']]):continue
        if r['kind']=='pad':
            p=next(p for p in c['pads']if p['uuid']==r['uuid']);q=pose['pads'][p['uuid']]
            if(p['x'],p['y'],p['net'])!=(q[2]/1e6,q[3]/1e6,q[1]):continue
        sourceShapes.append(r['shape'])
    sourceShapes.extend(LineString([t['a'],t['b']]).buffer(.1,quad_segs=128)for t in selected['tracks']+[t for t in minimal['only_new_tracks']if L.norm(t['net'])==NET]);sourceCu=unary_union(sourceShapes);ht=STRtree(holes);localHoles=unary_union([holes[int(j)]for j in ht.query(sourceCu,predicate='intersects')]);sourceCu=sourceCu.difference(localHoles);progress=[];new=[];routes=[]
    for pinfo in selected['unconnected_pads']:
        p=next(p for p in c['pads']if p['uuid']==pinfo['UUID']);start=Point(p['x'],p['y']);ownedPad=unary_union(L.poly(p['layers']['F.Cu']));face=next((f for f in faces if f.covers(start)),None);row={'pad_UUID':p['uuid'],'ref':p['ref'],'pin':p['num'],'at':[p['x'],p['y']],'start_centre_free':face is not None,'route':None}
        if face is None:progress.append(row);continue
        target=sourceCu.intersection(face)
        if target.is_empty:row['no_SOURCE_before_Cu_in_same_F_centre_component']=True;progress.append(row);continue
        _,near=nearest_points(start,target);endpoint=[round(near.x,6),round(near.y,6)]
        if not face.covers(Point(*endpoint)):
            part=min(RF.parts(target),key=lambda sh:sh.distance(start));pt=part.representative_point();endpoint=[round(pt.x,6),round(pt.y,6)]
        if not face.covers(Point(*endpoint)):row['finite_nm_endpoint_not_covered']=True;progress.append(row);continue
        path,method=TR.route(face,[p['x'],p['y']],endpoint);path=[[round(x,6),round(y,6)]for x,y in path];axis=LineString(path);body=unary_union([LineString([a,b]).buffer(.1,quad_segs=128)for a,b in zip(path,path[1:])]);length=sum(math.dist(a,b)for a,b in zip(path,path[1:]));contact=body.intersection(sourceCu).area;pc=body.intersection(ownedPad).area
        if not face.covers(axis)or contact<=0 or pc<=0 or length>15:row.update({'rejected_length_or_exact_Cu_contact_or_containment':True,'length_mm':length,'source_contact_mm2':contact,'pad_contact_mm2':pc});progress.append(row);continue
        tracks=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM51-R443-ground:'+p['uuid']+':'+str(i))),'net':NET,'layer':'F.Cu','w':.2,'a':a,'b':b}for i,(a,b)in enumerate(zip(path,path[1:]))];new.extend(tracks);routes.append({'pad_UUID':p['uuid'],'ref':p['ref'],'pin':p['num'],'tracks':tracks,'source_before_finite_Cu_contact_mm2':contact,'own_CM_pad_finite_Cu_contact_mm2':pc,'path_length_mm':length,'native_actual_AFTER_SOURCE':'OPEN'});row.update({'route':path,'method':method,'length_mm':length,'source_contact_mm2':contact,'pad_contact_mm2':pc});progress.append(row);sourceCu=sourceCu.union(body);put('constructive-no-new-hole-DC-route-progress.json',progress);print('R443_ROUTE',p['ref'],p['num'],length,len(tracks),flush=True)
    put('constructive-no-new-hole-DC-route-progress.json',progress);packet={'new_tracks':new,'new_vias':[],'new_DC_routes':routes,'R442_selected_source_before_subset_dependency':str(pf.resolve()),'R442_packet_SHA256':sha(pf),'R435_minimal_patch_dependency':str(mp.resolve()),'R435_packet_SHA256':sha(mp),'still_unconnected_pads':[r for r in progress if r['route']is None],'actual_native_AFTER_SOURCE_fullbody_oldrefs_current_thermal':'OPEN'};(OUT/'only-new-constructive-DC-F-tracks-no-holes-no-old-edits.pkl').write_bytes(pickle.dumps(packet,protocol=5));put('receipt.json',{'status':'CONSTRUCTIVE_NO_NEW_HOLE_CM_DC_F_SOURCE_BEFORE_JOINS','R442_receipt_SHA256':sha(d/'receipt.json'),'R442_initial_connected_CM_pad_count':sr['CM51_source_before_finite_connected_pad_count'],'remaining_CM_pads_screened':len(progress),'newly_nominated_finite_SOURCE_before_CM_joins':len(routes),'still_unconnected_CM_pad_count':len(packet['still_unconnected_pads']),'new_F20_track_count':len(new),'new_holes_original_Cu_deletes_FP_moves_zone_definition_changes':0,'entire_locked_CORE_dc1a_retained':True,'all_true_current_foreign_Cu_native_intents_and_selected_peer_holes_hard':True,'fast_SIGNAL_shadow_gate_not_applied_to_DC_GROUND':'raw shadow/current/native still pending separately; finite source attachment is mandatory','packet_SHA256':sha(OUT/'only-new-constructive-DC-F-tracks-no-holes-no-old-edits.pkl'),'actual_current_NATIVE_AFTER_SOURCE_oldbodyrefs_masks_current_thermal':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R443_COMPLETE',sha(OUT/'receipt.json'),len(routes),len(packet['still_unconnected_pads']),len(new),flush=True)
if __name__=='__main__':main()
