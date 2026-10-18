"""Extend two preserved feeder planes to actual same-layer CORE source Cu.

The historical planner retained an In4 goal when selecting a different
routing layer. All five feed additions are retained; this adds only exact
contained same-layer source attachments and verifies the full projected graph.
"""
import json,pickle,hashlib
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
import core_inner_feed_r18 as I
import continuous_path_prepared_r2 as CP
L=I.L;p=I.p;P=I.P;Q=I.Q;C=I.C;NET=I.NET
OUT=L.OUT/'actual-core-source-attachment-repair-r35'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir();prior=L.OUT/'five-core-and-b5-checkpoint-r32/model.pkl'
    assert sha(prior)=='8bd79b8233520e02aaf4c4c4988076ec45543d3639d75f20e2cdc0156307678b'
    g,h,binding,zones,candidate=pickle.loads(prior.read_bytes())
    audit=L.OUT/'five-core-attachment-diagnostic-r34';ar=json.loads((audit/'receipt.json').read_text());assert ar['model_sha256']==sha(prior)
    cache=pickle.loads((audit/'groups.pkl').read_bytes());groups=cache['groups'];parts=cache['parts'];assign=cache['assign'];root=ar['source_group']
    ownholes=[Point(v['x'],v['y']).buffer(v['drill']/2) for v in h['vias'] if p.norm(v['net'])==NET]
    ownholes += [s for q in h['pads'] if p.norm(q['net'])==NET for s in p.base.polygons(q.get('hole') or [])]
    holes=unary_union(ownholes);rows=[];newzones=[]
    for r in ar['rows']:
        if r['all_target_pads_source_connected']:continue
        assert len(r['attached_proposed_inner_planes'])==1
        uid=r['attached_proposed_inner_planes'][0]['uuid'];old=next(q for q in zones if q['uuid']==uid);layer=old['layer']
        freefile=L.OUT/'core-inner-feed-r33'/(layer+'-free.wkb')
        from shapely import from_wkb
        free=set_precision(from_wkb(freefile.read_bytes()),1e-6)
        # Remove own drills from physical source goal: a source marker in an
        # empty barrel center cannot substitute for a real source annulus.
        goal=unary_union([s for s,j in zip(parts[layer],assign[layer]) if j==root]+[q['shape'] for q in newzones if q['layer']==layer]).difference(holes)
        answer=None
        for width in (1.25,1.,.75,.5,.35,.25,.20):
            safe=set_precision(free.buffer(-width/2-.01),1e-6)
            for component in p.hubs.components(safe):
                aa=component.intersection(old['shape']).buffer(-.005);bb=component.intersection(goal).buffer(-.005)
                if aa.is_empty or bb.is_empty:continue
                a,b=nearest_points(aa,bb);start=tuple(round(v,6) for v in a.coords[0]);end=tuple(round(v,6) for v in b.coords[0])
                if not component.covers(Point(start)) or not component.covers(Point(end)):continue
                print('CORE_SAME_LAYER_ATTACHMENT_SEARCH',uid,layer,width,start,end,flush=True)
                route=CP.path(component,start,end,node_cap=500000)
                if route['verdict']!='HOST_PATH':continue
                pts=[[round(x,6),round(y,6)] for x,y in route['points']];line=LineString(pts);core=line.buffer(width/2)
                if not free.covers(core):continue
                outline=set_precision(line.buffer(2).intersection(free),1e-6)
                outline=unary_union([s for s in p.hubs.components(outline) if s.intersection(core).area>0])
                physical=set_precision(outline.difference(holes),1e-6)
                if physical.intersection(old['shape']).area<=.001 or physical.intersection(goal).area<=.001:continue
                z={'uuid':C.uid('CORE-real-layer-attachment-r35-'+uid),'label':'CORE-real-layer-attachment-r35-'+uid,
                   'net':old['net'],'layer':layer,'shape':physical,'zone_outline_shape':outline,'clearance_mm':.15,
                   'route':{**route,'points':pts,'length_mm':line.length,'minimum_core_width_mm':width,'exact_quantized_core_free_containment':True},
                   'target_preserved_feeder_uuid':uid,'source_contact_is_actual_same_layer_and_drill_subtracted':True}
                answer=z;break
            if answer:break
        assert answer is not None,('same_layer_attachment_unresolved',uid,layer)
        newzones.append(answer);rows.append({'preserved_feeder_uuid':uid,'new_attachment_uuid':answer['uuid'],'actual_routing_layer':layer,
            'route':answer['route'],'physical_source_overlap_mm2':answer['shape'].intersection(goal).area,
            'physical_target_overlap_mm2':answer['shape'].intersection(old['shape']).area,'new_holes':0,
            'source_root_before':root,'exact_source_contact':'R11022.2 on actual chosen layer; own empty drills subtracted'})
        (OUT/'checkpoint.json').write_text(json.dumps(rows,indent=2)+'\n');print('CORE_SAME_LAYER_ATTACHMENT_CONSTRUCTED',uid,answer['route']['length_mm'],flush=True)
    assert len(newzones)==2
    zones+=newzones
    known=set(binding['restored_generated_grid_UUIDs'])|{q['uuid'] for q in newzones}
    for q in zones:
        if q['uuid'] in known:q['shape']=set_precision(q['shape'],1e-6)
    candidate,cuts=P.projected(g,h,zones);Q.NET=NET
    after,aparts,aassign=Q.groups(candidate,return_details=True);ids={q['uuid']:i for i,rr in enumerate(after) for q in rr}
    sp=next(q for q in h['pads'] if (q['ref'],q['num'])==('R11022','2'));sr=ids[sp['uuid']]
    all_feed_targets=[]
    for r in ar['rows']:
        pads=[{**q,'final_group':ids[q['uuid']],'source_connected':ids[q['uuid']]==sr} for q in r['target_physical_pads']]
        all_feed_targets.append({'via_uuid':r['via']['uuid'],'pads':pads,'all_target_pads_source_connected':all(q['source_connected'] for q in pads)})
    assert all(q['all_target_pads_source_connected'] for q in all_feed_targets),'Actual full projected source graph must pass for every preserved target'
    binding.update({'five_CORE_attachment_diagnostic_receipt_sha256':sha(audit/'receipt.json'),
        'actual_same_layer_attachment_fix':'Reload goal from chosen layer; historical goal retained final In4 iteration',
        'actual_same_layer_attachment_new_zones':rows,'all_five_preserved_target_groups_source_connected_host':True,
        'restored_generated_grid_UUIDs':sorted(known)})
    model=OUT/'model.pkl';model.write_bytes(pickle.dumps((g,h,binding,zones,candidate),protocol=5))
    (OUT/'groups.pkl').write_bytes(pickle.dumps({'groups':after,'parts':aparts,'assign':aassign},protocol=5))
    receipt={'verdict':'PASS_FIVE_PRESERVED_CORE_TARGET_SOURCE_ATTACHMENTS_FULL_CONTACT_CURRENT_NATIVE_PENDING','model_sha256':sha(model),
        'parent_model_sha256':sha(prior),'binding':binding,'rows':rows,'five_feed_target_checks':all_feed_targets,
        'remaining_CORE_named_groups':[{'group':i,'pads':[q for q in rr if not q['ref'].startswith('@')]} for i,rr in enumerate(after) if i!=sr and any(not q['ref'].startswith('@') for q in rr)],
        'old_fill_retreats':cuts,'new_vias':0,'new_segments':0,'new_zone_shapes':len(newzones),
        'all_original_contact_foreign_mutual_current_native_gates':'OPEN','native_jobs':0,'board_written':False}
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('CORE_SAME_LAYER_ATTACHMENT_REPAIR_PASS',sha(model),len(receipt['remaining_CORE_named_groups']),flush=True)
if __name__=='__main__':main()
