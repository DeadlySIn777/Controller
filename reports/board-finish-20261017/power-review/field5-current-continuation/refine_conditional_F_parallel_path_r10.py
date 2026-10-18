"""Refine the continuous half-mm power corridor without weakening Cu gaps."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,time
import shapely
from shapely.geometry import Point,LineString
HERE=Path(__file__).resolve().parent;OUT=HERE/'F-parallel-offset-FA-landing-refined-r10';PRE=HERE/'F-parallel-offset-FA-landing-probe-r9';hp=HERE/'probe_parallel_existing_barrel_corridors_r2.py';sp=importlib.util.spec_from_file_location('corridor',hp);H=importlib.util.module_from_spec(sp);sp.loader.exec_module(H);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir();started=time.monotonic();fp=PRE/'F-Cu-free-centerline-area.wkb';free=shapely.from_wkb(fp.read_bytes());source=(317.7459258541723,160.47156870634757);target=(278.687,149.387);part=next(p for p in free.geoms if p.covers(Point(source)));assert part.covers(Point(target));r=H.route(part,source,target,.0125);r.update({'continuous_free_component_contains_source_and_target':True,'source_terminal':'L11003.2 actual native F pad center','target_barrel':'0901cf4a-0f1c-4f5a-8c92-68ccf5d1bfe3 F annulus','trace_width_mm':.5,'same_native_clearances_and_25um_guard_as_parent':True,'conditional_FA_retirements':['f231adb1-b5c9-422a-82eb-c6a859d26a93','21702822-e41c-488c-a23a-db6e3e94614d'],'conditional_FA_new_via_mm':[297.65,155.35],'conditional_FA_new_via_size_drill_mm':[.5,.2],'conditional_FA_short_F_stub_mm':[[297.25,155.65],[297.65,155.35]],'all_layer_new_via_drill_SMD_pair_return_old_signal_contacts_reference_and_In3_route':'OPEN; independent routing review, nothing adopted','FG_F_copper_negative_source_contacts_reference_signed_return_current_and_thermal':'OPEN','native_and_full_FIELD5_KCL_all_simultaneous_loads_voltage_budget_material_and_thermal':'OPEN','input_sha256':{str(p):sha(p)for p in(fp,PRE/'receipt.json',hp,Path(__file__))},'native_jobs':0,'board_written':False,'adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-started})
    if'path_mm'in r:
        axis=LineString(r['path_mm']);assert part.covers(axis);r['rectangular_ideal_track_squares_length_over_width']=axis.length/.5;(OUT/'candidate-axis.wkb').write_bytes(axis.wkb);(OUT/'candidate-nominal-track-body.wkb').write_bytes(axis.buffer(.25,quad_segs=128).wkb)
    (OUT/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
if __name__=='__main__':main()
