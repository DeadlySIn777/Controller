"""Identify net groups that individually sever the real old current corridor.

These are necessary corridor edits within this exact old sheet, not a claim of
the globally smallest PCB redesign or permission to remove a required signal.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from collections import defaultdict
from datetime import datetime,timezone
import hashlib,json,pickle,sys
import shapely
from shapely.ops import unary_union,nearest_points
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
CONT=ROOT/'reports/board-finish-20261011/continuation-r2'
for p in(CONT/'coupled-recovery',CONT/'field-power',CONT/'sbc-power'):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import physical_reference_losses_r3_zero_r208 as RF
import trace_actual_field5_replacement as T
OUT=HERE/'necessary-real-In4-reference-corridor-edits-r1'
TRIAGE=HERE/'old-In4-restoration-triage-r2';CONSTRUCT=HERE/'reference-hard-real-In4-sheet-construction-r1'
ACTUAL=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')

def main():
    assert not OUT.exists();OUT.mkdir()
    files=[TRIAGE/'old-physical-fill-with-current-holes.wkb',CONSTRUCT/'all-raw-source-reference-floor-constraints.json',ACTUAL/'actual-combined-full-after-all-net-groups.pkl',Path(__file__),Path(K.__file__),Path(RF.__file__)]
    inputs={str(p):sha(p)for p in files};sheet=shapely.from_wkb(files[0].read_bytes());inventory=json.loads(files[1].read_text());groups=pickle.loads(files[2].read_bytes());field=K.root(groups[T.NET],'L11003','2');src=unary_union([q['shape']for q in field if q['kind']=='via'and q['uuid']==T.T2 and q['layer']=='In4.Cu']);tgt=unary_union([q['shape']for q in field if q['kind']=='via'and q['uuid']==T.T1 and q['layer']=='In4.Cu']);groundcache={};by_net=defaultdict(list)
    for row in inventory:
        ground=row['source_ground']
        if ground not in groundcache:
            rr=K.root(groups[ground],'J11001'if ground=='/LOGIC_GND'else'J11003','2');groundcache[ground]=unary_union([q['shape']for q in rr if q['kind']=='fill'and q['layer']=='In4.Cu'])
        t=row['track'];floor=K.L.body(t).intersection(groundcache[ground]);by_net[K.L.norm(t['net'])].append((row,floor.buffer(row['required_guard_plus_0p1um_inward_reservation_mm'],quad_segs=128)))
    rows=[]
    for net,entries in sorted(by_net.items()):
        cutter=unary_union([s for _,s in entries]);remaining=sheet.difference(cutter);parts=RF.parts(remaining);sourceparts=[p for p in parts if p.intersection(src).area>1e-10];targetparts=[p for p in parts if p.intersection(tgt).area>1e-10];connected=any(p.intersection(tgt).area>1e-10 for p in sourceparts);r={'net':net,'track_UUIDs':[a['track']['uuid']for a,_ in entries],'tracks':[a['track']for a,_ in entries],'source_ground':[a['source_ground']for a,_ in entries],'full_restore_raw_reference_losses_mm2':[a['raw_full_restore_reference_loss_mm2']for a,_ in entries],'this_net_guard_alone_severs_old_source_to_target_Cu':not connected,'remaining_area_mm2':remaining.area,'source_contact_mm2':sum(p.intersection(src).area for p in sourceparts),'target_contact_mm2':sum(p.intersection(tgt).area for p in targetparts)}
        if sourceparts and targetparts and not connected:
            a,b=nearest_points(unary_union(sourceparts),unary_union(targetparts));r['nearest_separated_source_target_component_boundaries_mm']=[list(a.coords)[0],list(b.coords)[0]];r['nearest_component_gap_mm']=a.distance(b)
        rows.append(r)
        if not connected:(OUT/(str(len(rows))+'-individually-severing-reference-guard.wkb')).write_bytes(cutter.wkb)
    result={'utc':datetime.now(timezone.utc).isoformat(),'status':'ACTUAL_NAMED_REFERENCE_NETS_NECESSARY_FOR_OLD_SHEET_CORRIDOR_REDESIGN','input_sha256':inputs,'all_groups':rows,'individually_unavoidable_net_groups':[r['net']for r in rows if r['this_net_guard_alone_severs_old_source_to_target_Cu']],'requirement':'Within the exact old In4 sheet, each individually severing reference guard must be preserved by a different physical return path or its signal corridor must be rerouted. Reopening that copper without an equivalent source-rooted reference violates the retained signal requirement. A route outside this old sheet is a separate design.','these_are_necessary_conditions_not_a_sufficient_or_globally_minimal_edit_set':True,'zero_area_raw_reference_rows_retained_without_automatic_waiver':True,'all_fitted_motors_I_O_and_signal_functions_preserved':True,'native_after_current_SI_and_thermal':'OPEN','native_jobs':0,'board_written':False,'adopted':False,'manufacturing_ready':False}
    assert all(sha(Path(p))==h for p,h in inputs.items());put('receipt.json',result);print(json.dumps({'status':result['status'],'necessary_net_groups':result['individually_unavoidable_net_groups'],'count':len(result['individually_unavoidable_net_groups'])}))

if __name__=='__main__':main()
