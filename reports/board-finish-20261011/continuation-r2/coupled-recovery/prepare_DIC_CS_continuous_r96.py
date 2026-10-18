"""Exact current-group ordinary DIC CS constructor; no new cap/profile."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;src=H/'construct_pen_existing_In3_or_dive_r86.py';b=src.read_bytes();s=b.decode().replace('/motherboard_process/PEN_ENABLE_LOGIC','/motherboard_io_control/DIC_IOL1_CS_BUFFER').replace('PEN','DIC-CS').replace('PEN recovery','DIC CS recovery').replace('r86','r96').replace("'B.Cu'","'F.Cu'").replace('B/','F/').replace(' B',' F').replace('B_components','F_components').replace('B_attachment','F_attachment')
s=s.replace("free={l:win.difference(obstacle(NET,l)).buffer(-.105,quad_segs=128).intersection(ref.intersection(win.buffer(1)).buffer(-.105,quad_segs=128)) for l in('F.Cu','In3.Cu')}", "free={l:win.difference(obstacle(NET,l)).buffer(-.105,quad_segs=128).intersection(planes['In1.Cu' if l=='F.Cu' else 'In4.Cu'].intersection(win.buffer(1)).buffer(-.105,quad_segs=128)) for l in('F.Cu','In3.Cu')}")
# Replacing the layer string duplicates F in the six-layer enumeration;
# retain exact B annuli/aperture/SMD authority there.
s=s.replace("LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','F.Cu']", "LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']")
s=s.replace("layer in('F.Cu','F.Cu')", "layer in('F.Cu','B.Cu')")
a=s.index(' endpoint_options=[];elig=[]');z=s.index(" print('DIC-CS_IN3_ELIGIBILITY'",a)
s=s[:a]+''' endpoint_options=[];elig=[];nominees=[]
 for transport_index,transport in enumerate(K.pieces(free['In3.Cu'])):
  sideopts=[]
  for side in range(2):
   direct=term['In3.Cu'][side].buffer(-.05,quad_segs=128).intersection(transport);preferred=list(term['F.Cu'][side].centroid.coords)[0];opts=[{'at_mm':q['at_mm'],'new_signal':False,'F_attachment':None,'pair':None} for q in K.sites(direct,preferred,2)];bc=[]
   fa=term['F.Cu'][side].buffer(-.05,quad_segs=128).intersection(free['F.Cu'])
   for part in K.pieces(free['F.Cu']):
    att=fa.intersection(part)
    if att.is_empty:continue
    v=via[NET].intersection(part).intersection(transport).intersection(Point(term['F.Cu'][side].centroid).buffer(5,quad_segs=128))
    if v.is_empty:continue
    pairs=return_options(v);bc.append({'attachment_mm2':att.area,'via_region_mm2':v.area,'paired_options':len(pairs)})
    for pair in pairs[:6]:
     pa=nearest_points(att,Point(pair['signal']))[0];opts.append({'at_mm':pair['signal'],'new_signal':True,'F_attachment':[round(pa.x,6),round(pa.y,6)],'pair':pair})
   sideopts.append(opts)
   if opts or bc or not direct.is_empty:elig.append({'transport_component':transport_index,'side':side,'direct_actual_In3_attach_mm2':direct.area,'F_components':bc,'options_count':len(opts)})
  endpoint_options.append({'transport_component':transport_index,'side_options':sideopts})
  if any(not opts for opts in sideopts):continue
  for a,b in itertools.product(*sideopts):
   new=[o['at_mm'] for o in(a,b) if o['new_signal']]+[o['pair']['return'] for o in(a,b) if o['new_signal'] and o['pair']['return_new']]
   if any(math.dist(x,y)<.81 for x,y in itertools.combinations(new,2)):continue
   nominees.append({'transport_component':transport_index,'endpoints':[a,b],'score':sum(o['new_signal'] for o in(a,b))*100+math.dist(a['at_mm'],b['at_mm'])})
'''+s[z:]
s=s.replace("gap=body.difference(ref);row['paths'].append({'layer':layer", "selected_reference_layer='In1.Cu' if layer=='F.Cu' else 'In4.Cu';gap=body.difference(planes[selected_reference_layer]);row['paths'].append({'source_reference_layer':selected_reference_layer,'layer':layer")
s=s.replace("'full_body_actual_In4_source_reference_gap_mm2'", "'full_body_actual_adjacent_source_reference_gap_mm2'")
dst=H/'construct_DIC_CS_continuous_F_In3_F_r96.py';assert not dst.exists();dst.write_text(s);compile(s,str(dst),'exec');out=H/'prepare-DIC-CS-continuous-r96.json';assert not out.exists();out.write_text(json.dumps({'source':str(src),'source_sha256':hashlib.sha256(b).hexdigest(),'derived':str(dst),'derived_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'delta':'DIC CS ordinary current groups; F uses real In1, In3 real In4; intersect continuous F/all6-via site region per In3 transport component before paired choices; max F/In3/F3segments; all6 F/B SMD/drill/ordinary masks retained.'},indent=1)+'\n');print(dst)
