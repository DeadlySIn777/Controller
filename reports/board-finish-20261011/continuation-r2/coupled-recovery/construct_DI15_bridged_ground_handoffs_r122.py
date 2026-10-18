"""Extend only new In3 reference copper toward real DI15 entry returns.

Every original and positive power shape is hard. Existing physical masks
are reusable only after exact local current-geometry comparison to R118.
Any source-only construction remains pending signal-hole and native gates.
"""
import sys,json,pickle,time,math,copy,uuid,itertools
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
for p in(H.parent/'field-power',H.parent/'sbc-power',H):sys.path.insert(0,str(p))
import audit_aux_exact_raw as A
import contact_layout as L
import complete_geometry_r2 as GE
import guarded_power_projection_r44 as Z
import construct_di6_direct_source_escape_r5 as K
import audit_c10036_r24_full_independent_r30 as Q
import audit_ao1_positive_operation_r4 as SERIAL
import tri_route as T
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points,substring
C=A.C;GND='/LOGIC_GND';LAYERS=Q.LAYERS
def lines(sh):
 if sh.is_empty:return []
 if sh.geom_type=='LineString':return [sh]
 return [p for q in getattr(sh,'geoms',[]) for p in lines(q)]
def localfills(g,layer,win):
 return {z['uuid']:(z['net'],float(z.get('clearance_mm',.15)),unary_union([p.intersection(win) for p in L.poly(z['fills'].get(layer,[])) if p.intersects(win)])) for z in g['zones'] if any(p.intersects(win) for p in L.poly(z['fills'].get(layer,[])))}
