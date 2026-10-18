"""Derive mirrored In3/B ordinary replacement; preserve R138/R140 failures."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
src=H/'construct_DI15_DI13_actual_attachments_r138.py';raw=src.read_bytes();s=raw.decode().replace('\r\n','\n').replace('r138','r146').replace('R138','R146')
start=s.index('def trackfree(');end=s.index('def projection(',start)
s=s[:start]+'''def viafree(h,cur,win,ground):
 rec,trees=F.build({**h,'zones':[]});domains=h['domains_normalized'];obs=[]
 for layer in LAYERS:
  for i in trees[layer].query(win.buffer(1),predicate='intersects'):
   q=rec[layer][int(i)];n=L.norm(q['net'])
   if n!=BLOCK:obs.append(Z.bounded_buffer(q['shape'],.25+(.15 if domains.get(n)==domains[BLOCK] else .6)+.030))
  for z in cur['zones']+[ground]:
   n=L.norm(z['net'])
   if z['layer']==layer and n!=BLOCK and z['shape'].distance(win)<1:obs.append(Z.bounded_buffer(z['shape'],.25+max(float(z.get('clearance_mm',.15)),.15 if domains.get(n)==domains[BLOCK] else .6)+.030))
  for z in cur['after']['zones']:
   n=L.norm(z['net'])
   if n==BLOCK or domains.get(n)==domains[BLOCK]:continue
   obs.extend(Z.bounded_buffer(p,.25+max(float(z.get('clearance_mm',.15)),.6)+.030) for p in L.poly(z['fills'].get(layer,[])) if p.distance(win)<1)
 reserve,exempt=A.reservations()
 for v in h['vias']:
  if Point(v['x'],v['y']).distance(win)<1:obs.append(Z.bounded_disk(v,max(.815,.1+v['drill']/2+.280)))
 for p in h['pads']:
  if p['smd']:
   for layer,rs in p['layers'].items():
    if layer in('F.Cu','B.Cu'):obs.extend(Z.bounded_buffer(q,.380) for q in L.poly(rs) if q.distance(win)<1)
  obs.extend(Z.bounded_buffer(q,.380) for q in L.poly(p.get('hole') or []) if q.distance(win)<1)
 for q in h['rule_areas']:
  if set(LAYERS).intersection(q['layers']) and q.get('no_vias'):obs.extend(Z.bounded_buffer(p,.275) for p in L.poly(q['outline']) if p.distance(win)<1)
 for q in reserve['keepouts']:
  if set(LAYERS).intersection(q['layers']) and BLOCK not in exempt.get(q['name'],set()):obs.extend(Z.bounded_buffer(p,.275) for p in L.poly(q['outline']) if p.distance(win)<1)
 return win.difference(unary_union(obs))
def trackfree(h,cur,win,ground,newvias,ownscope):
 layer='B.Cu';rec,trees=F.build({**h,'zones':[]});domains=h['domains_normalized'];obs=[]
 for i in trees[layer].query(win.buffer(1),predicate='intersects'):
  q=rec[layer][int(i)];n=L.norm(q['net'])
  if n!=BLOCK:obs.append(Z.bounded_buffer(q['shape'],(.15 if domains.get(n)==domains[BLOCK] else .6)+.030))
 for z in cur['zones']:
  n=L.norm(z['net'])
  if z['layer']==layer and n!=BLOCK and z['shape'].distance(win)<1:obs.append(Z.bounded_buffer(z['shape'],max(float(z.get('clearance_mm',.15)),.15 if domains.get(n)==domains[BLOCK] else .6)+.030))
 for z in cur['after']['zones']:
  n=L.norm(z['net'])
  if n==BLOCK or domains.get(n)==domains[BLOCK]:continue
  obs.extend(Z.bounded_buffer(p,max(float(z.get('clearance_mm',.15)),.6)+.030) for p in L.poly(z['fills'].get(layer,[])) if p.distance(win)<1)
 for v in h['vias']:
  if L.norm(v['net'])!=BLOCK and Point(v['x'],v['y']).distance(win)<1:obs.append(Z.bounded_disk(v,v['drill']/2+.280))
 for p in h['pads']:
  if L.norm(p['net'])!=BLOCK:obs.extend(Z.bounded_buffer(q,.280) for q in L.poly(p.get('hole') or []) if q.distance(win)<1)
 reserve,exempt=A.reservations()
 for q in h['rule_areas']:
  if layer in q['layers'] and q.get('no_tracks'):obs.extend(Z.bounded_buffer(p,.025) for p in L.poly(q['outline']) if p.distance(win)<1)
 for q in reserve['keepouts']:
  if layer in q['layers'] and BLOCK not in exempt.get(q['name'],set()):obs.extend(Z.bounded_buffer(p,.025) for p in L.poly(q['outline']) if p.distance(win)<1)
 reference=cur['source_planes']['In4.Cu'].intersection(win.buffer(1)).difference(unary_union([Z.bounded_disk(v,v['drill']/2 if L.norm(v['net'])==GND else .525) for v in newvias]));physical=win.difference(unary_union(obs)).buffer(-.105,quad_segs=128)
 return physical.intersection(reference.union(ownscope).buffer(-.105,quad_segs=128))
''' +s[end:]
s=s.replace('win=box(120,99,134,112)','win=box(110,85,145,125)')
s=s.replace("endmetal=unary_union([q['shape'] for q in end_components[0] if q['kind']!='fill' and q['layer']=='In3.Cu'])","endmetal=unary_union([q['shape'] for q in end_components[0] if q['kind']!='fill' and q['layer']=='B.Cu'])")
old="h=copy.deepcopy(hbase);h['vias']+=nv;free,oldviawitness,startphys,endphys,startref,endref=trackfree(h,cur,win,z,nv);row.update({'exact_retained_DI13_transition_witnesses':oldviawitness,'start_physical_center_covered':startphys,'end_physical_center_covered':endphys,'start_adjacent_source_center_covered':startref,'end_adjacent_source_center_covered':endref});start=[123.95,102.15];end=[130.549999,109.65];sourceattach=startmetal.buffer(-.04,quad_segs=128).intersection(free).intersection(Point(start).buffer(5,quad_segs=128));targetattach=endmetal.buffer(-.04,quad_segs=128).intersection(free).intersection(Point(end).buffer(5,quad_segs=128));parts=[p for p in K.pieces(free) if p.intersects(sourceattach) and p.intersects(targetattach)];row['DI13_continuous_full_body_source_reference_components']=len(parts);row['actual_referenced_surviving_source_attachment_mm2']=sourceattach.area;row['actual_referenced_surviving_target_attachment_mm2']=targetattach.area;row['actual_surviving_contact_component_authority']=actual_surviving_contact_component_authority\n  if parts:\n   start_options=K.sites(sourceattach.intersection(parts[0]),start,6);end_options=K.sites(targetattach.intersection(parts[0]),end,6)\n   if not start_options or not end_options:parts=[]\n   else:start=start_options[0]['at_mm'];end=end_options[0]['at_mm'];row['actual_new_attachment_centres_mm']=[start,end];row['actual_start_existing_metal_overlap_mm2']=Point(start).buffer(.1,quad_segs=128).intersection(startmetal).area;row['actual_end_existing_metal_overlap_mm2']=Point(end).buffer(.1,quad_segs=128).intersection(endmetal).area\n  if not parts:continue"
new="""h=copy.deepcopy(hbase);h['vias']+=nv;start=[123.95,102.15];end=[130.549999,109.65];ordinary=viafree(h,cur,win,z);reference=cur['source_planes']['In4.Cu'].intersection(win.buffer(1)).difference(unary_union([Z.bounded_disk(v,.1) for v in nv]));sourceattach=startmetal.buffer(-.04,quad_segs=128).intersection(ordinary).intersection(Point(start).buffer(15,quad_segs=128));row['actual_ordinary_surviving_In3_attachment_mm2']=sourceattach.area;row['actual_surviving_contact_component_authority']=actual_surviving_contact_component_authority;row['DI13_new_signal_layer']='B.Cu';row['DI13_new_signal_vias']=1;row['same_plane_source_attempts']=[];chosen_signal=None
  for sr in K.sites(sourceattach,start,18):
   pos=sr['at_mm'];point=Point(pos);inner=Z.bounded_disk({'x':pos[0],'y':pos[1]},.525);ring=Z.bounded_disk({'x':pos[0],'y':pos[1]},.725).difference(inner);actualpieces=[q for q in K.pieces(reference) if q.covers(ring)];ann=point.buffer(.25,quad_segs=128).difference(point.buffer(.1,quad_segs=128));contact=ann.intersection(startmetal).area;srproof={'at_mm':pos,'exact_source_continuous_In4_ring_gap_mm2':ring.difference(reference).area,'same_source_piece_count':len(actualpieces),'real_surviving_In3_annular_contact_mm2':contact};row['same_plane_source_attempts'].append(srproof)
   if not actualpieces or contact<.004:continue
   uid,ch=SERIAL.serial_via(identity,BLOCK,pos);sig={'uuid':uid,'net':identity.raw(BLOCK),'x':pos[0],'y':pos[1],'d':.5,'drill':.2,'flashed':list(LAYERS)};hh=copy.deepcopy(h);hh['vias'].append(sig);free=trackfree(hh,cur,win,z,nv+[sig],inner);targetattach=endmetal.buffer(-.04,quad_segs=128).intersection(free).intersection(Point(end).buffer(15,quad_segs=128));parts=[q for q in K.pieces(free) if q.covers(point) and q.intersects(targetattach)];srproof['actual_referenced_B_target_attachment_mm2']=targetattach.area;srproof['continuous_B_components']=len(parts)
   if not parts:continue
   end_options=K.sites(targetattach.intersection(parts[0]),end,6)
   if not end_options:continue
   chosen_signal={'via':sig,'chunk':ch,'scope':inner,'proof':srproof};h=hh;nv.append(sig);chunks[uid]=ch;start=pos;end=end_options[0]['at_mm'];oldviawitness=[];row['actual_new_attachment_centres_mm']=[start,end];row['DI13_same_plane_transition_proposal']={'layers':['In3.Cu','B.Cu'],'same_actual_reference':'In4.Cu','own_aperture_radius_mm':.525,'radius_expansion_mm':0,'source_piece_WKB_sha256':[C.sha(q.wkb) for q in actualpieces],'new_conservative_all6_via_UUID':uid,'inherited_blanket_paired_checker':'FAIL_OR_NOT_RUN_PRESERVED','actual_scope_native_and_policy_validator':'OPEN'};break
  print(json.dumps({'phase':'DI13_mirrored_B_source','entry':at,'ordinary_In3_area':sourceattach.area,'sites':len(row['same_plane_source_attempts']),'selected':chosen_signal['proof'] if chosen_signal else None}),flush=True)
  if chosen_signal is None:continue"""
assert old in s;s=s.replace(old,new)
s=s.replace("identity.serial_segment(BLOCK,'In3.Cu'","identity.serial_segment(BLOCK,'B.Cu'").replace("'layer':'In3.Cu','a':a,'b':b,'w':.2","'layer':'B.Cu','a':a,'b':b,'w':.2")
s=s.replace("oldscope=unary_union(final_old_disks);trackrefs=", "same_point=chosen_signal['proof']['at_mm'];same_ring=Z.bounded_disk({'x':same_point[0],'y':same_point[1]},.725).difference(chosen_signal['scope']);row['final_same_plane_In4_ring_gap_mm2']=same_ring.difference(refs['In4.Cu']).area;oldscope=chosen_signal['scope'];trackrefs=")
s=s.replace("if not lost and gap.is_empty and not contactloss and all(","if row['final_same_plane_In4_ring_gap_mm2']==0 and not lost and gap.is_empty and not contactloss and all(")
s=s.replace("'DI15_complete_F_In2_F_signal_constructor_and_pairing':'OPEN'","'DI15_complete_F_In2_F_signal_constructor_and_pairing':'OPEN','DI13_same_plane_engineering_proposal_and_independent_native_validator':'OPEN'")
dst=H/'construct_DI15_DI13_mirrored_back_replacement_r146.py';assert not dst.exists();dst.write_text(s,newline='\n');out=H/'prepare-DI13-mirrored-back-group-replacement-r146.json';assert not out.exists();out.write_text(json.dumps({'source_file':str(src),'source_sha256':sha(raw),'derived_file':str(dst),'derived_sha256':sha(dst.read_bytes()),'delta':'Keep exactly two In3 deletes and source/target physical groups. Nominate one all6 ordinary new signal via on actual surviving In3 metal and transport B to existing target B metal, with actual continuous In4 ring/.525 own aperture proof and no invented target scope. SAME_PLANE proposal remains distinct from inherited blanket checker. All power hard.'},indent=1)+'\n');print(sha(dst.read_bytes()))
