"""Confined entry point for profile completion or exact recipe emission."""
import os,psutil,sys
for task_env in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[task_env]='2'
task_process=psutil.Process();task_process.cpu_affinity(list(range(16,28)));task_process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
assert len(sys.argv)==4,'profiles current_model.pkl fresh_profile_directory | emit immutable_manifest.json fresh_recipe_directory'
mode= sys.argv[1]
if mode=='profiles':
 import complete_current_owned_native_profiles_r276 as task_tool
elif mode=='emit':
 import emit_current_owned_native_recipe_r286 as task_tool
else:raise ValueError('Only profile metadata or file-only current recipe emission is supported')
sys.argv=[task_tool.__file__,*sys.argv[2:]];task_tool.main()
