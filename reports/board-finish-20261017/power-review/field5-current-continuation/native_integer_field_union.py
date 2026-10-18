"""Exact KiCad integer set operations for FIELD5 source and finite patch union.

Input/output are integer native IU. No board load/save and no fill occurs.
"""
import ctypes
k=ctypes.WinDLL('kernel32',use_last_error=True);k.GetCurrentProcess.restype=ctypes.c_void_p;k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t];k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
h=k.GetCurrentProcess();assert k.SetProcessAffinityMask(h,(1<<16)|(1<<17));assert k.SetPriorityClass(h,0x4000)
from pathlib import Path
import hashlib,json,time
import pcbnew
HERE=Path(__file__).resolve().parent;OUT=HERE/'native-integer-field-union-r1';p=OUT/'input.json';d=json.loads(p.read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();started=time.monotonic()
def poly(rows):
    ps=pcbnew.SHAPE_POLY_SET()
    for rr in rows:
        oi=ps.NewOutline()
        for x,y in rr[0]:ps.Append(x,y,oi,-1)
        for ring in rr[1:]:
            hi=ps.NewHole(oi)
            for x,y in ring:ps.Append(x,y,oi,hi)
    return ps
def coords(ps):
    return[[[[chain.CPoint(j).x,chain.CPoint(j).y]for j in range(chain.PointCount())]for chain in[ps.COutline(oi)]+[ps.CHole(oi,hi)for hi in range(ps.HoleCount(oi))]]for oi in range(ps.OutlineCount())]
old=poly(d['old_field_integer_IU']);support=poly(d['support_integer_IU']);result=pcbnew.SHAPE_POLY_SET();result.BooleanAdd(old,support)
lost=pcbnew.SHAPE_POLY_SET();lost.BooleanSubtract(old,result);assert lost.OutlineCount()==0
delta=pcbnew.SHAPE_POLY_SET();delta.BooleanSubtract(result,old)
remote=pcbnew.SHAPE_POLY_SET();remote.BooleanSubtract(delta,support);assert remote.OutlineCount()==0
rows={'status':'EXACT_NATIVE_INTEGER_OLD_INTENT_RETENTION_AND_NEW_POSITIVE_LOCALITY_PASS','new_field_integer_IU':coords(result),'native_positive_integer_IU':coords(delta),'integer_old_minus_new_outline_count':lost.OutlineCount(),'integer_positive_minus_support_outline_count':remote.OutlineCount(),'input_sha256':{str(p):sha(p),str(Path(__file__)):sha(Path(__file__))},'native_version':pcbnew.GetBuildVersion(),'board_loaded':False,'fill_called':False,'adopted':False,'elapsed_seconds':time.monotonic()-started}
(OUT/'output.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps({k:v for k,v in rows.items()if k.endswith('count')or k in('status','elapsed_seconds')}))
