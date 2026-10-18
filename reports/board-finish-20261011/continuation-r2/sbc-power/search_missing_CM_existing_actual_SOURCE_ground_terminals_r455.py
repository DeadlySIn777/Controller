"""Named existing SOURCE-barrel terminals; no new holes or borrowed caps."""
import sys,json,pickle,time,math,copy,uuid
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
P=Path(__file__).resolve().parent;H=P.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import search_remaining_CM_actual_source_local_ground_ports_r452 as S
N=S.N;K=S.K;L=S.L;F=S.F;RF=S.RF;TR=S.TR;sha=S.sha;NET=S.NET
OUT=P/'CM51-missing-seven-named-existing-actual-SOURCE-F-ground-terminal-search-r455'
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
    started=time.monotonic();assert not OUT.exists();OUT.mkdir();ctx,c,alt,prev,nt,nv=S.assemble();region=box(102,154,143,181);roi=region.buffer(2);dom=c['domains_normalized'];gap=lambda n:.15 if dom.get(L.norm(n))==dom.get(NET)else .6;rec,trees=F.build(c,layers={'F.Cu'});native={z['uuid']:z for z in c['zones']};cuts=[]
    for jj in trees['F.Cu'].query(roi,predicate='intersects'):
        r=rec['F.Cu'][int(jj)];n=L.norm(r['net'])
        if n==NET:continue
        req=max(gap(n),float(native[r['uuid']].get('clearance_mm',.15))if r['kind']=='fill'and r['uuid']in native else .15)+.026;cuts.append(r['shape'].buffer(.1+req,quad_segs=128))
    for z in ctx['all_current_native_intents']:
        if z['layer']=='F.Cu'and L.norm(z['net'])!=NET and z['shape'].intersects(roi):cuts.append(z['shape'].buffer(.1+max(gap(z['net']),z['clearance_mm'])+.026,quad_segs=128))
    for r in ctx['all_current_native_rule_areas']:
        if r['no_tracks']and'F.Cu'in r['layers']:cuts.extend(sh.buffer(.126,quad_segs=128)for sh in L.poly(N.O.polys(r['outline']))if sh.intersects(roi))
    fixed=region.intersection(unary_union(L.poly(c['outline'])).buffer(-.626)).difference(unary_union(cuts));holes=[(v['uuid'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in c['vias']]+[(p['uuid'],sh)for p in c['pads']for sh in L.poly(p.get('hole')or[])];holes=[(u,sh)for u,sh in holes if sh.intersects(roi)];gs,_=N.bound_R663_before_groups({NET});root=K.root(gs[NET],'J11001','2');rootkeys=K.keys(root);before={v['uuid']:v for v in ctx['actual_BEFORE_model']['vias']};ports=[]
    for v in c['vias']:
        u=v['uuid']
        if L.norm(v['net'])!=NET or u not in before or('via',u,'F.Cu')not in rootkeys:continue
        if any(v.get(k)!=before[u].get(k)for k in ('net','x','y','d','drill','flashed')):continue
        if any(math.dist([v['x'],v['y']],next(p for p in c['pads']if p['uuid']==i['pad_UUID'])['xy']if False else[next(p for p in c['pads']if p['uuid']==i['pad_UUID'])[k]for k in ('x','y')])<=8 for i in prev['still_unconnected']):ports.append(v)
    cases={};rows=[];newtracks=[];routes=[]
    for info in prev['still_unconnected']:
        p=next(p for p in c['pads']if p['uuid']==info['pad_UUID']);start=Point(p['x'],p['y']);row={'pad_UUID':p['uuid'],'ref':p['ref'],'pin':p['num'],'eligible_existing_actual_SOURCE_ports':[],'route':None};accepted=[]
        for v in sorted(ports,key=lambda v:math.dist([p['x'],p['y']],[v['x'],v['y']])):
            if start.distance(Point(v['x'],v['y']))>8:continue
            if v['uuid']not in cases:
                space=fixed.difference(unary_union([sh.buffer(.381,quad_segs=128)for u,sh in holes if u!=v['uuid']]));cases[v['uuid']]=(space,RF.parts(space))
            space,faces=cases[v['uuid']];end=Point(v['x'],v['y']);face=next((sh for sh in faces if sh.covers(start)and sh.covers(end)),None);trial={'via_UUID':v['uuid'],'xy':[v['x'],v['y']],'diameter_drill':[v['d'],v['drill']],'same_full20_F_component_with_ONLY_own_drill_guard_removed':face is not None,'actual_BEFORE_J1_SOURCE_F_key':True};row['eligible_existing_actual_SOURCE_ports'].append(trial)
            if face is None:continue
            path,method=TR.route(face,[p['x'],p['y']],[v['x'],v['y']]);path=[[round(x,6),round(y,6)]for x,y in path];axis=LineString(path);body=axis.buffer(.1,quad_segs=128);ann=end.buffer(v['d']/2,quad_segs=128).difference(end.buffer(v['drill']/2,quad_segs=128));caprad=v['d']/2+.275;outside=body.difference(end.buffer(caprad,quad_segs=128));clear=None if outside.is_empty else outside.distance(end.buffer(v['drill']/2,quad_segs=128));pc=body.intersection(unary_union(L.poly(p['layers']['F.Cu']))).area;ac=body.intersection(ann).area
            if axis.length>15 or not face.covers(axis)or pc<=0 or ac<=0 or(clear is not None and clear<.28):continue
            accepted.append((axis.length,v,path,method,pc,ac,clear,caprad))
            if axis.length<3:break
        if accepted:
            length,v,path,method,pc,ac,clear,caprad=min(accepted,key=lambda x:x[0]);ts=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM-R455-own-existing-ground:'+p['uuid']+':'+str(i))),'net':NET,'layer':'F.Cu','w':.2,'a':a,'b':b}for i,(a,b)in enumerate(zip(path,path[1:]))];newtracks+=ts;row.update(route=path,tracks=ts,only_named_existing_SOURCE_terminal_UUID=v['uuid'],length_mm=length,finite_pad_contact_mm2=pc,finite_existing_annulus_contact_mm2=ac,exact_owncap_radius_mm=caprad,outside_owncap_drill_gap_mm=clear,method=method);routes.append(row);print('R455_ROUTE',p['ref'],p['num'],length,v['uuid'],flush=True)
        rows.append(row);put('all-seven-existing-source-terminal-attempts.json',rows)
    # Attribute every raw R454 drill deficit without converting it to a pass.
    d=P/'CM51-fresh-joint-alternate-ground-analytic-guards-and-finite-SOURCE-before-graph-r454';errs=json.loads((d/'all-new-and-moved-true-analytic-errors.json').read_bytes());bindings=[]
    for e in errs:
        t=next(t for t in nt if t['uuid']==e['new_UUID']);owner=next((v for v in c['vias']if v['uuid']==e['other_UUID']),None);pad=next((p for p in c['pads']if p['uuid']==e['other_UUID']),None);bindings.append({'raw_error':e,'new_track':t,'hole_owner_via':owner,'hole_owner_pad':{k:pad[k]for k in ('uuid','ref','num','net','x','y')}if pad else None,'same_net':L.norm((owner or pad)['net'])==L.norm(t['net']),'nearest_endpoint_distance_to_hole_axis_mm':min(math.dist(a,[owner['x'],owner['y']])for a in (t['a'],t['b']))if owner else None})
    put('seven-raw-joint-drill-deficits-exact-ownership-binding.json',bindings);pkt={'new_tracks':newtracks,'new_vias':[],'routes':routes,'still_unconnected':[{'pad_UUID':r['pad_UUID'],'ref':r['ref'],'pin':r['pin']}for r in rows if r['route']is None],'actual_current_native_AFTER_SOURCE_oldrefs_current_thermal':'OPEN'};(OUT/'only-new-existing-real-SOURCE-terminal-F-handoffs.pkl').write_bytes(pickle.dumps(pkt,protocol=5));put('receipt.json',{'status':'BOUNDED_NAMED_EXISTING_SOURCE_TERMINAL_SEARCH','existing_actual_SOURCE_F_barrels_screened':len(ports),'qualified_routes':len(routes),'new_tracks':len(newtracks),'still_unconnected':pkt['still_unconnected'],'newholes':0,'original_Cu_edits':0,'raw_R454_deficits_preserved':len(bindings),'packet_SHA256':sha(OUT/'only-new-existing-real-SOURCE-terminal-F-handoffs.pkl'),'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R455_COMPLETE',sha(OUT/'receipt.json'),len(routes),len(ports),flush=True)
if __name__=='__main__':main()
