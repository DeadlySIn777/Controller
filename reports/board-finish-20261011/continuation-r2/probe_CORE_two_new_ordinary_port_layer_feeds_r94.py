"""Finite ordinary-via pair route proposals; all actual antipad and PDN gates stay open."""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='2'
import hashlib,json,pickle,sys,uuid
from pathlib import Path
from shapely import set_precision,get_num_coordinates
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent
for folder in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/folder))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
import restore_SAFE_generated_precision_states_r168 as PS
import tri_route as T
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(sh):return hashlib.sha256(sh.wkb).hexdigest()
def put(p,d):p.write_text(json.dumps(d,indent=1)+'\n')
def parts(sh):
 if sh.is_empty:return[]
 if sh.geom_type=='Polygon':return[sh]
 return[p for q in getattr(sh,'geoms',[])for p in parts(q)]
def root(gs,ref):return next(xs for xs in gs if any(q['kind']=='pad'and(q['ref'],q['pin'])==(ref,'2')for q in xs))
def main():
 parent=H/'joint-positive-head-signal-reference-mask-proposal-r83';mp=parent/'model.pkl';assert sha(mp)=='e9d67e30fd34bf5e42db2faa23b8c4c32ea11e8be9b8e414b8f8e5419fd2bd2c';assert sha(parent/'receipt.json')=='ec4a2744f502fc250ecf5f5e0e04c6e043dd7b5b1fe916419231163e4aafaf33'
 ports=H/'CORE-native-IO3-antipad-external-port-nominees-r93';assert sha(ports/'receipt.json')=='a206d92084e3f64d92d17c1ebb841e9cc9600d9dd6c9961e5ab4c97ac891dc06';main_ports=pickle.loads((ports/'main-prospective-new-ordinary-ports.pkl').read_bytes());source_ports=pickle.loads((ports/'source-prospective-new-ordinary-ports.pkl').read_bytes());assert len(main_ports)==len(source_ports)==1
 pair=[source_ports[0]['via'],main_ports[0]['via']];assert {q['uuid']for q in pair}=={'04d05723-e107-55db-ab38-b494ef73fd44','ba6844fd-46da-52c3-a576-bf0dae97cc04'}
 g,h,b,z,current=pickle.loads(mp.read_bytes());replay=PS.restore_bound_generated_precision_states(b,z);groups=pickle.loads((parent/'source-groups.pkl').read_bytes());source=root(groups['/CORE_1V2'],'L2001');target=next(xs for xs in groups['/CORE_1V2']if any(q['kind']=='pad'and q['ref']=='U1001'for q in xs));lg=root(groups['/LOGIC_GND'],'J11001');raw='/CORE_1V2';out=H/'CORE-two-new-ordinary-port-layer-feed-proposals-r94';assert not out.exists();out.mkdir();put(out/'parent-generated-role-replay.json',replay)
 overlaps=[]
 for via,xs in zip(pair,[source,target]):
  ann=N.bounded_disk(via,.25).difference(N.bounded_disk(via,.1));actual=unary_union([q['shape']for q in xs if q['layer']=='In3.Cu'and q['kind']!='via']);area=ann.intersection(actual).area;assert area>.01;overlaps.append({'via_UUID':via['uuid'],'actual_existing_source_or_main_CORE_In3_annular_overlap_mm2':area,'via_diameter_drill_mm':[.5,.2]})
 put(out/'actual-native-In3-landing-overlaps.json',overlaps);records,trees=F.build({**h,'zones':[]});window=box(153,70,250,126);search=window.buffer(2);board=unary_union(C.poly(h['outline'])).buffer(-.526);attempts=[];routes=[];layer_grids=[];allowed_native='54921f4b-0308-4821-9549-ff9360bf05ca';cuttable={'In2.Cu':'6b1d4fb8-13a7-596c-bd98-8e6c89a155df','In3.Cu':'47888e35-9a96-5393-b579-7c0b4a64ec93'}
 # Exact generated In2 LG UUID is bound from the parent's actual role ledger,
 # rather than guessing an incomplete prefix from a previous status note.
 in2=[q for q in z if q['layer']=='In2.Cu'and C.norm(q['net'])=='/LOGIC_GND'and q['uuid'].startswith('6b1d4fb8-')];assert len(in2)==1;cuttable['In2.Cu']=in2[0]['uuid']
 for layer in ('In2.Cu','F.Cu','B.Cu','In4.Cu','In3.Cu','In1.Cu'):
  obs=[]
  for idx in trees[layer].query(search,predicate='intersects'):
   row=records[layer][int(idx)]
   if row['net']==raw:continue
   guard=(.15 if h['domains_normalized'][C.norm(row['net'])]==h['domains_normalized'][raw]else .6)+.025+.000100
   if row['kind']=='track':t=row['source'];shape=N.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+guard)
   elif row['kind']=='via':v=row['source'];shape=N.bounded_disk(v,v['d']/2+guard)
   else:shape=N.bounded_buffer(row['shape'],guard)
   obs.append(shape)
  for q in z:
   if q['layer']!=layer or q['net']==raw or q['uuid']==cuttable.get(layer)or not search.intersects(q['shape']):continue
   gap=.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][raw]else .6;obs.append(N.bounded_buffer(q['zone_outline_shape'],max(gap,float(q.get('clearance_mm',.15)))+.025+.000100))
  owned_UUIDs={q['uuid']for q in z}
  for native in current['zones']:
   if C.norm(native['net'])in('/CORE_1V2','/LOGIC_GND')or native['uuid']in owned_UUIDs:continue
   if native['uuid']==allowed_native:
    assert native['net']=='/IO_3V3';continue
   gap=.15 if h['domains_normalized'][C.norm(native['net'])]==h['domains_normalized'][raw]else .6
   for shape in C.poly(native['fills'].get(layer,[])):
    if search.intersects(shape):obs.append(N.bounded_buffer(shape,max(gap,float(native.get('clearance_mm',.15)))+.025+.000100))
  for via in h['vias']:
   if via['net']!=raw and search.intersects(Point(via['x'],via['y'])):obs.append(N.bounded_disk(via,via['drill']/2+.275+.000100))
  for pad in h['pads']:
   if pad['net']!=raw:obs.extend(N.bounded_buffer(shape,.275+.000100)for shape in C.poly(pad.get('hole')or[])if search.intersects(shape))
  for rule in h['rule_areas']:
   if rule.get('no_zones')and layer in rule['layers']:obs.extend(N.bounded_buffer(shape,.025+.000100)for shape in C.poly(rule['outline'])if search.intersects(shape))
  # Existing outer signal bodies retain their exact already source-covered
  # portions. Only prospective new LG roles may be clipped elsewhere.
  outer={'In1.Cu':'F.Cu','In4.Cu':'B.Cu'}.get(layer)
  if outer:
   before_ref=unary_union([q['shape']for q in lg if q['kind']=='fill'and q['layer']==layer]).intersection(search);shadows=[]
   for track in h['tracks']:
    if track['layer']!=outer or C.norm(track['net'])=='/LOGIC_GND'or h['domains_normalized'][C.norm(track['net'])]!=h['domains_normalized']['/LOGIC_GND']:continue
    body=N.bounded_buffer(LineString([track['a'],track['b']]),track['w']/2);covered=body.intersection(before_ref)
    if not covered.is_empty:shadows.append(covered)
   if shadows:obs.append(N.bounded_buffer(unary_union(shadows),.175+.000100))
  legal=set_precision(window.intersection(board).difference(unary_union(obs)),1e-6);(out/(layer+'-legal.wkb')).write_bytes(legal.wkb);anns=[N.bounded_disk(v,.25).difference(N.bounded_disk(v,.1))for v in pair];print('R94_LAYER',layer,'portannareas',[round(legal.intersection(a).area,6)for a in anns],flush=True)
  for width in (4.,3.,2.,1.,.5,.35,.25):
   common=[]
   for face in parts(legal.buffer(-width/2-.000100)):
    aa=face.intersection(anns[0]);bb=face.intersection(anns[1])
    if aa.area>.01 and bb.area>.01:common.append((aa.distance(bb),face,aa,bb))
   attempts.append({'layer':layer,'minimum_CORE_body_width_mm':width,'common_port_faces':len(common)});put(out/'route-face-checkpoint.json',attempts)
   for distance,face,aa,bb in sorted(common,key=lambda x:x[0]):
    if get_num_coordinates(face)>5000:
     conservative=face.buffer(-.002).simplify(.0005,preserve_topology=True).intersection(face);choices=[q for q in parts(conservative)if q.intersection(aa).area>.01 and q.intersection(bb).area>.01]
     if not choices:continue
     face=max(choices,key=lambda q:q.area);aa=face.intersection(aa);bb=face.intersection(bb)
    a,end=nearest_points(aa,bb);chord=LineString([a,end]);print('R94_ROUTE',layer,width,distance,get_num_coordinates(face),flush=True)
    if face.covers(chord):points=list(chord.coords);proof={'method':'exact_covered_nearest_chord'}
    else:
     try:points,proof=T.route(face,tuple(a.coords[0]),tuple(end.coords[0]))
     except(AssertionError,ValueError):continue
    points=[[round(x,6),round(y,6)]for x,y in points];line=LineString(points)
    if not face.covers(line):continue
    core=N.bounded_buffer(line,width/2)
    if not legal.covers(core):continue
    native=set_precision(unary_union([q for q in parts(N.bounded_buffer(line,max(.6,width)).intersection(legal))if q.intersection(core).area>0]),1e-6);ownholes=unary_union([N.bounded_disk(v,v['drill']/2)for v in h['vias']+pair if v['net']==raw]+[shape for pad in h['pads']if pad['net']==raw for shape in C.poly(pad.get('hole')or[])]);physical=native.difference(ownholes)
    if any(physical.intersection(a).area<.01 for a in anns):continue
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-core-two-new-ordinary-feed-r94/'+layer+'/'+repr(points)));proposal={'uuid':uid,'net':raw,'layer':layer,'shape':physical,'zone_outline_shape':native,'priority':124,'clearance_mm':.15,'min_thickness_mm':.15,'pad_connect_mode':'FULL_SOLID','island_removal_mode':1,'physical_Cu_drill_subtracted':True,'label':'Two ordinary external-fill CORE ports R94'};routes.append({'zone':proposal,'source_to_main_points':points,'core_width_mm':width,'length_mm':line.length,'constructor':proof,'normal_IO3_native_antipad_proposal':allowed_native,'only_new_owned_LG_bounded_notch_proposed':cuttable.get(layer)});break
   if routes:break
  if routes:break
 (out/'proposed-discrete.pkl').write_bytes(pickle.dumps({'vias':pair if routes else[],'tracks':[]},protocol=5));(out/'proposed-route-and-zone.pkl').write_bytes(pickle.dumps(routes,protocol=5));put(out/'receipt.json',{'verdict':'FINITE_TWO_ORDINARY_CORE_PORT_FEED_CONSTRUCTOR_NOMINEE_FULL_GATES_OPEN'if routes else'NO_ACCEPTED_TWO_ORDINARY_CORE_PORT_FEED_IN_DECLARED_WINDOW','parent_model_sha256':sha(mp),'ordinary_port_nomination_receipt_sha256':sha(ports/'receipt.json'),'actual_existing_CORE_In3_landing_overlaps':overlaps,'routes':[{'zone_UUID':r['zone']['uuid'],'layer':r['zone']['layer'],'physical_WKB_sha256':digest(r['zone']['shape']),'core_width_mm':r['core_width_mm'],'length_mm':r['length_mm'],'normal_IO3_native_antipad_proposal':allowed_native,'only_new_owned_LG_notch':r['only_new_owned_LG_bounded_notch_proposed']}for r in routes],'attempts':attempts,'full_fitted_CORE1V2_A':.8,'full_IO3_A':2.,'actual_all6_new_ordinary_native_antipads_all77_contacts_direct_original_fill_contacts_source_no_loss_reference_current_drop_cap_loops_stability_thermal_native_DRC':'OPEN','original104_PDN_proposal_and_all_raw_reference_failed_ledgers_preserved':True,'native_jobs':0,'board_written':False,'adopted':False});print('R94_FINITE_FEED_PROPOSAL',len(routes),sha(out/'receipt.json'),flush=True)
if __name__=='__main__':main()
