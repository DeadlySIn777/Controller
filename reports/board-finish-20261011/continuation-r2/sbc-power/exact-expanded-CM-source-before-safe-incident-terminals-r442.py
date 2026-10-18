"""Select finite actual-SOURCE-before handoffs from saved passing candidates.

No current full-fill equivalence or native-after mask assertion. Every source
terminal is an exact retained SOURCE-before F record or a named prospective
ground barrel with finite J1-rooted native annuli on both reference planes.
"""
import sys,json,pickle,time,math,copy,collections,heapq
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely import STRtree
P=Path(__file__).resolve().parent;H=P.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
import physical_reference_losses_r3_zero_r208 as RF
K=N.K;L=N.L;sha=N.sha;NET='/LOGIC_GND'
OUT=P/'CM51-pruned-real-source-before-safe-subset-incident-terminal-handoffs-r442'
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
    started=time.monotonic();assert not OUT.exists();OUT.mkdir();screen=P/'CM49-saved-candidates-exact-current-retained-CORE-minimal-CDONE-screen-r440';assert sha(screen/'receipt.json')=='019f0fadb93b87b57a6ae4ab065e92bbe8ec37201d9f357c24f7a281de1455fd';vr=json.loads((screen/'all34-saved-ordinary-via-exact-current-peer-and-source-before-screen.json').read_bytes());tr=json.loads((screen/'all115-saved-ground-F-track-exact-current-guards-raw-shadow.json').read_bytes());prev=P/'CM79-R300-all-native-intents-and-local-unchanged-definition-binding-r431';rr=json.loads((prev/'receipt.json').read_bytes());pf=prev/'only-active-current-Cu-native-poses-all-native-intents-BEFORE-fill-context.pkl';assert sha(pf)==rr['packet_SHA256'];context=pickle.loads(pf.read_bytes());c=copy.deepcopy(context['current_Cu_and_local_native_pads']);mp=P/'CM79-CDONE-one-move-five-tracks-one-LG-native-sparse-patch-r435/only-one-original-via-move-five-tracks-one-ground-via-no-zones.pkl';assert sha(mp)=='458f3078eb3a48d850574d1977c7ef373400f7e82c5dfb9b9cab6f5053cf03c4';minimal=pickle.loads(mp.read_bytes());c['vias']=[minimal['moved_original_via']if v['uuid']==minimal['moved_original_via']['uuid']else v for v in c['vias']]+minimal['only_new_vias'];c['tracks']+=minimal['only_new_tracks'];sf=P/'CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289/only-new-CM-ordinary-discrete-no-deletes.pkl';assert sha(sf)=='72321f8b75794e2cf2bd5d4ba6788da7bbdb8eaa4ba692cf9a121d4c3bde3207';saved=pickle.loads(sf.read_bytes());vdict={v['uuid']:v for v in saved['vias']};r441=P/'CM51-actual-source-before-finite-safe-subset-owned-terminal-handoffs-r441';p441=r441/'only-source-before-connected-safe-CM-subset-no-old-edits.pkl';assert sha(p441)=='f88507f06651daeeaa5ca904b4cd04f0c710cea427d59a599588f3b75c0331ab';prior=pickle.loads(p441.read_bytes());passV={v['uuid']for v in prior['vias']};assert passV<={r['via_UUID']for r in vr if not r['deficits']};prospective=[vdict[u]for u in sorted(passV)];portmap={v['uuid']:v for v in prospective+minimal['only_new_vias']};rows=[];tracks=[]
    for t,r in zip(saved['tracks'],tr):
        assert t['uuid']==r['track_UUID'];body=LineString([t['a'],t['b']]).buffer(.1,quad_segs=128);bad=[];owned=[];withdrawn=[]
        for e in r['deficits']:
            uid=e.get('UUID');kind=e['kind']
            if kind=='prospective_saved_ground_peer_drill'and uid not in passV:withdrawn.append(e);continue
            if kind in {'prospective_saved_ground_peer_drill','current_or_minimal_peer_drill'}and uid in portmap:
                v=portmap[uid];p=Point(v['x'],v['y']);ann=p.buffer(.25,quad_segs=128).difference(p.buffer(.1,quad_segs=128));ends=[j for j,xy in enumerate((t['a'],t['b']))if Point(*xy).distance(p)<=.25 and body.intersection(ann).area>0]
                if ends:
                    owncap=p.buffer(.525,quad_segs=128);outside=body.difference(owncap);assert outside.is_empty or outside.distance(p.buffer(.1,quad_segs=128))>=.28;owned.append({'via_UUID':uid,'endpoint_indices':ends,'finite_incident_track_annulus_contact_mm2':body.intersection(ann).area,'endpoint_centres_within_exact_own_barrel_Cu':True,'own_named_terminal_only_cap_radius_mm':.525,'outside_owncap_physical_drill_clearance_mm':None if outside.is_empty else outside.distance(p.buffer(.1,quad_segs=128)),'SOURCE_before_both_annuli':True,'native_AFTER_F_In1_In4_masks_SOURCE':'OPEN'});continue
            bad.append(e)
        rows.append({'UUID':t['uuid'],'deficits':bad,'removed_peer_not_in_this_subset':withdrawn,'only_exact_own_terminal_handoff':owned,'raw_R440_results_retained':True})
        if not bad:tracks.append(t)
    put('saved-F-track-selected-peer-and-owned-ordinary-terminal-delta.json',rows)
    gs,_=N.bound_R663_before_groups({NET});j1=K.root(gs[NET],'J11001','2');roi=box(105,155,139,212);pose=json.loads((H/'combined-R753-one-full-native-fill-cached-DRC-r299/native-full/before-native-all-FP-pad-pose.json').read_bytes());iv0=K.A.C.inventory((N.R157/'copy/board.kicad_pcb').read_bytes());iv1=K.A.C.inventory(Path(context['active_board']).read_bytes());anchors=[]
    for r in j1:
        if r['layer']!='F.Cu'or not r['shape'].intersects(roi):continue
        if r['kind']in {'track','via'}:
            if r['uuid']not in iv1[3]or iv1[3][r['uuid']]!=iv0[3][r['uuid']]:continue
        elif r['kind']=='pad':
            p=next(p for p in c['pads']if p['uuid']==r['uuid']);q=pose['pads'][p['uuid']]
            if(p['x'],p['y'],p['net'])!=(q[2]/1e6,q[3]/1e6,q[1]):continue
        elif r['kind']!='fill':continue
        anchors.append({**r,'role':'retained_actual_BEFORE_J1_SOURCE_F_terminal','anchor':True})
    allholes=[Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)for v in c['vias']+prospective]+[s for p in c['pads']for s in L.poly(p.get('hole')or[])];ht=STRtree(allholes);records=[]
    def add(shape,**r):
        local=[allholes[int(j)]for j in ht.query(shape,predicate='intersects')];physical=shape.difference(unary_union(local))if local else shape
        for part in RF.parts(physical):records.append({**r,'shape':part})
    pads=[p for p in c['pads']if p['ref']in {'J15001','J15002'}and L.norm(p['net'])==NET];assert len(pads)==51
    for p in pads:
        for sh in L.poly(p['layers']['F.Cu']):add(sh,kind='pad',uuid=p['uuid'],ref=p['ref'],pin=p['num'],anchor=False)
    for t in tracks+[t for t in minimal['only_new_tracks']if L.norm(t['net'])==NET]:add(LineString([t['a'],t['b']]).buffer(.1,quad_segs=128),kind='track',uuid=t['uuid'],anchor=False,new=True)
    for v in prospective+minimal['only_new_vias']:
        p=Point(v['x'],v['y']);ann=p.buffer(.25,quad_segs=128).difference(p.buffer(.1,quad_segs=128));add(ann,kind='via',uuid=v['uuid'],anchor=True,role='prospective_named_finite_J1_SOURCE_before_In1_In4_handoff_native_AFTER_OPEN')
    for r in anchors:add(r['shape'],**{k:v for k,v in r.items()if k!='shape'})
    # Retained current F ground transport may join two declared SOURCE-before
    # terminals; credit does not extend to unknown native-new via masks.
    existingAdded=set()
    for t in c['tracks']:
        if t['layer']!='F.Cu'or L.norm(t['net'])!=NET or t['uuid']in {x['uuid']for x in minimal['only_new_tracks']}:continue
        sh=LineString([t['a'],t['b']]).buffer(t['w']/2,quad_segs=128)
        if sh.intersects(roi):add(sh,kind='track',uuid=t['uuid'],anchor=False,new=False);existingAdded.add(t['uuid'])
    tree=STRtree([r['shape']for r in records]);adj=[set()for r in records]
    for i,r in enumerate(records):
        for jj in tree.query(r['shape'].buffer(.000002),predicate='intersects'):
            j=int(jj)
            if i<j and r['shape'].distance(records[j]['shape'])<=.000002:adj[i].add(j);adj[j].add(i)
    sources=[i for i,r in enumerate(records)if r['anchor']];dist={i:0 for i in sources};parent={};heap=[(0,i)for i in sources];heapq.heapify(heap)
    while heap:
        d,i=heapq.heappop(heap)
        if d!=dist[i]:continue
        for j in adj[i]:
            r=records[j];cost=0 if not r.get('new')else next((math.dist(t['a'],t['b'])for t in tracks if t['uuid']==r['uuid']),0);nd=d+cost+.000000001
            if nd<dist.get(j,float('inf')):dist[j]=nd;parent[j]=i;heapq.heappush(heap,(nd,j))
    witnesses=[];selectedT=set();selectedV=set();unconnected=[]
    for p in pads:
        starts=[i for i,r in enumerate(records)if r['kind']=='pad'and r['uuid']==p['uuid']and i in dist]
        if not starts:unconnected.append({'UUID':p['uuid'],'ref':p['ref'],'pin':p['num'],'at':[p['x'],p['y']]});continue
        i=min(starts,key=lambda i:dist[i]);chain=[i]
        while not records[i]['anchor']:i=parent[i];chain.append(i)
        path=[{k:r[k]for k in ('kind','uuid','ref','pin','role')if k in r}for r in (records[i]for i in chain)];selectedT|={records[i]['uuid']for i in chain if records[i]['kind']=='track'and records[i].get('new')};selectedV|={records[i]['uuid']for i in chain if records[i]['kind']=='via'and records[i]['uuid']in passV};witnesses.append({'UUID':p['uuid'],'ref':p['ref'],'pin':p['num'],'finite_actual_source_BEFORE_handoff_witness':path,'current_native_after_SOURCE':'OPEN'})
    nt=[t for t in tracks if t['uuid']in selectedT];nv=[v for v in prospective if v['uuid']in selectedV];selected={'tracks':nt,'vias':nv,'R435_minimal_patch_dependency':str(mp.resolve()),'R435_minimal_patch_SHA256':sha(mp),'source_before_witnesses':witnesses,'unconnected_pads':unconnected,'withdrawn_originals_or_native_zone_FP_pose_edits':[],'actual_current_native_AFTER_SOURCE_alloldrefs_current_thermal':'OPEN'};(OUT/'only-source-before-connected-safe-CM-subset-no-old-edits.pkl').write_bytes(pickle.dumps(selected,protocol=5));put('all51-CM-finite-source-before-selected-handoffs.json',{'connected':witnesses,'unconnected':unconnected});put('receipt.json',{'status':'FINITE_SOURCE_BEFORE_SAFE_SUBSET_NO_NATIVE_CURRENT_SOURCE_CREDIT','R440_receipt_SHA256':sha(screen/'receipt.json'),'R441_raw_no_annulus_contact_in_endpoint_disc_result':'RETAINED; endpoint disc of radius .1 lies inside own .1 drill, while incident .2 track tail has positive true annulus contact','R441_initial_subset_SHA256':sha(p441),'withdrawn_unused_prospective_ground_port_count':22-len(prospective),'R435_minimal_dependency_SHA256':sha(mp),'safe_track_count_after_exact_peer_terminal_attribution':len(tracks),'initial_new_ordinary_SOURCE_before_port_count':len(prospective),'selected_new_track_count':len(nt),'selected_new_ordinary_port_count':len(nv),'CM51_source_before_finite_connected_pad_count':len(witnesses),'CM51_unconnected_pad_count':len(unconnected),'own_terminal_delta_rows':sum(bool(r['only_exact_own_terminal_handoff'])for r in rows),'retained_actual_SOURCE_before_F_anchor_count':len(anchors),'selected_packet_SHA256':sha(OUT/'only-source-before-connected-safe-CM-subset-no-old-edits.pkl'),'foreign_plane_Cu_outline_carves':0,'whole_current_model_overlays':0,'exact_native_all_after_SOURCE_body_oldrefs_masks_current_thermal':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R442_COMPLETE',sha(OUT/'receipt.json'),len(witnesses),len(unconnected),len(nt),len(nv),unconnected,flush=True)
if __name__=='__main__':main()
