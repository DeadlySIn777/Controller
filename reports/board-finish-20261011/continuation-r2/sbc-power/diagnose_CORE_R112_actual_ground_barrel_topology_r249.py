"""Exact drill-subtracted ground faces and literal cross-layer return topology.

This identifies actual route obligations before any return resistance is
granted. Plane-face nodes are topological, never zero-ohm electrical models.
"""
import hashlib,json,pickle,sys,math,traceback,collections,heapq
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in('sbc-power','field-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
import guarded_declared_settings_projection_r58 as GP
O=H/'sbc-power/CORE-R112-exact-ground-cross-layer-topology-r249'
LS=('F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1)+'\n')
def pieces(sh):return[sh]if sh.geom_type=='Polygon'else[p for p in getattr(sh,'geoms',[])if p.geom_type=='Polygon']
def main():
 assert not O.exists();O.mkdir();mp=H/'CORE-wide-reserved-IO3-immutable-R214-materialized-r112/model.pkl';assert sha(mp)=='6312b10a88b2d3614e21760d1709866d2417b419d418e20e09055eb13b8e3b7e';g,h,b,z,c=pickle.loads(mp.read_bytes());gs=pickle.loads((mp.parent/'groups.pkl').read_bytes());lg=next(xs for xs in gs['/LOGIC_GND']if any(q['kind']=='pad'and(q['ref'],q['pin'])==('J11001','2')for q in xs));vias={v['uuid']:v for v in h['vias']};holes=[GP.bounded_disk(v,v['drill']/2+.00000002)for v in h['vias']]+[sh.buffer(.00000002)for p in h['pads']for sh in C.poly(p.get('hole')or[])];ht=STRtree(holes);parts={};nodes={};trees={};face_rows=[];graph=collections.defaultdict(list)
 for l in LS:
  bodies=[q['shape']for q in lg if q['layer']==l];sh=unary_union(bodies);removed=unary_union([holes[int(i)]for i in ht.query(sh,predicate='intersects')]);sh=sh.difference(removed);ps=pieces(sh);parts[l]=ps;trees[l]=STRtree(ps);nodes[l]=[(l,i)for i in range(len(ps))];f=O/(l+'-exact-drilled-source-ground-union.wkb');f.write_bytes(sh.wkb);face_rows.extend({'node':[l,i],'area_mm2':p.area,'bounds':list(p.bounds),'source_record_union_WKB_sha256':sha(f),'actual_drill_circumscribed_20nm_voids':True}for i,p in enumerate(ps));print('R249_GROUND_FACES',l,len(ps),sh.area,flush=True)
 def contacts(l,body):return[(nodes[l][int(i)],body.intersection(parts[l][int(i)]).area)for i in trees[l].query(body,predicate='intersects')if body.intersection(parts[l][int(i)]).area>0]
 barrel_rows=[]
 for v in h['vias']:
  if v['net']!='/LOGIC_GND':continue
  p=Point(v['x'],v['y']);ann=p.buffer(v['d']/2-.00000002,quad_segs=128).difference(GP.bounded_disk(v,v['drill']/2+.00000002));cc=[(node,a)for l in v['flashed']for node,a in contacts(l,ann)];native=next((q for q in g['vias']if q['uuid']==v['uuid']),None);record={'UUID':v['uuid'],'at':[v['x'],v['y']],'d_mm':v['d'],'drill_mm':v['drill'],'flashed_layers':v['flashed'],'exact_native_original_record':native,'contacts':[{'face':list(n),'finite_annular_Cu_mm2':a}for n,a in cc],'prospective_layer_or_new_via_scope_requires_native':native is None or native.get('flashed')!=v['flashed']}
  if len({n[0]for n,a in cc})<2:continue
  barrel_rows.append(record)
  for a,area in cc:
   for bb,ar in cc:
    if a==bb:continue
    witness={'kind':'actual_or_explicit_prospective_ground_via_barrel','UUID':v['uuid'],'at':[v['x'],v['y']],'source_face':list(a),'target_face':list(bb),'source_finite_annular_Cu_mm2':area,'target_finite_annular_Cu_mm2':ar,'actual_masks_from_record_not_all6_assumption':True,'native_scope_required':record['prospective_layer_or_new_via_scope_requires_native']};graph[a].append((bb,abs(LS.index(a[0])-LS.index(bb[0])),witness))
 # Native plated pads must also retain their literal barrel continuity.
 for p in h['pads']:
  if p['net']!='/LOGIC_GND'or not p.get('hole'):continue
  hh=unary_union(C.poly(p['hole']));cc=[]
  for l,rs in p['layers'].items():
   body=unary_union(C.poly(rs)).difference(hh.buffer(.00000002));cc.extend(contacts(l,body))
  for a,area in cc:
   for bb,ar in cc:
    if a==bb:continue
    graph[a].append((bb,abs(LS.index(a[0])-LS.index(bb[0])),{'kind':'literal_plated_ground_pad_barrel','UUID':p['uuid'],'ref':p['ref'],'pin':p['num'],'source_face':list(a),'target_face':list(bb),'source_Cu_mm2':area,'target_Cu_mm2':ar}))
 def padfaces(p):return[list(n)for l,rs in p['layers'].items()for n,a in contacts(l,unary_union(C.poly(rs)))if a>0]
 sp=next(p for p in h['pads']if(p['ref'],p['num'])==('U2001','4'));assert sp['net']=='/LOGIC_GND';starts=[tuple(n)for n in padfaces(sp)];assert starts;dist={n:0. for n in starts};prev={};queue=[(0.,n)for n in starts];heapq.heapify(queue)
 while queue:
  cost,n=heapq.heappop(queue)
  if cost!=dist[n]:continue
  for nn,w,e in graph[n]:
   cand=cost+w
   if cand<dist.get(nn,float('inf')):dist[nn]=cand;prev[nn]=(n,e);heapq.heappush(queue,(cand,nn))
 endpoints=[]
 for p in h['pads']:
  if p['net']!='/LOGIC_GND'or p['ref']not in('U1001','C2002','U2001'):continue
  faces=[tuple(n)for n in padfaces(p)];reachable=[n for n in faces if n in dist];best=min(reachable,key=lambda n:dist[n])if reachable else None;route=[];nn=best
  while nn in prev:old,e=prev[nn];route.append(e);nn=old
  route.reverse();endpoints.append({'ref':p['ref'],'pin':p['num'],'UUID':p['uuid'],'at':[p['x'],p['y']],'face_nodes':[list(n)for n in faces],'literal_U2001_GND4_cross_layer_topological_path_exists':bool(reachable),'fewest_layer_crossing_witness_ONLY_not_shortest_or_lowest_resistance_route':route,'all_within_plane_lengths_widths_source_current_and_local_potential_remain_electrical_obligations':True})
 # Diagnose why the actual nearest paired ports cannot be modelled as one
 # local straight sheet, without substituting them for device ground pins.
 paired=[]
 for l in LS:
  rows=[]
  for uid in('c68f8d3c-e3bc-4deb-ad5f-9208c48cd820','1fc85fd7-343f-4eef-968f-235ed3564d01'):
   v=vias[uid];p=Point(v['x'],v['y']);ann=p.buffer(v['d']/2-.00000002,quad_segs=128).difference(GP.bounded_disk(v,v['drill']/2+.00000002));rows.append({'UUID':uid,'actual_flashed_on_layer':l in v['flashed'],'faces':[list(n)for n,a in contacts(l,ann)]})
  paired.append({'layer':l,'port_face_rows':rows,'same_exact_global_layer_face':bool(set(map(tuple,rows[0]['faces']))&set(map(tuple,rows[1]['faces'])))})
 put(O/'physical-face-rows.json',face_rows);put(O/'exact-ground-barrel-contact-rows.json',barrel_rows);put(O/'actual-regulator-FPGA-return-route-witnesses.json',endpoints);put(O/'two-paired-port-global-face-diagnosis.json',paired)
 put(O/'receipt.json',{'verdict':'EXACT_GROUND_COMPONENT_BARREL_RETURN_TOPOLOGY_NOT_ZERO_OHM_MODEL','exact_R112_model_sha256':sha(mp),'source_pin':'U2001.4 actual GND_4','endpoint_count':len(endpoints),'U1001_ground_pads':sum(e['ref']=='U1001'for e in endpoints),'ground_endpoints_without_cross_layer_witness':[{'ref':e['ref'],'pin':e['pin'],'UUID':e['UUID']}for e in endpoints if not e['literal_U2001_GND4_cross_layer_topological_path_exists']],'paired_port_layer_faces':paired,'endpoint_witness_sha256':sha(O/'actual-regulator-FPGA-return-route-witnesses.json'),'barrel_contact_sha256':sha(O/'exact-ground-barrel-contact-rows.json'),'every_nonempty_finite_contact_retained_no_area_threshold_waiver':True,'minimum_layer_crossing_weight_has_NO_electrical_resistance_rating_meaning':True,'return_mesh_all_actual_FPGA_pin_loads_and_each_intermediate_sheet_geodesic_narrow_neck_ordinary_barrel_current_shared_logic_potential_and_transient_loop':'OPEN','full_CORE_0p8A_IO3_2A_retained':True,'board_written':False,'native_jobs':0,'script_sha256':sha(__file__)})
 print('R249_COMPLETE',sha(O/'receipt.json'),sum(not e['literal_U2001_GND4_cross_layer_topological_path_exists']for e in endpoints),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
