"""Exact bounded component blocker attribution; no edits or broad claim."""
import sys,json,pickle,time,collections
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely import from_wkb
P=Path(__file__).resolve().parent;H=P.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import search_remaining_CM_actual_source_local_ground_ports_r452 as S
K=S.K;L=S.L;F=S.F;RF=S.RF;N=S.N;sha=S.sha;NET=S.NET
OUT=P/'CM51-seven-ground-pad-components-all-layer-port-blocker-attribution-r459'
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
    started=time.monotonic();assert not OUT.exists();OUT.mkdir();ctx,c,alt,prev,nt,nv=S.assemble();freefile=P/'CM51-seven-missing-finite-partial-SOURCE-annulus-local-ground-ports-r453/bounded-full20-F-centre-free.wkb';free=from_wkb(freefile.read_bytes());faces=RF.parts(free);dom=c['domains_normalized'];gap=lambda n:.15 if dom.get(L.norm(n))==dom.get(NET)else .6;rec,trees=F.build(c);native={z['uuid']:z for z in c['zones']};oldtrack={t['uuid']for t in ctx['actual_BEFORE_model']['tracks']};oldvia={v['uuid']for v in ctx['actual_BEFORE_model']['vias']};rows=[]
    for info in prev['still_unconnected']:
        p=next(p for p in c['pads']if p['uuid']==info['pad_UUID']);start=Point(p['x'],p['y']);face=next(f for f in faces if f.covers(start));region=face.intersection(start.buffer(8,quad_segs=128));cons=[]
        def add(kind,uid,shape,**meta):
            if shape.intersects(region):cons.append({'kind':kind,'UUID':uid,'shape':shape,**meta})
        for ly in K.LAYERS:
            for jj in trees[ly].query(region.buffer(1.1),predicate='intersects'):
                r=rec[ly][int(jj)];n=L.norm(r['net'])
                if n==NET or r['kind']=='fill'and r['uuid']in S.NORMAL:continue
                req=max(gap(n),float(native[r['uuid']].get('clearance_mm',.15))if r['kind']=='fill'and r['uuid']in native else .15)+.026;origin='actual_BEFORE_original'if r['uuid']in oldtrack|oldvia else'current_or_plane';add('true_current_foreign_'+r['kind'],r['uuid'],r['shape'].buffer(.25+req,quad_segs=128),layer=ly,net=r['net'],origin=origin)
        for z in ctx['all_current_native_intents']:
            if L.norm(z['net'])!=NET and z['uuid']not in S.NORMAL and z['shape'].distance(region)<1.1:add('held_foreign_native_intent',z['uuid'],z['shape'].buffer(.25+max(gap(z['net']),z['clearance_mm'])+.026,quad_segs=128),layer=z['layer'],net=z['net'],unchanged_native_definition=z['unchanged_native_definition'])
        for v in c['vias']:
            q=Point(v['x'],v['y'])
            if q.distance(region)<.82:add('global_existing_or_selected_peer_pitch',v['uuid'],q.buffer(.816,quad_segs=128),xy=[v['x'],v['y']],net=v['net'],origin='actual_BEFORE_original'if v['uuid']in oldvia else'current_or_selected_new')
        for p0 in c['pads']:
            if p0.get('hole'):
                for sh in L.poly(p0['hole']):
                    if sh.distance(region)<.4:add('physical_pad_hole',p0['uuid'],sh.buffer(.381,quad_segs=128),ref=p0['ref'],pin=p0['num'])
            else:
                for ly in ('F.Cu','B.Cu'):
                    for sh in L.poly(p0['layers'].get(ly,[])):
                        if sh.distance(region)<.4:add('actual_SMD_to_new_drill',p0['uuid'],sh.buffer(.381,quad_segs=128),ref=p0['ref'],pin=p0['num'],layer=ly,net=p0['net'])
        for r in ctx['all_current_native_rule_areas']:
            if r['no_vias']:
                for sh in L.poly(N.O.polys(r['outline'])):
                    if sh.distance(region)<.3:add('actual_native_no_via',r['uuid'],sh.buffer(.276,quad_segs=128),name=r['name'])
        ranked=sorted(cons,key=lambda r:r['shape'].intersection(region).area,reverse=True);top=[{**{k:v for k,v in r.items()if k!='shape'},'blocked_component_area_mm2':r['shape'].intersection(region).area,'whole_bounded_component_covered':region.difference(r['shape']).is_empty}for r in ranked[:12]];remaining=region;greedy=[];unused=list(cons)
        for _ in range(12):
            if remaining.is_empty or not unused:break
            best=max(unused,key=lambda r:r['shape'].intersection(remaining).area);area=best['shape'].intersection(remaining).area
            if area<=0:break
            remaining=remaining.difference(best['shape']);unused.remove(best);greedy.append({**{k:v for k,v in best.items()if k!='shape'},'newly_removed_candidate_area_mm2':area,'remaining_mm2':remaining.area})
        row={'pad_UUID':p['uuid'],'ref':p['ref'],'pin':p['num'],'full20_F_component_area_mm2':face.area,'bounded_8mm_component_area_mm2':region.area,'top_individual_all_layer_port_constraints':top,'greedy_exact_local_cover':greedy,'remaining_after_cover_mm2':remaining.area,'source_or_native_global_impossibility_claim':False};rows.append(row);put('all-seven-exact-local-port-blocker-attribution.json',rows);print('R459_BLOCKER',p['num'],[(r['kind'],r['UUID'],r['newly_removed_candidate_area_mm2'])for r in greedy[:3]],flush=True)
    put('receipt.json',{'status':'BOUNDED_SEVEN_COMPONENT_PORT_BLOCKERS_ATTRIBUTED','source_F_free_WKB_SHA256':sha(freefile),'pads':len(rows),'all_seven_have_complete_local_constraint_cover':all(r['remaining_after_cover_mm2']==0 for r in rows),'original_Cu_holes_FP_native_edits':0,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R459_COMPLETE',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
