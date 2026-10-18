"""Separate local In3 nominee: all F/B SMD plus actual existing returns."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
p=HERE/'construct_di15_reference_escape_r35.py';s=p.read_text()
s=s.replace('import di15_current_joint_base_r34 as BIND','import di15_reuse_joint_base_r36 as BIND\nimport audit_c10036_r24_full_independent_r30 as Q')
s=s.replace("'di15-joint-r11-In3-nomination-r35.json'","'di15-joint-r11-In3-existing-return-nomination-r36.json'")
old="if l in('F.Cu','In3.Cu') for sh in L.poly(rs) if sh.distance(win)<2";assert old in s;s=s.replace(old,"if l in('F.Cu','B.Cu') for sh in L.poly(rs) if sh.distance(win)<2")
start=s.index(" for si,srow in enumerate(sp):");end=s.index(" site_diagnosis=",start)
replacement=""" rooted_keys=Q.discrete_keys(current['root'])
 existing_returns=[]
 for v in h['vias']:
  if L.norm(v['net'])!=GND or('via',v['uuid']) not in rooted_keys or Point(v['x'],v['y']).distance(win)>1:continue
  if not {'In1.Cu','In4.Cu'}<=set(v.get('flashed',LAYERS)):continue
  ann=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=128).difference(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))
  contact={l:refs[l].buffer(-.075).intersection(ann).area for l in('F.Cu','In3.Cu')}
  if all(a>=.004 for a in contact.values()):existing_returns.append({'UUID':v['uuid'],'at_mm':[v['x'],v['y']],'finite_source_rooted_annular_interior_mm2':contact,'actual_flashes':v.get('flashed',LAYERS)})
 def signal_choices(region,preferred):
  options=[];seen=set()
  for ret in existing_returns:
   p=Point(ret['at_mm']);pair_region=region.intersection(p.buffer(1,quad_segs=128).difference(p.buffer(.825,quad_segs=128)))
   if pair_region.is_empty:continue
   for site in K.sites(pair_region,preferred,4):
    key=(tuple(site['at_mm']),ret['UUID'])
    if key in seen:continue
    seen.add(key);options.append({'site':site,'return_at_mm':ret['at_mm'],'return_UUID':ret['UUID'],'return_new':False,'old_return_native_contact':ret})
  for site in K.sites(region,preferred,12):
   p=Point(site['at_mm']);newregion=via[GND].intersection(p.buffer(1,quad_segs=128).difference(p.buffer(.825,quad_segs=128)))
   for ret in K.sites(newregion,[site['at_mm'][0]-.9,site['at_mm'][1]],4):options.append({'site':site,'return_at_mm':ret['at_mm'],'return_UUID':None,'return_new':True})
  return sorted(options,key=lambda q:q['site']['cost_mm'])[:16]
 for si,srow in enumerate(sp):
  sf=unary_union([p for p in K.pieces(free[NET,'F.Cu']) if p.covers(Point(srow['at_mm']))]);sr=via[NET].intersection(sf).intersection(Point(sourcepad.centroid).buffer(5,quad_segs=128))
  for di,drow in enumerate(dp):
   df=unary_union([p for p in K.pieces(free[NET,'F.Cu']) if p.covers(Point(drow['at_mm']))]);dr=via[NET].intersection(df).intersection(Point(targetpad.centroid).buffer(5,quad_segs=128))
   for part_index,part in enumerate(ins):
    a=sr.intersection(part);b=dr.intersection(part);diagnosis={'source_attachment_index':si,'target_attachment_index':di,'transport_component':part_index,'component_area_mm2':part.area,'source_signal_site_area_mm2':a.area,'target_signal_site_area_mm2':b.area,'both_terminal_regions_present':not a.is_empty and not b.is_empty};component_diagnosis.append(diagnosis)
    if a.is_empty or b.is_empty:continue
    so=signal_choices(a,[118.45,90.75]);do=signal_choices(b,[131.25,112.35]);diagnosis.update(source_paired_options=len(so),target_paired_options=len(do),source_existing_return_options=sum(not q['return_new'] for q in so),target_existing_return_options=sum(not q['return_new'] for q in do))
    for sa in so:
     for sb in do:pairs.append({'source_attachment':srow['at_mm'],'target_attachment':drow['at_mm'],'signals':[sa['site']['at_mm'],sb['site']['at_mm']],'returns':[sa['return_at_mm'],sb['return_at_mm']],'return_new':[sa['return_new'],sb['return_new']],'existing_return_UUIDs':[sa['return_UUID'],sb['return_UUID']],'score_mm':sa['site']['cost_mm']+sb['site']['cost_mm']})
   if pairs:break
  if pairs:break
"""
s=s[:start]+replacement+s[end:]
s=s.replace("returncuts=unary_union([Point(at).buffer(.530,quad_segs=128) for at in pair['returns']])","returncuts=unary_union([Point(at).buffer(.530,quad_segs=128) for at,new in zip(pair['returns'],pair['return_new']) if new])")
s=s.replace("'pairs':pairs,", "'every_F_and_B_SMD_aperture_restored':True,'preserved_R35_incomplete_nomination_omitted_B_SMD_screen':True,'existing_source_rooted_return_nominees':existing_returns,'pairs':pairs,")
out=HERE/'construct_di15_reference_escape_r36.py';assert not out.exists();out.write_text(s)
