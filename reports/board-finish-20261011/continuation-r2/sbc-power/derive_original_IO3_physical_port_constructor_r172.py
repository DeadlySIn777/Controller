"""Preserve R171 and derive same-layer actual fill ports before via ports."""
from pathlib import Path
import ast,hashlib,json
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
s=(P/'construct_original_IO3_existing_annulus_bridges_r171.py').read_text()
s=s.replace('original-IO3-existing-annulus-bridges-r171','original-IO3-physical-port-bridges-r172').replace('controller/original-IO3-existing-annulus-r171/','controller/original-IO3-physical-port-r172/')
old="  options.sort(key=lambda r:r[0]);options=options[:40];answer=None"
new="""  bylayer={l:[] for l in ('In2.Cu','In3.Cu','In1.Cu','In4.Cu')}
  for option in sorted(options,key=lambda r:r[0]):
   if option[1] in bylayer and len(bylayer[option[1]])<3:bylayer[option[1]].append(option)
  options=[]
  for layer in ('In2.Cu','In3.Cu','In1.Cu','In4.Cu'):
   target=unary_union([s for s,j in zip(parts[layer],assign[layer]) if j==gi]).difference(ownholes)
   if not target.is_empty and not source[layer].is_empty:
    aa,bb=nearest_points(target,source[layer]);port={'uuid':'actual-original-IO3-retained-group-'+str(original_group)+'/'+layer,'x':aa.x,'y':aa.y,'actual_filled_port':True}
    options.append((aa.distance(bb),layer,port,target,list(bb.coords[0])))
  for rank in range(3):
   for layer in ('In2.Cu','In3.Cu','In1.Cu','In4.Cu'):
    if len(bylayer[layer])>rank:options.append(bylayer[layer][rank])
  answer=None"""
assert old in s;s=s.replace(old,new)
s=s.replace("    free=set_precision(outline.intersection(window).difference(unary_union(obs)),1e-6)","    free=set_precision(outline.intersection(window).difference(unary_union(obs)),1e-6);print('IO3_PHYSICAL_PORT_FREE',original_group,layer,margin,'target',free.intersection(ann).area,'source',free.intersection(source[layer]).area,flush=True)")
s=s.replace("'existing_via_UUID':v['uuid']","'actual_target_port_UUID_or_fill_group':v['uuid'],'port_is_existing_filled_Cu':bool(v.get('actual_filled_port')),'target_physical_WKB_SHA256':digest(ann)")
s=s.replace("'annulus_overlap_mm2':q['shape'].intersection(ann).area","'actual_target_Cu_overlap_mm2':q['shape'].intersection(ann).area")
s=s.replace('Existing-annulus','Existing physical Cu').replace('existing-annulus source bridge','actual-physical-Cu source bridge')
ast.parse(s);out=P/'construct_original_IO3_physical_port_bridges_r172.py';assert not out.exists();out.write_text(s)
(P/'original-IO3-physical-port-constructor-derivation-r172.json').write_text(json.dumps({'preserved_original_file':str((P/'construct_original_IO3_existing_annulus_bridges_r171.py').resolve()),'preserved_original_sha256':sha(P/'construct_original_IO3_existing_annulus_bridges_r171.py'),'new_file':str(out.resolve()),'new_sha256':sha(out),'delta':'Exact actual same-layer retained filled Cu ports precede round-robin bounded existing-via options; all frozen native/new hard bodies and source/reference guards unchanged; no original native outline or copper mutations','original_run_deliberately_stopped_before_accepted_geometry':True},indent=1)+'\n')
