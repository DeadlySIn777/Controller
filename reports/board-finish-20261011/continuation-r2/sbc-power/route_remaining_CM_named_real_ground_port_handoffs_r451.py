"""Direct named ordinary GND terminal handoffs; only own drill excluded."""
import sys,json,pickle,time,math,copy,uuid
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely import STRtree
P=Path(__file__).resolve().parent;H=P.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
import fast_contacts as F
import tri_route as TR
import physical_reference_losses_r3_zero_r208 as RF
K=N.K;L=N.L;sha=N.sha;NET='/LOGIC_GND';OUT=P/'CM51-alternate-CDONE-direct-named-source-before-ground-port-handoffs-r451'
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
    started=time.monotonic();assert not OUT.exists();OUT.mkdir();prev=P/'CM79-R300-all-native-intents-and-local-unchanged-definition-binding-r431';rr=json.loads((prev/'receipt.json').read_bytes());pf=prev/'only-active-current-Cu-native-poses-all-native-intents-BEFORE-fill-context.pkl';assert sha(pf)==rr['packet_SHA256'];ctx=pickle.loads(pf.read_bytes());c=copy.deepcopy(ctx['current_Cu_and_local_native_pads']);sf=P/'CM51-pruned-real-source-before-safe-subset-incident-terminal-handoffs-r442/only-source-before-connected-safe-CM-subset-no-old-edits.pkl';assert sha(sf)=='f88507f06651daeeaa5ca904b4cd04f0c710cea427d59a599588f3b75c0331ab';selected=pickle.loads(sf.read_bytes());af=P/'CM79-alternate-CDONE-LG16-ONLY_NEW-CM85-leg-controlled-r448/only-qualified-minimal-pose-and-new-tracks.pkl';alt=pickle.loads(af.read_bytes());ef=P/'CM51-retained-CORE-no-new-hole-constructive-F-DC-source-joins-r443/only-new-constructive-DC-F-tracks-no-holes-no-old-edits.pkl';assert sha(ef)=='7de6002db2fafc160769b86c6288a1184075051929dda14823e9d02ab3627bef';extra=pickle.loads(ef.read_bytes());dp=P/'CM73-original-prospective-de03-site-alternate-CDONE-LG16-r450';assert sha(dp/'receipt.json')=='a9af9b3db87a29629b2e99f52eaa0786ea14170f0eaa1315799bca03e9ac8518';df=dp/'only-qualified-prospective-de03-source-port-two-owned-tracks.pkl';de=pickle.loads(df.read_bytes());ports=selected['vias']+[de['via']];c['vias']=[alt['moved_original_barrel']if v['uuid']==alt['moved_original_barrel']['uuid']else v for v in c['vias']]+ports;c['tracks']+=selected['tracks']+[t for t in extra['new_tracks']if t['uuid']!='65f3a90e-a953-5caa-8493-4623cfc05f2f']+alt['only_new_tracks']+de['tracks'];dom=c['domains_normalized'];gap=lambda n:.15 if dom.get(L.norm(n))==dom.get(NET)else .6;region=box(105,154,140,213);roi=region.buffer(2);board=unary_union(L.poly(c['outline'])).buffer(-.626);rec,trees=F.build(c,layers={'F.Cu'});nativeZones={z['uuid']:z for z in c['zones']};cuts=[]
    for jj in trees['F.Cu'].query(roi,predicate='intersects'):
        r=rec['F.Cu'][int(jj)]
        if L.norm(r['net'])==NET:continue
        req=max(gap(r['net']),float(nativeZones[r['uuid']].get('clearance_mm',.15))if r['kind']=='fill'and r['uuid']in nativeZones else .15)+.026;cuts.append(r['shape'].buffer(.1+req,quad_segs=128))
    for z in ctx['all_current_native_intents']:
        if z['layer']=='F.Cu'and L.norm(z['net'])!=NET and z['shape'].intersects(roi):cuts.append(z['shape'].buffer(.1+max(gap(z['net']),z['clearance_mm'])+.026,quad_segs=128))
    for r in ctx['all_current_native_rule_areas']:
        if r['no_tracks']and'F.Cu'in r['layers']:cuts.extend(sh.buffer(.126,quad_segs=128)for sh in L.poly(N.O.polys(r['outline']))if sh.intersects(roi))
    fixed=region.intersection(board).difference(unary_union(cuts));holes=[(v['uuid'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in c['vias']]+[(p['uuid'],s)for p in c['pads']for s in L.poly(p.get('hole')or[])];holes=[(u,sh)for u,sh in holes if sh.intersects(roi)];cases={};progress=[];tracks=[];routes=[];gs,_=N.bound_R663_before_groups({NET});j1=K.root(gs[NET],'J11001','2');planes={ly:unary_union([r['shape']for r in j1 if r['kind']=='fill'and r['layer']==ly])for ly in ('In1.Cu','In4.Cu')};sig=alt['moved_original_barrel'];sigcap=Point(sig['x'],sig['y']).buffer(.575,quad_segs=128)
    for v in ports:
        pp=Point(v['x'],v['y']);ann=pp.buffer(.25,quad_segs=128).difference(pp.buffer(.1,quad_segs=128));over={ly:ann.intersection(planes[ly].difference(sigcap)).area for ly in planes};assert all(x>0 for x in over.values());space=fixed.difference(unary_union([sh.buffer(.381,quad_segs=128)for u,sh in holes if u!=v['uuid']]));cases[v['uuid']]={'free':space,'faces':RF.parts(space),'ann':ann,'source_annuli':over}
    # CM73 has its own newly requalified two-track handoff already. Rebind CM85
    # as well, whose future second leg was necessarily withdrawn for CDONE.
    remaining=[r for r in extra['still_unconnected_pads']if not(r['ref']=='J15002'and str(r['pin'])=='73')]+[{'pad_UUID':'cd8ff67e-caa2-4493-8323-f083a0c9d796','ref':'J15002','pin':'85'}]
    for info in remaining:
        uid=info.get('pad_UUID',info.get('UUID'));p=next(p for p in c['pads']if p['uuid']==uid);start=Point(p['x'],p['y']);pad=unary_union(L.poly(p['layers']['F.Cu']));row={'pad_UUID':uid,'ref':p['ref'],'pin':p['num'],'routes_screened':[],'route':None};choices=sorted(ports,key=lambda v:start.distance(Point(v['x'],v['y'])))[:8];accepted=[]
        for v in choices:
            case=cases[v['uuid']];end=Point(v['x'],v['y']);face=next((f for f in case['faces']if f.covers(start)and f.covers(end)),None);trial={'only_owned_target_ground_via_UUID':v['uuid'],'same_full20_F_component':face is not None};row['routes_screened'].append(trial)
            if face is None:continue
            path,method=TR.route(face,[p['x'],p['y']],[v['x'],v['y']]);path=[[round(x,6),round(y,6)]for x,y in path];axis=LineString(path);body=unary_union([LineString([a,b]).buffer(.1,quad_segs=128)for a,b in zip(path,path[1:])]);length=sum(math.dist(a,b)for a,b in zip(path,path[1:]));contact=body.intersection(case['ann']).area;pc=body.intersection(pad).area;own=body.difference(end.buffer(.525,quad_segs=128));clear=None if own.is_empty else own.distance(end.buffer(.1,quad_segs=128));trial.update(length_mm=length,finite_own_annulus_contact_mm2=contact,finite_pad_contact_mm2=pc)
            if not face.covers(axis)or contact<=0 or pc<=0 or length>15 or(clear is not None and clear<.28):continue
            accepted.append((length,v,path,method,contact,pc,clear))
            # A short real terminal handoff suffices; no repeated wider search.
            if length<4:break
        if accepted:
            length,v,path,method,ac,pc,clear=min(accepted,key=lambda x:x[0]);nt=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM51-R451:'+uid+':'+str(i))),'net':NET,'layer':'F.Cu','w':.2,'a':a,'b':b}for i,(a,b)in enumerate(zip(path,path[1:]))];tracks+=nt;routes.append({'pad_UUID':uid,'ref':p['ref'],'pin':p['num'],'tracks':nt,'only_owned_ordinary_SOURCE_before_port_UUID':v['uuid'],'source_annuli_both_planes':cases[v['uuid']]['source_annuli'],'finite_own_annulus_contact_mm2':ac,'finite_pad_contact_mm2':pc,'outside_own525cap_physical_drill_clearance_mm':clear,'length_mm':length,'native_actual_AFTER_source_masks':'OPEN'});row.update(route=path,length_mm=length,owned_port=v['uuid'],method=method);print('R451_ROUTE',p['ref'],p['num'],length,len(nt),flush=True)
        progress.append(row);put('only-named-ground-terminal-handoff-progress.json',progress)
    packet={'new_tracks':tracks,'new_vias':[],'routes':routes,'still_unconnected':[{k:r[k]for k in ('pad_UUID','ref','pin')}for r in progress if r['route']is None],'dependencies':{'R442':str(sf),'R443':str(ef),'R448_alternate':str(af),'R450_de03':str(df)},'only_retired_NEW_Cu':['65f3a90e-a953-5caa-8493-4623cfc05f2f'],'R435_native_patch_NOT_REPLAYED':True,'actual_NATIVE_AFTER_SOURCE_oldref_current_thermal':'OPEN'};(OUT/'only-new-named-source-before-ground-terminal-F-handoffs.pkl').write_bytes(pickle.dumps(packet,protocol=5));put('receipt.json',{'status':'EXACT_NAMED_ORDINARY_SOURCE_BEFORE_GROUND_HANDOFFS_ONLY','pads_screened':len(progress),'new_ground_pad_routes':len(routes),'still_unconnected_pad_count':len(packet['still_unconnected']),'new_F20_track_count':len(tracks),'own_terminal_cap_radius_mm':.525,'only_owned_ground_drill_guard_excluded_each_case':True,'all_other_current_and_new_peer_holes_foreign_Cu_native_intents_hard':True,'planner_axis_additional_margin_mm':.026,'SOURCE_before_real_annuli_bothplanes_required':True,'packet_SHA256':sha(OUT/'only-new-named-source-before-ground-terminal-F-handoffs.pkl'),'actual_current_NATIVE_AFTER_SOURCE_masks_oldref_current_thermal':'OPEN','original_Cu_withdrawals_other_than_exact_alternate_b1_pose':0,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R451_COMPLETE',sha(OUT/'receipt.json'),len(routes),len(packet['still_unconnected']),len(tracks),packet['still_unconnected'],flush=True)
if __name__=='__main__':main()
