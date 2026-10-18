"""Fresh combined CM DC graph and independent analytic true-Cu/holes guards."""
import sys,json,pickle,time,math,copy,collections,heapq
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely import STRtree
P=Path(__file__).resolve().parent;H=P.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import search_remaining_CM_actual_source_local_ground_ports_r452 as S
N=S.N;K=S.K;L=S.L;F=S.F;RF=S.RF;sha=S.sha;NET=S.NET;SIG='/fpga_core/FPGA_CDONE';NORMAL=S.NORMAL
OUT=P/'CM51-explicit-terminal-joints-fresh-true-guards-and-SOURCE-before-graph-r458'
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
    started=time.monotonic();assert not OUT.exists();OUT.mkdir();ctx,c,alt,prev,nt,nv=S.assemble();dep=P/'CM51-seven-missing-finite-partial-SOURCE-annulus-local-ground-ports-r453';rr=json.loads((dep/'receipt.json').read_bytes());p453=dep/'only-new-local-real-source-ground-ports-and-F-handoffs.pkl';assert sha(p453)==rr['packet_SHA256'];ex=pickle.loads(p453.read_bytes());nt+=ex['new_tracks'];nv+=ex['new_vias'];c['tracks']+=ex['new_tracks'];c['vias']+=ex['new_vias'];assert len({t['uuid']for t in nt})==len(nt);assert len({v['uuid']for v in nv})==len(nv);repairdir=P/'CM51-explicit-only-NEW-ground-terminal-joints-and-named-R450-path-r457';repairfile=repairdir/'only-NEW-six-terminal-joint-repairs-one-path-ownership.pkl';repair=pickle.loads(repairfile.read_bytes());retired=set(repair['retired_ONLY_NEW_tracks']);assert retired<={t['uuid']for t in nt};nt=[t for t in nt if t['uuid']not in retired]+repair['replacement_ONLY_NEW_tracks'];c['tracks']=[t for t in c['tracks']if t['uuid']not in retired]+repair['replacement_ONLY_NEW_tracks'];moved=alt['moved_original_barrel'];items=nt+nv+[moved];newids={x['uuid']for x in items};native={z['uuid']:z for z in c['zones']};dom=c['domains_normalized'];gap=lambda n,m:.15 if dom.get(L.norm(n))==dom.get(L.norm(m))else .6;rec,trees=F.build(c);checks=[];errors=[];normal=[];terminal=[];holes=[(v['uuid'],L.norm(v['net']),Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128),v)for v in c['vias']]+[(p['uuid'],L.norm(p['net']),sh,p)for p in c['pads']for sh in L.poly(p.get('hole')or[])];ht=STRtree([x[2]for x in holes]);smd=[(p['uuid'],sh)for p in c['pads']if not p.get('hole')for ly in ('F.Cu','B.Cu')for sh in L.poly(p['layers'].get(ly,[]))];st=STRtree([x[1]for x in smd]);vpoints=[Point(v['x'],v['y'])for v in c['vias']];vt=STRtree(vpoints);nativeRules=ctx['all_current_native_rule_areas'];outline=unary_union(L.poly(c['outline'])).buffer(-.626)
    def deficit(kind,item,other,ly,d,req):
        row={'kind':kind,'new_UUID':item['uuid'],'other_UUID':other,'layer':ly,'actual_analytic_gap_mm':d,'guarded_required_mm':req,'physical_requirement_mm':(.275 if kind in {'every_other_physical_drill','new_drill_to_actual_SMD'}else .8 if kind=='ordinary_via_pitch'else req-.025)};checks.append(row)
        if d<req-1e-10:errors.append(row)
    for it in items:
        via='d'in it;n=L.norm(it['net']);ax=Point(it['x'],it['y'])if via else LineString([it['a'],it['b']]);rad=it['d']/2 if via else it['w']/2;body=ax.buffer(rad,quad_segs=128);layers=K.LAYERS if via else[it['layer']]
        for ly in layers:
            for jj in trees[ly].query(body.buffer(.85),predicate='intersects'):
                r=rec[ly][int(jj)];rn=L.norm(r['net'])
                if rn==n or r['uuid']==it['uuid']:continue
                local=float(native[r['uuid']].get('clearance_mm',.15))if r['kind']=='fill'and r['uuid']in native else .15;req=max(gap(n,rn),local)+.025
                if r['kind']=='track':ot=r['source'];d=ax.distance(LineString([ot['a'],ot['b']]))-rad-ot['w']/2
                elif r['kind']=='via':ov=r['source'];d=ax.distance(Point(ov['x'],ov['y']))-rad-ov['d']/2
                else:d=ax.distance(r['shape'])-rad
                if via and r['kind']=='fill'and r['uuid']in NORMAL:
                    if d<req:normal.append({'via_UUID':it['uuid'],'normal_original_plane_UUID':r['uuid'],'layer':ly,'raw_gap_mm':d,'native_local_clearance_mm':local,'native_antipad_operation_pending':True})
                    continue
                deficit('true_foreign_'+r['kind'],it,r['uuid'],ly,d,req)
            for z in ctx['all_current_native_intents']:
                if z['layer']!=ly or L.norm(z['net'])==n or via and z['uuid']in NORMAL:continue
                if z['shape'].distance(ax)>.25+.85:continue
                deficit('held_current_foreign_intent',it,z['uuid'],ly,ax.distance(z['shape'])-rad,max(gap(n,z['net']),z['clearance_mm'])+.025)
        if not outline.covers(body):errors.append({'kind':'board_edge626','new_UUID':it['uuid']})
        for r in nativeRules:
            if not set(layers)&set(r['layers'])or not r['no_vias'if via else'no_tracks']:continue
            if any(body.distance(sh)<.025 for sh in L.poly(N.O.polys(r['outline']))):errors.append({'kind':'native_rule_area','new_UUID':it['uuid'],'other_UUID':r['uuid']})
        for jj in ht.query(body.buffer(.4),predicate='intersects'):
            uid,hn,sh,owner=holes[int(jj)]
            if uid==it['uuid']:continue
            owned=False;cap=None
            if not via and hn==n and'd'in owner and min(Point(xy).distance(Point(owner['x'],owner['y']))for xy in (it['a'],it['b']))<=owner['d']/2+.000002:
                op=Point(owner['x'],owner['y']);ann=op.buffer(owner['d']/2,quad_segs=128).difference(sh);caprad=owner['d']/2+.275;cap=op.buffer(caprad,quad_segs=128);outside=body.difference(cap);d=None if outside.is_empty else outside.distance(sh);owned=body.intersection(ann).area>0 and(d is None or d>=.28-1e-10)
                if owned:terminal.append({'track_UUID':it['uuid'],'exact_owned_terminal_via_UUID':uid,'cap_radius_mm':caprad,'finite_incident_annulus_contact_mm2':body.intersection(ann).area,'outside_cap_drill_gap_mm':d})
            if not owned and not via:
                for ownpath in repair['exact_whole_terminal_path_ownership']:
                    if uid!=ownpath['via_UUID']or it['uuid']not in ownpath['tracks']:continue
                    pathtracks=[t for t in nt if t['uuid']in ownpath['tracks']];assert len(pathtracks)==len(ownpath['tracks']);pathbody=unary_union([LineString([t['a'],t['b']]).buffer(t['w']/2,quad_segs=128)for t in pathtracks]);op=Point(owner['x'],owner['y']);ann=op.buffer(owner['d']/2,quad_segs=128).difference(sh);outside=pathbody.difference(op.buffer(ownpath['owncap_radius_mm'],quad_segs=128));clear=None if outside.is_empty else outside.distance(sh);assert pathbody.intersection(ann).area>0 and(clear is None or clear>=.28);owned=True;terminal.append({'track_UUID':it['uuid'],'exact_owned_terminal_via_UUID':uid,'cap_radius_mm':ownpath['owncap_radius_mm'],'explicit_named_whole_R450_terminal_path':ownpath['tracks'],'finite_whole_path_own_annulus_contact_mm2':pathbody.intersection(ann).area,'outside_cap_whole_path_drill_gap_mm':clear})
            if owned:continue
            d=ax.distance(sh)-(it['drill']/2 if via else rad);deficit('every_other_physical_drill',it,uid,'ALL'if via else it['layer'],d,.28)
        if via:
            for jj in st.query(ax.buffer(.5),predicate='intersects'):
                uid,sh=smd[int(jj)];deficit('new_drill_to_actual_SMD',it,uid,'F/B',ax.distance(sh)-it['drill']/2,.28)
            for jj in vt.query(ax.buffer(.82),predicate='intersects'):
                v=c['vias'][int(jj)]
                if v['uuid']!=it['uuid']:deficit('ordinary_via_pitch',it,v['uuid'],'ALL',ax.distance(vpoints[int(jj)]),.815)
    put('all-new-and-moved-true-analytic-checks.json',checks);put('all-new-and-moved-true-analytic-errors.json',errors);put('exact-own-terminal-only-drill-handoffs.json',terminal);put('normal_original_same_domain_plane-antipad-operations-native-AFTER-open.json',normal);print('R458_ANALYTIC',len(items),len(checks),len(errors),flush=True)
    # Build the entire CM F DC graph anew. SOURCE-before anchors are explicit;
    # no unknown current via mask, fill island, or previous witness is a seed.
    gs,_=N.bound_R663_before_groups({NET});j1=K.root(gs[NET],'J11001','2');roi=box(103,155,140,213);sigcap=Point(moved['x'],moved['y']).buffer(.575,quad_segs=128);planes={ly:unary_union([r['shape']for r in j1 if r['kind']=='fill'and r['layer']==ly]).difference(sigcap)for ly in ('In1.Cu','In4.Cu')};portrows=[];sourceports=set()
    for v in nv:
        p=Point(v['x'],v['y']);ann=p.buffer(v['d']/2,quad_segs=128).difference(p.buffer(v['drill']/2,quad_segs=128));over={ly:ann.intersection(sh).area for ly,sh in planes.items()};row={'UUID':v['uuid'],'xy':[v['x'],v['y']],'actual_BEFORE_J1_source_annuli_mm2':over,'native_actual_current_AFTER_F_In1_In4_masks_SOURCE':'OPEN'};portrows.append(row)
        if min(over.values())>0:sourceports.add(v['uuid'])
    records=[]
    def add(sh,**r):
        local=[holes[int(j)][2]for j in ht.query(sh,predicate='intersects')];physical=sh.difference(unary_union(local))if local else sh
        for part in RF.parts(physical):records.append({**r,'shape':part})
    pads=[p for p in c['pads']if p['ref']in {'J15001','J15002'}and L.norm(p['net'])==NET];assert len(pads)==51
    for p in pads:
        for sh in L.poly(p['layers']['F.Cu']):add(sh,kind='pad',uuid=p['uuid'],ref=p['ref'],pin=p['num'],anchor=False)
    oldTrack={t['uuid']:t for t in ctx['actual_BEFORE_model']['tracks']};curTrack={t['uuid']:t for t in c['tracks']};oldVia={v['uuid']:v for v in ctx['actual_BEFORE_model']['vias']};curVia={v['uuid']:v for v in c['vias']};oldPads={p['uuid']:p for p in ctx['actual_BEFORE_model']['pads']};curPads={p['uuid']:p for p in c['pads']};nativePose=json.loads((H/'combined-R753-one-full-native-fill-cached-DRC-r299/native-full/before-native-all-FP-pad-pose.json').read_bytes());unchangedZ={(z['uuid'],z['layer'])for z in ctx['all_current_native_intents']if z['unchanged_native_definition']}
    for r in j1:
        if r['layer']!='F.Cu'or not r['shape'].intersects(roi):continue
        uid=r['uuid'];kind=r['kind']
        if kind=='track':
            if uid not in curTrack or any(curTrack[uid].get(k)!=oldTrack[uid].get(k)for k in ('net','layer','w','a','b','m')):continue
        elif kind=='via':
            if uid not in curVia or any(curVia[uid].get(k)!=oldVia[uid].get(k)for k in ('net','x','y','d','drill','flashed')):continue
        elif kind=='pad':
            if uid not in curPads or uid not in nativePose['pads']:continue
            p=curPads[uid];q=nativePose['pads'][uid]
            if(p['x'],p['y'],p['net'])!=(q[2]/1e6,q[3]/1e6,q[1])or p['layers']!=oldPads[uid]['layers']:continue
        elif kind=='fill':
            if(uid,'F.Cu')not in unchangedZ:continue
        else:continue
        add(r['shape'],**{k:v for k,v in r.items()if k!='shape'},anchor=True,role='exact_retained_actual_BEFORE_J1_SOURCE_F_terminal')
    for t in c['tracks']:
        if t['layer']=='F.Cu'and L.norm(t['net'])==NET:
            sh=LineString([t['a'],t['b']]).buffer(t['w']/2,quad_segs=128)
            if sh.intersects(roi):add(sh,kind='track',uuid=t['uuid'],anchor=False,new=t['uuid']in newids)
    for v in nv:
        p=Point(v['x'],v['y']);add(p.buffer(v['d']/2,quad_segs=128),kind='via',uuid=v['uuid'],anchor=v['uuid']in sourceports,role='prospective_finite_actual_J1_SOURCE_before_both_annuli_native_AFTER_OPEN')
    tree=STRtree([r['shape']for r in records]);adj=[set()for r in records]
    for i,r in enumerate(records):
        for jj in tree.query(r['shape'].buffer(.000002),predicate='intersects'):
            j=int(jj)
            if i<j and r['shape'].distance(records[j]['shape'])<=.000002:adj[i].add(j);adj[j].add(i)
    sources=[i for i,r in enumerate(records)if r['anchor']];parent={};reached=set(sources);queue=collections.deque(sources)
    while queue:
        i=queue.popleft()
        for j in adj[i]:
            if j not in reached:reached.add(j);parent[j]=i;queue.append(j)
    connected=[];missing=[]
    for p in pads:
        starts=[i for i,r in enumerate(records)if r['kind']=='pad'and r['uuid']==p['uuid']and i in reached]
        if not starts:missing.append({'UUID':p['uuid'],'ref':p['ref'],'pin':p['num']});continue
        i=starts[0];chain=[i]
        while not records[i]['anchor']:i=parent[i];chain.append(i)
        connected.append({'UUID':p['uuid'],'ref':p['ref'],'pin':p['num'],'fresh_finite_source_before_witness':[{k:records[i][k]for k in ('kind','uuid','ref','pin','role')if k in records[i]}for i in chain],'actual_current_SOURCE':'OPEN'})
    put('fresh-all51-joint-finite-source-before-connectivity.json',{'connected':connected,'unconnected':missing,'source_port_annuli':portrows,'records':len(records),'source_seeds':len(sources),'full_native_after_SOURCE':'OPEN'});pkt={'only_new_tracks':nt,'only_new_vias':nv,'only_original_pose_change':moved,'retired_only_prospective_tracks':['65f3a90e-a953-5caa-8493-4623cfc05f2f']+sorted(retired),'R457_controlled_terminal_packet_SHA256':sha(repairfile),'raw_R454_drill_deficits_preserved':True,'never_replay_R435_or_all49':True,'connected_SOURCE_before':connected,'unconnected':missing,'analytic_errors':errors,'native_after_oldgroups_oldrefs_current_thermal':'OPEN'};(OUT/'joint-reviewed-CM-sparse-packet-NOT-native-authority.pkl').write_bytes(pickle.dumps(pkt,protocol=5));put('receipt.json',{'status':'FRESH_JOINT_CM_DIAGNOSTIC_PASS'if not errors and not missing else'FRESH_JOINT_CM_DIAGNOSTIC_HOLD','new_track_count':len(nt),'new_ground_via_count':len(nv),'original_barrel_moves':1,'analytic_check_count':len(checks),'analytic_deficit_count':len(errors),'finite_SOURCE_before_connected_CM_pads':len(connected),'unconnected':missing,'actual_current_AFTER_SOURCE_oldgroups_oldrefs_masks_current_thermal':'OPEN','packet_SHA256':sha(OUT/'joint-reviewed-CM-sparse-packet-NOT-native-authority.pkl'),'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R458_COMPLETE',sha(OUT/'receipt.json'),len(errors),len(connected),len(missing),flush=True)
if __name__=='__main__':main()
