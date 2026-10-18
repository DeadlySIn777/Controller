"""Explicit native-grid FIELD5 widening and FG negative source splices."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,pickle,sys,time
import shapely
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
CONT=ROOT/'reports/board-finish-20261011/continuation-r2'
for p in(CONT/'coupled-recovery',CONT/'field-power',CONT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import trace_actual_field5_replacement as T
import native_lattice_boolean_splice as N
OUT=HERE/'native-50um-splice-construction-r3'
CON=HERE/'bounded-current-In2-widening-construction-r2'
ACTUAL=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
FG='/motherboard_motors/FIELD_GND';LY='In2.Cu';ZID='5655cb90-5071-5499-8df8-2b73c23dc1fa'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def sm(s):return{'empty':s.is_empty,'area_mm2':s.area,'bounds':list(s.bounds)if not s.is_empty else[],'sha256':hashlib.sha256(s.wkb).hexdigest()}
def outline(z):return unary_union(K.L.poly([[r[0],r[1:]]for r in z['outline']]))

def main():
    assert not OUT.exists();OUT.mkdir();started=time.monotonic()
    files=[ACTUAL/'actual-combined-full-after-model.pkl',CON/'50um-support-patch.wkb',HERE/'construct_bounded_current_In2_widening_r2.py',Path(__file__),Path(N.__file__)]
    inputs={str(p):sha(p)for p in files};g=pickle.loads(files[0].read_bytes());support=shapely.set_precision(shapely.from_wkb(files[1].read_bytes()),0);fz=next(z for z in g['zones']if z['uuid']==ZID);oldintent=outline(fz);oldCu=unary_union(K.L.poly(fz['fills'][LY]));floating=oldintent.union(support);field_intent,fieldproof=N.splice(oldintent,floating,True);field_addition=field_intent.difference(oldintent);targetCu=oldCu.union(support).union(field_addition);delta=targetCu.difference(oldCu);assert oldintent.difference(field_intent).is_empty
    for name,s in(('field-old-intent',oldintent),('field-native-positive-intent',field_intent),('field-literal-positive-intent-delta',field_addition),('field-support-patch',support),('field-target-raw-Cu',targetCu),('field-all-positive-target-Cu',delta)):(OUT/(name+'.wkb')).write_bytes(s.wkb)
    put('field-positive-lattice-proof.json',fieldproof)
    cuts=[];negative_rows={}
    for z in g['zones']:
        if LY not in z['fills']or K.L.norm(z['net'])!=FG:continue
        oldfill=unary_union(K.L.poly(z['fills'][LY]));oldline=outline(z);gap=max(float(fz['clearance_mm']),float(z['clearance_mm']),.15)+.0251;mask=delta.buffer(gap,quad_segs=128)
        if oldfill.intersection(mask).is_empty and oldline.intersection(mask).is_empty:continue
        floating_fg=oldline.difference(mask);newintent,proof=N.splice(oldline,floating_fg,False);negative=oldline.difference(newintent);actualcut=oldfill.intersection(negative);assert newintent.difference(oldline).is_empty
        for suffix,s in(('old-intent',oldline),('native-negative-intent',newintent),('literal-intent-negative',negative),('literal-native-Cu-negative',actualcut)):(OUT/(z['uuid']+'-'+suffix+'.wkb')).write_bytes(s.wkb)
        put(z['uuid']+'-negative-lattice-proof.json',proof);negative_rows[z['uuid']]=negative;cuts.append({'uuid':z['uuid'],'native_Cu_cut':sm(actualcut),'literal_intent_cut':sm(negative),'primary_mask':sm(mask),'additional_negative_outside_primary_mask':sm(negative.difference(mask)),'required_native_and_engineering_gap_mm':gap-.0001,'reserved_constructor_gap_mm':gap,'all_native_positive_gains_empty':True,'native_lattice_selected_margin_nm':proof['selected_margin_nm']});put('ground-splice-checkpoint.json',cuts);print(json.dumps({'ground_zone':z['uuid'],'Cu_cut_mm2':actualcut.area,'extra_negative_mm2':negative.difference(mask).area,'native_margin_nm':proof['selected_margin_nm']}),flush=True)
    zones=[]
    for z in g['zones']:
        if z['uuid']==ZID:zones.append(z|{'fills':z['fills']|{LY:T.records(targetCu)},'host_target_not_native_after':True})
        elif z['uuid']in negative_rows:
            before=unary_union(K.L.poly(z['fills'][LY]));zones.append(z|{'fills':z['fills']|{LY:T.records(before.difference(negative_rows[z['uuid']]))},'host_target_not_native_after':True})
        else:zones.append(z)
    h=g|{'zones':zones,'host_target_not_native_after':True};(OUT/'prospective-native-splice-target-model.pkl').write_bytes(pickle.dumps(h,protocol=5));result={'utc':datetime.now(timezone.utc).isoformat(),'status':'EXPLICIT_NATIVE_1NM_POSITIVE_FIELD_AND_NEGATIVE_FG_SPLICES_CONSTRUCTED_HOST_GATES_OPEN','input_sha256':inputs,'field_zone_UUID':ZID,'field_all_positive_target_Cu':sm(delta),'field_native_positive_intent_delta':sm(field_addition),'field_literal_old_intent_retained':True,'field_selected_native_margin_nm':fieldproof['selected_margin_nm'],'FG_native_negative_splices':cuts,'FG_all_actual_target_Cu_removed_mm2':sum(r['native_Cu_cut']['area_mm2']for r in cuts),'all_additional_native_wedges_are_explicit_no_tiny_area_waiver':True,'new_drills':0,'native_jobs':0,'board_written':False,'sparse_packet_frozen':False,'native_serialization_source_contacts_current_ground_return_thermal_and_AFTERMATH':'OPEN','adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-started}
    assert all(sha(Path(p))==h for p,h in inputs.items());put('receipt.json',result);print(json.dumps({'status':result['status'],'positive_Cu_mm2':delta.area,'FG_Cu_cut_mm2':result['FG_all_actual_target_Cu_removed_mm2'],'seconds':result['elapsed_seconds']}),flush=True)

if __name__=='__main__':main()
