"""Owned native zone outlines in a minimal six-zone document, no fill or DRC."""
import ctypes
k=ctypes.WinDLL('kernel32',use_last_error=True);k.GetCurrentProcess.restype=ctypes.c_void_p;k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t];k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32];handle=k.GetCurrentProcess();assert k.SetProcessAffinityMask(handle,(1<<16)|(1<<17));assert k.SetPriorityClass(handle,0x4000)
from pathlib import Path
import hashlib,json,time
import pcbnew
HERE=Path(__file__).resolve().parent;OUT=HERE/'separate-real-corridor-native-r7';p=OUT/'input.json';d=json.loads(p.read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(d['minimal_native_input'])==d['minimal_native_input_SHA256'];started=time.monotonic();b=pcbnew.LoadBoard(d['minimal_native_input']);index={z.m_Uuid.AsString():z for z in b.Zones()};assert len(index)==len(d['zones']);print('Minimal native source loaded',flush=True)
for row in d['zones']:
    z=index[row['uuid']]
    if not row['polygons_integer_IU']:b.Remove(z);continue
    ps=z.Outline();ps.RemoveAllContours()
    for poly in row['polygons_integer_IU']:
        oi=ps.NewOutline()
        for x,y in poly[0]:ps.Append(x,y,oi,-1)
        for ring in poly[1:]:
            hi=ps.NewHole(oi)
            for x,y in ring:ps.Append(x,y,oi,hi)
    z.UnFill();z.SetNeedRefill(True)
print('Owned native outlines replaced, saving',flush=True);assert pcbnew.SaveBoard(d['minimal_native_output'],b);del b,index
b=pcbnew.LoadBoard(d['minimal_native_output']);index={z.m_Uuid.AsString():z for z in b.Zones()};rows=[]
for row in d['zones']:
    if not row['polygons_integer_IU']:assert row['uuid']not in index;rows.append({'uuid':row['uuid'],'empty_fill_role_retired':True});continue
    z=index[row['uuid']];ps=z.Outline();actual=[]
    for oi in range(ps.OutlineCount()):
        actual.append([[[c.CPoint(j).x,c.CPoint(j).y]for j in range(c.PointCount())]for c in[ps.COutline(oi)]+[ps.CHole(oi,hi)for hi in range(ps.HoleCount(oi))]])
    assert actual==row['polygons_integer_IU'];assert all(not z.HasFilledPolysForLayer(ly)for ly in(pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.B_Cu));rows.append({'uuid':row['uuid'],'exact_native_integer_outline_roundtrip':True,'filled_cache_absent_all6':True,'outline_count':ps.OutlineCount()})
assert sha(d['stage3_board'])==d['stage3_board_SHA256'];result={'status':'EXACT_NATIVE_MINIMAL_ZONE_LOAD_SAVE_RELOAD_PASS_NO_FILL','input_sha256':{str(p):sha(p),str(Path(__file__)):sha(Path(__file__)),d['minimal_native_input']:sha(d['minimal_native_input'])},'output':d['minimal_native_output'],'output_SHA256':sha(d['minimal_native_output']),'rows':rows,'native_version':pcbnew.GetBuildVersion(),'fill_called':False,'DRC_called':False,'source_board_unchanged':True,'native_physical_AFTER':'OPEN','adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-started};(OUT/'native-roundtrip-receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'rows':len(rows),'seconds':result['elapsed_seconds']}),flush=True)
