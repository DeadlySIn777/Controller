"""Independent frozen AUX recipe/contact/clearance audit, host only.

Fresh198b native fills/annuli replace the older cached reference geometry.
Unchanged full pad stacks and native graphics/holes are reused only after exact
noncopper source identity; first-layer pad polygons use fresh integer geometry.
This does not load/save KiCad or qualify current/reference/return behavior.
"""
import collections,copy,hashlib,json,math,re,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import coupled_screen as P
G,S,C=P.G,P.S,P.C
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree

SOURCE_SHA='198bba53ad2cf983940c68f5e732b575d28d5fb962bc1fa4d3fd959c23a427ab'
CAND_SHA='0fb4ae9b7db986e2d11c87e947fe7e777f48f88847f22a4d05376ffb84b6e3d9'
NATIVE=HERE.parent/'native-198b-geometry'
POWER='/motherboard_motors/AUX_24V_A'
ILIM='/motherboard_power_entry/AUX24_A_ILIM'
DVDT='/motherboard_power_entry/AUX24_A_DVDT'
READS={}
def read(p):
    p=Path(p).resolve();raw=p.read_bytes();READS[str(p)]=C.sha(raw);return raw
def polys(rings):return [[r[0],r[1:]] for r in rings]

def fresh_template(old,current,template,native):
    if old[0]!=current[0] or old[2]!=current[2] or old[5]!=current[5]:
        raise ValueError('Pad/footprint/graphic/rule/plane source definitions differ')
    g=copy.deepcopy(template)
    if len(native['pads'])!=len(g['pads']):raise ValueError('Native pad inventory differs')
    checked=[];precision=[]
    for i,(prior,new) in enumerate(zip(g['pads'],native['pads'])):
        if (prior['ref'],prior['num'],S.norm(prior['net']))!=(new['ref'],new['num'],S.norm(new['net'])):
            raise ValueError('Native pad identity/order differs at '+str(i))
        # IsOnLayer reports nominal Cu flags for NPTH. The older full export
        # correctly omits their copper; keep them as holes, never conductive
        # pads. Plated/SMD membership must match exactly.
        if prior['npth']:
            if new['attr']!='npth' or prior['layers']:raise ValueError('NPTH source membership differs '+prior['uuid'])
        elif set(prior['layers'])!=set(new['layers']):raise ValueError('Native pad layer membership differs '+prior['uuid'])
        deviation=math.dist((prior['x'],prior['y']),new['at'])
        if deviation>.00008:raise ValueError('Prior native pad pose differs '+prior['uuid'])
        if deviation:precision.append({'uuid':prior['uuid'],'pose_delta_mm':deviation})
        prior['x'],prior['y']=new['at']
        if new['layers'] and not prior['npth']:prior['layers'][new['layers'][0]]=polys(new['poly'])
        checked.append(prior['uuid'])
    z={row['uuid']:row for row in native['zones']}
    for zone in g['zones']:
        new=z[zone['uuid']]
        if S.norm(zone['net'])!=S.norm(new['net']) or zone['layers']!=new['layers']:
            raise ValueError('Fresh zone identity differs')
        zone['fills']={layer:polys(rings) for layer,rings in new['fills'].items()}
        zone['outline']=polys(new['outline'])
    g['outline']=polys(native['outline'])
    return g,{'exact_non_copper_definitions_same':True,'native_pad_identity_pose_layers_checked':len(checked),
              'old_rounded_pad_pose_count':len(precision),'maximum_old_pose_delta_mm':max((r['pose_delta_mm'] for r in precision),default=0),
              'first_layer_pad_polygons':'fresh integer native export','other_pad_layers_holes_graphics':'unchanged native r06 source definitions; reused geometry with conservative .010mm audit uncertainty',
              'fresh_zone_count':len(z),'polygon_export_inside_error_mm':.005}

def reservations():
    r=json.loads(read(G.C06/'alternate-r07/reserved-r07.json'));ex={}
    for line in read(G.C06/'alternate-r07/reserve/board.kicad_dru').decode().splitlines():
        m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if m:ex[m.group(1)]={S.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m.group(2))}
    return r,ex

