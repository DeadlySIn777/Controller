"""KiCad 10 load/outline/save/reload only. No fill, DRC, or board adoption."""
import ctypes
k=ctypes.WinDLL('kernel32',use_last_error=True);k.GetCurrentProcess.restype=ctypes.c_void_p;k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t];k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
h=k.GetCurrentProcess();assert k.SetProcessAffinityMask(h,(1<<16)|(1<<17));assert k.SetPriorityClass(h,0x4000)
from pathlib import Path
import hashlib,json,time
import pcbnew
HERE=Path(__file__).resolve().parent;OUT=HERE/'native-50um-splice-roundtrip-r1'
p=OUT/'native-integer-outline-input.json';d=json.loads(p.read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(d['source_board'])==d['source_board_SHA256'];started=time.monotonic()
board=pcbnew.LoadBoard(d['source_board']);index={str(z.m_Uuid.AsString()):z for z in board.Zones()};rows=[]
def polygon_input(row):
    ps=pcbnew.SHAPE_POLY_SET()
    for poly in row['polygons_integer_IU']:
        oi=ps.NewOutline()
        for x,y in poly[0]:ps.Append(x,y,oi,-1)
        for ring in poly[1:]:
            hi=ps.NewHole(oi)
            for x,y in ring:ps.Append(x,y,oi,hi)
    return ps
for row in d['zones']:
    z=index[row['uuid']];z.SetOutline(polygon_input(row));z.UnFill();z.SetNeedRefill(True)
assert pcbnew.SaveBoard(d['output_board'],board)
del board,index
board=pcbnew.LoadBoard(d['output_board']);index={str(z.m_Uuid.AsString()):z for z in board.Zones()}
for row in d['zones']:
    z=index[row['uuid']];ps=z.Outline();polys=[]
    for oi in range(ps.OutlineCount()):
        rings=[]
        for chain in [ps.COutline(oi)]+[ps.CHole(oi,hi)for hi in range(ps.HoleCount(oi))]:
            rings.append([[chain.CPoint(j).x,chain.CPoint(j).y]for j in range(chain.PointCount())])
        polys.append(rings)
    assert polys==row['polygons_integer_IU']
    assert all(not z.HasFilledPolysForLayer(ly)for ly in (pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.B_Cu))
    rows.append({'uuid':row['uuid'],'exact_native_integer_outline_roundtrip':True,'native_outline_count':ps.OutlineCount(),'filled_cache_absent_all6':True,'NeedRefill':z.NeedRefill()})
assert sha(d['source_board'])==d['source_board_SHA256']
(OUT/'native-load-save-reload-receipt.json').write_text(json.dumps({'status':'SIX_NATIVE_OUTLINES_INTEGER_EXACT_LOAD_SAVE_RELOAD_NO_FILL','inputs':{str(p):sha(p),str(Path(__file__)):sha(Path(__file__)),d['source_board']:sha(d['source_board'])},'output_board':d['output_board'],'output_board_SHA256':sha(d['output_board']),'rows':rows,'native_version':pcbnew.GetBuildVersion(),'fill_called':False,'DRC_called':False,'adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-started},indent=2)+'\n')
print(json.dumps({'status':'NATIVE_OUTLINE_ROUNDTRIP_PASS','zones':len(rows),'seconds':time.monotonic()-started}))
