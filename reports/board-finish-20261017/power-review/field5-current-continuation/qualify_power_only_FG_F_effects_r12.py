"""Isolate new F power-body effects before the separately unqualified FA transfer.

No FA new drill or return is silently assumed harmless. This stage inventories
power-only FG/F negative targets and all old rooted source/partition/reference
consequences; the full coupled signal-transfer target must be requalified later.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math,pickle,sys,time,uuid
import shapely
from shapely.geometry import LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];CONT=ROOT/'reports/board-finish-20261011/continuation-r2';ACTUAL=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763';CAND=HERE/'F-parallel-offset-FA-landing-refined-r10';OUT=HERE/'power-only-FG-F-effects-host-r12'
for p in(CONT/'coupled-recovery',CONT/'field-power',CONT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import physical_reference_losses_r3_zero_r208 as RF
import trace_actual_field5_replacement as T
FG='/motherboard_motors/FIELD_GND';LY='F.Cu';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def sm(s):return{'empty':s.is_empty,'area_mm2':s.area,'bounds':list(s.bounds)if not s.is_empty else[],'sha256':hashlib.sha256(s.wkb).hexdigest()}
def main():
    assert not OUT.exists();OUT.mkdir();started=time.monotonic();files=[ACTUAL/'actual-combined-full-after-model.pkl',ACTUAL/'actual-combined-full-after-all-net-groups.pkl',CAND/'receipt.json',HERE/'conditional-new-F-real-source-target-two-level-r11/receipt.json',Path(__file__)];inputs={str(p):sha(p)for p in files};g=pickle.loads(files[0].read_bytes());old=pickle.loads(files[1].read_bytes());r=json.loads(files[2].read_text());points=[[round(x,6),round(y,6)]for x,y in r['path_mm']];axis=LineString(points);body=axis.buffer((.25+1e-8)/math.cos(math.pi/512),quad_segs=128);records,_=K.F.build(g,nets={T.NET},layers={LY});fieldCu=unary_union([q['shape']for q in records[LY]]);positive=body.difference(fieldCu);zones=[];cuts=[]
    for z in g['zones']:
        if K.L.norm(z['net'])!=FG or LY not in z['fills']:zones.append(z);continue
        before=unary_union(K.L.poly(z['fills'][LY]));gap=max(float(z['clearance_mm']),.15)+.0251;mask=positive.buffer(gap,quad_segs=128);negative=before.intersection(mask)
        if negative.is_empty:zones.append(z);continue
        after=before.difference(mask);zones.append(z|{'fills':z['fills']|{LY:T.records(after)},'power_only_host_target_not_native':True});cuts.append({'uuid':z['uuid'],'actual_target_negative':sm(negative),'target_gap_mm':gap,'native_original_profile':{k:v for k,v in z.items()if k not in('fills','outline')},'native_source_negative_serialization_and_minwidth_band_effects':'OPEN'});(OUT/(z['uuid']+'-FG-F-native-Cu-negative-target.wkb')).write_bytes(negative.wkb)
    tracks=[]
    for i,(a,b)in enumerate(zip(points,points[1:])):tracks.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/R299/FIELD5/wide-F-r12/'+str(i))),'net':T.NET,'layer':LY,'a':a,'b':b,'w':.5})
    h=g|{'zones':zones,'tracks':g['tracks']+tracks,'power_only_host_target_FA_transfer_holes_and_return_not_applied':True};ctx=K.hole_context(h);new={};sources=[];partitions=[];refs=[]
    for net,ref,pin in((FG,'J11003','2'),(T.NET,'L11003','2')):
        new[net]=K.physical(h,net,ctx)[1];a=K.root(old[net],ref,pin);b=K.root(new[net],ref,pin);lost=K.keys(a)-K.keys(b);oldpads={q['ref']+'.'+q['pin']for q in a if q['kind']=='pad'};newpads={q['ref']+'.'+q['pin']for q in b if q['kind']=='pad'};sources.append({'net':net,'old_source_keys_lost':[list(x)for x in sorted(lost)],'old_source_pads_lost':sorted(oldpads-newpads),'newly_source_joined_existing_pad_nodes':sorted(newpads-oldpads)});relation,bad=K.contact_losses(old[net],new[net]);partitions.append({'net':net,'old_partition_losses':bad,'before_groups':len(old[net]),'after_groups':len(new[net])})
        if net==FG:rr,proof=RF.audit(g,K.source_refs(a),K.source_refs(b),FG);refs.append({'net':net,'raw_old_reference_losses':rr,'proof':proof})
        put('source-checkpoint.json',sources);put('partition-checkpoint.json',partitions);put('reference-checkpoint.json',refs);print(json.dumps({'net':net,'lost_keys':len(lost),'lost_partitions':len(bad),'new_pad_nodes':sorted(newpads-oldpads),'raw_ref_losses':len(rr)if net==FG else None}),flush=True)
    oldmetal=[q for xs in old[FG]for q in xs if q['kind']!='fill'and q['layer']==LY];tree=STRtree([q['shape']for q in oldmetal]);afterfill={}
    for xs in new[FG]:
        for q in xs:
            if q['kind']=='fill'and q['layer']==LY:afterfill.setdefault(q['uuid'],[]).append(q['shape'])
    changed={c['uuid']for c in cuts};direct=[];failed=[]
    for xs in old[FG]:
        for f in xs:
            if f['kind']!='fill'or f['layer']!=LY or f['uuid']not in changed:continue
            for j in tree.query(f['shape'],predicate='intersects'):
                q=oldmetal[int(j)];a=q['shape'].intersection(f['shape']).area
                if a<=0:continue
                b=q['shape'].intersection(unary_union(afterfill.get(f['uuid'],[]))).area;row={'zone_UUID':f['uuid'],'metal':T.describe(q),'old_positive_finite_overlap_mm2':a,'new_positive_finite_overlap_mm2':b,'positive_contact_retained':b>0};direct.append(row)
                if b<=0:failed.append(row)
    put('all_positive_finite_old_FG_F_direct_contacts.json',{'rows':direct,'failures':failed});(OUT/'power-only-target-model.pkl').write_bytes(pickle.dumps(h,protocol=5));(OUT/'power-only-two-net-target-groups.pkl').write_bytes(pickle.dumps(new,protocol=5));put('native-quantized-power-track-operations.json',tracks);put('FG-F-negative-targets.json',cuts);ok=all(not q['old_source_keys_lost']for q in sources)and all(not q['old_partition_losses']for q in partitions)and all(not q['raw_old_reference_losses']for q in refs)and not failed
    result={'utc':datetime.now(timezone.utc).isoformat(),'status':'POWER_BODY_ONLY_OLD_SOURCE_CONTACT_REFERENCE_GATES_PASS_FULL_FA_AND_NATIVE_COUPLED_GATES_OPEN'if ok else'POWER_BODY_ONLY_RAW_SOURCE_CONTACT_REFERENCE_FAIL_NOT_PROMOTED','input_sha256':inputs,'source_rows':sources,'partition_rows':partitions,'reference_rows':refs,'all_finite_old_FG_F_contact_failures':failed,'new_power_tracks':len(tracks),'nominal_width_mm':.5,'length_mm':axis.length,'positive_upper_envelope_new_power_Cu':sm(positive),'FG_F_actual_negative_target_mm2':sum(c['actual_target_negative']['area_mm2']for c in cuts),'changed_FG_F_native_roles':len(cuts),'FA_old_signal_retirements_new_via_and_paired_return_holes_and_all_layer_clearance_cuts':'NOT_APPLIED; separate pending coupled obligation, no silent pass','original_In2_all_Cu_and_source_intents_unchanged':True,'all_simultaneous12_motor_and_other_power_planning_limits_preserved':True,'newly_joined_loads_must_be_counted_not_zeroed':True,'full_signed_FG_return_current_path_source_electrode_spreading_and_thermal':'OPEN','native_source_negative_serialization_positive_retention_minwidth_DRC_reference_SI_material_voltage_budget_and_full_KCL':'OPEN','native_jobs':0,'adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-started};put('receipt.json',result);print(json.dumps({'status':result['status'],'negative_FG_mm2':result['FG_F_actual_negative_target_mm2'],'roles':len(cuts),'seconds':result['elapsed_seconds']}),flush=True)
if __name__=='__main__':main()
