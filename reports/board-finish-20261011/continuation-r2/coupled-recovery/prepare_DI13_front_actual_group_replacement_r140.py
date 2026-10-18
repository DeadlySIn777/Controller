"""Derive separate F-only DI13 replacement from the preserved R138 attempt."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
src=H/'construct_DI15_DI13_actual_attachments_r138.py';raw=src.read_bytes();s=raw.decode().replace('\r\n','\n').replace('r138','r140').replace('R138','R140')
start=s.index('def trackfree(');end=s.index('def projection(',start)
s=s[:start]+'''def trackfree(h,cur,win,ground,newvias):
 # Exact existing DI13 source/target groups already have F copper. No new
 # DI13 vias or invented endpoint disk; every new F body needs actual In1.
 layer='F.Cu';rec,trees=F.build({**h,'zones':[]});domains=h['domains_normalized'];obs=[]
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
 reference=cur['source_planes']['In1.Cu'].intersection(win.buffer(1)).difference(unary_union([Z.bounded_disk(v,.1) for v in newvias]));physical=win.difference(unary_union(obs)).buffer(-.105,quad_segs=128)
 return physical.intersection(reference.buffer(-.105,quad_segs=128)),[],physical.covers(Point(123.95,102.15)),physical.covers(Point(130.549999,109.65)),reference.covers(Point(123.95,102.15)),reference.covers(Point(130.549999,109.65))
''' +s[end:]
s=s.replace('win=box(120,99,134,112)','win=box(110,85,145,125)')
old="startmetal=unary_union([q['shape'] for q in start_components[0] if q['kind']!='fill' and q['layer']=='In3.Cu']);endmetal=unary_union([q['shape'] for q in end_components[0] if q['kind']!='fill' and q['layer']=='In3.Cu'])"
new="startmetal=unary_union([q['shape'] for q in start_components[0] if q['kind']!='fill' and q['layer']=='F.Cu']);endmetal=unary_union([q['shape'] for q in end_components[0] if q['kind']!='fill' and q['layer']=='F.Cu'])"
assert old in s;s=s.replace(old,new)
s=s.replace('Point(start).buffer(5,quad_segs=128)','Point(start).buffer(15,quad_segs=128)').replace('Point(end).buffer(5,quad_segs=128)','Point(end).buffer(15,quad_segs=128)')
s=s.replace("identity.serial_segment(BLOCK,'In3.Cu'","identity.serial_segment(BLOCK,'F.Cu'")
s=s.replace("'layer':'In3.Cu','a':a,'b':b,'w':.2","'layer':'F.Cu','a':a,'b':b,'w':.2")
s=s.replace("A.shape({'kind':'segment',**t}).difference(refs['In4.Cu'])","A.shape({'kind':'segment',**t}).difference(refs['In1.Cu'])")
s=s.replace("A.shape({'kind':'segment',**t}).difference(refs['In4.Cu'].union(oldscope))","A.shape({'kind':'segment',**t}).difference(refs['In1.Cu'])")
s=s.replace('actual_adjacent_In4_J1_source_full_body_gap','actual_adjacent_In1_J1_source_full_body_gap')
s=s.replace("row['actual_surviving_contact_component_authority']=actual_surviving_contact_component_authority","row['actual_surviving_contact_component_authority']=actual_surviving_contact_component_authority;row['new_signal_layer']='F.Cu';row['new_DI13_signal_vias']=0;print(json.dumps({'phase':'actual_F_groups','entry':at,'source_attachment_mm2':sourceattach.area,'target_attachment_mm2':targetattach.area,'common_components':len(parts)}),flush=True)")
s=s.replace("route,search=T.route(parts[0],tuple(start),tuple(end));route=", "print(json.dumps({'phase':'F_route','chosen_endpoints':[start,end],'component_area_mm2':parts[0].area}),flush=True);route,search=T.route(parts[0],tuple(start),tuple(end));route=")
dst=H/'construct_DI15_DI13_front_replacement_r140.py';assert not dst.exists();dst.write_text(s,newline='\n')
out=H/'prepare-DI13-front-actual-group-replacement-r140.json';assert not out.exists();out.write_text(json.dumps({'source_file':str(src),'source_sha256':sha(raw),'derived_file':str(dst),'derived_sha256':sha(dst.read_bytes()),'delta':'Keep exactly two original In3 removals and actual surviving source/target components; attach on their F metal through actual source-rooted In1 coverage, with no new DI13 signal vias or own-transition reference scopes. Original and positive power copper held hard. New ground two-return recipe unchanged.'},indent=1)+'\n');print(sha(dst.read_bytes()))
