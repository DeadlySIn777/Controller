"""Separate exact Cu versus reference disconnection, without another route sweep."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
src=H/'construct_DI15_DI13_native_barrel_bound_r156.py';raw=src.read_bytes();s=raw.decode().replace('\r\n','\n').replace('r156','r160').replace('R156','R160')
old="return physical.intersection(augmented.buffer(-.105,quad_segs=128)),oldviawitness,physical.covers"
new="return physical,augmented.buffer(-.105,quad_segs=128),oldviawitness,physical.covers"
assert old in s;s=s.replace(old,new)
s=s.replace('free,oldviawitness,startphys,endphys,startref,endref=trackfree','free,reference_centres,oldviawitness,startphys,endphys,startref,endref=trackfree')
old="if not parts:continue\n  route,search=T.route"
new="""refsa=startmetal.buffer(-.04,quad_segs=128).intersection(reference_centres).intersection(win);refea=endmetal.buffer(-.04,quad_segs=128).intersection(reference_centres).intersection(win);refparts=[q for q in K.pieces(reference_centres) if q.intersects(refsa) and q.intersects(refea)];row['physical_only_common_components']=len(parts);row['reference_only_common_components']=len(refparts);row['reference_only_source_attachment_mm2']=refsa.area;row['reference_only_target_attachment_mm2']=refea.area;row['no_original_or_positive_Cu_removed_for_diagnosis']=True;row['physical_component_bodies_WKB_sha256']=[C.sha(q.wkb) for q in parts];row['reference_component_WKB_sha256']=[C.sha(q.wkb) for q in refparts];print(json.dumps({'phase':'exact_DI13_disconnection_authority','physical_common':len(parts),'reference_common':len(refparts),'physical_source_area':sourceattach.area,'physical_target_area':targetattach.area,'referenced_source_area':refsa.area,'referenced_target_area':refea.area}),flush=True)
  if refparts:
   ra=K.sites(refsa.intersection(refparts[0]),[123.95,102.15],1)[0]['at_mm'];rb=K.sites(refea.intersection(refparts[0]),[130.549999,109.65],1)[0]['at_mm'];rpath,rsearch=T.route(refparts[0],tuple(ra),tuple(rb));rpath=[[round(x,6),round(y,6)] for x,y in rpath];rbody=unary_union([A.shape({'kind':'segment','a':a,'b':b,'w':.2}) for a,b in zip(rpath,rpath[1:])]);records,trees=F.build({**h,'zones':[]});blockers=[]
   for i in trees['In3.Cu'].query(rbody.buffer(.65),predicate='intersects'):
    q=records['In3.Cu'][int(i)];n=L.norm(q['net'])
    if n==BLOCK:continue
    gap=.15 if h['domains_normalized'].get(n)==h['domains_normalized'][BLOCK] else .6;dist=q['shape'].distance(rbody)
    if dist<gap+.030:blockers.append({'kind':q['kind'],'UUID':q['uuid'],'raw_net':q['net'],'distance_body_to_exact_Cu_mm':dist,'guarded_requirement_mm':gap+.030,'exact_obstacle_WKB_sha256':C.sha(q['shape'].wkb)})
   for q in cur['zones']+[z]:
    n=L.norm(q['net'])
    if q['layer']!='In3.Cu' or n==BLOCK:continue
    gap=max(float(q.get('clearance_mm',.15)),.15 if h['domains_normalized'].get(n)==h['domains_normalized'][BLOCK] else .6)+.030;dist=q['shape'].distance(rbody)
    if dist<gap:blockers.append({'kind':'positive_plane_HARD','UUID':q['uuid'],'raw_net':q['net'],'distance_body_to_exact_Cu_mm':dist,'guarded_requirement_mm':gap,'exact_obstacle_WKB_sha256':C.sha(q['shape'].wkb)})
   row['reference_only_path_diagnostic']={'points_mm':rpath,'search':rsearch,'length_mm':LineString(rpath).length,'body_WKB_sha256':C.sha(rbody.wkb),'actual_full_body_reference_gap_mm2':rbody.difference(reference_centres.buffer(.105,quad_segs=128)).area,'exact_blockers_to_construct':blockers,'path_nomination_only':True,'physical_clearance_PASS':False}
  break
  route,search=T.route"""
assert old in s;s=s.replace(old,new)
s=s.replace("'max_signal_layer_segments':3","'max_signal_layer_segments':3,'diagnostic_only_constructor_disabled':True")
dst=H/'diagnose_DI13_exact_reference_vs_copper_wall_r160.py';assert not dst.exists();dst.write_text(s,newline='\n');out=H/'prepare-DI13-exact-reference-wall-diagnostic-r160.json';assert not out.exists();out.write_text(json.dumps({'source_file':str(src),'source_sha256':sha(raw),'derived_file':str(dst),'derived_sha256':sha(dst.read_bytes()),'delta':'No new search-bound/grid/mask relaxation: use exact R156 native barrel-bound source/target components and legitimate own scope, then independently count physical-only versus reference-only continuous components. If actual reference permits a path, name exact serialized Cu/positive-plane blockers for smallest coupled rework. Candidate constructor disabled; no board or acceptance.'},indent=1)+'\n');print(sha(dst.read_bytes()))
