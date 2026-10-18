"""Saved candidates only: exact active Cu/intents plus minimal CDONE patch.

No foreign owned plane outline carve, shadow waiver, or native SOURCE credit.
Every saved candidate/new peer is explicit; reject before constructive repair.
"""
import sys,json,pickle,time,math,copy,collections
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely import STRtree
P=Path(__file__).resolve().parent;H=P.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
import fast_contacts as F
K=N.K;L=N.L;sha=N.sha;NET='/LOGIC_GND'
OUT=P/'CM49-saved-candidates-exact-current-retained-CORE-minimal-CDONE-screen-r440'
ORIGINAL_NORMAL_PLANE_UIDS={'58c55cd5-98e6-4467-88e3-146ceeee361a','c1d27fa1-452b-4e27-985d-5ad23644d800','54921f4b-0308-4821-9549-ff9360bf05ca'}
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
    started=time.monotonic();assert not OUT.exists();OUT.mkdir();prev=P/'CM79-R300-all-native-intents-and-local-unchanged-definition-binding-r431';rr=json.loads((prev/'receipt.json').read_bytes());pf=prev/'only-active-current-Cu-native-poses-all-native-intents-BEFORE-fill-context.pkl';assert sha(pf)==rr['packet_SHA256'];context=pickle.loads(pf.read_bytes());c=copy.deepcopy(context['current_Cu_and_local_native_pads']);d=P/'CM79-CDONE-one-move-five-tracks-one-LG-native-sparse-patch-r435';dr=json.loads((d/'receipt.json').read_bytes());mp=d/'only-one-original-via-move-five-tracks-one-ground-via-no-zones.pkl';assert sha(mp)==dr['patch_packet_SHA256'];minimal=pickle.loads(mp.read_bytes());c['vias']=[minimal['moved_original_via']if v['uuid']==minimal['moved_original_via']['uuid']else v for v in c['vias']]+minimal['only_new_vias'];c['tracks']+=minimal['only_new_tracks'];candidateFile=P/'CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289/only-new-CM-ordinary-discrete-no-deletes.pkl';assert sha(candidateFile)=='72321f8b75794e2cf2bd5d4ba6788da7bbdb8eaa4ba692cf9a121d4c3bde3207';saved=pickle.loads(candidateFile.read_bytes());assert len(saved['tracks'])==115 and len(saved['vias'])==34;nom=json.loads((P/'CM51-final-two-real-positive-cap-land-edge-nominations-r281/receipt.json').read_bytes());assert len(nom['accepted'])==49;allq=context['all_current_native_intents'];rules=[{**r,'outline':N.O.polys(r['outline'])}for r in context['all_current_native_rule_areas']];domain=c['domains_normalized'];gap=lambda n:.15 if domain.get(L.norm(n))==domain.get(NET)else .6;rec,trees=F.build(c);q={ly:[z for z in allq if z['layer']==ly and L.norm(z['net'])!=NET and z['uuid']not in ORIGINAL_NORMAL_PLANE_UIDS]for ly in K.LAYERS};nativeZones={z['uuid']:z for z in c['zones']};holes=[(v['uuid'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in c['vias']]+[(p['uuid'],sh)for p in c['pads']for sh in L.poly(p.get('hole')or[])];ht=STRtree([sh for u,sh in holes]);smds=[(p['uuid'],sh)for p in c['pads']if not p.get('hole')for ly in ('F.Cu','B.Cu')for sh in L.poly(p['layers'].get(ly,[]))];st=STRtree([sh for u,sh in smds]);vs=[Point(v['x'],v['y'])for v in c['vias']];vt=STRtree(vs);gs,_=N.bound_R663_before_groups({NET});source=K.root(gs[NET],'J11001','2');sourceKeys=K.keys(source);planes={ly:unary_union([r['shape']for r in source if r['kind']=='fill'and r['layer']==ly])for ly in ('In1.Cu','In4.Cu')};reserve,exempt=K.A.reservations();nativePose=json.loads((H/'combined-R753-one-full-native-fill-cached-DRC-r299/native-full/before-native-all-FP-pad-pose.json').read_bytes());iv0=K.A.C.inventory((N.R157/'copy/board.kicad_pcb').read_bytes());iv1=K.A.C.inventory(Path(context['active_board']).read_bytes());fpids=[u for u,r in nativePose['footprints'].items()if r[0]in {'J15001','J15002'}];assert len(fpids)==2 and all(iv0[3][u]==iv1[3][u]for u in fpids),'CM native footprints/padstacks/poses changed';pads=[p for p in c['pads']if p['ref']in {'J15001','J15002'}and L.norm(p['net'])==NET];assert len(pads)==51;necessary=[p for p in pads if not any(('pad',p['uuid'],ly)in sourceKeys for ly in p['layers'])];put('all51-CM-actual-BEFORE-source-necessity.json',[{'UUID':p['uuid'],'ref':p['ref'],'pin':p['num'],'already_actual_BEFORE_J1_SOURCE':p not in necessary,'current_native_SOURCE':'OPEN'}for p in pads]);ids={v['uuid']for v in c['vias']};peerV=[v for v in saved['vias']if v['uuid']not in ids];peerRows=[];viapass=[]
    def allowed_normal(r):return r['kind']=='fill'and r['uuid']in ORIGINAL_NORMAL_PLANE_UIDS and domain.get(L.norm(r['net']))==domain.get(NET)
    for v in saved['vias']:
        if v['uuid']in ids:continue
        p=Point(v['x'],v['y']);ann=p.buffer(.25,quad_segs=128).difference(p.buffer(.1,quad_segs=128));bad=[];normal=[]
        for ly in K.LAYERS:
            for j in trees[ly].query(p.buffer(1.2),predicate='intersects'):
                r=rec[ly][int(j)];n=L.norm(r['net'])
                if n==NET:continue
                local=float(nativeZones[r['uuid']].get('clearance_mm',.15))if r['kind']=='fill'and r['uuid']in nativeZones else .15;req=max(local,gap(n))+.025
                if allowed_normal(r):
                    if p.distance(r['shape'])-.25<req:normal.append({'UUID':r['uuid'],'layer':ly,'actual_native_normal_same_domain_antipad_radius_mm':.25+local})
                    continue
                if p.distance(r['shape'])-.25<req:bad.append({'kind':'actual_current_foreign_Cu','UUID':r['uuid'],'layer':ly,'net':r['net']})
            for z in q[ly]:
                if p.distance(z['shape'])-.25<max(gap(z['net']),z['clearance_mm'])+.025:bad.append({'kind':'held_foreign_current_native_intent','UUID':z['uuid'],'layer':ly,'net':z['net']})
        for j in ht.query(p.buffer(.6),predicate='intersects'):
            u,sh=holes[int(j)]
            if p.distance(sh)-.1<.28:bad.append({'kind':'current_other_drill','UUID':u})
        for j in st.query(p.buffer(.4),predicate='intersects'):
            u,sh=smds[int(j)]
            if p.distance(sh)-.1<.28:bad.append({'kind':'current_SMD_drill','UUID':u})
        for j in vt.query(p.buffer(.82),predicate='intersects'):
            u=c['vias'][int(j)]['uuid']
            if p.distance(vs[int(j)])<.815:bad.append({'kind':'current_minimal_new_peer_via_pitch','UUID':u,'distance_mm':p.distance(vs[int(j)])})
        for other in peerV:
            if other['uuid']!=v['uuid']and math.dist([v['x'],v['y']],[other['x'],other['y']])<.815:bad.append({'kind':'prospective_saved_new_peer_via_pitch','UUID':other['uuid']})
        for rule in rules:
            if rule['no_vias']and any(p.distance(sh)<.275 for sh in L.poly(rule['outline'])):bad.append({'kind':'actual_native_no_via','UUID':rule['uuid']})
        overlaps={ly:ann.intersection(planes[ly]).area for ly in planes}
        if not all(x>0 for x in overlaps.values()):bad.append({'kind':'no_actual_BEFORE_J1_SOURCE_annulus_both_planes','overlap_mm2':overlaps})
        row={'via_UUID':v['uuid'],'at_mm':[v['x'],v['y']],'deficits':bad,'normal_native_original_plane_operations':normal,'before_actual_J1_annuli_mm2':overlaps,'all_foreign_Cu_planes_original_intents_held':True};peerRows.append(row)
        if not bad:viapass.append(v)
    put('all34-saved-ordinary-via-exact-current-peer-and-source-before-screen.json',peerRows);trackrows=[]
    for t in saved['tracks']:
        axis=LineString([t['a'],t['b']]);body=axis.buffer(.1,quad_segs=128);bad=[]
        for j in trees[t['layer']].query(body.buffer(.7),predicate='intersects'):
            r=rec[t['layer']][int(j)];n=L.norm(r['net'])
            if n==NET:continue
            if allowed_normal(r):continue
            req=max(gap(n),float(nativeZones[r['uuid']].get('clearance_mm',.15))if r['kind']=='fill'and r['uuid']in nativeZones else .15)+.025
            if body.distance(r['shape'])<req:bad.append({'kind':'actual_current_foreign_Cu','UUID':r['uuid'],'net':r['net']})
        for z in q[t['layer']]:
            if body.distance(z['shape'])<max(gap(z['net']),z['clearance_mm'])+.025:bad.append({'kind':'held_foreign_current_native_intent','UUID':z['uuid'],'net':z['net']})
        for j in ht.query(body.buffer(.3),predicate='intersects'):
            u,sh=holes[int(j)]
            if body.distance(sh)<.28:bad.append({'kind':'current_or_minimal_peer_drill','UUID':u})
        for v in peerV:
            if body.distance(Point(v['x'],v['y']).buffer(.1,quad_segs=128))<.28:
                # Own LG transport touching its own ordinary barrel is a real
                # drilled conductor, not a foreign drill-clearance conflict.
                if body.intersects(Point(v['x'],v['y']).buffer(.25,quad_segs=128)):continue
                bad.append({'kind':'prospective_saved_ground_peer_drill','UUID':v['uuid']})
        for rule in rules:
            if t['layer']in rule['layers']and rule['no_tracks']and any(body.intersects(sh)for sh in L.poly(rule['outline'])):bad.append({'kind':'actual_native_no_track','UUID':rule['uuid']})
        trackrows.append({'track_UUID':t['uuid'],'a':t['a'],'b':t['b'],'deficits':bad,'raw_SOURCE_before_shadow_gap_mm2':body.difference(planes['In1.Cu']).area,'DC_ground_finite_SOURCE_handoff_required_not_fast_SIGNAL_shadow':True})
    put('all115-saved-ground-F-track-exact-current-guards-raw-shadow.json',trackrows)
    put('receipt.json',{'status':'SAVED49_PAD_CANDIDATES_ONLY_CURRENT_REQUAL_NO_ADOPTION','R435_minimal_patch_receipt_SHA256':sha(d/'receipt.json'),'R431_current_all_native_intent_binding_SHA256':sha(prev/'receipt.json'),'saved_discrete_SHA256':sha(candidateFile),'saved_ground_pad_candidate_count':49,'saved_tracks_vias':[115,34],'CM51_before_SOURCE_necessary_count':len(necessary),'already_minimal_ground_return_count':len(saved['vias'])-len(peerV),'remaining_saved_via_candidates_checked':len(peerRows),'remaining_saved_via_zero_deficit_count':len(viapass),'saved_track_zero_deficit_count':sum(not r['deficits']for r in trackrows),'foreign_owned_plane_outline_carves':0,'all_saved_new_peer_Cu_holes_and_minimal_CDONE_guarded':True,'SOURCE_nativeAfter_alloldrefs_current_thermal':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R440_COMPLETE',sha(OUT/'receipt.json'),len(necessary),len(viapass),sum(not r['deficits']for r in trackrows),flush=True)
if __name__=='__main__':main()
