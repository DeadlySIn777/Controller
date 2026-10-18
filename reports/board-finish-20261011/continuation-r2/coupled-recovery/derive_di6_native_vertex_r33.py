"""Preserve failed R31 and derive direct native ring integer iteration."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
p=HERE/'diagnose_di6_remote_native_contour_r31.py';s=p.read_text()
old=""" for sh in L.poly(A.polys(z['fills'].get(layer,[]))):
  for ring in [sh.exterior,*sh.interiors]:
   for x,y in ring.coords:"""
new=""" for native_polygon in z['fills'].get(layer,[]):
  for native_ring in native_polygon:
   for x,y in native_ring:"""
assert old in s;s=s.replace(old,new).replace('di6-remote-native-contour-return-diagnostic-r31.json','di6-remote-native-contour-return-diagnostic-r33.json')
out=HERE/'diagnose_di6_remote_native_contour_r33.py';assert not out.exists();out.write_text(s)
