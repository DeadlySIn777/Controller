"""Rebuild the finite 50um FIELD5 widening against genuine saved R299.

The 100um constructor failed literal old-intent retention. Only the smaller
separately rechecked construction is used here; all native/current gates stay
distinct from these prospective host source/contact/reference checks.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
from collections import defaultdict
import hashlib,json,pickle,sys,time
import shapely
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
CONT=ROOT/'reports/board-finish-20261011/continuation-r2'
for p in(CONT/'coupled-recovery',CONT/'field-power',CONT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import physical_reference_losses_r3_zero_r208 as RF
import trace_actual_field5_replacement as T
OUT=HERE/'50um-current-In2-widening-host-qualification-r1'
CON=HERE/'bounded-current-In2-widening-construction-r2'
ACTUAL=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
FG='/motherboard_motors/FIELD_GND';LY='In2.Cu';ZID='5655cb90-5071-5499-8df8-2b73c23dc1fa'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def summary(s):return{'empty':s.is_empty,'area_mm2':s.area,'bounds':list(s.bounds)if not s.is_empty else[],'sha256':hashlib.sha256(s.wkb).hexdigest()}
def outline(z):return unary_union(K.L.poly([[r[0],r[1:]]for r in z['outline']]))

def main():
    assert not OUT.exists();OUT.mkdir();started=time.monotonic()
    files=[ACTUAL/'actual-combined-full-after-model.pkl',ACTUAL/'actual-combined-full-after-all-net-groups.pkl',CON/'checkpoint.json',CON/'50um-support-patch.wkb',CON/'50um-new-only-In2-positive.wkb',CON/'50um-full-In2-proposed-intent.wkb',HERE/'construct_bounded_current_In2_widening_r2.py',HERE/'construct_bounded_current_In2_widening.py',Path(__file__),Path(K.__file__),Path(RF.__file__)]
    inputs={str(p):sha(p)for p in files};g=pickle.loads(files[0].read_bytes());oldgroups=pickle.loads(files[1].read_bytes());row=json.loads(files[2].read_text())[0];assert row['maximum_lateral_growth_mm']==.05;support,delta,intent=[shapely.from_wkb(p.read_bytes())for p in files[3:6]];fz=next(z for z in g['zones']if z['uuid']==ZID);oldintent=outline(fz);oldCu=unary_union(K.L.poly(fz['fills'][LY]));oldroot=K.root(oldgroups[T.NET],'L11003','2');oldsource=unary_union([q['shape']for q in oldroot if q['kind']=='fill'and q['layer']==LY]);assert support.difference(intent).is_empty;assert oldintent.difference(intent).is_empty;assert intent.difference(oldintent).difference(support).is_empty;assert support.difference(oldCu).equals(delta);assert all(p.intersection(oldsource).area>1e-8 for p in RF.parts(support))
    put('bounded-constructor-recheck.json',{'growth_mm':.05,'support':summary(support),'actual_new_Cu_target':summary(delta),'field_intent':summary(intent),'literal_all_old_field_intent_retained':True,'every_support_patch_finite_source_Cu_overlap_mm2':[p.intersection(oldsource).area for p in RF.parts(support)],'100um_constructor':'REJECTED; not used.','no_drills_or_component_moves':True})
    zones=[];cuts=[];masks={}
    for z in g['zones']:
        if z['uuid']==ZID:
            zones.append(z|{'fills':z['fills']|{LY:T.records(oldCu.union(support))},'host_desired_not_native':True});continue
        if LY not in z['fills']or K.L.norm(z['net'])!=FG:zones.append(z);continue
        gap=max(float(fz['clearance_mm']),float(z['clearance_mm']),.15)+.0251;mask=delta.buffer(gap,quad_segs=128);before=unary_union(K.L.poly(z['fills'][LY]));cut=before.intersection(mask)
        if cut.is_empty:zones.append(z);continue
        masks[z['uuid']]=mask;after=before.difference(mask);zones.append(z|{'fills':z['fills']|{LY:T.records(after)},'host_desired_not_native':True});cuts.append({'uuid':z['uuid'],'guarded_gap_mm':gap,'old_native_Cu':summary(before),'desired_Cu_removed':summary(cut),'desired_remaining_Cu':summary(after),'old_literal_intent_cut_required':summary(outline(z).intersection(mask))});(OUT/(z['uuid']+'-desired-Cu-negative-mask.wkb')).write_bytes(mask.wkb)
    h=g|{'zones':zones,'prospective_host_not_native_after':True};put('exact-FG-In2-cut-obligations.json',cuts);(OUT/'prospective-widened-model.pkl').write_bytes(pickle.dumps(h,protocol=5))
    unchanged=[]
    for net in sorted({K.L.norm(z['net'])for z in g['zones']}-{FG,T.NET}):
        assert [z for z in g['zones']if K.L.norm(z['net'])==net]==[z for z in h['zones']if K.L.norm(z['net'])==net];unchanged.append(net)
    assert all(g[k]==h[k]for k in g if k!='zones');put('unchanged-net-physical-record-identity.json',{'zone_net_count':len(unchanged),'nets':unchanged,'every_pad_track_via_hole_rule_outline_and_all_other_native_records_exact':True,'no_new_holes_or_flash_overrides':True,'unchanged_physical_graphs_by_exact_arrays':True})
    # Independent positive-target clearance screen uses upper via circles and
    # extra5um reservations for native pad/arc polygons.
    rec,trees=K.F.build(g,layers={LY});domain=g['domains_normalized'][T.NET];errors=[];near=[]
    for j in trees[LY].query(delta.buffer(2)):
        q=rec[LY][int(j)];net=K.L.norm(q['net'])
        if net==T.NET or(q['kind']=='fill'and net==FG):continue
        gap=.15 if q['domain']==domain else.6
        if q['kind']=='fill':gap=max(gap,float(next(z for z in g['zones']if z['uuid']==q['uuid'])['clearance_mm']))
        d=delta.distance(q['shape']);reservation=.005 if q['kind']=='pad'or(q['kind']=='track'and q['source'].get('m')is not None)else 0
        if q['kind']=='via':
            v=q['source'];d=delta.distance(Point(v['x'],v['y']))-v['d']/2
        if q['kind']=='track'and q['source'].get('m')is None:
            t=q['source'];d=delta.distance(LineString([t['a'],t['b']]))-t['w']/2
        guaranteed=d-reservation;check=T.describe(q)|{'net':net,'geometric_gap_mm':d,'native_polygon_reservation_mm':reservation,'guaranteed_gap_mm':guaranteed,'required_mm':gap+.025}
        if guaranteed<gap+.2:near.append(check)
        if guaranteed<gap+.025:errors.append(check)
    put('new-positive-target-Cu-clearance-controls.json',{'errors':errors,'near_constraints':near,'native_after_required':True})
    ctx=K.hole_context(h);sources=[];partitions=[];references=[];newgroups={}
    for net,ref,pin in((FG,'J11003','2'),(T.NET,'L11003','2')):
        put('status.json',{'phase':'ACTUAL_SAVED_SOURCE_OLD_CONTACT_REFERENCE_REQUALIFICATION','net':net,'native_jobs':0});newgroups[net]=K.physical(h,net,ctx)[1];a=K.root(oldgroups[net],ref,pin);b=K.root(newgroups[net],ref,pin);lost=K.keys(a)-K.keys(b);sources.append({'net':net,'source':ref+'.'+pin,'old_source_keys':len(K.keys(a)),'new_source_keys':len(K.keys(b)),'old_source_keys_lost':[list(k)for k in sorted(lost)],'old_source_pads_lost':sorted({q['ref']+'.'+q['pin']for q in a if q['kind']=='pad'}-{q['ref']+'.'+q['pin']for q in b if q['kind']=='pad'})});relation,bad=K.contact_losses(oldgroups[net],newgroups[net]);partitions.append({'net':net,'before_group_count':len(oldgroups[net]),'after_group_count':len(newgroups[net]),'old_partition_losses':bad,'all_prior_group_relations_checked':len(relation)})
        if net==FG:
            rr,proof=RF.audit(g,K.source_refs(a),K.source_refs(b),net);references.append({'net':net,'strict_zero_old_reference_losses':rr,'proof':proof})
        put('source-checkpoint.json',sources);put('partition-checkpoint.json',partitions);put('reference-checkpoint.json',references);print(json.dumps({'net':net,'source_keys_lost':len(lost),'old_partitions_lost':len(bad),'old_ref_losses':len(rr)if net==FG else None}),flush=True)
    # Direct positive finite contacts of every changed FG native role are
    # inventoried; source membership alone cannot substitute for this check.
    direct=[];directbad=[];metal=[q for xs in oldgroups[FG]for q in xs if q['kind']!='fill'and q['layer']==LY];tree=STRtree([q['shape']for q in metal]);afterfill=defaultdict(list)
    for xs in newgroups[FG]:
        for q in xs:
            if q['kind']=='fill'and q['layer']==LY:afterfill[q['uuid']].append(q['shape'])
    for xs in oldgroups[FG]:
        for f in xs:
            if f['kind']!='fill'or f['layer']!=LY or f['uuid']not in masks:continue
            for j in tree.query(f['shape'],predicate='intersects'):
                q=metal[int(j)];oldarea=q['shape'].intersection(f['shape']).area
                if oldarea<=1e-10:continue
                newarea=q['shape'].intersection(unary_union(afterfill[f['uuid']])).area;check={'zone_UUID':f['uuid'],'metal':T.describe(q),'old_finite_overlap_mm2':oldarea,'new_finite_overlap_mm2':newarea,'retained':newarea>1e-10};direct.append(check)
                if not check['retained']:directbad.append(check)
    put('all-changed-FG-finite-native-direct-contacts.json',{'rows':direct,'failures':directbad})
    fieldroot=K.root(newgroups[T.NET],'L11003','2');sheet=unary_union([q['shape']for q in fieldroot if q['kind']=='fill'and q['layer']==LY]);(OUT/'prospective-source-rooted-In2-sheet.wkb').write_bytes(sheet.wkb)
    physical_ok=not errors and not directbad and all(not r['old_source_keys_lost']for r in sources)and all(not r['old_partition_losses']for r in partitions)and all(not r['strict_zero_old_reference_losses']for r in references)
    result={'utc':datetime.now(timezone.utc).isoformat(),'status':'50UM_PHYSICAL_WIDENING_HOST_SOURCE_CONTACT_REFERENCE_PASS_NATIVE_AND_BOTH_RAIL_CURRENT_OPEN'if physical_ok else'50UM_PHYSICAL_WIDENING_RAW_HOST_GATE_FAIL_NOT_PROMOTED','input_sha256':inputs,'support':summary(support),'actual_new_Cu_target':summary(delta),'proposed_current_source_In2_sheet':summary(sheet),'same_domain_FG_In2_negative_Cu_mm2':sum(q['desired_Cu_removed']['area_mm2']for q in cuts),'source_rows':sources,'partition_rows':partitions,'reference_rows':references,'new_positive_Cu_clearance_errors':errors,'changed_FG_direct_contact_failures':directbad,'unchanged_NETS_physical_records_exact':len(unchanged),'new_drills':0,'configured_electrical_limits_and_all12_motor_aux_and_other_loads_unchanged':True,'FIELD5_matched_resistance_FG_signed_return_capacity_material_thermal_and_native_after':'OPEN; no physical current rating or adoption implied','new_native_zone_intent_serialization_and_strict_inward_FG_negative_splices':'OPEN; no unsafe native packet emitted','native_jobs':0,'board_written':False,'sparse_packet_frozen':False,'adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-started}
    assert all(sha(Path(p))==h for p,h in inputs.items());put('receipt.json',result);put('status.json',{'phase':'COMPLETE_HOST_ONLY_CURRENT_NATIVE_OPEN','seconds':result['elapsed_seconds']});print(json.dumps({'status':result['status'],'positive_mm2':delta.area,'FG_cut_mm2':result['same_domain_FG_In2_negative_Cu_mm2'],'seconds':result['elapsed_seconds']}),flush=True)

if __name__=='__main__':main()
