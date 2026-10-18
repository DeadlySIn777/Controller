from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;p=H/'construct_AO1_old_COM_barrel_owned_stub_detour_escape_r690.generated.py';s=p.read_text()
changes=[('controlled-detour-escape-r690','controlled-detour-separate-return-escape-r694'),('R690_','R694_'),('COM_obs=[];stub_obs=[]','COM_obs=[];RET_obs=[];stub_obs=[]'),("COM_obs.append(K.Z.bounded_buffer(shape,req+.3+inside))","COM_obs.append(K.Z.bounded_buffer(shape,req+.3+inside));RET_obs.append(K.Z.bounded_buffer(shape,req+.25+inside))"),("COM_obs.append(K.Z.bounded_buffer(sh.intersection(clip),req+.3))","COM_obs.append(K.Z.bounded_buffer(sh.intersection(clip),req+.3));RET_obs.append(K.Z.bounded_buffer(sh.intersection(clip),req+.25))"),("COM_obs.append(K.Z.bounded_buffer(sh,.15+.275));","COM_obs.append(K.Z.bounded_buffer(sh,.15+.275));RET_obs.append(K.Z.bounded_buffer(sh,.1+.275));"),("COM_obs.append(K.Z.bounded_buffer(sh,.15+.275+.005));","COM_obs.append(K.Z.bounded_buffer(sh,.15+.275+.005));RET_obs.append(K.Z.bounded_buffer(sh,.1+.275+.005));"),("COM_obs.append(K.Z.bounded_buffer(sh,.325));SG_obs", "COM_obs.append(K.Z.bounded_buffer(sh,.325));RET_obs.append(K.Z.bounded_buffer(sh,.275));SG_obs"),("if set(rule['layers']).intersection(K.LAYERS):va.append(K.Z.bounded_buffer(sh,.325 if net==COM else .275))", "if set(rule['layers']).intersection(K.LAYERS):\n     va.append(K.Z.bounded_buffer(sh,.325 if net==COM else .275))\n     if net==COM:RET_obs.append(K.Z.bounded_buffer(sh,.275))"),("COMfree=win.difference(unary_union(COM_obs));SGfree=", "COMfree=win.difference(unary_union(COM_obs));RETfree=win.difference(unary_union(RET_obs));SGfree=")]
for a,b in changes:
 assert a in s,a;s=s.replace(a,b)
marker=" (OUT/'bounded-source-COM-SG-stub-axis-regions.pkl')"
assert marker in s
s=s.replace(marker," RETsource=RETfree.intersection(refs['In1.Cu']).intersection(refs['In4.Cu']);print('R694_RET_REGION',RETsource.area,'distance_to_SG',RETsource.distance(SGsites),flush=True)\n"+marker)
s=s.replace("'SOURCEcenters':sourcecenters}","'SOURCEcenters':sourcecenters,'RETsource':RETsource}")
start=s.index("  sg=SGsites.intersection(pt.buffer(.999,");end=s.index("   face=",start)
replacement="""  f1=Ffree.difference(K.Z.bounded_buffer(pt,.3+.175+.1));faces=[s for s in parts(f1)if s.covers(Point(start))];sourceSG=SGsites.difference(pt.buffer(.815,quad_segs=128)).intersection(unary_union(faces));opts=sites(sourceSG,[376.67,127.71],6);trial={'old_COM_move_mm':at,'offset_um':[dx*25,dy*25],'actual_BEFORE_both_inner_SOURCE_annulus_contact_mm2':contact,'source_SG_options':opts};trials.append(trial)
  for pos in opts:
   ring=Point(pos).buffer(.999,quad_segs=128).difference(Point(pos).buffer(.901,quad_segs=128));returnOptions=sites(RETsource.intersection(ring).difference(pt.buffer(.815,quad_segs=128)),[pos[0]+.95,pos[1]],8)
   if not returnOptions:continue
   groundReturn=returnOptions[0]
   if not all(Point(groundReturn).buffer(.25,quad_segs=128).difference(Point(groundReturn).buffer(.1,quad_segs=128)).intersection(refs[ly]).area>.005 for ly in refs):continue
   bface=next((s for s in Bfaces if s.covers(pt)),None)
   if bface is None:continue
   bpath,bsearch=T.route(bface,tuple(stub['a']),tuple(at));bpath=[[round(x,6),round(y,6)]for x,y in bpath]
   if len(bpath)<2 or not bface.covers(LineString(bpath)):continue
   facesWithReturn=[s for s in parts(f1.difference(K.Z.bounded_buffer(Point(groundReturn),.25+.175+.1)))if s.covers(Point(start))]
   faces=facesWithReturn
"""
s=s[:start]+replacement+s[end:]
s=s.replace("'source_pair_distance_mm':math.dist(at,pos)","'source_pair_distance_mm':math.dist(groundReturn,pos),'NEW_source_return_via_mm':groundReturn,'NEW_source_return_via_d_drill_mm':[.5,.2]")
s=s.replace("offsets=sorted(((dx,dy)for dx in range(-50,51)for dy in range(-50,51)","offsets=sorted(((dx,dy)for dx in range(-120,121)for dy in range(-120,121)")
s=s.replace("'source_signal_candidate_is_entry_only_not_a_complete_route':True","'source_signal_candidate_is_entry_only_not_a_complete_route':True,'ordinary_source_return_is_distinct_NEW_via_NOT_old_moved_barrel':True")
out=H/'construct_AO1_old_COM_barrel_separate_ordinary_return_r694.generated.py';assert not out.exists();out.write_text(s)
(H/'derive-AO1-owned-COM-separate-return-r694.json').write_text(json.dumps({'source':str(p.resolve()),'source_SHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'generated':str(out.resolve()),'generated_SHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'scope':'moved .60/.30 ground barrel preserves own B stub; test separate ordinary .50/.20 SOURCE-rooted ground return within .90–1.00mm of source SG, all foreign fills held hard'},indent=1)+'\n')
