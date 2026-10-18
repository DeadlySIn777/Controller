"""Whole-board A main-output return search; original barriers retained."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
from pathlib import Path
path=Path(__file__).with_name('variable_return_r2.py')
text=path.read_text(encoding='utf-8').replace("OUT=HERE/'variable-return-r2'","OUT=HERE/'variable-return-r4'")
old="[('FBG',0,box(0,120,255,239)),('FAG',0,box(180,120,455,239))]"
assert old in text
text=text.replace(old,"[('FAG',38,box(0,0,455,239))]").replace('node_cap=650000','node_cap=1200000').replace('time.monotonic()+35','time.monotonic()+45')
exec(compile(text,str(path),'exec'))
