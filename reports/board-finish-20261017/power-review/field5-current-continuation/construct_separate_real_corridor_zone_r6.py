"""Add one finite FIELD5 current-corridor zone; keep original role exact.

The original large merged zone is never re-unioned or changed. Local same-net
support overlaps its real native source Cu and widens the actual R543 branch.
Exact FG source-negative splices and physical outside-intent targets differ.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,pickle,sys,time,uuid
import shapely
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];CONT=ROOT/'reports/board-finish-20261011/continuation-r2'
for p in(CONT/'coupled-recovery',CONT/'field-power',CONT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import trace_actual_field5_replacement as T
import native_lattice_boolean_splice as N
import physical_reference_losses_r3_zero_r208 as RF
OUT=HERE/'separate-real-corridor-zone-construction-r6';CON=HERE/'bounded-current-In2-widening-construction-r4';ACTUAL=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
FG='/motherboard_motors/FIELD_GND';LY='In2.Cu';ZID='5655cb90-5071-5499-8df8-2b73c23dc1fa';NEW=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/R299/FIELD5/50um-real-In2-corridor-r6'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def sm(s):return{'empty':s.is_empty,'area_mm2':s.area,'bounds':list(s.bounds)if not s.is_empty else[],'sha256':hashlib.sha256(s.wkb).hexdigest()}
def outline(z):return unary_union(K.L.poly([[r[0],r[1:]]for r in z['outline']]))
def main():
    assert not OUT.exists();OUT.mkdir();started=time.monotonic();files=[ACTUAL/'actual-combined-full-after-model.pkl',CON/'50um-support-patch.wkb',CON/'exact-robust-allowed-positive-area.wkb',Path(__file__),Path(N.__file__)];inputs={str(p):sha(p)for p in files};g=pickle.loads(files[0].read_bytes());support,allowed=[shapely.set_precision(shapely.from_wkb(p.read_bytes()),0)for p in files[1:3]];fz=next(z for z in g['zones']if z['uuid']==ZID);oldCu=unary_union(K.L.poly(fz['fills'][LY]));delta=support.difference(oldCu)
    assert support.difference(allowed).is_empty;assert delta.difference(support).is_empty
    finite=[p.intersection(oldCu).area for p in RF.parts(support)];assert all(a>1e-8 for a in finite)
    for name,s in(('field-new-real-corridor-intent',support),('field-all-positive-target-Cu',delta),('field-support-patch',support)):(OUT/(name+'.wkb')).write_bytes(s.wkb)
    cuts=[];negative_rows={}
    for z in g['zones']:
        if LY not in z['fills']or K.L.norm(z['net'])!=FG:continue
        oldfill=unary_union(K.L.poly(z['fills'][LY]));oldline=outline(z);gap=max(float(fz['clearance_mm']),float(z['clearance_mm']),.15)+.0251;mask=delta.buffer(gap+.05001,quad_segs=128)
        if oldfill.intersection(mask).is_empty and oldline.intersection(mask).is_empty:continue
        floating=oldline.difference(mask)
        if floating.is_empty:newintent=shapely.GeometryCollection();proof={'positive':False,'literal_new_subset_of_old':True,'entire_literal_old_intent_retired':True,'selected_margin_nm':0,'no_area_or_distance_waiver':True}
        else:newintent,proof=N.splice(oldline,floating,False)
        negative=oldline.difference(newintent);assert newintent.difference(oldline).is_empty;target_negative=negative.union(mask);actualcut=oldfill.intersection(target_negative);outside=actualcut.difference(negative)
        for suffix,s in(('old-intent',oldline),('native-negative-intent',newintent),('literal-intent-negative',negative),('literal-native-Cu-negative',actualcut),('negative-fill-target-outside-literal-source-cut',outside)):(OUT/(z['uuid']+'-'+suffix+'.wkb')).write_bytes(s.wkb)
        put(z['uuid']+'-negative-lattice-proof.json',proof);negative_rows[z['uuid']]=target_negative;cuts.append({'uuid':z['uuid'],'native_Cu_cut':sm(actualcut),'literal_intent_cut':sm(negative),'native_fill_negative_target_outside_literal_intent_cut':sm(outside),'required_native_and_engineering_gap_mm':gap-.0001,'source_cut_extra_band_reservation_mm':.05001,'native_fill_required_to_prove_target_removal':True,'all_native_positive_gains_empty':True,'native_lattice_selected_margin_nm':proof['selected_margin_nm']})
    zones=[]
    for z in g['zones']:
        if z['uuid']in negative_rows:
            before=unary_union(K.L.poly(z['fills'][LY]));zones.append(z|{'fills':z['fills']|{LY:T.records(before.difference(negative_rows[z['uuid']]))},'host_target_not_native_after':True})
        else:zones.append(z)
    rawoutline=[[list(p.exterior.coords)[:-1],*[list(r.coords)[:-1]for r in p.interiors]]for p in RF.parts(support)]
    zones.append(fz|{'uuid':NEW,'outline':rawoutline,'fills':{LY:T.records(support)},'host_target_not_native_after':True});h=g|{'zones':zones,'host_target_not_native_after':True};assert next(z for z in h['zones']if z['uuid']==ZID)==fz
    (OUT/'prospective-native-splice-target-model.pkl').write_bytes(pickle.dumps(h,protocol=5));result={'utc':datetime.now(timezone.utc).isoformat(),'status':'LOCAL_REAL_CORRIDOR_NEW_ZONE_AND_FG_NEGATIVE_SOURCE_SPlices_CONSTRUCTED_HOST_GATES_OPEN','input_sha256':inputs,'original_field_zone_UUID_retained_exact':ZID,'field_zone_UUID':NEW,'new_zone_outline':sm(support),'field_all_positive_target_Cu':sm(delta),'every_support_component_finite_old_source_Cu_overlap_mm2':finite,'FG_native_negative_splices':cuts,'FG_all_actual_target_Cu_removed_mm2':sum(r['native_Cu_cut']['area_mm2']for r in cuts),'remote_old_FIELD5_source_outline_and_native_Cu_not_reunioned':True,'native_fill_required_for_all_positive_and_negative_targets':True,'new_drills':0,'native_jobs':0,'board_written':False,'sparse_packet_frozen':False,'adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-started};put('receipt.json',result);print(json.dumps({'new_zone':NEW,'support':support.area,'positive_Cu_mm2':delta.area,'FG_negative_Cu_mm2':result['FG_all_actual_target_Cu_removed_mm2'],'FG_source_splices':len(cuts)}))
if __name__=='__main__':main()
