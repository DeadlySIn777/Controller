"""Preserve R647 affinity API failure; use typed Win64 process handles."""
from pathlib import Path
s=(Path(__file__).with_name('native_eedf_exact_cached_BEFORE_dump_r647.py')).read_text(encoding='utf-8')
old="assert ctypes.windll.kernel32.SetProcessAffinityMask(ctypes.windll.kernel32.GetCurrentProcess(),sum(1<<i for i in range(16,28)))\nassert ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(),0x4000)"
new="from ctypes import wintypes\nkt=ctypes.windll.kernel32\nkt.GetCurrentProcess.restype=wintypes.HANDLE\nkt.SetProcessAffinityMask.argtypes=(wintypes.HANDLE,ctypes.c_size_t)\nkt.SetPriorityClass.argtypes=(wintypes.HANDLE,wintypes.DWORD)\nassert kt.SetProcessAffinityMask(kt.GetCurrentProcess(),sum(1<<i for i in range(16,28)))\nassert kt.SetPriorityClass(kt.GetCurrentProcess(),0x4000)"
assert old in s;s=s.replace(old,new)
exec(compile(s,str(Path(__file__)),'exec'))
