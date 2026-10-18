"""Exact current DI15 separator and nine owned fault-track coupled diagnosis."""
import sys,json,pickle,math,time,collections
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import audit_c10036_r24_full_independent_r30 as Q
import construct_di6_direct_source_escape_r5 as K
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
C,G,N=A.C,A.G,A.N
NET='/motherboard_di/DI15_LOGIC';FAULT='/motherboard_io_control/DI_SENSOR_G2_FAULT';GND='/LOGIC_GND'
def main():
 started=time.monotonic();out=HERE/'di15-fault-transport-coupling-diagnostic-r42.json';assert not out.exists();A.read(__file__)
 rp=HERE/'di15-joint-r11-In3-existing-return-nomination-r38.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='19fc476d7016caeb76e4413157754b35a327d03bdcea988950612344c1a5d519'
 lr=A.read(r['saved_local_site_checkpoint']);assert C.sha(lr)=='7f454fd9404c280a61c12eed5be338b41bacd04be58a27223e35baa17645d18c';local=pickle.loads(lr);cr=A.read(HERE/'di15-current-joint-r11-projection-r34.pkl');assert C.sha(cr)==r['exact_DI6_delta_only_current_checkpoint_sha256']=='ca01c67961d85d528014511defbc03cf0d5da4776d273e407c22cac5207b7451';cur=pickle.loads(cr);h=cur['h'];before=cur['after'];zones=cur['zones'];refs=local['refs'];win=local['window'];domain=h['domains_normalized'];tracks={t['uuid']:t for t in h['tracks']}
 cg=json.loads(A.read(HERE/'conflict-graph.json'));row=next(q for q in cg['lost_route_rows'] if q['net']==NET);remove=set(row['blocking_nets'][FAULT]['item_uuids']);assert len(remove)==9 and remove<=set(tracks)
 source=A.read(cur['binding']['exact_native_discrete_board_file']);assert C.sha(source)==r['source_parent_sha256'];identity=N.SourceNets(source);inv=C.inventory(source);owned=[]
 for u in sorted(remove):
  q=G.parse(u,inv[4][u],{});t=tracks[u];assert q['kind']=='segment' and q['net']==FAULT and q['layer']=='In3.Cu';assert(t['a'],t['b'],t['w'],t['layer'],t['net'])==(q['a'],q['b'],q['w'],q['layer'],identity.raw(FAULT));owned.append({'UUID':u,'exact_native_raw_chunk':inv[4][u].decode(),'parsed':{k:v for k,v in q.items() if k!='shape'},'exact_shape_WKB_sha256':C.sha(q['shape'].wkb)})
 sourcepart=local['transport_pieces'][7];targetpart=local['transport_pieces'][15];a,b=nearest_points(sourcepart,targetpart);connector=LineString([a,b]);separators=[]
 for q in local['records']['In3.Cu']:
  n=L.norm(q['net']);gap=.15 if domain.get(n)==domain.get(NET) else .6;mask=q['shape'].buffer(gap+.030+.105,quad_segs=128)
  if mask.intersects(connector):separators.append({'UUID':q['uuid'],'kind':q['kind'],'raw_net':q['net'],'connector_distance_to_Cu_mm':q['shape'].distance(connector),'owned_original_fault_blocker':q['uuid'] in remove})
 def free_without_owned(layer):
  obs=[]
  for q in local['records'][layer]:
   n=L.norm(q['net'])
   if n==NET or q['uuid'] in remove:continue
   gap=.15 if domain.get(n)==domain.get(NET) else .6;obs.append(q['shape'].buffer(gap+.030,quad_segs=128))
  for z in before['zones']:
   n=L.norm(z['net']);gap=.15 if domain.get(n)==domain.get(NET) else .6
   if n==NET or gap==.15:continue
   for sh in L.poly(z['fills'].get(layer,[])):
    if sh.distance(win)<2:obs.append(sh.buffer(max(gap,float(z.get('clearance_mm',.15)))+.030,quad_segs=128))
  for z in zones:
   n=L.norm(z['net'])
   if z['layer']!=layer or n==NET or z['shape'].distance(win)>2:continue
   gap=.15 if domain.get(n)==domain.get(NET) else .6;obs.append(z['shape'].buffer(max(gap,float(z.get('clearance_mm',.15)))+.030,quad_segs=128))
  for v in h['vias']:
   if L.norm(v['net'])!=NET and Point(v['x'],v['y']).distance(win)<2:obs.append(Point(v['x'],v['y']).buffer(v['drill']/2+.280,quad_segs=128))
  for p in h['pads']:
   if L.norm(p['net'])==NET:continue
   for sh in L.poly(p.get('hole') or []):
    if sh.distance(win)<2:obs.append(sh.buffer(.280,quad_segs=128))
  obs += [q['shape'].buffer(.025,quad_segs=128) for q in local['hard'] if q['no_tracks'] and layer in q['layers'] and NET not in q['exempt']]
  return win.difference(unary_union(obs)).buffer(-.105).intersection(refs[layer].buffer(-.105))
 print('DI15_EXACT_NINE_FAULT_CHUNKS_RELEASED_IN_MEMORY_ONLY',flush=True);free=free_without_owned('In3.Cu');sp=local['source_attachments'][0];dp=local['target_attachments'][0];sf=unary_union([p for p in K.pieces(local['free'][NET,'F.Cu']) if p.covers(Point(sp['at_mm']))]);df=unary_union([p for p in K.pieces(local['free'][NET,'F.Cu']) if p.covers(Point(dp['at_mm']))]);sr=local['via'][NET].intersection(sf).intersection(Point(local['sourcepad'].centroid).buffer(5,quad_segs=128));dr=local['via'][NET].intersection(df).intersection(Point(local['targetpad'].centroid).buffer(5,quad_segs=128));components=[]
 for i,p in enumerate(K.pieces(free)):
  aa=sr.intersection(p);bb=dr.intersection(p)
  if aa.is_empty and bb.is_empty:continue
  components.append({'component':i,'component_area_mm2':p.area,'source_via_area_mm2':aa.area,'target_via_area_mm2':bb.area,'common_transport_after_only_nine_owned_removals':not aa.is_empty and not bb.is_empty,'source_sites':K.sites(aa,[118.45,90.75],4),'target_sites':K.sites(bb,[131.25,112.35],4)})
 ou,oldgroups=Q.physical(before,FAULT);afterremove={**before,'tracks':[t for t in before['tracks'] if t['uuid'] not in remove]};nu,groups=Q.physical(afterremove,FAULT);changed=[]
 for i,xs in enumerate(oldgroups):
  oldkeys=Q.discrete_keys(xs);retained=oldkeys-{('track',u) for u in remove};fragments=[]
  for j,ys in enumerate(groups):
   keys=Q.discrete_keys(ys)
   if retained&keys:fragments.append({'component':j,'retained_keys':[list(k) for k in sorted(retained&keys)],'physical_pad_UUIDs':[q['uuid'] for q in ys if q['kind']=='pad'],'retained_vias':[{'UUID':v['uuid'],'at_mm':[v['x'],v['y']],'d_mm':v['d'],'drill_mm':v['drill'],'flashes':v.get('flashed')} for v in h['vias'] if('via',v['uuid']) in keys]})
  if oldkeys&{('track',u) for u in remove}:changed.append({'old_component':i,'retained_contact_fragments_to_rejoin':fragments})
 saved=HERE/'di15-r42-nine-removal-transport-checkpoint.pkl';assert not saved.exists();saved.write_bytes(pickle.dumps({'transport_free':free,'source_region':sr,'target_region':dr,'owned_remove_UUIDs':remove,'fault_old_groups':oldgroups,'fault_after_remove_groups':groups,'local_R38_sha256':C.sha(lr),'current_R34_sha256':C.sha(cr)},protocol=5))
 report={'verdict':'EXACT_DI15_FAULT_COUPLED_TRANSPORT_DIAGNOSED_REPLACEMENT_NOT_YET_CONSTRUCTED','R38_sha256':C.sha(A.read(rp)),'current_ROOT_R11_model_sha256':cur['joint_R11_model_sha256'],'current_only_DI6_checkpoint_sha256':C.sha(cr),'source_parent_sha256':C.sha(source),'owned_nine_exact_original_fault_chunks':owned,'original_source_target_transport_separation_mm':connector.length,'closest_transport_connector_mm':list(connector.coords),'closest_connector_actual_discrete_separators':separators,'transport_components_after_only_exact_nine_removals':components,'current_fault_surviving_physical_contacts':changed,'saved_transport_checkpoint':str(saved),'saved_transport_checkpoint_sha256':C.sha(saved.read_bytes()),'new_signal_and_fault_wholebody_reference_pairedreturn_ordinarycontact_current_r06_r07_native_gates':'OPEN','removed_items_in_memory_only':True,'native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'separator':separators,'components':components,'fault_fragments':changed}),flush=True)
if __name__=='__main__':main()
