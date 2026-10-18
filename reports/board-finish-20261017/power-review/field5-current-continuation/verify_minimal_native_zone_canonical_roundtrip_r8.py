"""Verify integer contours with only ring start/order/orientation normalized.

Preserves the failed sequence-order check; native source geometry must use every
exact integer point, with exact hole association and counts. No distance/area
tolerance is applied and no fill or save occurs here.
"""
import ctypes
k=ctypes.WinDLL('kernel32',use_last_error=True);k.GetCurrentProcess.restype=ctypes.c_void_p;k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t];k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32];h=k.GetCurrentProcess();assert k.SetProcessAffinityMask(h,(1<<16)|(1<<17));assert k.SetPriorityClass(h,0x4000)
from pathlib import Path
import hashlib,json
import pcbnew
HERE=Path(__file__).resolve().parent;OUT=HERE/'separate-real-corridor-native-r7';p=OUT/'input.json';d=json.loads(p.read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();b=pcbnew.LoadBoard(d['minimal_native_output']);index={z.m_Uuid.AsString():z for z in b.Zones()}
def ring(r):
    t=tuple(map(tuple,r));m=min(t);a=[t[i:]+t[:i]for i,x in enumerate(t)if x==m];u=tuple(reversed(t));a +=[u[i:]+u[:i]for i,x in enumerate(u)if x==m];return min(a)
def canon(ps):return sorted((ring(p[0]),tuple(sorted(ring(r)for r in p[1:])))for p in ps)
rows=[];fail=[]
for row in d['zones']:
    if not row['polygons_integer_IU']:assert row['uuid']not in index;rows.append({'uuid':row['uuid'],'empty_fill_role_retired':True});continue
    z=index[row['uuid']];ps=z.Outline();actual=[]
    for oi in range(ps.OutlineCount()):actual.append([[[c.CPoint(j).x,c.CPoint(j).y]for j in range(c.PointCount())]for c in[ps.COutline(oi)]+[ps.CHole(oi,hi)for hi in range(ps.HoleCount(oi))]])
    same=canon(actual)==canon(row['polygons_integer_IU']);r={'uuid':row['uuid'],'integer_contours_and_hole_associations_exact_modulo_ring_start_and_orientation':same,'native_outline_count':ps.OutlineCount(),'input_outline_count':len(row['polygons_integer_IU']),'native_point_counts':[[len(r)for r in p]for p in actual],'input_point_counts':[[len(r)for r in p]for p in row['polygons_integer_IU']],'native_fills_absent_all6':all(not z.HasFilledPolysForLayer(ly)for ly in(pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.B_Cu))};rows.append(r)
    if not same:fail.append(row['uuid']);(OUT/(row['uuid']+'-native-readback-integer-polygons.json')).write_text(json.dumps(actual,indent=2)+'\n')
result={'status':'EXACT_NATIVE_INTEGER_CONTOURS_AND_HOLES_ROUNDTRIP_PASS'if not fail else'NATIVE_ROUNDTRIP_GEOMETRY_MISMATCH_RAW_NOT_PROMOTED','inputs':{str(p):sha(p),d['minimal_native_output']:sha(d['minimal_native_output']),str(Path(__file__)):sha(Path(__file__))},'rows':rows,'failures':fail,'ring_order_normalization_changes_no_point_or_edge':True,'no_distance_or_area_tolerance':True,'fill_called':False,'board_saved':False,'stage3_board_unchanged':sha(d['stage3_board'])==d['stage3_board_SHA256'],'native_physical_AFTER':'OPEN','adopted':False,'manufacturing_ready':False};(OUT/'native-canonical-roundtrip-receipt-r8.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'rows':rows}));assert not fail
