"""Native owned single-outer polygons, exact integer contours and holes, no fill."""
import ctypes
k=ctypes.WinDLL('kernel32',use_last_error=True);k.GetCurrentProcess.restype=ctypes.c_void_p;k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t];k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32];handle=k.GetCurrentProcess();assert k.SetProcessAffinityMask(handle,(1<<16)|(1<<17));assert k.SetPriorityClass(handle,0x4000)
from pathlib import Path
import hashlib,json,time
import pcbnew
HERE=Path(__file__).resolve().parent;OUT=HERE/'single-outer-real-corridor-native-r9';p=OUT/'input.json';d=json.loads(p.read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(d['minimal_native_input'])==d['minimal_native_input_SHA256'];started=time.monotonic();b=pcbnew.LoadBoard(d['minimal_native_input']);index={z.m_Uuid.AsString():z for z in b.Zones()};assert len(index)==len(d['zones'])
def canonical_ring(r):
    t=tuple(map(tuple,r));u=tuple(reversed(t));m=min(t);return min([t[i:]+t[:i]for i,x in enumerate(t)if x==m]+[u[i:]+u[:i]for i,x in enumerate(u)if x==m])
def canonical(p):return(canonical_ring(p[0]),tuple(sorted(canonical_ring(r)for r in p[1:])))
for row in d['zones']:
    assert len(row['polygons_integer_IU'])==1;z=index[row['uuid']];ps=z.Outline();ps.RemoveAllContours();poly=row['polygons_integer_IU'][0];oi=ps.NewOutline()
    for x,y in poly[0]:ps.Append(x,y,oi,-1)
    for ring in poly[1:]:
        hi=ps.NewHole(oi)
        for x,y in ring:ps.Append(x,y,oi,hi)
    z.UnFill();z.SetNeedRefill(True)
assert pcbnew.SaveBoard(d['minimal_native_output'],b);del b,index;b=pcbnew.LoadBoard(d['minimal_native_output']);index={z.m_Uuid.AsString():z for z in b.Zones()};rows=[]
for row in d['zones']:
    z=index[row['uuid']];ps=z.Outline();assert ps.OutlineCount()==1;actual=[[[c.CPoint(j).x,c.CPoint(j).y]for j in range(c.PointCount())]for c in[ps.COutline(0)]+[ps.CHole(0,hi)for hi in range(ps.HoleCount(0))]];assert canonical(actual)==canonical(row['polygons_integer_IU'][0]);empty=all(z.GetFilledPolysList(ly).OutlineCount()==0 for ly in(pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.B_Cu));assert empty;rows.append({'uuid':row['uuid'],'exact_native_integer_points_edges_and_hole_associations':True,'source_outer_contours':1,'source_holes':ps.HoleCount(0),'actual_filled_polygon_count_all6':0,'native_minimum_thickness_mm':pcbnew.ToMM(z.GetMinThickness()),'native_local_clearance_mm':pcbnew.ToMM(z.GetLocalClearance()),'native_priority':z.GetAssignedPriority()})
assert sha(d['stage3_board'])==d['stage3_board_SHA256'];r={'status':'ALL_SINGLE_OUTER_NATIVE_INTEGER_CONTOURS_HOLES_LOAD_SAVE_RELOAD_PASS_NO_FILL','input_sha256':{str(p):sha(p),str(Path(__file__)):sha(Path(__file__)),d['minimal_native_input']:sha(d['minimal_native_input'])},'output':d['minimal_native_output'],'output_SHA256':sha(d['minimal_native_output']),'rows':rows,'ring_start_order_orientation_only_canonicalized_no_point_or_edge_change':True,'native_version':pcbnew.GetBuildVersion(),'fill_called':False,'DRC_called':False,'source_board_unchanged':True,'native_physical_AFTER_minwidth_current_return_and_SI':'OPEN','adopted':False,'manufacturing_ready':False,'elapsed_seconds':time.monotonic()-started};(OUT/'native-roundtrip-receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'zones':len(rows),'seconds':r['elapsed_seconds']}))
