"""Exact local AUX5 detour with fixed FAULT pin and an explicit moved supply pad."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import copy,json,pickle,sys,uuid,re
from pathlib import Path
from shapely import set_precision
from shapely.affinity import rotate
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
import contact_layout as C
import fast_contacts as F
import tri_route as T
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import complete_geometry_r2 as G
import guarded_declared_settings_projection_r58 as P
O=H/'R11054-fault-preserving-exact-AUX-wall-r192'
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def polys(s):return [s] if s.geom_type=='Polygon' else [q for q in getattr(s,'geoms',[]) if q.geom_type=='Polygon']
def main():
 assert not O.exists();O.mkdir();B=H.parent/'sbc-power/SAFE-repaired-owned-zone-normalization-r160/model.pkl';assert sha(B)=='d7e0fe77a8ee25fef4e45538da29aa72809c102192879330c7a5b32a200e711b'
 g,h,b,z,c=pickle.loads(B.read_bytes());fp=next(q for q in h['footprints'] if q['ref']=='R11054');pads=[q for q in h['pads'] if q['ref']=='R11054'];p1=next(q for q in pads if q['num']=='1');p2=next(q for q in pads if q['num']=='2');origin=(p2['x'],p2['y']);p1new=set_precision(rotate(unary_union(C.poly(p1['layers']['F.Cu'])),180,origin=origin),1e-6);p2old=unary_union(C.poly(p2['layers']['F.Cu']));assert p2old.equals(set_precision(rotate(p2old,180,origin=origin),1e-6))
 owned=[next(t for t in h['tracks'] if t['uuid']==u) for u in ('b81b7cf8-f4fa-48b7-ac89-e03f782cac0a','b16daa8b-7cb9-40bd-b78f-bcd0efb732a0')];a=owned[0]['a'];bb=owned[1]['b'];net=owned[0]['net'];assert net==owned[1]['net']=='/motherboard_motors{slash}AUX_5V_B';assert owned[0]['b']==owned[1]['a'];assert all(t['w']==.2 and t['layer']=='F.Cu' for t in owned)
 hh=copy.deepcopy(h);hh['tracks']=[t for t in hh['tracks'] if t['uuid'] not in {q['uuid'] for q in owned}];pp=next(q for q in hh['pads'] if q['uuid']==p1['uuid']);xy=rotate(Point(p1['x'],p1['y']),180,origin=origin);pp['x'],pp['y']=round(xy.x,6),round(xy.y,6);pp['layers']['F.Cu']=G.records(p1new)
 ff=next(q for q in hh['footprints'] if q['ref']==fp['ref']);fxy=rotate(Point(fp['x'],fp['y']),180,origin=origin);ff['x'],ff['y']=round(fxy.x,6),round(fxy.y,6);ff['rot']=(ff.get('rot',0)+180)%360;newcourt=set_precision(rotate(unary_union(C.poly(fp['courtyard']['F'])),180,origin=origin),1e-6);ff['courtyard']['F']=G.records(newcourt)
 rec,trees=F.build({**hh,'zones':[]});tm={q['uuid']:q for q in hh['tracks']};vm={q['uuid']:q for q in hh['vias']};oldbody=unary_union([C.body(q) for q in owned]);outside=[]
 for j in trees['F.Cu'].query(oldbody.buffer(.000002),predicate='intersects'):
  q=rec['F.Cu'][int(j)]
  if q['net']==net and q['shape'].distance(oldbody)<=.000002:outside.append(q)
 masks=[]
 for q in rec['F.Cu']:
  if q['net']==net:continue
  gap=G.gap(hh,net,q['net'])+.025+.1+.00002
  if q['kind']=='track':t=tm[q['uuid']];m=P.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+gap)
  elif q['kind']=='via':v=vm[q['uuid']];m=P.bounded_buffer(Point(v['x'],v['y']),v['d']/2+gap)
  else:m=P.bounded_buffer(q['shape'],gap)
  masks.append(m)
 for q in z:
  if q['layer']=='F.Cu' and q['net']!=net:masks.append(P.bounded_buffer(q['shape'],max(G.gap(hh,net,q['net']),float(q.get('clearance_mm',.15)))+.025+.1+.00002))
 for q in hh['rule_areas']:
  if q.get('no_tracks') and 'F.Cu' in q['layers']:masks.extend(P.bounded_buffer(s,.025+.1+.00002) for s in C.poly(q['outline']))
 res=json.loads((C.BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text(encoding='utf-8'));dru=(C.BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text(encoding='utf-8');exceptions={}
 for line in dru.splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
  if m:exceptions[m[1]]={C.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
 for q in res['keepouts']:
  if 'F.Cu' in q['layers'] and C.norm(net) not in exceptions.get(q['name'],set()):masks.extend(P.bounded_buffer(s,.025+.1+.00002) for s in C.poly(q['outline']))
 from shapely.strtree import STRtree
 mt=STRtree(masks);outline=unary_union(C.poly(hh['outline'])).buffer(-.526);attempts=[];answer=None
 for margin in (1.5,3.,6.,12.):
  win=box(min(a[0],bb[0])-margin,min(a[1],bb[1])-margin,max(a[0],bb[0])+margin,max(a[1],bb[1])+margin).intersection(outline);ii=mt.query(win,predicate='intersects');free=set_precision(win.difference(unary_union([masks[int(j)] for j in ii])),1e-6);parts=[q for q in polys(free) if q.covers(Point(a)) and q.covers(Point(bb))];row={'margin_mm':margin,'joint_faces':len(parts),'start_in_free':free.covers(Point(a)),'end_in_free':free.covers(Point(bb))};attempts.append(row);print('R192',row,flush=True)
  if not parts:continue
  part=max(parts,key=lambda q:q.area);pts,search=T.route(part,a,bb);pts=[[round(x,6),round(y,6)] for x,y in pts];line=LineString(pts);body=P.bounded_buffer(line,.1);assert free.covers(line);assert all(P.bounded_buffer(LineString([u,v]),.1).distance(q['shape'])+1e-10>=G.gap(hh,net,q['net'])+.025 for u,v in zip(pts,pts[1:]) for q in rec['F.Cu'] if q['net']!=net and q['kind']=='pad')
  tracks=[{**owned[0],'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller-R11054-AUX-exact-r192/{i}')),'a':u,'b':v,'prospective_not_native':True} for i,(u,v) in enumerate(zip(pts,pts[1:])) if u!=v];lost=[q['uuid'] for q in outside if not body.intersects(q['shape'])];assert not lost
  answer={'tracks':tracks,'pad1':pp,'footprint':ff,'new_courtyard':newcourt,'route':{'points_mm':pts,'length_mm':line.length,'width_mm':.2,'search':search},'outside_contact_losses':lost};(O/'nomination.pkl').write_bytes(pickle.dumps(answer,protocol=5));break
 write(O/'receipt.json',{'verdict':'SCOPED_EXACT_DETOUR_NOMINATION_FULL_SOURCE_CURRENT_REFERENCE_NATIVE_OPEN' if answer else 'NO_EXACT_LOCAL_AUX_DETOUR_IN_DECLARED_WINDOWS','source_model_sha256':sha(B),'owned_original_two_tracks':owned,'old_outside_contact_ledger':[{k:v for k,v in q.items() if k!='shape'} for q in outside],'old_pad1':p1,'new_pad1':pp,'old_pad2':p2,'pin2_full_raw_geometry_and_BOM_limits_unchanged':True,'old_FP':fp,'new_FP':ff,'attempts':attempts,'nomination_sha256':sha(O/'nomination.pkl') if answer else None,'new_route':answer['route'] if answer else None,'width_preserved_mm':.2,'new_holes':0,'native_jobs':0,'board_written':False,'complete_AUX_branch_current_and_drop_and_old_reference_and_full76_contact_gates':'OPEN'})
 print('R192_RECEIPT',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
