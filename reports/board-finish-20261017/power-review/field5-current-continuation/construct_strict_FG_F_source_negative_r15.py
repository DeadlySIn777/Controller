"""Exact native source-negative reserve for the single affected FG/F zone.

Preserve its old profile and book all native filled-band targets separately.
The hypothetical FA drill is excluded; final no-new-drill In3 transfer pending.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math,pickle,sys,time
import shapely
from shapely.geometry import LineString
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];CONT=ROOT/'reports/board-finish-20261011/continuation-r2';ACTUAL=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763';HOST=HERE/'power-only-FG-F-effects-host-r12';OUT=HERE/'strict-FG-F-source-negative-r15';ZID='28475285-01e4-4198-a0cd-e4790c7b8908';FG='/motherboard_motors/FIELD_GND';LY='F.Cu'
for p in(CONT/'coupled-recovery',CONT/'field-power',CONT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import physical_reference_losses_r3_zero_r208 as RF
import trace_actual_field5_replacement as T
import native_lattice_boolean_splice as N
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def sm(s):return{'empty':s.is_empty,'area_mm2':s.area,'bounds':list(s.bounds)if not s.is_empty else[],'sha256':hashlib.sha256(s.wkb).hexdigest()}
def main():
    assert not OUT.exists();OUT.mkdir();started=time.monotonic();files=[ACTUAL/'actual-combined-full-after-model.pkl',ACTUAL/'actual-combined-full-after-all-net-groups.pkl',HOST/'power-only-target-model.pkl',HOST/'native-quantized-power-track-operations.json',HOST/'receipt.json',Path(__file__),Path(N.__file__)];inputs={str(p):sha(p)for p in files};g=pickle.loads(files[0].read_bytes());old=pickle.loads(files[1].read_bytes());h=pickle.loads(files[2].read_bytes());tracks=json.loads(files[3].read_text());points=[tracks[0]['a']]+[t['b']for t in tracks];body=LineString(points).buffer((.25+1e-8)/math.cos(math.pi/512),quad_segs=128);records,_=K.F.build(g,nets={T.NET},layers={LY});positive=body.difference(unary_union([q['shape']for q in records[LY]]));z=next(z for z in g['zones']if z['uuid']==ZID);oldintent=unary_union(K.L.poly([[r[0],r[1:]]for r in z['outline']]));oldCu=unary_union(K.L.poly(z['fills'][LY]));gap=max(.15,float(z['clearance_mm']))+.0251;mask=positive.buffer(gap,quad_segs=128);halo=float(z['min_thickness_mm'])/2+.00001;source_mask=mask.buffer(halo,quad_segs=128);newintent,proof=N.splice(oldintent,oldintent.difference(source_mask),False);negative=oldintent.difference(newintent);assert newintent.difference(oldintent).is_empty;actualcut=oldCu.intersection(negative.union(mask));after=oldCu.difference(negative.union(mask));outside=actualcut.difference(negative)
    for name,s in(('old-intent',oldintent),('native-negative-intent',newintent),('literal-source-negative',negative),('actual-native-Cu-negative-target',actualcut),('negative-target-outside-literal-source-cut',outside),('target-remaining-native-Cu',after)):(OUT/(name+'.wkb')).write_bytes(s.wkb)
    put('native-negative-lattice-proof.json',proof);zones=[q|{'fills':q['fills']|{LY:T.records(after)},'strict_power_only_native_source_target_not_AFTER':True}if q['uuid']==ZID else q for q in h['zones']];h=h|{'zones':zones};(OUT/'strict-power-only-target-model.pkl').write_bytes(pickle.dumps(h,protocol=5));new=K.physical(h,FG,K.hole_context(h))[1];a=K.root(old[FG],'J11003','2');b=K.root(new,'J11003','2');lost=K.keys(a)-K.keys(b);relation,bad=K.contact_losses(old[FG],new);refs,refproof=RF.audit(g,K.source_refs(a),K.source_refs(b),FG)
    # Every pre-existing positive finite F-role contact, including tiny literal
    # overlaps, is tested against the exact updated native-Cu target.
    contacts=[]
    from shapely.strtree import STRtree
    metals=[q for xs in old[FG]for q in xs if q['kind']!='fill'and q['layer']==LY];tree=STRtree([q['shape']for q in metals]);oldfills=[q for xs in old[FG]for q in xs if q['kind']=='fill'and q['uuid']==ZID and q['layer']==LY];newfill=unary_union([q['shape']for xs in new for q in xs if q['kind']=='fill'and q['uuid']==ZID and q['layer']==LY])
    for f in oldfills:
        for j in tree.query(f['shape'],predicate='intersects'):
            q=metals[int(j)];before=q['shape'].intersection(f['shape']).area
            if before<=0:continue
            aa=q['shape'].intersection(newfill).area;contacts.append({'metal':T.describe(q),'old_finite_overlap_mm2':before,'new_finite_overlap_mm2':aa,'retained':aa>0})
    failures=[q for q in contacts if not q['retained']];result={'utc':datetime.now(timezone.utc).isoformat(),'status':'EXACT_NEGATIVE_FG_F_SOURCE_PROFILE_CONSTRUCTION_POWER_ONLY_HOST_GATES_PASS_FA_AND_NATIVE_OPEN'if not lost and not bad and not refs and not failures else'EXACT_NEGATIVE_FG_F_SOURCE_RAW_HOST_GATE_FAIL_NOT_PROMOTED','input_sha256':inputs,'zone_UUID':ZID,'native_min_thickness_mm_unchanged':z['min_thickness_mm'],'native_clearance_mm_unchanged':z['clearance_mm'],'native_priority_unchanged':z['priority'],'strict_inward_source_subset':True,'new_native_source_outer_parts':len(RF.parts(newintent)),'source_negative_halo_reservation_mm':halo,'actual_target_negative_Cu':sm(actualcut),'literal_source_negative':sm(negative),'negative_target_outside_literal_source_cut':sm(outside),'all_old_source_keys_lost':[list(x)for x in sorted(lost)],'all_old_partition_losses':bad,'raw_old_reference_losses':refs,'raw_reference_proof':refproof,'all_positive_finite_old_role_contacts':contacts,'finite_contact_failures':failures,'new_FA_drill_or_return_holes_applied':False,'no_new_FA_hole_topology_transfer':'Use38 exact F retirements and finite In3 existing-port replacement; route/reference still pending','full_coupled_FA_FG_source_old_contacts_reference_current_thermal_KCL_native_positive_negative_minwidth_DRC_and_SI':'OPEN','original_In2_Cu_and_intents_unchanged':True,'all12_motor_and_other_full_current_limits_unchanged':True,'native_jobs':0,'adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-started};put('receipt.json',result);print(json.dumps({'status':result['status'],'FG_Cu_negative_mm2':actualcut.area,'source_parts':len(RF.parts(newintent)),'seconds':result['elapsed_seconds']}),flush=True)
if __name__=='__main__':main()
