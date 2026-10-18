"""Reconnect DI15's unaccepted new strip around exact retained DI13 copper.

Zero existing deletions or power carves. Only exact new GND reference/returns
are nominated; body/source/current/r06/native/SI remain separate gates.
"""
import sys,json,pickle,time,math,copy,uuid
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
for p in(H.parent/'field-power',H.parent/'sbc-power',H):sys.path.insert(0,str(p))
import audit_aux_exact_raw as A
import contact_layout as L
import construct_di6_direct_source_escape_r5 as K
import construct_DI15_DI13_actual_attachments_r138 as R
import audit_c10036_r24_full_independent_r30 as Q
import guarded_power_projection_r44 as Z
import audit_ao1_positive_operation_r4 as SERIAL
import tri_route as T
from shapely import set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
C=A.C;GND='/LOGIC_GND'
def main():
 started=time.monotonic();out=H/'DI15-new-only-reference-branches-r150.json';assert not out.exists();A.read(__file__);rp=H/'di15-safe-root-r42-DI6-bind-r118.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='bb171905c94a5795d7ae3e3ded2a367c4d02a4b463bf9c82b4c6c962126c69c6';raw=A.read(r['model_path']);assert C.sha(raw)==r['model_sha256'];cur=pickle.loads(raw);h0=cur['h'];source=A.read(cur['binding']['exact_native_discrete_board_file']);identity=A.N.SourceNets(source);inventory=C.inventory(source)
 r94p=H/'di15-zero-power-carve-reference-pieces-r94/receipt.json';rr=json.loads(A.read(r94p));assert C.sha(A.read(r94p))=='271c9f168df53b0fa35150cc40575aceea3ce528b1adce40bca9ec2b3e7c6e3f';raw=A.read(rr['source_only_model_file']);assert C.sha(raw)==rr['source_only_model_sha256'];saved=pickle.loads(raw);chosen=next(z for z in saved['new_zones'] if z['uuid']=='dfa413d0-8afc-5c3a-a113-b1ec1487b3b8');original=chosen['shape'];line=LineString(saved['points']);body=saved['body'];win=box(117,94,136,115);legal,maskledger=R.newzonelegal(h0,cur,win,set());island=set_precision(original.intersection(legal).buffer(-.000010,quad_segs=64),Z.GRID);assert legal.covers(island);centres=legal.buffer(-.155,quad_segs=128);islandcore=island.buffer(-.155,quad_segs=128);connected=unary_union([q for q in K.pieces(centres) if q.intersects(islandcore)]);overlap=line.intersection(cur['source_planes']['In1.Cu'].buffer(-.110,quad_segs=128)).intersection(connected)
 cpraw=A.read(H/'fresh-partial-annular-return-r108-physical-checkpoint.pkl');assert C.sha(cpraw)=='0aa98f5c476d32127623ca1de144bdca4e595527dc90b17db6b075af8a5be803';cp=pickle.loads(cpraw);assert cp['current']['h']['tracks']==h0['tracks'] and cp['current']['h']['vias']==h0['vias'] and cp['current']['h']['pads']==h0['pads'];reg=cp['physical_GND_return_region'].intersection(connected).intersection(overlap.buffer(.990,quad_segs=128));nominations=[]
 for site in K.sites(reg,[123.675923,103.21109],80):
  p=Point(site['at_mm']);ann=p.buffer(.25,quad_segs=128).difference(p.buffer(.1,quad_segs=128));areas={l:ann.intersection(cur['source_planes'][l].intersection(p.buffer(1))).area for l in('In1.Cu','In4.Cu')}
  if not all(a>.004 for a in areas.values()):continue
  shared=nearest_points(overlap,p)[0];nominations.append({**site,'existing_source_annular_contacts_mm2':areas,'proposed_handoff_point_mm':list(shared.coords)[0],'handoff_return_distance_mm':shared.distance(p)})
 print(json.dumps({'phase':'DI15_new_only_connected_reference','retained_DI13':True,'island_area_mm2':island.area,'new_only_island_trim_mm2':original.difference(island).area,'connected_legal_area_mm2':connected.area,'potential_overlap_length_mm':overlap.length,'ordinary_return_region_mm2':reg.area,'finite_return_nominees':len(nominations)}),flush=True);attempts=[];selected=None;exit_at=[128.695,109.614094]
 for entry in nominations[:20]:
  pos=entry['at_mm'];row={'entry_return':entry,'branch_attempts':[]};attempts.append(row);nv=[];chunks={};branches=[]
  for at in(pos,exit_at):
   p=Point(at);parts=[q for q in K.pieces(connected) if q.covers(p) and q.intersects(islandcore)];br={'return_at_mm':at,'connected_branch_components':len(parts)};row['branch_attempts'].append(br)
   if not parts:break
   attach=nearest_points(parts[0].intersection(islandcore),p)[0];points,search=T.route(parts[0],tuple(attach.coords)[0],tuple(at));points=[[round(x,6),round(y,6)] for x,y in points]
   if len(points)<2:break
   shape=Z.bounded_buffer(LineString(points),.15);br.update({'branch_points_mm':points,'branch_length_mm':LineString(points).length,'minimum_width_mm':.30,'shape_WKB_sha256':C.sha(shape.wkb),'strict_legal_covers':legal.covers(shape),'island_contact_mm2':shape.intersection(island).area,'search':search})
   if not legal.covers(shape) or shape.intersection(island).area<.004:break
   uid,ch=SERIAL.serial_via(identity,GND,at);assert uid not in inventory[3] and uid not in chunks;chunks[uid]=ch;nv.append({'uuid':uid,'net':identity.raw(GND),'x':at[0],'y':at[1],'d':.5,'drill':.2,'flashed':list(Q.LAYERS)});branches.append(shape)
  if len(branches)!=2:continue
  shape=island.union(unary_union(branches));uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/DI15/new-only-reference-r150/'+C.sha(shape.wkb)));z={**chosen,'uuid':uid,'shape':shape,'name':'DI15 new-only source reference R150 original DI13 retained'};h=copy.deepcopy(h0);h['vias']+=nv;after,ledger=R.projection(cur,h,[],nv,z);_,groups=Q.physical(after,GND);root=next(xs for xs in groups if any(q['kind']=='pad' and(q['ref'],str(q['pin']))==('J11001','2') for q in xs));refs={l:unary_union([q['shape'] for q in root if q['kind']=='fill' and q['layer']==l]) for l in('In1.Cu','In3.Cu','In4.Cu')};lost=sorted(Q.discrete_keys(cur['root'])-Q.discrete_keys(root));gap=body.difference(refs['In1.Cu'].union(refs['In3.Cu']));shared=line.intersection(refs['In1.Cu'].buffer(-.110,quad_segs=128)).intersection(refs['In3.Cu'].buffer(-.110,quad_segs=128));pairproof=[]
  for v in nv:
   p=Point(v['x'],v['y']);ann=p.buffer(.25,quad_segs=128).difference(p.buffer(.1,quad_segs=128));areas={l:ann.intersection(ref).area for l,ref in refs.items()};hand=nearest_points(shared,p)[0] if not shared.is_empty else Point();pairproof.append({'return_UUID':v['uuid'],'return_at_mm':[v['x'],v['y']],'finite_actual_J1_source_annular_contacts_mm2':areas,'actual_shared_handoff_point_mm':list(hand.coords)[0] if not hand.is_empty else None,'distance_mm':p.distance(hand) if not hand.is_empty else None,'guarded_handoff_signal_disk_source_coverage':{l:ref.covers(hand.buffer(.105,quad_segs=128)) if not hand.is_empty else False for l,ref in refs.items() if l in('In1.Cu','In3.Cu')}})
  row.update({'remaining_full_In2_body_source_union_gap_mm2_nomination_only':gap.area,'prior_LG_source_keys_lost':[list(k) for k in lost],'actual_handoff_pairs':pairproof})
  if not lost and gap.is_empty and all(q['distance_mm'] is not None and q['distance_mm']<=1 and all(a>.004 for a in q['finite_actual_J1_source_annular_contacts_mm2'].values()) and all(q['guarded_handoff_signal_disk_source_coverage'].values()) for q in pairproof):
   model=H/'DI15-new-only-reference-branches-r150-model.pkl';assert not model.exists();model.write_bytes(pickle.dumps({'current':cur,'h':h,'after':after,'new_zones':[z],'new_vias':nv,'exact_new_chunks':chunks,'refs':refs,'root':root,'groups':groups,'body':body,'points':saved['points'],'handoff_returns':pairproof,'removed_UUIDs':[]},protocol=5));selected={**row,'model_file':str(model),'model_sha256':C.sha(model.read_bytes()),'exact_new_chunks':{u:c.decode() for u,c in chunks.items()},'new_zone_UUID':uid,'new_zone_WKB_sha256':C.sha(shape.wkb),'new_zone_profile':{k:z[k] for k in('net','layer','clearance_mm','priority','minimum_thickness_mm','island_removal_mode','island_area_min_mm2','thermal_gap_mm','thermal_bridge_width_mm')},'projection_ledger':ledger};break
 report={'verdict':'DI15_NEW_ONLY_REFERENCE_BRANCH_CONSTRUCTION_NOMINATED_FULL_GATES_OPEN' if selected else'DI15_NEW_ONLY_REFERENCE_BRANCH_CONSTRUCTION_INCOMPLETE','source_parent_sha256':C.sha(source),'current_model_sha256':r['model_sha256'],'R118_receipt_sha256':C.sha(A.read(rp)),'original_DI13_Cu_all_retained':True,'existing_items_deleted':0,'existing_power_carves':0,'actual_current_legal_new_ground_mask_ledger':maskledger,'central_new_only_trim_mm2':original.difference(island).area,'connected_ground_centre_area_mm2':connected.area,'potential_actual_In1_overlap_length_mm':overlap.length,'continuous_ordinary_return_region_area_mm2':reg.area,'finite_return_nominations':nominations,'attempts':attempts,'selected':selected,'strict_max_DI15_layer_segments':3,'complete_DI15_F_In2_F_signal_and_same_plane_source_validator':'OPEN','complete_independent_all_net_contact_reference_source_current_native_r06_r07_SI':'OPEN','board_written':False,'native_jobs':0,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':report['verdict'],'nominations':len(nominations),'attempts':len(attempts),'selected':selected}),flush=True)
if __name__=='__main__':main()
