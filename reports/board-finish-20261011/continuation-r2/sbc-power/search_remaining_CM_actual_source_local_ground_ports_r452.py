"""Seven missing CM grounds: bounded genuine SOURCE-before local ports."""
import sys,json,pickle,time,math,copy,uuid
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
P=Path(__file__).resolve().parent;H=P.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
import fast_contacts as F
import tri_route as TR
import physical_reference_losses_r3_zero_r208 as RF
K=N.K;L=N.L;sha=N.sha;NET='/LOGIC_GND'
OUT=P/'CM51-seven-missing-bounded-real-SOURCE-before-local-ordinary-ground-ports-r452'
NORMAL={'58c55cd5-98e6-4467-88e3-146ceeee361a','c1d27fa1-452b-4e27-985d-5ad23644d800','54921f4b-0308-4821-9549-ff9360bf05ca'}
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def load(folder,name):return pickle.loads((P/folder/name).read_bytes())
def assemble():
    ctx=load('CM79-R300-all-native-intents-and-local-unchanged-definition-binding-r431','only-active-current-Cu-native-poses-all-native-intents-BEFORE-fill-context.pkl');c=copy.deepcopy(ctx['current_Cu_and_local_native_pads'])
    sel=load('CM51-pruned-real-source-before-safe-subset-incident-terminal-handoffs-r442','only-source-before-connected-safe-CM-subset-no-old-edits.pkl');ex=load('CM51-retained-CORE-no-new-hole-constructive-F-DC-source-joins-r443','only-new-constructive-DC-F-tracks-no-holes-no-old-edits.pkl');alt=load('CM79-alternate-CDONE-LG16-ONLY_NEW-CM85-leg-controlled-r448','only-qualified-minimal-pose-and-new-tracks.pkl');de=load('CM73-original-prospective-de03-site-alternate-CDONE-LG16-r450','only-qualified-prospective-de03-source-port-two-owned-tracks.pkl');r451=load('CM51-alternate-CDONE-direct-named-source-before-ground-port-handoffs-r451','only-new-named-source-before-ground-terminal-F-handoffs.pkl')
    nt=sel['tracks']+[t for t in ex['new_tracks']if t['uuid']!='65f3a90e-a953-5caa-8493-4623cfc05f2f']+alt['only_new_tracks']+de['tracks']+r451['new_tracks'];nv=sel['vias']+[de['via']]
    c['vias']=[alt['moved_original_barrel']if v['uuid']==alt['moved_original_barrel']['uuid']else v for v in c['vias']]+nv;c['tracks']+=nt
    return ctx,c,alt,r451,nt,nv
