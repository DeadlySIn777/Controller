"""One exact successful XF local geometry, component/barrier nomination only.

No emitted board and no approval credit for exploratory omission of obstacles.
No native/GPU jobs. Reuses the preserved r6 four-path result instead of repeating
the ten coupled landings. All ordinary/copper/reference acceptance stays open.
"""
import json,math,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import net_identity_exact as N
import native_flash_model as F
import xf_continuous_landings_r6 as X
import prospective_B_ground as B
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
P,G,S,C=A.P,A.G,A.S,A.C
REQ,EN,GND=X.REQ,X.EN,X.GND

def main():
    out=HERE/'xf-component-diagnostic-r1.json';started=time.time()
    if out.exists():raise ValueError('Fresh diagnostic receipt required')
    for module in list(sys.modules.values()):
        q=getattr(module,'__file__',None)
        if q and str(q).endswith('.py') and ('pcb-runs' in str(q) or 'board-finish-20261011' in str(q)):A.read(q)
    raw=A.read(G.SOURCE);now=C.inventory(raw);old=C.inventory(A.read(S.overlay_tool.base.BASE));identity=N.SourceNets(raw)
    receipt=json.loads(A.read(HERE/'xf-continuous-landings-r6.json'));attempt=receipt['attempts'][0]
    if len(attempt['paths'])!=4 or C.sha(raw)!=A.SOURCE_SHA:raise ValueError('Frozen four-path source differs')
    native=json.loads(A.read(A.NATIVE/'geometry.json'));template=json.loads(A.read(S.overlay_tool.base.GEOM));template,proof=A.fresh_template(old,now,template,native)
    source_masks={u:set(ls) for u,ls in json.loads(A.read(A.NATIVE/'actual-via-flashes.json'))['vias'].items()};masks=dict(source_masks)
    deleted=set(receipt['deleted_owned_items']);restored=set(receipt['restored_original_items'])
    chunks={u:ch for u,ch in now[4].items() if u not in deleted};chunks.update({u:old[4][u] for u in restored})
    for v in attempt['via_sites']:
        u,ch=X.serial_via(identity.raw(v['net']),v['at_mm'])
        if u!=v['uuid']:raise ValueError('Frozen via serialization differs')
        chunks[u]=ch;masks[u]=set(template['copper_layers'])
    for path in attempt['paths']:
        items=[]
        for a,b in zip(path['points_mm'],path['points_mm'][1:]):u,ch=identity.serial_segment(path['net'],path['layer'],a,b,.2);chunks[u]=ch;items.append(u)
        if items!=path['new_items']:raise ValueError('Frozen successful path serialization differs')
    reserve,exempt=A.reservations();print('XF_COMPONENT_EXACT_MODEL',flush=True)
    model=F.Model(identity.geometry(chunks,template),reserve,exempt,native['vias'],source_masks)
    signal_sites=[r['at_mm'] for r in attempt['via_sites'] if r['net'] in (REQ,EN)]+[[326.15,100.15]]
    refs,witness=X.refs_after(model,masks,signal_sites)
    start=next(r['at_mm'] for r in attempt['via_sites'] if r['net']==EN);goal=[326.15,100.15];window=box(289,93,336,115)
    void=unary_union([Point(v['x'],v['y']).buffer(v['d']/2+.175,resolution=128) for v in model.g['vias'] if v['net']==EN and [v['x'],v['y']] in signal_sites])
    free,blocked=B.free(model,EN,'B.Cu',window);strict=free.intersection(refs['B.Cu'].union(void).buffer(-.1))
    source=[q for q in P.K.D.components(strict) if q.covers(Point(start))];targets=[q for q in P.K.D.components(strict) if q.covers(Point(goal))]
    if len(source)!=1 or len(targets)!=1:raise ValueError('Expected exact source/target routing components')
    component=source[0];boundary=component.boundary;barriers=[]
    for i in model.trees['B.Cu'].query(component.envelope.buffer(1),predicate='intersects'):
        r=model.records['B.Cu'][i]
        if r.get('net')==EN or B.permitted(r,EN,model):continue
        gap=.25 if r['kind']=='hole' else (.15 if r.get('domain')==model.domains[EN] else .6)
        body=r['shape'].buffer(gap+.1+S.MARGIN)
        if body.distance(boundary)<=.000005:
            barriers.append({'kind':r['kind'],'uuid':r.get('uuid'),'key':list(r['key']) if r.get('key') else None,'net':r.get('net'),'domain':r.get('domain'),'body_bounds_mm':list(r['shape'].bounds),'source_shape_wkb_sha256':C.sha(r['shape'].wkb),'pad_id':r.get('pad_id'),'buffered_clearance_boundary_distance_mm':body.distance(boundary)})
    # Exploratory removal of same-domain non-GND fill cannot qualify a route.
    exploratory_obstacles=[];omitted=[]
    for i in model.trees['B.Cu'].query(window.buffer(2),predicate='intersects'):
        r=model.records['B.Cu'][i]
        if r.get('net')==EN:continue
        if r['kind']=='fill' and r.get('domain')==model.domains[EN]:
            if r.get('net')!=GND:omitted.append({'uuid':r['uuid'],'net':r['net'],'source_shape_wkb_sha256':C.sha(r['shape'].wkb),'bounds_mm':list(r['shape'].bounds)})
            continue
        gap=.25 if r['kind']=='hole' else (.15 if r.get('domain')==model.domains[EN] else .6)
        exploratory_obstacles.append(r['shape'].buffer(gap+.1+S.MARGIN))
    for r in model.hard['B.Cu']:
        if EN not in r['exempt'] and r['shape'].intersects(window.buffer(2)):exploratory_obstacles.append(r['shape'].buffer(.1+S.MARGIN))
    exploratory=window.intersection(model.outline.buffer(-.5-.1-S.MARGIN)).difference(unary_union(exploratory_obstacles)).intersection(refs['B.Cu'].union(void).buffer(-.1))
    exploratory_source=[q for q in P.K.D.components(exploratory) if q.covers(Point(start))]
    print('XF_COMPONENT_ROUTING_NOMINATION',flush=True)
    path,search=S.astar(exploratory,*[[((tuple(p)),{'kind':'track','uuid':'diagnostic-only'})] if exploratory.covers(Point(p)) else [] for p in (start,goal)],time.monotonic()+30,node_cap=200000)
    foreign_fills=[]
    if path:
        trackbody=LineString(path['points_mm']).buffer(.1,resolution=128)
        for i in model.trees['B.Cu'].query(trackbody.buffer(.3),predicate='intersects'):
            r=model.records['B.Cu'][i]
            if r['kind']=='fill' and r.get('net') not in (GND,EN) and r.get('domain')==model.domains[EN]:
                overlap=trackbody.buffer(.175,resolution=128).intersection(r['shape']).area
                if overlap>1e-10:foreign_fills.append({'zone_uuid':r['uuid'],'net':r['net'],'source_shape_wkb_sha256':C.sha(r['shape'].wkb),'prospective_nomination_cut_area_mm2':overlap,'power_continuity_current_drop_width_return_qualification':'OPEN_NO_WAIVER'})
    # Exact F/B component intersection nominates a possible F/B/F second dive.
    freeF,_=B.free(model,EN,'F.Cu',window);legalF=freeF.intersection(refs['F.Cu'].union(void).buffer(-.1))
    downstream=[r for r in model.own[EN] if r['layer']=='F.Cu' and r['uuid'] in now[4] and r['uuid'] not in deleted]
    land=unary_union([r['shape'] for r in downstream]);reaching=[q for q in P.K.D.components(legalF) if q.intersects(land)]
    freevia,_=B.freevia(model,EN,window);joint=component.intersection(unary_union(reaching)).intersection(freevia)
    candidates=X.sites(joint,[start[0]+.9,start[1]],12)
    for q,h in A.READS.items():
        if C.sha(Path(q).read_bytes())!=h:raise ValueError('Frozen read changed '+q)
    result={'schema':'xf-exact-component-diagnostic-r1','verdict':'DIAGNOSTIC_ONLY_NO_BOARD_OR_ACCEPTANCE','source_sha256':C.sha(raw),'frozen_four_path_receipt_sha256':C.sha(Path(HERE/'xf-continuous-landings-r6.json').read_bytes()),'native_geometry_proof':proof,'source_actual_annuli':model.source_annulus_proof,'start_mm':start,'goal_mm':goal,'source_component':{'area_mm2':component.area,'bounds_mm':list(component.bounds),'wkb_sha256':C.sha(component.wkb)},'target_component':{'area_mm2':targets[0].area,'bounds_mm':list(targets[0].bounds),'wkb_sha256':C.sha(targets[0].wkb)},'physical_clearance_boundary_nominations':barriers,'reference_boundary_gap_area_mm2':component.envelope.buffer(.3).difference(refs['B.Cu'].union(void)).area,'source_rooted_drilled_reference_witness':witness,'exploratory_same_domain_fill_omissions':omitted,'exploratory_source_components':[{'area_mm2':q.area,'bounds_mm':list(q.bounds),'goal_inside':q.covers(Point(goal))} for q in exploratory_source],'exploratory_search':search,'exploratory_path':path,'exploratory_affected_power_fill_nominations':foreign_fills,'existing_downstream_F_uuids':[r['uuid'] for r in downstream],'F_downstream_reachable_components':[{'area_mm2':q.area,'bounds_mm':list(q.bounds)} for q in reaching],'ordinary_second_via_component_candidates':candidates,'read_files_sha256':A.READS,'seconds':time.time()-started,'native_jobs':0,'gpu_jobs':0,'board_emitted':False,'adopted':False,'limits':['Diagnostic component and blocker nomination, not positive geometric/electrical qualification','Any same-domain power-zone displacement needs separately constructed/audited exact old/new physical-contact and rooted-source/current/width/drop/thermal/return obligations plus root coordination','Second F/B/F transition candidates require ordinary all6-layer via/hole/SMD/pitch, correct local rooted return, all full-body references and every source/current/r06 contact obligation before board emission','No native/DRC/gate credit; no live/source zone/board/project mutation']}
    out.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8');print(json.dumps({'receipt':str(out),'source_component_mm2':component.area,'same_domain_fill_omission_path':bool(path),'second_via_nominations':len(candidates)}),flush=True)
if __name__=='__main__':main()
