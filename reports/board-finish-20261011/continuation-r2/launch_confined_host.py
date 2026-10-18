"""Start a task-owned host script inside the existing 12-CPU reservation."""
import os,sys,runpy
from pathlib import Path
os.environ.update(OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',PYTHONUTF8='1')
import psutil
def main():
    if len(sys.argv)<2:raise ValueError('Task script path required')
    script=Path(sys.argv[1]).resolve();allowed=Path(__file__).resolve().parent.parent
    if not script.is_relative_to(allowed) or not script.is_file() or script==Path(__file__).resolve():raise ValueError('Only existing board-finish task scripts allowed')
    process=psutil.Process();process.cpu_affinity(list(range(16,28)));process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    sys.path.insert(0,str(script.parent));sys.argv=[str(script),*sys.argv[2:]]
    runpy.run_path(str(script),run_name='__main__')
if __name__=='__main__':main()
