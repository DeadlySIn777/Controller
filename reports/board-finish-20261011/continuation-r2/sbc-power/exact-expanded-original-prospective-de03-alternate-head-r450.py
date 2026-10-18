"""Prospective-only de03 80 um shift and two genuinely owned GND tracks."""
import sys,json,pickle,time,math,copy,uuid
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely import STRtree
P=Path(__file__).resolve().parent;H=P.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
import fast_contacts as F
K=N.K;L=N.L;sha=N.sha;NET='/LOGIC_GND';OUT=P/'CM73-original-prospective-de03-site-alternate-CDONE-LG16-r450'
NORMAL={'58c55cd5-98e6-4467-88e3-146ceeee361a','c1d27fa1-452b-4e27-985d-5ad23644d800','54921f4b-0308-4821-9549-ff9360bf05ca'}
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
    started=time.monotonic();assert not OUT.exists();OUT.mkdir();prev=P/'CM79-R300-all-native-intents-and-local-unchanged-definition-binding-r431';rr=json.loads((prev/'receipt.json').read_bytes());pf=prev/'only-active-current-Cu-native-poses-all-native-intents-BEFORE-fill-context.pkl';assert sha(pf)==rr['packet_SHA256'];ctx=pickle.loads(pf.read_bytes());c=copy.deepcopy(ctx['current_Cu_and_local_native_pads']);r442=P/'CM51-pruned-real-source-before-safe-subset-incident-terminal-handoffs-r442';selected=pickle.loads((r442/'only-source-before-connected-safe-CM-subset-no-old-edits.pkl').read_bytes());alternate=P/'CM79-alternate-CDONE-LG16-ONLY_NEW-CM85-leg-controlled-r448';assert sha(alternate/'receipt.json')=='e53622a3d6bcca7a2ad5818758e2464db63cbcff69cb70b8264ba26394fd5b05';mp=alternate/'only-qualified-minimal-pose-and-new-tracks.pkl';alt=pickle.loads(mp.read_bytes());minimal={'moved_original_via':alt['moved_original_barrel'],'only_new_vias':[],'only_new_tracks':alt['only_new_tracks']};r443=P/'CM51-retained-CORE-no-new-hole-constructive-F-DC-source-joins-r443';assert sha(r443/'receipt.json')=='486886b6fe8000cf1b64a4e0e54a6bddea15411f2c3bb0c59daaf96c6b51f351';p443=r443/'only-new-constructive-DC-F-tracks-no-holes-no-old-edits.pkl';extra=pickle.loads(p443.read_bytes());c['vias']=[minimal['moved_original_via']if v['uuid']==minimal['moved_original_via']['uuid']else v for v in c['vias']]+selected['vias'];c['tracks']+=minimal['only_new_tracks']+selected['tracks']+[t for t in extra['new_tracks']if t['uuid']!='65f3a90e-a953-5caa-8493-4623cfc05f2f'];uid='de03bc75-a546-50e2-86eb-bb1dd0e34a9e';assert uid not in {v['uuid']for v in c['vias']};v={'uuid':uid,'net':NET,'x':118.357505,'y':200.400031,'d':.5,'drill':.2,'span':K.LAYERS,'flashed':K.LAYERS,'mask_provenance':'prospective conservative guard only; actual native masks OPEN'};p=Point(v['x'],v['y']);dom=c['domains_normalized'];gap=lambda n:.15 if dom.get(L.norm(n))==dom.get(NET)else .6;rec,trees=F.build(c);nativeZones={z['uuid']:z for z in c['zones']};bad=[];normal=[]
    for ly in K.LAYERS:
        for jj in trees[ly].query(p.buffer(1.3),predicate='intersects'):
            r=rec[ly][int(jj)];n=L.norm(r['net'])
            if n==NET:continue
            local=float(nativeZones[r['uuid']].get('clearance_mm',.15))if r['kind']=='fill'and r['uuid']in nativeZones else .15;req=max(local,gap(n))+.025
            if r['kind']=='fill'and r['uuid']in NORMAL and dom.get(n)==dom.get(NET):
                if p.distance(r['shape'])-.25<req:normal.append({'UUID':r['uuid'],'layer':ly,'native_original_normal_same_domain_antipad_radius_mm':.25+local})
                continue
            distance=p.distance(r['shape'])-.25
            if r['kind']=='via':distance=math.dist([v['x'],v['y']],[r['source']['x'],r['source']['y']])-.25-r['source']['d']/2
            if r['kind']=='track':distance=LineString([r['source']['a'],r['source']['b']]).distance(p)-.25-r['source']['w']/2
            if distance<req:bad.append({'kind':'new_port_true_current_foreign_Cu','UUID':r['uuid'],'layer':ly,'distance_mm':distance,'required_mm':req})
        for z in ctx['all_current_native_intents']:
            if z['layer']==ly and L.norm(z['net'])!=NET and z['uuid']not in NORMAL and p.distance(z['shape'])-.25<max(gap(z['net']),z['clearance_mm'])+.025:bad.append({'kind':'new_port_held_current_foreign_intent','UUID':z['uuid'],'layer':ly})
    holes=[(vv['uuid'],Point(vv['x'],vv['y']).buffer(vv['drill']/2,quad_segs=128))for vv in c['vias']]+[(pp['uuid'],sh)for pp in c['pads']for sh in L.poly(pp.get('hole')or[])];ht=STRtree([sh for u,sh in holes]);smds=[(pp['uuid'],sh)for pp in c['pads']if not pp.get('hole')for ly in ('F.Cu','B.Cu')for sh in L.poly(pp['layers'].get(ly,[]))];st=STRtree([sh for u,sh in smds]);vp=[Point(vv['x'],vv['y'])for vv in c['vias']];vt=STRtree(vp)
    for jj in ht.query(p.buffer(.6),predicate='intersects'):
        u,sh=holes[int(jj)]
        if p.distance(sh)-.1<.28:bad.append({'kind':'new_port_current_other_drill','UUID':u})
    for jj in st.query(p.buffer(.4),predicate='intersects'):
        u,sh=smds[int(jj)]
        if p.distance(sh)-.1<.28:bad.append({'kind':'new_port_current_SMD_drill','UUID':u})
    for jj in vt.query(p.buffer(.82),predicate='intersects'):
        if p.distance(vp[int(jj)])<.815:bad.append({'kind':'new_port_current_or_selected_peer_pitch','UUID':c['vias'][int(jj)]['uuid']})
    for r in ctx['all_current_native_rule_areas']:
        if r['no_vias']and any(p.distance(sh)<.275 for sh in L.poly(N.O.polys(r['outline']))):bad.append({'kind':'new_port_actual_native_no_via','UUID':r['uuid']})
    gs,_=N.bound_R663_before_groups({NET});root=K.root(gs[NET],'J11001','2');planes={ly:unary_union([r['shape']for r in root if r['kind']=='fill'and r['layer']==ly])for ly in ('In1.Cu','In4.Cu')};ann=p.buffer(.25,quad_segs=128).difference(p.buffer(.1,quad_segs=128));sig=minimal['moved_original_via'];signalcap=Point(sig['x'],sig['y']).buffer(.575,quad_segs=128);over={ly:ann.intersection(planes[ly].difference(signalcap)).area for ly in planes}
    if not all(x>0 for x in over.values()):bad.append({'kind':'no_actual_BEFORE_J1_SOURCE_both_annuli','overlap':over})
    tracks=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM73-R450-owned-F:'+str(i))),'net':NET,'layer':'F.Cu','w':.2,'a':a,'b':b}for i,(a,b)in enumerate([([118.652,201.175],[118.652,200.608184]),([118.652,200.608184],[v['x'],v['y']])])];tb=[]
    for t in tracks:
        axis=LineString([t['a'],t['b']]);body=axis.buffer(.1,quad_segs=128);errs=[]
        for jj in trees['F.Cu'].query(body.buffer(.8),predicate='intersects'):
            r=rec['F.Cu'][int(jj)];n=L.norm(r['net'])
            if n==NET:continue
            req=max(gap(n),float(nativeZones[r['uuid']].get('clearance_mm',.15))if r['kind']=='fill'and r['uuid']in nativeZones else .15)+.025;distance=body.distance(r['shape'])
            if r['kind']=='via':distance=axis.distance(Point(r['source']['x'],r['source']['y']))-.1-r['source']['d']/2
            if r['kind']=='track':distance=axis.distance(LineString([r['source']['a'],r['source']['b']]))-.1-r['source']['w']/2
            if distance<req:errs.append({'kind':'owned_track_true_current_foreign_Cu','UUID':r['uuid'],'distance_mm':distance,'required_mm':req})
        for z in ctx['all_current_native_intents']:
            if z['layer']=='F.Cu'and L.norm(z['net'])!=NET and body.distance(z['shape'])<max(gap(z['net']),z['clearance_mm'])+.025:errs.append({'kind':'owned_track_held_foreign_current_intent','UUID':z['uuid']})
        for jj in ht.query(body.buffer(.3),predicate='intersects'):
            u,sh=holes[int(jj)]
            if body.distance(sh)<.28:errs.append({'kind':'owned_track_other_current_peer_drill','UUID':u})
        own=body.difference(p.buffer(.525,quad_segs=128));assert own.is_empty or own.distance(p.buffer(.1,quad_segs=128))>=.28;tb.append({'UUID':t['uuid'],'deficits':errs,'own_named_de03_terminal_only_525_cap':True,'finite_own_annulus_contact_mm2':body.intersection(ann).area,'raw_SOURCE_before_F_shadow_gap_mm2':body.difference(planes['In1.Cu']).area});bad.extend(errs)
    cm=next(pp for pp in c['pads']if(pp['ref'],str(pp['num']))==('J15002','73'));body=unary_union([LineString([t['a'],t['b']]).buffer(.1,quad_segs=128)for t in tracks]);pc=body.intersection(unary_union(L.poly(cm['layers']['F.Cu']))).area;ac=body.intersection(ann).area;assert pc>0 and ac>0;put('new-prospective-port-all-current-guards-and-owned-track-screen.json',{'via':v,'delta_from_saved_prospective_mm':[0,0],'original_native_pose_change':False,'deficits':bad,'normal_original_plane_operations':normal,'before_actual_J1_annuli_after_separate_CDONE575_cap_mm2':over,'tracks':tb,'finite_CM73_pad_contact_mm2':pc,'finite_return_annulus_contact_mm2':ac,'moved_CDONE_new_via_pitch_mm':p.distance(Point(sig['x'],sig['y']))})
    packet={'via':v,'tracks':tracks,'source_before_both_annuli':over,'original_native_changes':[],'only_prospective_saved_de03_move':False,'original_de03_saved_site_requalified_no_active_native_via_move':True,'R435_R442_R443_dependencies':[str(mp),str(r442),str(p443)],'actual_native_AFTER_SOURCE_masks_oldrefs_current_thermal':'OPEN'}
    if not bad:(OUT/'only-qualified-prospective-de03-source-port-two-owned-tracks.pkl').write_bytes(pickle.dumps(packet,protocol=5))
    put('receipt.json',{'status':'QUALIFIED_ORIGINAL_PROSPECTIVE_DE03_CM73_ON_ALTERNATE_CDONE_LG16'if not bad else'PROSPECTIVE_DE03_SMALL_MOVE_REJECTED_SCOPED','deficit_count':len(bad),'qualified_count':int(not bad),'new_port_count':int(not bad),'new_F20_track_count':len(tracks)if not bad else 0,'original_Cu_hole_FP_pose_zone_definition_changes':0,'saved_de03_was_not_active_native_current_Cu':True,'all_selected_current_new_peers_and_foreign_planes_hard':True,'ordinary_global_pitch815_no_D4':True,'actual_current_NATIVE_after_SOURCE_oldrefs_masks_current_thermal':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R450_COMPLETE',sha(OUT/'receipt.json'),bad,over,flush=True)
if __name__=='__main__':main()