def relationships(model,masks,native_parts,nets):
    failures=[];summaries=[];ufs={};groups={}
    for net in nets:
        uf,gs=P.physical(model,net,masks);ufs[net]=uf;groups[net]=gs
        expected={frozenset(r) for r in native_parts[net]}
        actual=P.exact_partitions(gs)
        summaries.append({'net':net,'pad_groups':len(expected),'host_groups':len(actual),'exact_native_partition_match':actual==expected})
        for rel in native_parts[net]:
            if len({uf.find(('p',p)) for p in rel})>1:failures.append({'net':net,'relationship':rel})
    return failures,summaries,ufs,groups

def shape(r):
    if r['kind']=='via':return Point(r['at']).buffer(r['d']/2,resolution=128)
    if r['kind']=='segment':return LineString([r['a'],r['b']]).buffer(r['w']/2,resolution=128)
    return r['shape']

def clearance(model,parsed,added,restored):
    errors=[];rows=[];error_guard=.010
    for uid in sorted(added|restored):
        r=parsed[uid];body=shape(r);net=r['net'];domain=model.domains[net]
        layers=model.g['copper_layers'] if r['kind']=='via' else [r['layer']]
        nearest=collections.defaultdict(lambda:float('inf'))
        for layer in layers:
            for i in model.trees[layer].query(body.buffer(.8),predicate='intersects'):
                b=model.records[layer][i]
                if b['uuid']==uid:continue
                if b['kind']=='hole':
                    # Existing own-net PTH attachment is not an unrelated
                    # drill violation; the restored ordinary via is checked
                    # against every hole regardless of net below.
                    if r['kind']!='via' and b['net']==net:continue
                    required=.25
                elif b['net']==net:
                    if r['kind']=='via' and b['kind']=='pad' and model.pads[b['pad_id']]['smd']:required=.1
                    else:continue
                else:required=.15 if b.get('domain')==domain else .6
                gap=body.distance(b['shape'])
                nearest[b['kind']]=min(nearest[b['kind']],gap-required)
                # Restore ordinary copper to the same conservative margin as
                # new copper; no source grandfathering is used here.
                if gap<required+error_guard-1e-8:
                    errors.append({'uuid':uid,'layer':layer,'other_uuid':b['uuid'],'other_kind':b['kind'],'other_net':b['net'],
                                   'gap_mm':gap,'required_mm':required,'uncertainty_guard_mm':error_guard})
            if layer in model.hard_trees:
                for i in model.hard_trees[layer].query(body.buffer(error_guard),predicate='intersects'):
                    b=model.hard[layer][i]
                    if net not in b['exempt'] and body.distance(b['shape'])<error_guard-1e-8:
                        errors.append({'uuid':uid,'layer':layer,'other_kind':b['kind'],'name':b['name'],'gap_mm':body.distance(b['shape'])})
        if not model.outline.buffer(-.5-error_guard).covers(body):errors.append({'uuid':uid,'kind':'board_edge'})
        via_extra=[]
        if r['kind']=='via':
            hole=Point(r['at']).buffer(r['drill']/2,resolution=128)
            for v in model.g['vias']:
                if v['uuid']==uid:continue
                center=math.dist(r['at'],(v['x'],v['y']))
                if center<.8+error_guard-1e-8:via_extra.append({'other_uuid':v['uuid'],'kind':'ordinary_via_pitch','center_mm':center})
                holegap=center-r['drill']/2-v['drill']/2
                if holegap<.25+error_guard-1e-8:via_extra.append({'other_uuid':v['uuid'],'kind':'hole_edge','gap_mm':holegap})
            for pad in model.g['pads']:
                for ph in S.poly(pad.get('hole') or []):
                    if hole.distance(ph)<.25+error_guard-1e-8:via_extra.append({'other_uuid':pad['uuid'],'kind':'pad_hole_edge','gap_mm':hole.distance(ph)})
            errors.extend(dict(uuid=uid,**r) for r in via_extra)
        rows.append({'uuid':uid,'net':net,'kind':r['kind'],'layers_checked':layers,'nearest_margin_after_required_mm':dict(nearest),'via_extra_errors':via_extra})
    return errors,rows