def main():
 started=time.monotonic();out=H/'DI15-extended-real-ground-handoffs-r122.json';assert not out.exists();A.read(__file__)
 rp=H/'di15-safe-root-r42-DI6-bind-r118.json';r=json.loads(A.read(rp));raw=A.read(r['model_path']);assert C.sha(raw)==r['model_sha256'];assert r['LOGIC_GND_J11001_2_prior_source_keys_lost']==[];cur=pickle.loads(raw);h=cur['h'];before=cur['after']
 oldrp=H/'di15-safe-root-r22-DI6-bind-r62.json';oldr=json.loads(A.read(oldrp));assert C.sha(A.read(oldrp))=='a8234fa46de66b43eeefcf2bfbdb3d8563bf862a2ce60c46212b17e77ea314be';oldraw=A.read(oldr['model_path']);assert C.sha(oldraw)==oldr['model_sha256'];oldcur=pickle.loads(oldraw)
 # The R42 additions are remote In2 LOGIC_GND polygons only. We must
 # prove locally unchanged discrete copper and every fill on all layers.
 assert h['tracks']==oldcur['h']['tracks'] and h['vias']==oldcur['h']['vias'] and h['pads']==oldcur['h']['pads'] and h['rule_areas']==oldcur['h']['rule_areas']
 win=box(110,81,137,123);localproof=[]
 for layer in LAYERS:
  a=localfills(oldcur['after'],layer,win);b=localfills(before,layer,win);assert a.keys()==b.keys()
  for u in a:assert a[u][:2]==b[u][:2] and a[u][2].equals(b[u][2])
  localproof.append({'layer':layer,'matched_local_zone_UUID_count':len(a),'exact_geometry_difference':False})
 p=H/'di15-original-boundary-detour-r80.json';rr=json.loads(A.read(p));assert C.sha(A.read(p))=='7676af5a9fa3b96e966a378a0edbbdac1711dc3158f14d606a5fe84f1bc4f720';rb=A.read(rr['saved_geometry']);assert C.sha(rb)==rr['saved_geometry_sha256'];legal=pickle.loads(rb)['reference_only_new_ground_legal']
 cpraw=A.read(H/'fresh-partial-annular-return-r108-physical-checkpoint.pkl');assert C.sha(cpraw)=='0aa98f5c476d32127623ca1de144bdca4e595527dc90b17db6b075af8a5be803';cp=pickle.loads(cpraw);assert cp['source_model_sha256']==oldr['model_sha256'];via=cp['physical_GND_return_region']
 r90p=H/'di15-adjacent-reference-handoff-geometric-nomination-r90.json';r90=json.loads(A.read(r90p));assert C.sha(A.read(r90p))=='71e9cb9446100ddeca47f8dd2acbdd73af4703fda83501edf98d87e100b714d5';points=r90['nominees'][0]['In2_points_mm'];line=LineString(points);body=unary_union([A.shape({'kind':'segment','a':a,'b':b,'w':.2}) for a,b in zip(points,points[1:])])
 ref1=cur['source_planes']['In1.Cu'].intersection(win);ref4=cur['source_planes']['In4.Cu'].intersection(win);missing=body.difference(ref1)
 r94p=H/'di15-zero-power-carve-reference-pieces-r94/receipt.json';r94=json.loads(A.read(r94p));assert C.sha(A.read(r94p))=='271c9f168df53b0fa35150cc40575aceea3ce528b1adce40bca9ec2b3e7c6e3f';b=A.read(r94['source_only_model_file']);assert C.sha(b)==r94['source_only_model_sha256'];saved=pickle.loads(b);selected=[z for z in saved['new_zones'] if z['layer']=='In3.Cu' and not z['shape'].intersection(missing).is_empty];assert len(selected)==1;island=selected[0]['shape'];assert C.sha(island.wkb)=='eaf305f54d183a01e689a13d68b5daf99daeda20a8e10aa8ca67a347a19b7fea'
 intervals=lines(line.difference(ref1.buffer(-.105,quad_segs=128)));ranges=[sorted([line.project(Point(p.coords[0])),line.project(Point(p.coords[-1]))]) for p in intervals];a,b=max(ranges,key=lambda q:q[1]-q[0]);newshape=legal.intersection(Z.bounded_buffer(substring(line,max(0,a-10),min(line.length,b+5)),.2));components=[p for p in K.pieces(newshape) if p.intersection(island).area>.004];assert components
 extended=max(components,key=lambda q:q.intersection(island).area);all_new_strip=unary_union(K.pieces(newshape));shared=line.intersection(ref1.buffer(-.105,quad_segs=128)).intersection(all_new_strip.buffer(-.105,quad_segs=128));parts=lines(shared);roles=[];opts=[];ground_bridge_center=legal.buffer(-.155,quad_segs=128)
 for role,endtest,pref in [('entry',lambda p:max(line.project(Point(p.coords[0])),line.project(Point(p.coords[-1])))<=a+1e-8,max(0,a-.4)),('exit',lambda p:min(line.project(Point(p.coords[0])),line.project(Point(p.coords[-1])))>=b-1e-8,min(line.length,b+.4))]:
  locus=unary_union([p for p in parts if endtest(p)]);reg=via.intersection(locus.buffer(1,quad_segs=128)).difference(line.buffer(.535,quad_segs=128));options=[];attempt=[]
  for s in K.sites(reg,list(line.interpolate(pref).coords)[0],80):
   at=s['at_mm'];pt=Point(at);station=nearest_points(locus,pt)[0];ann=pt.buffer(.25,quad_segs=128).difference(pt.buffer(.1,quad_segs=128));contacts={l:ann.intersection(sh).area for l,sh in [('In1.Cu',ref1),('In4.Cu',ref4)]}
   if not all(v>.004 for v in contacts.values()):continue
   localpieces=[p for p in K.pieces(newshape) if p.covers(station.buffer(.105,quad_segs=128))];assert localpieces;handoff_piece=localpieces[0];link=None;link_search={'method':'same_new_only_reference_piece'}
   if handoff_piece.intersection(extended).area>.004:link=handoff_piece
   else:
    target=handoff_piece.buffer(-.155,quad_segs=128);origin=extended.buffer(-.155,quad_segs=128);bridgeparts=[p for p in K.pieces(ground_bridge_center.intersection(station.buffer(7,quad_segs=128))) if p.intersects(target) and p.intersects(origin)]
    if not bridgeparts:attempt.append({'at_mm':at,'handoff_at_mm':list(station.coords)[0],'reason':'no .30 mm new ground bridge component to central piece'});continue
    start,end=nearest_points(bridgeparts[0].intersection(origin),bridgeparts[0].intersection(target));bridgepoints,link_search=T.route(bridgeparts[0],tuple(start.coords)[0],tuple(end.coords)[0]);bridgepoints=[[round(x,6),round(y,6)] for x,y in bridgepoints];link=Z.bounded_buffer(LineString(bridgepoints),.15).union(handoff_piece)
    if not legal.covers(link) or link.intersection(extended).area<.004:attempt.append({'at_mm':at,'reason':'exact serialized new ground bridge full-body or central contact failed'});continue
   attach=nearest_points(handoff_piece.buffer(-.12,quad_segs=128),pt)[0];direct=LineString([list(attach.coords)[0],at]);branch=Z.bounded_buffer(direct,.175);path=list(direct.coords);search={'method':'exact_direct_full_body'}
   if not legal.covers(branch):
    center=legal.buffer(-.180,quad_segs=128).intersection(pt.buffer(3,quad_segs=128));components=[q for q in K.pieces(center) if q.covers(pt) and q.intersects(handoff_piece.buffer(-.18,quad_segs=128))]
    if not components:attempt.append({'at_mm':at,'reason':'no full-width .35 In3 branch component'});continue
    start=nearest_points(components[0].intersection(handoff_piece.buffer(-.18,quad_segs=128)),pt)[0]
    path,search=T.route(components[0],tuple(start.coords)[0],tuple(at));path=[[round(x,6),round(y,6)] for x,y in path];branch=Z.bounded_buffer(LineString(path),.175)
   if not legal.covers(branch) or branch.intersection(handoff_piece).area<.004:continue
   branch=branch.union(link);search={'return_branch':search,'new_reference_piece_bridge':link_search};assert branch.intersection(extended).area>.004
   options.append({'at_mm':at,'handoff_signal_at_mm':list(station.coords)[0],'pair_distance_mm':pt.distance(station),'contact_mm2':contacts,'branch_points_mm':path,'branch_width_mm':.35,'branch_WKB_sha256':C.sha(branch.wkb),'branch_length_mm':LineString(path).length,'search':search,'branch':branch})
   if len(options)>=12:break
  roles.append({'role':role,'actual_shared_locus_length_mm':locus.length,'ordinary_return_region_mm2':reg.area,'options':[{k:v for k,v in q.items() if k!='branch'} for q in options],'failed_branch_attempts':attempt});opts.append(options)
 print('DI15_EXTENDED_ENTRY_EXIT_OPTIONS',json.dumps(roles),flush=True)
 source=A.read(cur['binding']['exact_native_discrete_board_file']);identity=A.N.SourceNets(source);inventory=C.inventory(source);nominee=None;sourceattempts=[]
 for entry,exit in itertools.islice(itertools.product(*opts),20):
  if math.dist(entry['at_mm'],exit['at_mm'])<.815:continue
  shape=extended.union(island).union(entry['branch']).union(exit['branch']);assert legal.covers(shape);new=[];chunks={}
  for q in(entry,exit):
   u,ch=SERIAL.serial_via(identity,GND,q['at_mm']);assert u not in inventory[3] and u not in {v['uuid'] for v in h['vias']};new.append({'uuid':u,'net':identity.raw(GND),'x':q['at_mm'][0],'y':q['at_mm'][1],'d':.5,'drill':.2,'flashed':list(LAYERS)});chunks[u]=ch
  u=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/DI15/entry-exit-reference-r122/'+C.sha(shape.wkb)));z={**selected[0],'uuid':u,'shape':shape,'name':'DI15 zero power carve ordinary In2 two-reference handoff R122'};fills=[];ledger=[]
  for oldz in before['zones']:
   nz={**oldz,'fills':{}};net=L.norm(nz['net'])
   for layer,records in oldz['fills'].items():
    original=unary_union(L.poly(records));cuts=[]
    for v in new:
     rad=.1 if net==GND else max(.375,.25+max(float(oldz.get('clearance_mm',.15)),.15 if h['domains_normalized'].get(net)==h['domains_normalized'][GND] else .6)+.025);cut=Z.bounded_disk(v,rad)
     if cut.intersects(original):cuts.append(cut)
    rem=original.difference(unary_union(cuts));nz['fills'][layer]=GE.records(rem)
    if cuts:ledger.append({'zone_UUID':oldz['uuid'],'layer':layer,'net':oldz['net'],'before_WKB_sha256':C.sha(original.wkb),'after_WKB_sha256':C.sha(rem.wkb),'removed_mm2':original.difference(rem).area})
   fills.append(nz)
  # Intended new ground outline includes the barrel centres. Physical
  # Q graph subtracts every drilled aperture independently.
  fills.append({'uuid':u,'net':GND,'clearance_mm':.25,'priority':124,'fills':{'In3.Cu':GE.records(shape)}});after={**before,'vias':h['vias']+new,'zones':fills};_,groups=Q.physical(after,GND);root=next(xs for xs in groups if any(q['kind']=='pad' and(q['ref'],str(q['pin']))==('J11001','2') for q in xs));refs={l:unary_union([q['shape'] for q in root if q['kind']=='fill' and q['layer']==l]).intersection(win) for l in('In1.Cu','In3.Cu','In4.Cu')};lost=sorted(Q.discrete_keys(cur['root'])-Q.discrete_keys(root));gap=body.difference(refs['In1.Cu'].union(refs['In3.Cu']));pair=[]
  for q,v in zip((entry,exit),new):
   pt=Point(q['at_mm']);ann=pt.buffer(.25,quad_segs=128).difference(pt.buffer(.1,quad_segs=128));s=Point(q['handoff_signal_at_mm']);pair.append({'via_UUID':v['uuid'],'at_mm':q['at_mm'],'signal_handoff_at_mm':q['handoff_signal_at_mm'],'distance_mm':q['pair_distance_mm'],'actual_source_annular_contacts_mm2':{l:ann.intersection(refs[l]).area for l in refs},'entire_handoff_guarded_signal_disk_both_source_planes':{l:refs[l].covers(s.buffer(.105,quad_segs=128)) for l in('In1.Cu','In3.Cu')}})
  row={'pairs':pair,'prior_LOGIC_source_keys_lost':lost,'actual_body_union_gap_mm2_nomination_only':gap.area,'new_ground_UUID':u,'shape_WKB_sha256':C.sha(shape.wkb),'projection_ledger':ledger};sourceattempts.append(row)
  if gap.is_empty and not lost and all(all(x>.004 for x in p['actual_source_annular_contacts_mm2'].values()) and all(p['entire_handoff_guarded_signal_disk_both_source_planes'].values()) for p in pair):
   identity.assert_chunks(chunks);model=H/'DI15-extended-real-ground-handoffs-r122-model.pkl';assert not model.exists();model.write_bytes(pickle.dumps({'current':cur,'after':after,'zones':cur['zones']+[z],'new_zones':[z],'new_vias':new,'exact_new_chunks':chunks,'refs':refs,'root':root,'groups':groups,'body':body,'points':points,'handoff_returns':pair},protocol=5));nominee={**row,'model_file':str(model),'model_sha256':C.sha(model.read_bytes()),'new_return_vias':new,'exact_new_chunks':{u:ch.decode() for u,ch in chunks.items()},'entry':{k:v for k,v in entry.items() if k!='branch'},'exit':{k:v for k,v in exit.items() if k!='branch'}};break
 report={'verdict':'DI15_NEW_ONLY_GROUND_EXTENSION_REAL_SOURCE_HANDOFF_CONSTRUCTED_NOMINATION_ONLY' if nominee else'DI15_NEW_ONLY_GROUND_ENTRY_EXTENSION_INCOMPLETE','R118_receipt_sha256':C.sha(A.read(rp)),'current_model_sha256':r['model_sha256'],'original_mask_authority_model_sha256':oldr['model_sha256'],'R80_exact_local_geometry_reuse_proof':localproof,'fresh_R108_actual_ordinary_region_sha256':C.sha(cpraw),'R94_original_central_piece_UUID':selected[0]['uuid'],'R94_piece_WKB_sha256':C.sha(island.wkb),'central_missing_station_mm':[a,b],'new_extended_shape_WKB_sha256':C.sha(extended.wkb),'new_extended_shape_area_mm2':extended.area,'eligibility':roles,'source_attempts':sourceattempts,'selected':nominee,'old_native_or_positive_power_deleted_carved_or_replaced':0,'old_Cu_source_FP_project_rules_changed':0,'max_signal_layer_segments':3,'remaining':'Exact two ordinary signal vias/endpoint returns and F/In2/F signal serialization; per-body assigned adjacent source after all signal/return holes; complete original copper/pad groups, foreign contact/outer refs, source-current/native/SI','native_jobs':0,'board_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};out.write_text(json.dumps(report,indent=1,allow_nan=False)+'\n');print(json.dumps({'sha256':C.sha(out.read_bytes()),'verdict':report['verdict'],'selected':nominee}),flush=True)
if __name__=='__main__':main()