def main():
    started=time.monotonic();assert not OUT.exists();OUT.mkdir();ctx,c,alt,prev,nt,nv=assemble();dom=c['domains_normalized'];gap=lambda n:.15 if dom.get(L.norm(n))==dom.get(NET)else .6;region=box(103,156,143,180);roi=region.buffer(2);rec,trees=F.build(c);native={z['uuid']:z for z in c['zones']};vcuts=[];fcuts=[]
    for ly in K.LAYERS:
        for jj in trees[ly].query(roi,predicate='intersects'):
            r=rec[ly][int(jj)];n=L.norm(r['net'])
            if n==NET:continue
            req=max(gap(n),float(native[r['uuid']].get('clearance_mm',.15))if r['kind']=='fill'and r['uuid']in native else .15)+.026
            if not(r['kind']=='fill'and r['uuid']in NORMAL):vcuts.append(r['shape'].buffer(.25+req,quad_segs=128))
            if ly=='F.Cu':fcuts.append(r['shape'].buffer(.1+req,quad_segs=128))
    for z in ctx['all_current_native_intents']:
        if L.norm(z['net'])==NET or not z['shape'].intersects(roi):continue
        req=max(gap(z['net']),z['clearance_mm'])+.026
        if z['uuid']not in NORMAL:vcuts.append(z['shape'].buffer(.25+req,quad_segs=128))
        if z['layer']=='F.Cu':fcuts.append(z['shape'].buffer(.1+req,quad_segs=128))
    for r in ctx['all_current_native_rule_areas']:
        for sh in L.poly(N.O.polys(r['outline'])):
            if not sh.intersects(roi):continue
            if r['no_vias']:vcuts.append(sh.buffer(.276,quad_segs=128))
            if r['no_tracks']and'F.Cu'in r['layers']:fcuts.append(sh.buffer(.126,quad_segs=128))
    holes=[(v['uuid'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in c['vias']]+[(p['uuid'],s)for p in c['pads']for s in L.poly(p.get('hole')or[])];holes=[(u,s)for u,s in holes if s.intersects(roi)]
    for u,sh in holes:vcuts.append(sh.buffer(.381,quad_segs=128));fcuts.append(sh.buffer(.381,quad_segs=128))
    for v in c['vias']:
        pp=Point(v['x'],v['y'])
        if pp.intersects(roi):vcuts.append(pp.buffer(.816,quad_segs=128))
    for p in c['pads']:
        if p.get('hole'):continue
        for ly in ('F.Cu','B.Cu'):
            for sh in L.poly(p['layers'].get(ly,[])):
                if sh.intersects(roi):vcuts.append(sh.buffer(.381,quad_segs=128))
    board=unary_union(L.poly(c['outline'])).buffer(-.626);vfree=region.intersection(board).difference(unary_union(vcuts));ffree=region.intersection(board).difference(unary_union(fcuts));gs,_=N.bound_R663_before_groups({NET});j1=K.root(gs[NET],'J11001','2');planes={ly:unary_union([r['shape']for r in j1 if r['kind']=='fill'and r['layer']==ly])for ly in ('In1.Cu','In4.Cu')};source=vfree
    for sh in planes.values():source=source.intersection(sh.buffer(-.251,quad_segs=128))
    source=source.difference(Point(alt['moved_original_barrel']['x'],alt['moved_original_barrel']['y']).buffer(.826,quad_segs=128));(OUT/'bounded-all-layer-new-port-free.wkb').write_bytes(vfree.wkb);(OUT/'bounded-fully-source-contained-new-port-free.wkb').write_bytes(source.wkb);rows=[];newvias=[];newtracks=[];routes=[]
    faces=RF.parts(ffree)
    for info in prev['still_unconnected']:
        p=next(p for p in c['pads']if p['uuid']==info['pad_UUID']);start=Point(p['x'],p['y']);face=next((f for f in faces if f.covers(start)),None);row={'pad_UUID':p['uuid'],'ref':p['ref'],'pin':p['num'],'pad_xy':[p['x'],p['y']],'full20_F_start_component_area_mm2':face.area if face else 0,'bands':[],'route':None};chosen=None
        for radius in (2.,4.,8.):
            local=source.intersection(start.buffer(radius,quad_segs=128));local=local.intersection(face.buffer(-.001))if face is not None else local.intersection(Point(0,0));parts=RF.parts(local);br={'radius_mm':radius,'genuine_source_port_free_area_mm2':local.area,'components':len(parts)};row['bands'].append(br)
            candidates=[]
            for sh in parts:
                safe=sh.buffer(-.002)
                if safe.is_empty:safe=sh
                q=nearest_points(safe,start)[0];candidates.extend([q,safe.representative_point()])
            for q in sorted(candidates,key=lambda q:q.distance(start))[:24]:
                x,y=round(q.x,6),round(q.y,6);end=Point(x,y)
                if not local.covers(end):continue
                try:path,method=TR.route(face,[p['x'],p['y']],[x,y])
                except Exception:continue
                path=[[round(a,6),round(b,6)]for a,b in path];axis=LineString(path);body=axis.buffer(.1,quad_segs=128);length=axis.length
                if length>10 or not face.covers(axis):continue
                cap=end.buffer(.525,quad_segs=128);drill=end.buffer(.1,quad_segs=128);outside=body.difference(cap);clear=None if outside.is_empty else outside.distance(drill)
                if clear is not None and clear<.28:continue
                ann=end.buffer(.25,quad_segs=128).difference(drill);over={ly:ann.intersection(sh).area for ly,sh in planes.items()};pc=body.intersection(unary_union(L.poly(p['layers']['F.Cu']))).area;ac=body.intersection(ann).area
                if min(over.values())<=0 or pc<=0 or ac<=0:continue
                chosen=(x,y,path,length,method,over,pc,ac,clear);break
            if chosen:break
        if chosen:
            x,y,path,length,method,over,pc,ac,clear=chosen;v={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM51-R452-ground-port:'+p['uuid'])),'net':NET,'x':x,'y':y,'d':.5,'drill':.2,'span':K.LAYERS,'flashed':K.LAYERS,'mask_provenance':'prospective guard only; native AFTER masks OPEN'};ts=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM51-R452-ground-track:'+p['uuid']+':'+str(i))),'net':NET,'layer':'F.Cu','w':.2,'a':a,'b':b}for i,(a,b)in enumerate(zip(path,path[1:]))];newvias.append(v);newtracks+=ts;row.update(route=path,length_mm=length,via=v,source_annuli_mm2=over,finite_pad_contact_mm2=pc,finite_port_annulus_contact_mm2=ac,outside_own525cap_drill_clearance_mm=clear,method=method);routes.append(row);source=source.difference(Point(x,y).buffer(.816,quad_segs=128));ffree=ffree.difference(Point(x,y).buffer(.481,quad_segs=128));faces=RF.parts(ffree);print('R452_ROUTE',p['ref'],p['num'],length,[x,y],flush=True)
        rows.append(row);put('bounded-seven-pad-progress.json',rows)
    pkt={'new_tracks':newtracks,'new_vias':newvias,'routes':routes,'still_unconnected':[{'pad_UUID':r['pad_UUID'],'ref':r['ref'],'pin':r['pin']}for r in rows if r['route']is None],'dependencies':'exact R442+R443 minus65f+R448 alternate+R450+R451; no R435/all49 replay','actual_current_native_AFTER_SOURCE_oldrefs_current_thermal':'OPEN'};(OUT/'only-new-local-real-source-ground-ports-and-F-handoffs.pkl').write_bytes(pickle.dumps(pkt,protocol=5));put('receipt.json',{'status':'BOUNDED_LOCAL_SOURCE_BEFORE_PORT_SEARCH','qualified_routes':len(routes),'still_unconnected':pkt['still_unconnected'],'new_vias':len(newvias),'new_F20_tracks':len(newtracks),'source_containment_margin_mm':.251,'port_search_radii_mm':[2,4,8],'planner_extra_mm':.026,'source_free_initial_area_mm2':sum(RF.parts(source)[i].area for i in range(len(RF.parts(source)))),'original_Cu_edits':0,'native_jobs':0,'adopted':False,'packet_SHA256':sha(OUT/'only-new-local-real-source-ground-ports-and-F-handoffs.pkl'),'elapsed_seconds':time.monotonic()-started});print('R452_COMPLETE',sha(OUT/'receipt.json'),len(routes),pkt['still_unconnected'],flush=True)
if __name__=='__main__':main()