def main():
    started=time.time();out=HERE/'aux-exact-audit-r2.json'
    if out.exists():raise ValueError('Fresh audit receipt required')
    recipe=json.loads(read(HERE/'aux-power-escape-r2.json'))
    source=read(G.SOURCE);candidate=read(recipe['candidate']);oldraw=read(S.overlay_tool.base.BASE)
    if C.sha(source)!=SOURCE_SHA or C.sha(candidate)!=CAND_SHA:raise ValueError('Frozen candidate identity differs')
    now,final,old=map(C.inventory,(source,candidate,oldraw))
    deletes=set(recipe['owned_power_items'])|set(recipe['delete_ILIM_items']);restores=set(recipe['restore_original_DVDT_items'])
    added=set().union(*(set(p['new_items']) for p in recipe['proposal']['paths']))
    if set(now[4])-set(final[4])!=deletes or set(final[4])-set(now[4])!=added|restores:raise ValueError('Recipe item ownership differs')
    if now[0]!=final[0] or now[2]!=final[2] or now[5]!=final[5]:raise ValueError('Candidate noncopper differs')
    if any(final[3].get(uid)!=ch for uid,ch in now[3].items() if uid not in deletes):raise ValueError('Retained source item differs')
    if any(final[4][uid]!=old[4][uid] for uid in restores):raise ValueError('Restored source bytes differ')
    generated={}
    for path in recipe['proposal']['paths']:
        for a,b in zip(path['points_mm'],path['points_mm'][1:]):
            uid,ch=P.serial_segment(path['net'],path['layer'],a,b,path['width_mm']);generated[uid]=ch
    if set(generated)!=added or any(final[4][uid]!=ch for uid,ch in generated.items()):raise ValueError('Frozen serialized path differs')
    native=json.loads(read(NATIVE/'geometry.json'));masksrow=json.loads(read(NATIVE/'actual-via-flashes.json'));receipt=json.loads(read(NATIVE/'receipt.json'))
    if receipt['verdict']!='PASS' or receipt['inputs_before']!=receipt['inputs_after'] or not receipt['exact_integer_coordinates'] or not native['fill']['filler_ok'] or masksrow['board_sha256']!=SOURCE_SHA:
        raise ValueError('Current native export identity/evidence differs')
    if C.sha(read(NATIVE/'geometry.json'))!='ad4d776a8703702d9bd682c1427d7883b729e8c6dcfbaad87c9e07c7b981d5d1':raise ValueError('Fresh geometry hash differs')
    template=json.loads(read(S.overlay_tool.base.GEOM));template,padproof=fresh_template(old,now,template,native)
    masks={uid:set(ls) for uid,ls in masksrow['vias'].items()}
    observed={v['uuid']:v for v in template['vias']}
    for uid in restores:
        if uid in observed:masks[uid]=set(observed[uid]['flashed'])
    reserve,exempt=reservations()
    parts={S.norm(n):gs for n,gs in json.loads(read(G.REPORT/'measure/r07-four-fag-shared/partitions.json'))['nets'].items()}
    r06parts={S.norm(n):gs for n,gs in json.loads(read(P.R.R06_PART))['nets'].items()}
    print('AUX_EXACT_CURRENT_MODEL',flush=True);current_g=P.geometry(now[4],template);current_model=S.Model(current_g,reserve,exempt)
    failures,checks,current_uf,current_groups=relationships(current_model,masks,parts,(POWER,ILIM,DVDT))
    if failures or not all(c['exact_native_partition_match'] for c in checks):raise ValueError('Fresh physical baseline graph differs from native pad partitions')
    print('AUX_EXACT_CANDIDATE_MODEL',flush=True);candidate_g=P.geometry(final[4],template);model=S.Model(candidate_g,reserve,exempt)
    new_failures,new_checks,new_uf,new_groups=relationships(model,masks,parts,(POWER,ILIM,DVDT))
    for net in (POWER,ILIM,DVDT):
        for rel in r06parts[net]:
            if len({new_uf[net].find(('p',p)) for p in rel})>1:new_failures.append({'net':net,'baseline':'r06','relationship':rel})
    # Preserve every surviving physical entity from every old component. This
    # catches pad-free branch loss, unused via/stub loss and interior contacts.
    obligations=[];contact_loss=[];boundary=[]
    for net,groups in current_groups.items():
        for group in groups:
            surviving=sorted({r['key'] for r in group['records'] if r['uuid'] not in deletes})
            roots={new_uf[net].find(k) for k in surviving}
            obligations.append({'net':net,'surviving_physical_keys':[list(k) for k in surviving],'candidate_component_count':len(roots)})
            if len(roots)>1:contact_loss.append(obligations[-1])
        for r in current_model.own[net]:
            if r['uuid'] not in deletes:continue
            for b in current_model.own[net]:
                if b['uuid'] in deletes or b['layer']!=r['layer']:continue
                if b['kind']=='via' and b['layer'] not in masks[b['uuid']]:continue
                if r['shape'].distance(b['shape'])<=.000002:
                    boundary.append({'removed_uuid':r['uuid'],'surviving_key':list(b['key']),'layer':r['layer'],'gap_mm':r['shape'].distance(b['shape'])})
    parsed={uid:G.parse(uid,ch,{}) for uid,ch in final[4].items() if uid in added|restores}
    print('AUX_EXACT_CLEARANCE',flush=True);errors,clearance_rows=clearance(model,parsed,added,restores)
    # Actual current reference coverage is a diagnostic for the electrical
    # reviewer; local RTN support cannot be qualified by FIELD_GND substitution.
    coverage=[]
    for path in recipe['proposal']['paths']:
        line=LineString(path['points_mm']);ref_layer=S.REF_LAYER[path['layer']]
        for refnet in ('/FIELD_GND','/motherboard_power_entry/AUX24_A_RTN'):
            fill=unary_union([r['shape'] for r in model.records[ref_layer] if r['kind']=='fill' and r['net']==refnet])
            coverage.append({'net':path['net'],'reference_net':refnet,'reference_layer':ref_layer,'uncovered_centerline_mm':line.difference(fill).length,'fresh_198b_fills':True,'electrical_qualification':False})
    # Full import closure is frozen as independent immutable helpers; imported
    # source read is not assumed solely from the constructor's short manifest.
    for module in list(sys.modules.values()):
        p=getattr(module,'__file__',None)
        if p and str(p).endswith('.py') and ('pcb-runs' in str(p) or 'board-finish-20261011' in str(p)):read(p)
    READS.update(S.READS)
    for p,h in READS.items():
        if C.sha(Path(p).read_bytes())!=h:raise ValueError('Frozen audit read changed '+p)
    result={'schema':'aux-exact-audit-r2','evidence_class':'HOST_ONLY_FROZEN_CANDIDATE_AUDIT','source_sha256':SOURCE_SHA,'candidate_sha256':CAND_SHA,
            'recipe_exact':True,'deleted_items':sorted(deletes),'restored_original_items':sorted(restores),'new_items':sorted(added),
            'pad_and_fill_provenance':padproof,'current_native_pad_graph_verification':checks,'candidate_pad_graph_checks':new_checks,
            'pad_relationship_failures':new_failures,'surviving_physical_component_obligations':obligations,'surviving_contact_losses':contact_loss,
            'removed_to_surviving_contacts':boundary,'clearance_errors':errors,'changed_item_clearance_rows':clearance_rows,'current_fill_coverage_diagnostic':coverage,
            'read_files_sha256':READS,'native_jobs':0,'gpu_jobs':0,'adopted':False,'manufacturing_ready':False,'seconds':time.time()-started,
            'verdict':'HOST_AUDIT_PASS_NATIVE_ELECTRICAL_OPEN' if not new_failures and not contact_loss and not errors else 'HOST_AUDIT_FAILED',
            'open_gates':['Fresh candidate native refill/ordinary DRC and full dual-r06/r07 no-loss guards','All changed local AUX circuit current/drop, support/RTN geometry, restored-via return and source-reference electrical audit','Native final all-layer pad-stack/annulus/graphics/hole checks; host reused unchanged definitions are conservative geometry only']}
    out.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({'verdict':result['verdict'],'clearance_errors':len(errors),'pad_loss':len(new_failures),'physical_contact_loss':len(contact_loss),'receipt':str(out)}),flush=True)
if __name__=='__main__':main()
