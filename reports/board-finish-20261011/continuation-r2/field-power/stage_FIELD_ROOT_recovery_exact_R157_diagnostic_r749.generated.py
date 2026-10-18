"""Exact sparse native diagnostic composition; no KiCad job, cache or adoption."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib,uuid,time,math,traceback
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent;REC=ROOT/'coupled-recovery'
for d in (H,ROOT,ROOT/'sbc-power',REC):sys.path.insert(0,str(d))
import freeze_FIELD_complete_R157_native_definition_replay_r735 as E
from shapely import set_precision
from shapely.geometry import Point,Polygon,MultiPolygon,box
from verify_source import parse,children,child,atom
O=E.O
OUT=H/'FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r749'
R735=H/'FIELD-complete-exact-R157-native-definition-only-replay-r735'
R741=H/'FIELD-ROOT-distinct-priority-exact-native-ownership-and-sparse-role-handoff-r741'
PEER=ROOT/'U10003-HOST-R157-exact-sparse-native-API-clone-r271'
RM=REC/'Q0-DIC-DI6-exact-R157-minimal-sparse-native-replay-manifest-r588/minimal-exact-Q0-DIC-DI6-native-replay-manifest.json'
def sha(p):return E.sha(p)
def artifact(p):return E.artifact(p)
def put(p,v):return E.put(p,v)
def hs(s):return E.hs(s)
def literal(s):
    r=set_precision(s,0);assert r.wkb==s.wkb;return r
def pp(s):return list(s.geoms) if s.geom_type=='MultiPolygon' else [s]
def rr(s):
    for x in pp(s):
        yield list(x.exterior.coords)
        for r in x.interiors:yield list(r.coords)
def vertices(s):return {tuple(v) for r in rr(s) for v in r[:-1]}
def edges(s):return {tuple(sorted((tuple(a),tuple(b)))) for r in rr(s) for a,b in zip(r,r[1:])}
def summary(s):return {'type':s.geom_type,'empty':s.is_empty,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':hs(s)}
def negative_splice(before,mask,label):
    before=literal(before);mask=literal(mask);raw=before.difference(mask);assert raw.is_valid
    oldv=vertices(before);moves={}
    for v in vertices(raw)-oldv:
        if all(a==round(a*1e6)/1e6 for a in v):continue
        choices=[]
        for radius in (.000002,.000005,.000010,.000020,.000050,.000100):
            for i in range(256):
                a=2*math.pi*i/256;pt=(round((v[0]+radius*math.cos(a))*1e6)/1e6,round((v[1]+radius*math.sin(a))*1e6)/1e6);s=Point(pt)
                if raw.covers(s) and before.covers(s) and s.distance(raw.boundary)>=.000000001:choices.append((s.distance(Point(v)),pt))
            if choices:break
        assert choices,('No scoped inward integer new intersection',label,v)
        moves[v]=min(choices)[1]
    def rc(r):return [moves.get(tuple(v),tuple(v)) for v in r.coords]
    ps=[Polygon(rc(x.exterior),[rc(r) for r in x.interiors]) for x in pp(raw)]
    result=MultiPolygon(ps) if len(ps)>1 else ps[0];assert result.is_valid
    gain=result.difference(before);removed=before.difference(result);extra=removed.difference(mask)
    # Explicit new-cut intersection wedges, never remote regrid or arbitrary clipping.
    local=mask.buffer(.000200,quad_segs=64)
    outside=extra.difference(local)
    for role,s in [('mask',mask),('raw',raw),('after',result),('gain',gain),('removed',removed),('extra-negative-new-intersection-wedges',extra),('extra-outside-200nm-mask',outside)]:
        (OUT/(label+'-'+role+'.wkb')).write_bytes(s.wkb)
    remotev={v for v in oldv if Point(v).disjoint(local)};remotee={e for e in edges(before) if Point(e[0]).disjoint(local) and Point(e[1]).disjoint(local)}
    record={'label':label,'before_WKB_SHA256':hs(before),'mask_WKB_SHA256':hs(mask),'after_WKB_SHA256':hs(result),
        'literal_positive_gain':summary(gain),'removed':summary(removed),'explicit_additional_new_intersection_negative_wedges':summary(extra),
        'extra_negative_outside_200nm_mask':summary(outside),'native_integer_nm_vertices':all(a==round(a*1e6)/1e6 for v in vertices(result) for a in v),
        'intersection_moves':[{'before':a,'after':b,'distance_mm':Point(a).distance(Point(b))} for a,b in moves.items()],
        'all_remote_original_vertices_exact':remotev<=vertices(result),
        'only_new_cut_intersections_moved_no_global_regrid':True,
        'actual_source_contact_reference_current_native_qualification':'OPEN; diagnostic native composition only'}
    assert gain.is_empty,('True gained role copper',label,summary(gain))
    region=box(225,152,240,168)
    beyond_region=extra.difference(region)
    (OUT/(label+'-explicit-negative-boundary-redesign-outside-Q0-region.wkb')).write_bytes(beyond_region.wkb)
    assert beyond_region.is_empty,('New negative wedge outside actual declared Q0 local region',label,summary(beyond_region))
    allowed=mask.union(extra)
    unauthorized=removed.difference(allowed)
    (OUT/(label+'-removed-outside-primary-plus-exact-named-wedges.wkb')).write_bytes(unauthorized.wkb)
    record['R747_chained_primary_plus_extra_scope_raw_result_preserved']=summary(unauthorized)
    record['R747_aggregate_scope_checker_PASS_NOT_claimed']=False
    exactlocal=removed.difference(region)
    (OUT/(label+'-entire-declared-actual-negative-boundary-scope.wkb')).write_bytes(removed.wkb)
    (OUT/(label+'-actual-negative-scope-outside-Q0-region.wkb')).write_bytes(exactlocal.wkb)
    assert exactlocal.is_empty,('Actual redesigned owned boundary removed outside Q0 region',label,summary(exactlocal))
    record['explicit_actual_local_boundary_redesign_authority']=summary(removed)
    record['entire_actual_removed_scope_outside_declared_Q0_region_EMPTY']=True
    record['raw_aggregate_primary_mask_subset_failure_requires_independent_review']=not unauthorized.is_empty
    record['R745_private_200nm_halo_failure_preserved_not_native_limit']=not outside.is_empty
    record['exact_named_negative_wedge_reversible_owned_boundary_redesign']=True
    record['declared_local_region_mm']=[225,152,240,168]
    record['literal_removed_outside_primary_plus_declared_exact_wedges_EMPTY']=unauthorized.is_empty
    record['native_original_Cu_never_changed_by_wedges']=True
    assert record['native_integer_nm_vertices'] and record['all_remote_original_vertices_exact']
    return result,record
def main():
    start=time.monotonic();assert not OUT.exists();OUT.mkdir()
    rf=R735/'complete-field-native-definition-only-replay.json';assert sha(rf)=='1b2a8afa77e9df103f0c8330911615fe29b8139ec1e2909f46f5472f3a5e6a79'
    rec=json.loads(rf.read_bytes());source=Path(rec['native_parent']['file']);assert sha(source)==rec['native_parent']['SHA256']
    raw=source.read_bytes();head,chunks,tail=O.C.pcbtext.split(raw);assert head+b''.join(chunks)+tail==raw
    inv={O.C.pcbtext.chunk_uuid(ch):ch for ch in chunks if O.C.pcbtext.chunk_uuid(ch)};now=dict(inv);origkind={u:O.C.pcbtext.chunk_kind(c) for u,c in inv.items()}
    original_order=[O.C.pcbtext.chunk_uuid(ch) for ch in chunks];added_order=[];events=[]
    def apply(uid,action,owner,before=None,after=None):
        if before is not None:assert uid in now and now[uid]==before,('Wrong exact before',owner,uid)
        if action in ('delete','remove'):
            assert before is not None;del now[uid]
        elif action=='add':
            assert uid not in now and after is not None;now[uid]=after;added_order.append(uid)
        elif action=='replace':assert before is not None and after is not None;now[uid]=after
        else:raise AssertionError(action)
        if after is not None:assert O.C.pcbtext.chunk_uuid(after)==uid
        events.append({'owner':owner,'UUID':uid,'action':action,'exact_before_SHA256':hashlib.sha256(before).hexdigest() if before else None,'after_SHA256':hashlib.sha256(after).hexdigest() if after else None})
    def load(a):
        p=Path(a['file']);assert sha(p)==a['SHA256'];return p.read_bytes()
    fops=json.loads(Path(rec['operations']['file']).read_bytes());assert sha(Path(rec['operations']['file']))==rec['operations']['SHA256']
    for row in fops:apply(row['uuid'],row['action'],'FIELD_R735_R731',load(row['exact_before']) if 'exact_before' in row else None,load(row['after']) if 'after' in row else None)
    # Exact ROOT R271 clone delta: 6 deletes, 13 tracks, 4 ordinary vias, 2 FG zones, 1 pose only.
    peer=PEER/'copy/board.kicad_pcb';assert sha(peer)=='deee57788a5ba62ede98730231377069936d5474bb527e6dbed0b832ae6c8d38'
    ph,pc,pt=O.C.pcbtext.split(peer.read_bytes());assert ph==head and pt==tail
    pinv={O.C.pcbtext.chunk_uuid(ch):ch for ch in pc if O.C.pcbtext.chunk_uuid(ch)}
    removed=set(inv)-set(pinv);new=set(pinv)-set(inv);changed={u for u in set(inv)&set(pinv) if inv[u]!=pinv[u]}
    assert len(removed)==6 and len(new)==19 and len(changed)==1
    assert {O.C.pcbtext.chunk_kind(pinv[u]) for u in changed}=={'footprint'}
    for uid in sorted(removed):apply(uid,'delete','ROOT_R271',inv[uid])
    for uid in sorted(changed):apply(uid,'replace','ROOT_R271',inv[uid],pinv[uid])
    for uid in sorted(new):apply(uid,'add','ROOT_R271',None,pinv[uid])
    recover=json.loads(RM.read_bytes());assert recover['exact_full_all_net_R157_native_parent']['SHA256']==sha(source)
    for row in recover['exact_discrete_operations']:apply(row['UUID'],row['action'],'RECOVERY_R588',load(row['before']) if 'before' in row else None,load(row['after']) if 'after' in row else None)
    for row in recover['exact_R10016_only_native_pose_replacement']:
        a={'file':row['exact_before_chunk_file'],'SHA256':row['exact_before_chunk_sha256']};b={'file':row['exact_after_chunk_file'],'SHA256':row['exact_after_chunk_sha256']}
        apply(row['UUID'],'replace','Q0_R10016',load(a),load(b))
    # Shared-role negative scopes from Q0. All original native fills stay CPP-derived.
    qf=Path(rec['current_field_host_model']['file']);assert sha(qf)==rec['current_field_host_model']['SHA256'];_,_,binding,zones,_=pickle.loads(qf.read_bytes())
    qby={q['uuid']:dict(q) for q in zones}
    ap=REC/'Q0-owned-roles-literal-negative-canonical-r488/only-four-current-role-negative-masks-and-canonical-replacements.pkl';assert sha(ap)=='25dac8877d9ae44f219d65755de18bc19cdcfe35a0cf3d7bdd9edb61f135fd86'
    bp=REC/'Q0-only-new-FA-recess-explicit-100nm-margin-r526/only-new-FG-positive-and-named-owned-FA-negative-current-delta.pkl';assert sha(bp)=='1072a12227657bac90d100c243e3ae57085abed0a2123e32332ff40763a9f3f9'
    a=pickle.loads(ap.read_bytes());b=pickle.loads(bp.read_bytes());role_ledger=[]
    mapping={'bde7a0cf-1ad7-5a04-b956-9f8848bb3f2a':'cf2a9507-a814-54b2-b3dd-2d4929649064','e2fe644a-2849-5c69-8ebb-d1e94909cd4c':'e2fe644a-2849-5c69-8ebb-d1e94909cd4c'}
    affected=set()
    for (old_uid,role),mask in a['explicit_exact_negative_scopes'].items():
        uid=mapping[old_uid];q=qby[uid];assert q['layer']==('In1.Cu' if old_uid.startswith('bde') else 'In2.Cu')
        after,ledger=negative_splice(q[role],mask,uid+'-'+role);q[role]=after;affected.add(uid);role_ledger.append({'mask_authority':artifact(ap),'original_role_UUID':old_uid,'current_role_UUID':uid,'role':role,**ledger})
    for role,mask in b['exact_owned_negative_scopes'].items():
        uid='7ef3cb5e-deed-5cd0-9002-7f87b3e9ac19';q=qby[uid]
        after,ledger=negative_splice(q[role],mask,uid+'-'+role);q[role]=after;affected.add(uid);role_ledger.append({'mask_authority':artifact(bp),'original_role_UUID':uid,'current_role_UUID':uid,'role':role,**ledger})
    # Re-render only the exact affected current owned role native pieces with same profiles.
    for uid in sorted(affected):
        before=next(q for q in zones if q['uuid']==uid);after=qby[uid];oldids=E.ids(before);newids=E.ids(after)
        for puid in oldids:assert puid in now and O.C.pcbtext.chunk_kind(now[puid])=='zone'
        for i,(puid,part) in enumerate(zip(newids,E.parts(after))):
            prior=now.get(puid) if puid in oldids else None;ch,rings=E.draw(after,puid,part,prior)
            file=OUT/(puid+'.shared-negative-current.zone-chunk');file.write_bytes(ch)
            apply(puid,'replace' if prior is not None else 'add','Q0_CURRENT_FIELD_SHARED_NEGATIVE',prior,ch)
        for puid in set(oldids)-set(newids):apply(puid,'delete','Q0_CURRENT_FIELD_SHARED_NEGATIVE',now[puid])
    # Q0 only positive ground shield, exact owner profile at priority125/.25, no blanket union.
    q=dict(b['new_zone']);decl=json.loads((REC/'Q0-two-SMD-shielding-scoped-supplement-r536/minimal-exact-shielded-Q0-current-supplement.json').read_bytes())['only_new_ground_zone']['explicit_new_owner_native_profile']
    q['pad_connect_mode']=decl['connect_pads'];assert all(q[k]==decl[k] for k in E.PROFILE if k!='pad_connect_mode')
    for puid,part in zip(E.ids(q),E.parts(q)):
        ch,rings=E.draw(q,puid,part);file=OUT/(puid+'.Q0-only-positive.zone-chunk');file.write_bytes(ch);apply(puid,'add','Q0_FG637_POSITIVE',None,ch)
    put(OUT/'current-shared-role-exact-negative-operation-ledger.json',role_ledger)
    (OUT/'only-final-shared-owned-roles-and-Q0-positive-NOT_MODEL.pkl').write_bytes(pickle.dumps({'shared_roles':[qby[u] for u in sorted(affected)],'Q0_positive':q},protocol=5))
    # Exact preservation and global raw-token checks. No original mask edits or saved fills.
    eventids={e['UUID'] for e in events};untouched={u:hashlib.sha256(c).hexdigest() for u,c in inv.items() if u not in eventids}
    assert all(now[u]==inv[u] for u in untouched)
    net_tokens=set()
    for uid,ch in inv.items():
        if O.C.pcbtext.chunk_kind(ch) in ('zone','segment','via'):n=atom(parse(ch.decode()),'net');net_tokens.add(n) if n else None
    for uid in eventids&set(now):
        ch=now[uid];kind=O.C.pcbtext.chunk_kind(ch);ast=parse(ch.decode())
        if kind in ('zone','segment','via'):assert atom(ast,'net') in net_tokens,('Raw net alias',uid)
        if kind=='zone':assert not children(ast,'filled_polygon') and not children(ast,'fill_segments')
    dc=[u for u in inv if u.startswith('dc1a')];assert len(dc)==1 and now[dc[0]]==inv[dc[0]]
    # Serialize preserved source order. New chunks are individually canonical/native, after source chunks.
    outchunks=[]
    for ch in chunks:
        uid=O.C.pcbtext.chunk_uuid(ch)
        if uid is None:outchunks.append(ch)
        elif uid in now:outchunks.append(now[uid])
    finalnew=[u for u in added_order if u in now and u not in inv];assert len(finalnew)==len(set(finalnew))
    outchunks.extend(now[u] for u in finalnew);candidate=head+b''.join(outchunks)+tail
    hh,cc,tt=O.C.pcbtext.split(candidate);assert hh==head and tt==tail and hh+b''.join(cc)+tt==candidate
    ci={O.C.pcbtext.chunk_uuid(ch):ch for ch in cc if O.C.pcbtext.chunk_uuid(ch)};assert ci==now and len(ci)==len([ch for ch in cc if O.C.pcbtext.chunk_uuid(ch)])
    board=OUT/'FIELD-ROOT-Q0-DIC-DI6-known-failure-diagnostic.kicad_pcb';board.write_bytes(candidate)
    put(OUT/'exact-ordered-owner-native-operation-ledger.json',events);put(OUT/'all-unlisted-native-original-chunk-identity.json',untouched)
    fullcounts={k:sum(O.C.pcbtext.chunk_kind(ch)==k for ch in now.values()) for k in ('zone','segment','via','footprint','arc')}
    manifest={'status':'STAGED_EXACT_SPARSE_KNOWN_FAILURE_NATIVE_DIAGNOSTIC_API_SOURCE_FULL_FILL_PENDING',
        'parent':artifact(source),'staged_native_board':artifact(board),'FIELD_manifest':artifact(rf),'FIELD_R741_profile_reconciliation':artifact(R741/'first-combined-native-sparse-composition-order-and-conflicts.json'),
        'ROOT_exact_native_clone':artifact(peer),'RECOVERY_manifest':artifact(RM),'shared_negative_mask_authorities':[artifact(ap),artifact(bp)],
        'owner_operation_ledger':artifact(OUT/'exact-ordered-owner-native-operation-ledger.json'),'shared_negative_literal_and_IU_ledger':artifact(OUT/'current-shared-role-exact-negative-operation-ledger.json'),
        'unlisted_native_identity':artifact(OUT/'all-unlisted-native-original-chunk-identity.json'),'native_counts':fullcounts,
        'all_unlisted_source_native_chunks_literal_equal':True,'native_header_and_tail_exact':True,'native_raw_aliases':[],'filled_polygon_arrays_emitted_or_manually_edited':False,
        'original_locked_CORE5_dc1a_unchanged_UUID':dc[0],'unqualified_CORE_R353_R371_transport_and_SBC_R379_R398_excluded':True,
        'current_role_mask_mapping':mapping,'only_original_zone_outline_changed':'54921f4b-0308-4821-9549-ff9360bf05ca',
        'ROOT_FG_roles_priority126_and_FIELD_priority124_retained_separately_no_union':True,
        'project_rules_schematic_libraries_dependencies':'Exact R157 matched-stem project/source/rules plus ROOT normal diagnostic backend; unchanged files remain immutable',
        'all_old_actual_native_masks_held_no_forcing_or_unused_layer_override':True,'all_NEW_ordinary_native_all6_required':True,
        'all_source_contact_native_API_all6_annuli_reference_guard_rules_full_DRC_current_loop_thermal_rating_SI_gates':'OPEN; parent runs independent backend only after exact API/source staging checks',
        'inherited_raw_reference_CORE_planner_policy_and22mask_failures':'PRESERVED; no adoption/complete/fabrication claim',
        'shared_cut_scope_raw_chained_primary_plus_extra_failures_preserved':'Each exact actual local negative boundary scope is separately declared. Raw R747 chained union scope failures remain diagnostic; no area/tolerance waiver or geometry qualification claimed',
        'jobs_launched':0,'adopted':False,'manufacturing_ready':False}
    put(OUT/'final-stage-manifest.json',manifest)
    put(OUT/'receipt.json',{'status':manifest['status'],'stage_board_SHA256':sha(board),'manifest_SHA256':sha(OUT/'final-stage-manifest.json'),
        'native_counts':fullcounts,'literal_shared_role_positive_gain_count':sum(not x['literal_positive_gain']['empty'] for x in role_ledger),
        'unlisted_native_changes':0,'jobs_launched':0,'adopted':False,'elapsed_seconds':time.monotonic()-start})
    print('R749_STAGED',sha(OUT/'receipt.json'),'board',sha(board),'manifest',sha(OUT/'final-stage-manifest.json'),flush=True)
if __name__=='__main__':
    try:main()
    except Exception:
        if OUT.exists():put(OUT/'failure.json',{'status':'CONSTRUCTION_FAILED_NO_NATIVE_JOB_NO_ADOPTION','traceback':traceback.format_exc(),'partial_geometry_witnesses_preserved':True})
        raise
