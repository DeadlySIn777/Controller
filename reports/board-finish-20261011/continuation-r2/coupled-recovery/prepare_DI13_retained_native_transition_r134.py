"""Qualify only exact retained DI13 barrels with real retained paired returns."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
src=H/'construct_DI15_DI13_coupled_reference_r130.py';raw=src.read_bytes();s=raw.decode().replace('\r\n','\n').replace('r130','r134').replace('R130','R134')
old="reference=cur['source_planes']['In4.Cu'].intersection(win.buffer(1)).difference(unary_union([Z.bounded_disk(v,.1) for v in newvias]));return win.difference(unary_union(obs)).buffer(-.105,quad_segs=128).intersection(reference.buffer(-.105,quad_segs=128))"
new="""reference=cur['source_planes']['In4.Cu'].intersection(win.buffer(1)).difference(unary_union([Z.bounded_disk(v,.1) for v in newvias]));physical=win.difference(unary_union(obs)).buffer(-.105,quad_segs=128);oldviawitness=[];disks=[];native=A.read(cur['binding']['exact_native_discrete_board_file']);inventory=C.inventory(native)
 for v in cur['h']['vias']:
  if L.norm(v['net'])!=BLOCK or Point(v['x'],v['y']).distance(win)>.5:continue
  if not any(math.dist([v['x'],v['y']],p)<.000002 for p in([123.95,102.15],[130.549999,109.65])):continue
  exact=A.G.parse(v['uuid'],inventory[3][v['uuid']],{});assert(exact['net'],exact['at'],exact['d'],exact['drill'])==(BLOCK,[v['x'],v['y']],v['d'],v['drill']);assert 'In3.Cu' in v['flashed']
  pairs=[]
  for gv in cur['h']['vias']:
   if L.norm(gv['net'])!=GND or not set(('In1.Cu','In4.Cu')).issubset(gv['flashed']):continue
   distance=math.dist([v['x'],v['y']],[gv['x'],gv['y']])
   if not .81<=distance<=1:continue
   p=Point(gv['x'],gv['y']);ann=p.buffer(gv['d']/2,quad_segs=128).difference(p.buffer(gv['drill']/2,quad_segs=128));areas={l:ann.intersection(cur['source_planes'][l]).area for l in('In1.Cu','In4.Cu')}
   if all(x>.004 for x in areas.values()):pairs.append({'return_UUID':gv['uuid'],'at_mm':[gv['x'],gv['y']],'diameter_drill_mm':[gv['d'],gv['drill']],'actual_flash_layers':gv['flashed'],'distance_mm':distance,'finite_original_J1_source_annular_contacts_mm2':areas})
  q={'retained_signal_UUID':v['uuid'],'at_mm':[v['x'],v['y']],'diameter_drill_mm':[v['d'],v['drill']],'actual_signal_flash_layers':v['flashed'],'exact_native_source_chunk_sha256':C.sha(inventory[3][v['uuid']]),'unchanged_own_transition_radius_mm':v['d']/2+.275,'radius_expansion_mm':0,'legitimate_actual_existing_paired_returns':pairs,'qualified_existing_own_scope':bool(pairs)};oldviawitness.append(q)
  if pairs:disks.append(Point(v['x'],v['y']).buffer(v['d']/2+.275,quad_segs=128))
 augmented=reference.union(unary_union(disks));return physical.intersection(augmented.buffer(-.105,quad_segs=128)),oldviawitness,physical.covers(Point(123.95,102.15)),physical.covers(Point(130.549999,109.65)),reference.covers(Point(123.95,102.15)),reference.covers(Point(130.549999,109.65))"""
assert old in s;s=s.replace(old,new)
old="free=trackfree(h,cur,win,z,nv);start=[123.95,102.15];end=[130.549999,109.65]"
new="free,oldviawitness,startphys,endphys,startref,endref=trackfree(h,cur,win,z,nv);row.update({'exact_retained_DI13_transition_witnesses':oldviawitness,'start_physical_center_covered':startphys,'end_physical_center_covered':endphys,'start_adjacent_source_center_covered':startref,'end_adjacent_source_center_covered':endref});start=[123.95,102.15];end=[130.549999,109.65]"
assert old in s;s=s.replace(old,new)
old="trackrefs=[{'uuid':t['uuid'],'actual_adjacent_In4_J1_source_full_body_gap_mm2':A.shape({'kind':'segment',**t}).difference(refs['In4.Cu']).area} for t in nt]"
new="""final_old_disks=[];final_old_witness=[]
  for witness in oldviawitness:
   retained=[]
   for pair in witness['legitimate_actual_existing_paired_returns']:
    p=Point(pair['at_mm']);diameter,drill=pair['diameter_drill_mm'];ann=p.buffer(diameter/2,quad_segs=128).difference(p.buffer(drill/2,quad_segs=128));areas={l:ann.intersection(refs[l]).area for l in('In1.Cu','In4.Cu')}
    if all(x>.004 for x in areas.values()):retained.append({**pair,'finite_final_J1_source_annular_contacts_mm2':areas})
   final_old_witness.append({**witness,'final_legitimate_paired_returns':retained})
   if retained:final_old_disks.append(Point(witness['at_mm']).buffer(witness['unchanged_own_transition_radius_mm'],quad_segs=128))
  oldscope=unary_union(final_old_disks);trackrefs=[{'uuid':t['uuid'],'actual_adjacent_In4_J1_source_full_body_gap_before_own_scope_mm2':A.shape({'kind':'segment',**t}).difference(refs['In4.Cu']).area,'actual_adjacent_In4_J1_source_full_body_gap_mm2':A.shape({'kind':'segment',**t}).difference(refs['In4.Cu'].union(oldscope)).area,'legitimate_retained_same_net_own_scopes':final_old_witness} for t in nt]"""
assert old in s;s=s.replace(old,new)
dst=H/'construct_DI15_DI13_retained_transition_r134.py';assert not dst.exists();dst.write_text(s,newline='\n');out=H/'prepare-DI13-retained-native-transition-r134.json';assert not out.exists();out.write_text(json.dumps({'source_file':str(src),'source_sha256':sha(raw),'derived_file':str(dst),'derived_sha256':sha(dst.read_bytes()),'delta':'Exact original-source existing endpoint barrel data/actual native flash layers and real retained J1-rooted In1/In4 paired return witness; unchanged own d/2+.275 disk only when legitimate pair exists before and after. Physical/reference endpoint diagnostics; no disk expansion/generic return/margin waiver.'},indent=1)+'\n');print(sha(dst.read_bytes()))
