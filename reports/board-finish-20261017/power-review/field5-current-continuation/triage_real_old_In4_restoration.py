"""Exact bounded full-sheet restoration control, with coupled ground gates.

The host negative cuts are explicitly prospective geometry. They are never
presented as native repour results, adopted copper, or an accepted sparse packet.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
from collections import defaultdict
import hashlib,importlib.util,json,math,pickle,sys,time
import shapely
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
CONT=ROOT/'reports/board-finish-20261011/continuation-r2';FIELD=CONT/'field-power'
for p in(CONT/'coupled-recovery',FIELD,CONT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import physical_reference_losses_r3_zero_r208 as RF
import trace_actual_field5_replacement as T
OUT=HERE/'old-In4-restoration-triage-r1'
ACTUAL=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
OLD=FIELD/'R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763'
COMPOSE=ROOT/'reports/board-finish-20261017/combined-route-stage-r1'
UID='61cb8179-7754-5031-bbea-0da464bf816f';LY='In4.Cu';FG='/motherboard_motors/FIELD_GND';LG='/LOGIC_GND'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def polys(records):return K.L.poly([[r[0],r[1]if len(r)>1 else[]]for r in records])
def records(s):return T.records(s)
def summary(s):return {'empty':s.is_empty,'area_mm2':s.area,'bounds':list(s.bounds)if not s.is_empty else[],'sha256':hashlib.sha256(s.wkb).hexdigest()}
def body(q):
    if q['kind']=='via':return Point(q['at_IU'][0]/1e6,q['at_IU'][1]/1e6).buffer(max(q['diameters_IU'].values())/2e6,quad_segs=128)
    assert q['kind']=='segment',q['kind'];return LineString([[v/1e6 for v in q['start_IU']],[v/1e6 for v in q['end_IU']]]).buffer(q['width_IU']/2e6,quad_segs=128)

def main():
    assert not OUT.exists();OUT.mkdir();started=time.monotonic()
    oldboard=CONT/'R155-known-reference-native-diagnostic-r157/copy/board.kicad_pcb';pcbhelper=ROOT/'reports/board-finish-20261011/parity-repair/root106/tools/pcbtext.py'
    files=[OLD/'actual-full-R157-before-model.pkl',ACTUAL/'actual-combined-full-after-model.pkl',ACTUAL/'actual-combined-full-after-all-net-groups.pkl',COMPOSE/'construction-receipt.json',COMPOSE/'all-copper-expected.json',FIELD/'FIELD-ROOT-distinct-priority-exact-native-ownership-and-sparse-role-handoff-r741/receipt.json',FIELD/'REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r368/three-bank-strict-zero-reference-rows.json',FIELD/'FIELD5-current-reference-envelope-correction-r238/receipt.json',FIELD/'FIELD5-source-plane-exact-owned-edge-negative-redesign-current-r543/receipt.json',FIELD/'construct_FIELD5_inner_reference_safe_replacement_r383.py',oldboard,pcbhelper,Path(__file__),Path(K.__file__),Path(RF.__file__),Path(T.__file__)]
    inputs={str(p):sha(p)for p in files};old=pickle.loads(files[0].read_bytes());g=pickle.loads(files[1].read_bytes());groups=pickle.loads(files[2].read_bytes());composition=json.loads(files[3].read_text());expected=json.loads(files[4].read_text());assert composition['candidate_SHA256']==expected['board_sha256']=='758f3968589948ce6550d30586818a5ffaa673d8dad7fe8c9a7e402598cff1ad'
    z=next(z for z in old['zones']if z['uuid']==UID);assert not any(z['uuid']==UID for z in g['zones']);intent=unary_union(polys(z['outline']));native=unary_union(K.L.poly(z['fills'][LY]));ctx=K.hole_context(g);holes,ht=ctx;physical=native.difference(unary_union([holes[int(i)]for i in ht.query(native,predicate='intersects')]))
    for name,s in(('old-exact-native-intent',intent),('old-exact-native-fill',native),('old-physical-fill-with-current-holes',physical)):(OUT/(name+'.wkb')).write_bytes(s.wkb)
    spec=importlib.util.spec_from_file_location('exact_old_board',pcbhelper);P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P);_,chunks,_=P.split(oldboard.read_bytes());oldchunk=next(c for c in chunks if P.chunk_uuid(c)==UID);(OUT/'original-native-R157-zone-intent.exact-chunk').write_bytes(oldchunk)
    # Preserve the withdrawal history as a raw failure record, without claiming
    # that every R368 reference loss was caused by this single sheet.
    history=json.loads(files[6].read_text());historic=[r for a in history for r in a['strict_ZERO_retained_old_reference_losses']if a['net']==FG and r['net']=='/motherboard_power_entry/FA_SHDN_CONTACT']
    put('withdrawal-history.json',{'R741_scope':'Explicit withdrawn failed In4 role; R543 is a distinct source-qualified In2 role, never scope-translated.','R383_scope':'Rejected In4 feed replaced with inner-layer nominee; only explicit same-domain FG cuts eligible, all other current fills/discrete items hard.','R368_specific_FA_SHDN_reference_failures':historic,'R368_is_multi_change_failure_not_single_cause_proof':True,'old_zone_metadata':{k:v for k,v in z.items()if k not in('outline','fills')},'old_intent':summary(intent),'old_native':summary(native),'old_current_drilled_Cu':summary(physical)})
    rec,trees=K.F.build(g,layers={LY});copper_checks=[];fill_controls=[];discrete_bad=[];hard=[];guard_masks={};domain=g['domains_normalized'][T.NET]
    for j in trees[LY].query(intent.buffer(2)):
        q=rec[LY][int(j)]
        if K.L.norm(q['net'])==T.NET:continue
        gap=.15 if q['domain']==domain else.6
        if q['kind']=='fill':gap=max(gap,float(next(a for a in g['zones']if a['uuid']==q['uuid'])['clearance_mm']))
        required=gap+.025;actual=physical.distance(q['shape']);row=T.describe(q)|{'net':K.L.norm(q['net']),'native_minimum_Cu_gap_mm':gap,'host_guarded_gap_mm':required,'actual_old_physical_Cu_gap_mm':actual,'native_gap_pass':actual>=gap,'host_guard_pass':actual>=required}
        if actual<required:
            row.update(old_native_intersection_mm2=native.intersection(q['shape']).area,old_intent_intersection_mm2=intent.intersection(q['shape']).area)
            if q['kind']=='fill':fill_controls.append(row)
            else:discrete_bad.append(row)
        copper_checks.append(row)
        if q['kind']=='fill':guard_masks[q['uuid']]=intent.buffer(required,quad_segs=128)
        hard.append(q['shape'].buffer(required,quad_segs=128))
    # Foreign fills kept fixed: clipping may leave islands but cannot be assumed
    # to retain source-to-target current continuity.
    fixed_safe=physical.difference(unary_union(hard));(OUT/'old-sheet-clipped-to-all-fixed-current-In4-Cu.wkb').write_bytes(fixed_safe.wkb)
    sourcevia=next(v for v in g['vias']if v['uuid']==T.T2);targetvia=next(v for v in g['vias']if v['uuid']==T.T1)
    contacts={}
    for key,v in(('source',sourcevia),('target',targetvia)):
        ann=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=128).difference(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128));contacts[key]=ann.intersection(fixed_safe)
    components=RF.parts(fixed_safe);same_fixed=any(p.intersection(contacts['source']).area>1e-10 and p.intersection(contacts['target']).area>1e-10 for p in components)
    put('fixed-native-Cu-restoration-geometry.json',{'all_checks':copper_checks,'discrete_guard_failures':discrete_bad,'foreign_fill_conflicts':fill_controls,'native_minimum_and_25um_guard_are_both_reported':True,'clipped_old_sheet':summary(fixed_safe),'source_contact':summary(contacts['source']),'target_contact':summary(contacts['target']),'same_finite_connected_physical_component':same_fixed,'no_tiny_zone_or_annular_reclassification':True})
    # Explicit prospective low-priority ground cuts needed by restoring the full
    # higher-priority old FIELD5 intent. Native refill behavior remains open.
    zones=[];cuts=[];cut_by_net=defaultdict(list)
    for q in g['zones']:
        if LY not in q['fills']or K.L.norm(q['net'])==T.NET:zones.append(q);continue
        gap=.15 if q['domain']==domain else.6;gap=max(gap,float(q['clearance_mm']));mask=intent.buffer(gap+.025,quad_segs=128);oldfill=unary_union(K.L.poly(q['fills'][LY]));cut=oldfill.intersection(mask)
        if cut.is_empty:zones.append(q);continue
        remain=oldfill.difference(mask);native_intent=unary_union(polys(q['outline']));intent_cut=native_intent.intersection(mask)
        row={'uuid':q['uuid'],'net':K.L.norm(q['net']),'priority':q['priority'],'native_local_clearance_mm':q['clearance_mm'],'guarded_Cu_gap_mm':gap+.025,'old_actual_Cu':summary(oldfill),'prospective_Cu_removed':summary(cut),'prospective_literal_intent_removed':summary(intent_cut),'prospective_remaining_Cu':summary(remain),'prospective_not_native':True};cuts.append(row);cut_by_net[K.L.norm(q['net'])].append(cut)
        (OUT/(q['uuid']+'-prospective-native-Cu-cut.wkb')).write_bytes(cut.wkb);zones.append(q|{'fills':q['fills']|{LY:records(remain)},'prospective_not_native':True})
    assert set(cut_by_net)<={LG,FG};zones.append(z|{'fills':{LY:records(physical)},'prospective_restoration_of_real_old_native_Cu':True});prospective=g|{'zones':zones};put('explicit-ground-Cu-and-intent-cut-obligations.json',cuts)
    # Every new/deleted 758f copper primitive is independently checked against
    # this restoration scope; native AFTER of that composition is still needed.
    peers=[]
    for op in composition['operations']:
        if op['action']not in('add','remove')or op['UUID']not in expected['copper']:
            if op['action']=='remove':
                # Retired primitives outside scope are established by their
                # exact source chunks in the construction receipt, not assumed.
                peers.append({'uuid':op['UUID'],'action':'remove','group':op['group'],'not_in_after_expected_Cu':True})
            continue
        q=expected['copper'][op['UUID']];shape=body(q);layers=list(K.LAYERS)if q['kind']=='via'else[q['layer']];peers.append({'uuid':op['UUID'],'action':op['action'],'group':op['group'],'kind':q['kind'],'layers':layers,'distance_to_old_intent_mm':shape.distance(intent),'within_2mm_of_old_intent':shape.distance(intent)<2,'actual_new_native_flash_and_fill':'OPEN'})
    assert not any(r.get('within_2mm_of_old_intent')for r in peers);put('758f-exact-addition-geometry-scope-check.json',peers)
    sources=[];partitions=[];reference=[];new_groups={};rootmap={LG:('J11001','2'),FG:('J11003','2'),T.NET:('L11003','2')}
    for net in(LG,FG,T.NET):
        put('status.json',{'phase':'PROSPECTIVE_EXPLICIT_RESTORATION_PHYSICAL_GROUND_GATES','net':net,'native_jobs':0})
        new_groups[net]=K.physical(prospective,net,ctx)[1];a=K.root(groups[net],*rootmap[net]);b=K.root(new_groups[net],*rootmap[net]);lost=K.keys(a)-K.keys(b);oldpads={(q['ref'],q['pin'])for q in a if q['kind']=='pad'};newpads={(q['ref'],q['pin'])for q in b if q['kind']=='pad'};sources.append({'net':net,'source':'.'.join(rootmap[net]),'before_source_key_count':len(K.keys(a)),'after_source_key_count':len(K.keys(b)),'source_keys_lost':[list(k)for k in sorted(lost)],'source_named_pads_lost':[list(k)for k in sorted(oldpads-newpads)]})
        rows,bad=K.contact_losses(groups[net],new_groups[net]);partitions.append({'net':net,'before_groups':len(groups[net]),'after_groups':len(new_groups[net]),'old_relationship_losses':bad,'all_group_relation_count':len(rows)})
        if net in(LG,FG):
            before_ref=K.source_refs(a);after_ref=K.source_refs(b);rr,proof=RF.audit(g,before_ref,after_ref,net);reference.append({'net':net,'strict_zero_reference_losses':rr,'proof':proof})
        put('source-checkpoint.json',sources);put('partition-checkpoint.json',partitions);put('reference-checkpoint.json',reference);print(json.dumps({'net':net,'lost_source_keys':len(lost),'lost_source_pads':len(oldpads-newpads),'partition_losses':len(bad),'old_reference_losses':len(rr)if net in(LG,FG)else None}),flush=True)
    result={'utc':datetime.now(timezone.utc).isoformat(),'status':'REAL_OLD_IN4_RESTORATION_TRIAGE_NOT_ADOPTED_ALL_RAW_CONSEQUENCES_RETAINED','input_sha256':inputs,'restored_UUID':UID,'real_old_intent':summary(intent),'real_old_native_fill':summary(native),'real_old_physical_Cu':summary(physical),'current_R299_discrete_guard_failure_count':len(discrete_bad),'foreign_fill_conflict_piece_count':len(fill_controls),'full_old_restore_requires_explicit_foreign_ground_Cu_intent_edits':True,'fixed_native_foreign_Cu_clipped_source_to_target_continuity':same_fixed,'prospective_ground_cut_obligations':cuts,'prospective_source_rows':sources,'prospective_partition_rows':partitions,'prospective_old_reference_rows':reference,'all_results_are_host_geometry_controls_not_native_AFTERMATH':True,'new_758f_native_fill_and_reference_source_behavior':'OPEN; exact additions are spatially disjoint, but actual full native repour may change remote fills','loads_current_material_thermal_and_other_banks_preserved':True,'no_tiny_annular_zone_patch':True,'native_jobs':0,'board_written':False,'sparse_packet_frozen':False,'adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-started}
    assert all(sha(Path(p))==h for p,h in inputs.items());put('receipt.json',result);put('status.json',{'phase':'COMPLETE_RAW_FULL_RESTORE_CONSEQUENCES_NOT_ADOPTED','seconds':result['elapsed_seconds']});print(json.dumps({'status':result['status'],'fixed_safe_continuity':same_fixed,'seconds':result['elapsed_seconds']}),flush=True)

if __name__=='__main__':main()
