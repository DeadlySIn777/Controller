"""Concrete outward ground branches from R94 island to real ordinary returns."""
import sys,json,pickle,time,math,copy,itertools
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'field-power'));sys.path.insert(0,str(HERE.parent/'sbc-power'));sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import contact_layout as L
import construct_di6_direct_source_escape_r5 as K
import audit_c10036_r24_full_independent_r30 as Q
import audit_ao1_positive_operation_r4 as SERIAL
import complete_geometry_r2 as GE
import guarded_power_projection_r44 as Z
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
C=A.C;GND='/LOGIC_GND';LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def lines(sh):
 if sh.is_empty:return []
 if sh.geom_type=='LineString':return [sh]
 return [p for q in getattr(sh,'geoms',[]) for p in lines(q)]
def main():
 started=time.monotonic();out=HERE/'DI15-ground-handoff-branches-r112.json';assert not out.exists();A.read(__file__);rp=HERE/'di15-zero-power-carve-reference-pieces-r94/receipt.json';r=json.loads(A.read(rp));assert C.sha(A.read(rp))=='271c9f168df53b0fa35150cc40575aceea3ce528b1adce40bca9ec2b3e7c6e3f';raw=A.read(r['source_only_model_file']);assert C.sha(raw)==r['source_only_model_sha256'];saved=pickle.loads(raw);cur=saved['current'];h=cur['h'];before=cur['after'];body=saved['body'];line=LineString(saved['points']);missing=body.difference(cur['source_planes']['In1.Cu']);chosen=[z for z in saved['new_zones'] if z['layer']=='In3.Cu' and not z['shape'].intersection(missing).is_empty];assert len(chosen)==1;zone=chosen[0];island=zone['shape'];source=A.read(cur['binding']['exact_native_discrete_board_file']);identity=A.N.SourceNets(source);inventory=C.inventory(source)
 rr=json.loads(A.read(HERE/'di15-original-boundary-detour-r80.json'));b=A.read(rr['saved_geometry']);assert C.sha(b)==rr['saved_geometry_sha256'];R80_geometry_sha256=C.sha(b);legal=pickle.loads(b)['reference_only_new_ground_legal'];raw38=A.read(HERE/'fresh-partial-annular-return-r108-physical-checkpoint.pkl');assert C.sha(raw38)=='0aa98f5c476d32127623ca1de144bdca4e595527dc90b17db6b075af8a5be803';nom=pickle.loads(raw38);assert nom['source_model_sha256']==r['source_model_sha256'];via=nom['physical_GND_return_region'];oldplanes={l:cur['source_planes'][l] for l in('In1.Cu','In4.Cu')};intervals=lines(line.difference(cur['source_planes']['In1.Cu'].intersection(line.envelope.buffer(1)).buffer(-.105,quad_segs=128)));stationrows=[]
 for part in intervals:
  a,b=[line.project(Point(p)) for p in(part.coords[0],part.coords[-1])];a,b=min(a,b),max(a,b);stationrows.append({'start_mm':a,'end_mm':b,'entry_handoff_at_mm':list(line.interpolate(max(0,a-.25)).coords)[0],'exit_handoff_at_mm':list(line.interpolate(min(line.length,b+.25)).coords)[0]})
 assert stationrows;longest=max(stationrows,key=lambda q:q['end_mm']-q['start_mm']);physical_island=unary_union([q['shape'] for group in saved['groups'] for q in group if q['kind']=='fill' and q['uuid']==zone['uuid'] and q['layer']=='In3.Cu']);shared=line.intersection(cur['source_planes']['In1.Cu'].buffer(-.105,quad_segs=128)).intersection(physical_island.buffer(-.105,quad_segs=128));shared_parts=lines(shared);entry=unary_union([p for p in shared_parts if max(line.project(Point(p.coords[0])),line.project(Point(p.coords[-1])))<=longest['start_mm']+1e-8]);exit=unary_union([p for p in shared_parts if min(line.project(Point(p.coords[0])),line.project(Point(p.coords[-1])))>=longest['end_mm']-1e-8]);stations=[{'role':'entry','preferred':longest['entry_handoff_at_mm'],'locus':entry},{'role':'exit','preferred':longest['exit_handoff_at_mm'],'locus':exit}];options=[];elig=[]
 for station_row in stations:
  station=station_row['preferred'];locus=station_row['locus'];p=Point(station);reg=via.intersection(locus.buffer(1,quad_segs=128)).difference(line.buffer(.535,quad_segs=128));rows=[]
  for s in K.sites(reg,station,24):
   at=s['at_mm'];pt=Point(at);actual_handoff=nearest_points(locus,pt)[0];station=list(actual_handoff.coords)[0];ann=pt.buffer(.25,quad_segs=128).difference(pt.buffer(.1,quad_segs=128));contact={l:ann.intersection(sh).area for l,sh in oldplanes.items()}
   if not all(x>.004 for x in contact.values()):continue
   attach=nearest_points(island.buffer(-.1,quad_segs=128),pt)[0];connector=LineString([tuple(attach.coords)[0],at]);branch=Z.bounded_buffer(connector,.175)
   if not legal.covers(branch):continue
   if not branch.intersects(island) or branch.intersection(island).area<.004:continue
   if not branch.covers(pt):continue
   rows.append({'at_mm':at,'handoff_signal_at_mm':station,'handoff_distance_mm':math.dist(at,station),'nearest_signal_body_center_distance_mm':pt.distance(line),'finite_J1_rooted_original_annular_contact_mm2':contact,'connector_points_mm':[list(attach.coords)[0],at],'connector_length_mm':connector.length,'branch_width_mm':.35,'branch_WKB_sha256':C.sha(branch.wkb),'branch_prior_island_overlap_mm2':branch.intersection(island).area,'branch':branch})
  options.append(rows);elig.append({'role':station_row['role'],'preferred_signal_handoff_at_mm':station_row['preferred'],'actual_shared_handoff_locus_length_mm':locus.length,'fresh_ordinary_return_region_mm2':reg.area,'legal_direct_branch_options':[{k:v for k,v in q.items() if k!='branch'} for q in rows]})
 print('DI15_CONTINUOUS_REAL_HANDOFF_BRANCH_OPTIONS',json.dumps(elig),flush=True);selected=None;attempts=[]
 for a,b in itertools.islice(itertools.product(*options),32):
  if math.dist(a['at_mm'],b['at_mm'])<.81:continue
  branchshape=island.union(a['branch']).union(b['branch']);updated={**zone,'shape':branchshape};nv=[];chunks={}
  for q in(a,b):
   u,ch=SERIAL.serial_via(identity,GND,q['at_mm']);assert u not in inventory[3] and u not in {v['uuid'] for v in h['vias']};chunks[u]=ch;nv.append({'uuid':u,'net':identity.raw(GND),'x':q['at_mm'][0],'y':q['at_mm'][1],'d':.5,'drill':.2,'flashed':LAYERS})
  fills=[];cutledger=[]
  for z in before['zones']:
   net=L.norm(z['net']);nz={**z,'fills':{}}
   for layer,rs in z['fills'].items():
    shape=unary_union(L.poly(rs));cuts=[]
    for v in nv:
     radius=.1 if net==GND else max(.375,.25+max(float(z.get('clearance_mm',.15)),.15 if h['domains_normalized'].get(net)==h['domains_normalized'][GND] else .6)+.025);cut=Z.bounded_disk(v,radius)
     if cut.intersects(shape):cuts.append(cut)
    remaining=shape.difference(unary_union(cuts));nz['fills'][layer]=GE.records(remaining)
    if cuts:cutledger.append({'zone_UUID':z['uuid'],'raw_net':z['net'],'layer':layer,'before_WKB_sha256':C.sha(shape.wkb),'after_WKB_sha256':C.sha(remaining.wkb),'physical_pieces_after':len(GE.records(remaining)),'removed_mm2':shape.difference(remaining).area})
   fills.append(nz)
  fills.append({'uuid':updated['uuid'],'net':GND,'clearance_mm':.25,'priority':124,'fills':{'In3.Cu':GE.records(branchshape)}});after={**before,'vias':h['vias']+nv,'zones':fills};_,groups=Q.physical(after,GND);root=next(xs for xs in groups if any(q['kind']=='pad' and(q['ref'],str(q['pin']))==('J11001','2') for q in xs));refs={layer:unary_union([q['shape'] for q in root if q['kind']=='fill' and q['layer']==layer]) for layer in('In1.Cu','In3.Cu')};gap=body.difference(unary_union(list(refs.values())));lost=sorted(Q.discrete_keys(cur['root'])-Q.discrete_keys(root));pairproof=[]
  for q,v in zip((a,b),nv):
   point=Point(q['at_mm']);ann=point.buffer(.25,quad_segs=128).difference(point.buffer(.1,quad_segs=128));pairproof.append({'via_UUID':v['uuid'],'handoff_signal_at_mm':q['handoff_signal_at_mm'],'distance_mm':q['handoff_distance_mm'],'finite_actual_source_annular_contact_mm2':{layer:ann.intersection(ref).area for layer,ref in refs.items()},'entire_handoff_signal_disk_105um_covered_by_both_actual_sources':{layer:ref.covers(Point(q['handoff_signal_at_mm']).buffer(.105,quad_segs=128)) for layer,ref in refs.items()}})
  row={'returns':[{k:v for k,v in q.items() if k!='branch'} for q in(a,b)],'new_vias':nv,'actual_source_union_body_gap_mm2_nomination_only':gap.area,'prior_LG_source_keys_lost':lost,'actual_handoff_return_proof':pairproof,'projection_cut_ledger':cutledger};attempts.append(row)
  if gap.is_empty and not lost and all(all(x>.004 for x in q['finite_actual_source_annular_contact_mm2'].values()) for q in pairproof):
   identity.assert_chunks(chunks);cp=HERE/'DI15-ground-handoff-branches-r112-model.pkl';assert not cp.exists();cp.write_bytes(pickle.dumps({'current':cur,'after':after,'zones':cur['zones']+[updated],'new_zones':[updated],'new_vias':nv,'exact_new_chunks':chunks,'refs':refs,'root':root,'groups':groups,'body':body,'points':saved['points'],'handoff_returns':pairproof},protocol=5));selected={**row,'exact_new_chunks':{u:b.decode() for u,b in chunks.items()},'source_only_model_file':str(cp),'source_only_model_sha256':C.sha(cp.read_bytes()),'new_In3_reference_zone_UUID':updated['uuid'],'new_zone_shape_WKB_sha256':C.sha(branchshape.wkb)};break
  if not gap.is_empty:break
 report={'verdict':'DI15_EXACT_ZERO_POWER_CARVE_REAL_SOURCE_HANDOFF_BRANCHES_NOMINATED_FULL_AUDIT_OPEN' if selected else'DI15_ZERO_CARVE_REAL_HANDOFF_BRANCH_NOMINATION_INCOMPLETE','R94_receipt_sha256':C.sha(A.read(rp)),'R80_legal_geometry_sha256':R80_geometry_sha256,'fresh_R108_all6_ordinary_geometry_sha256':C.sha(raw38),'current_source_model_sha256':r['source_model_sha256'],'source_parent_sha256':C.sha(source),'all_potential_handoff_intervals':stationrows,'chosen_longest_handoff_interval':longest,'handoff_branch_eligibility':elig,'attempts':attempts,'selected':selected,'power_planes_released':[],'old_native_Cu_or_source_FP_deleted':0,'max_signal_layer_segments':3,'union_no_unqualified_reference_credit':True,'remaining':'Complete signal outer escapes/paired endpoint returns and exact per-body actual plane assignment; all new-hole/source/current/r06/r07/discrete and fillcontact/neighbour/native/SI gates','native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':report['verdict'],'selected':selected,'eligibility':elig}),flush=True)
if __name__=='__main__':main()
