"""Find ordinary all-layer sites on actual existing CORE fill outside dense via escape walls."""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[n]='2'
import hashlib,json,pickle,sys,uuid
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,r):p.write_text(json.dumps(r,indent=1)+'\n')
def parts(s):
 if s.is_empty:return[]
 if s.geom_type=='Polygon':return[s]
 return[p for q in getattr(s,'geoms',[])for p in parts(q)]
def root(gs,ref):return next(xs for xs in gs if any(q['kind']=='pad'and(q['ref'],q['pin'])==(ref,'2')for q in xs))
def main():
 parent=H/'joint-positive-head-signal-reference-mask-proposal-r83';mp=parent/'model.pkl';assert sha(parent/'receipt.json')=='ec4a2744f502fc250ecf5f5e0e04c6e043dd7b5b1fe916419231163e4aafaf33'and sha(mp)=='e9d67e30fd34bf5e42db2faa23b8c4c32ea11e8be9b8e414b8f8e5419fd2bd2c';g,h,b,z,current=pickle.loads(mp.read_bytes());saved=pickle.loads((parent/'source-groups.pkl').read_bytes());source=root(saved['/CORE_1V2'],'L2001');main=next(xs for xs in saved['/CORE_1V2']if any(q['kind']=='pad'and q['ref']=='U1001'for q in xs));lground=root(saved['/LOGIC_GND'],'J11001');raw='/CORE_1V2';layer='In3.Cu';records,trees=F.build({**h,'zones':[]});out=H/'CORE-ordinary-external-fill-port-nominations-r90';assert not out.exists();out.mkdir();rows=[];proposals=[]
 local_ground=max(float(q['clearance_mm'])for q in h['zones']if C.norm(q['net'])=='/LOGIC_GND');reference_guard=.25+max(.15,local_ground)+.025+.000100
 for label,xs,window in[('main',main,box(170,92.5,181,100)),('source',source,box(226,89,241,101))]:
  search=window.buffer(2);actual=unary_union([q['shape']for q in xs if q['layer']==layer and q['kind']!='via']);candidate=set_precision(window.intersection(actual.buffer(-.25-.000100)),1e-6);obs=[]
  for l in('F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'):
   for i in trees[l].query(search,predicate='intersects'):
    q=records[l][int(i)]
    if q['net']==raw:continue
    gap=.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][raw]else .6;guard=.25+gap+.025+.000100
    if q['kind']=='track':t=q['source'];sh=N.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+guard)
    elif q['kind']=='via':v=q['source'];sh=N.bounded_disk(v,v['d']/2+guard)
    else:sh=N.bounded_buffer(q['shape'],guard)
    obs.append(sh)
  for q in z:
   if q['net']==raw or C.norm(q['net'])=='/LOGIC_GND' or not search.intersects(q['shape']):continue
   gap=.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][raw]else .6;obs.append(N.bounded_buffer(q['zone_outline_shape'],.25+max(gap,float(q.get('clearance_mm',.15)))+.025+.000100))
  for native in current['zones']:
   if C.norm(native['net'])in('/CORE_1V2','/LOGIC_GND'):continue
   for rings in native['fills'].values():
    for sh in C.poly(rings):
     if search.intersects(sh):obs.append(N.bounded_buffer(sh,.25+(.15 if h['domains_normalized'][C.norm(native['net'])]==h['domains_normalized'][raw]else .6)+.025+.000100))
  for v in h['vias']:
   if search.intersects(Point(v['x'],v['y'])):obs.append(N.bounded_disk(v,v['drill']/2+.1+.275+.000100))
  for pad in h['pads']:
   for rings in pad['layers'].values():
    if pad.get('smd'):obs.extend(N.bounded_buffer(sh,.1+.275+.000100)for sh in C.poly(rings)if search.intersects(sh))
   obs.extend(N.bounded_buffer(sh,.1+.275+.000100)for sh in C.poly(pad.get('hole')or[])if search.intersects(sh))
  for rule in h['rule_areas']:
   if rule.get('no_vias')or rule.get('no_pads'):obs.extend(N.bounded_buffer(sh,.25+.025+.000100)for sh in C.poly(rule['outline'])if search.intersects(sh))
  shadows=[]
  for outer,inner in[('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]:
   reference=unary_union([q['shape']for q in lground if q['kind']=='fill'and q['layer']==inner]).intersection(search)
   for t in h['tracks']:
    if t['layer']!=outer or C.norm(t['net'])=='/LOGIC_GND'or h['domains_normalized'][C.norm(t['net'])]!=h['domains_normalized']['/LOGIC_GND']:continue
    if max(t['a'][0],t['b'][0])<search.bounds[0]or min(t['a'][0],t['b'][0])>search.bounds[2]or max(t['a'][1],t['b'][1])<search.bounds[1]or min(t['a'][1],t['b'][1])>search.bounds[3]:continue
    covered=N.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2).intersection(reference)
    if not covered.is_empty:shadows.append(covered)
  if shadows:obs.append(N.bounded_buffer(unary_union(shadows),reference_guard))
  region=set_precision(candidate.difference(unary_union(obs)),1e-6);(out/(label+'-ordinary-site-region.wkb')).write_bytes(region.wkb);sites=[]
  for face in sorted(parts(region),key=lambda x:-x.area)[:8]:
   p=face.representative_point();xy=[round(p.x,6),round(p.y,6)]
   if not region.covers(Point(xy)):continue
   uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-CORE-external-fill-r90/'+label+'/'+repr(xy)));v={'uuid':uid,'net':raw,'x':xy[0],'y':xy[1],'d':.5,'drill':.2,'flashed':['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'],'prospective_not_native':True};ann=N.bounded_disk(v,.25).difference(N.bounded_disk(v,.1));overlap=ann.intersection(actual).area
   if overlap<.01:continue
   sites.append({'via':v,'actual_existing_CORE_In3_annular_Cu_overlap_mm2':overlap,'site_face_area_mm2':face.area});proposals.append({'side':label,'via':v,'actual_Cu_overlap_mm2':overlap})
  rows.append({'side':label,'legal_site_area_mm2':region.area,'sites':sites,'all6_actual_foreign_Cu_all_held_planes_all_source_SMDs_every_drill_native_keepouts_hard':True,'actual_old_F_In1_B_In4_body_shadows_guard_mm':reference_guard});put(out/'checkpoint.json',rows);print('R90_EXTERNAL_PORTS',label,region.area,len(sites),flush=True)
 (out/'prospective-new-ordinary-ports.pkl').write_bytes(pickle.dumps(proposals,protocol=5));put(out/'receipt.json',{'verdict':'PROSPECTIVE_ORDINARY_CORE_EXTERNAL_FILL_PORTS_ONLY','parent_model_sha256':sha(mp),'sides':rows,'prospective_ports_sha256':sha(out/'prospective-new-ordinary-ports.pkl'),'required_new_ordinary_barrels_diameter_drill_mm':[.5,.2],'full_fitted_CORE1V2_load_A':.8,'no_old_barrel_unsuppression_or_native_Cu_pad_hole_outline_edits':True,'selected_pair_layer_feed_all77_contacts_full_source_current_return_drop_thermal_stability_native_DRC':'OPEN','no_site_region_is_proof_of_global_no_path':True,'native_jobs':0,'adopted':False});print('R90_PORT_NOMINATION_FROZEN',sha(out/'receipt.json'),flush=True)
if __name__=='__main__':main()
