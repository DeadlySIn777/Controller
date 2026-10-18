"""Read-only primary-source sliver predicate translation for position recovery.

Native DRC remains authoritative. This locator uses the installed exact arc
approximation constant and retains literal integer geometry, without an area
threshold, changing copper, or changing DRC settings.
"""
from pathlib import Path
import sys,json,math,time
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-two-local-barrel-correction-r04/motherboard-U25-two-local-barrels-candidate.kicad_pcb')
O=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-native-B-sliver-location-r01');assert not O.exists();O.mkdir()
inputs={str(q):sha(q)for q in[B,Path(__file__),Path('reports/motherboard-return-zoning-20261001/U25-primary-sliver-checker-r01/drc_test_provider_sliver_checker.cpp'),Path('reports/motherboard-return-zoning-20261001/U25-primary-sliver-checker-r01/advanced_config.cpp')]}
b=pcbnew.LoadBoard(str(B));layer=pcbnew.B_Cu;poly=pcbnew.SHAPE_POLY_SET();count=0;start=time.monotonic();err=pcbnew.FromMM(pcbnew.ARC_LOW_DEF_MM);assert err==20000
for item in list(b.GetTracks())+list(b.GetPads())+list(b.GetDrawings())+[q for f in b.GetFootprints()for q in f.GraphicalItems()]:
 if not item.IsOnLayer(layer):continue
 item.TransformShapeToPolygon(poly,layer,0,err,pcbnew.ERROR_INSIDE);count+=1
for z in b.Zones():
 if not z.GetIsRuleArea()and z.IsOnLayer(layer):poly.Append(z.GetFilledPolysList(layer))
print('Simplifying literal B copper union',count,flush=True);poly.Simplify();print('Literal outlines',poly.OutlineCount(),flush=True)
minlen=pcbnew.FromMM(.0008);width2=pcbnew.FromMM(.08)**2;cosbound=2*math.cos(math.radians(20));rows=[]
for oi in range(poly.OutlineCount()):
 chain=poly.Outline(oi);pts=[tuple(chain.CPoint(i))for i in range(chain.PointCount())];N=len(pts)
 if N<=5:continue
 def area(p,q,r):return(q[1]-p[1])*(r[0]-q[0])-(q[0]-p[0])*(r[1]-q[1])
 def local(a,c):
  prev=(N+a-1)%N;next=(a+1)%N
  if area(pts[prev],pts[a],pts[next])<0:return area(pts[a],pts[c],pts[next])>=0 and area(pts[a],pts[prev],pts[c])>=0
  return area(pts[a],pts[c],pts[prev])<0 or area(pts[a],pts[next],pts[c])<0
 k=0
 while k<N:
  prior=(N+k-1)%N;next=(k+1)%N;pt=pts[k];pp=pts[prior];vp=(pp[0]-pt[0],pp[1]-pt[1]);forward=1;offset=1
  while abs(vp[0])<minlen and abs(vp[1])<minlen and offset<N:
   pt=pts[(k+offset)%N];offset+=1;vp=(pp[0]-pt[0],pp[1]-pt[1])
  if offset>=N:break
  pa=pts[next];va=(pa[0]-pt[0],pa[1]-pt[1])
  while abs(va[0])<minlen and abs(va[1])<minlen and forward<N:
   next=(k+forward)%N;forward+=1;pa=pts[next];va=(pa[0]-pt[0],pa[1]-pt[1])
  if offset>=N:break
  dot=vp[0]*va[0]+vp[1]*va[1]
  if dot>0 and local(prior,next):
   v=(pa[0]-pp[0],pa[1]-pp[1]);arm1=vp[0]**2+vp[1]**2;arm2=va[0]**2+va[1]**2;opp=v[0]**2+v[1]**2
   if arm1 and arm2:
    cosang=abs((opp-arm1-arm2)/(math.sqrt(arm1)*math.sqrt(arm2)))
    if cosang>cosbound and 2-cosang>1.1920928955078125e-7 and opp>width2:
     rows.append(dict(outline_index=oi,vertex_index=k,point_mm=[pcbnew.ToMM(x)for x in pt],prior_mm=[pcbnew.ToMM(x)for x in pp],after_mm=[pcbnew.ToMM(x)for x in pa],literal_integer_points=[pt,pp,pa],cos_angle=cosang,opposite_width_mm=math.sqrt(opp)/1e6))
  k+=offset
write(O/'location.json',dict(board_sha256=sha(B),input_sha256=inputs,primary_predicate_translated=True,native_DRC_authoritative=True,arc_error_mm=pcbnew.ARC_LOW_DEF_MM,width_tolerance_mm=.08,minimum_vertex_length_mm=.0008,angle_tolerance_deg=20,all_B_copper_items=count,outer_outline_count=poly.OutlineCount(),elapsed_s=time.monotonic()-start,rows=rows));assert all(sha(Path(q))==h for q,h in inputs.items());print(json.dumps(rows),flush=True)
